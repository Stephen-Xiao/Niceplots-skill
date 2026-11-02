"""
nicefig: figure rules on top of MDO Lab's niceplots (the niceplots Claude skill).

niceplots supplies the style (fonts, colours, no top/right spines, no legend
frame) and helpers such as adjust_spines and label_line_ends. This module adds
the rules niceplots does not enforce on its own:

    setup()                 apply the niceplots style + our rcParams
    ylabel()                horizontal y label (rotation 0), left of the tick labels
    smart_legend()          line-end labels if lines are separate, else a frameless legend below
    color_scale()           sequential cmap for one-signed data, diverging for signed data
    colorbar()              colour bar flush with the axes, ticks at both ends, pointed ends
    stack_shared_x()        stacked plots: x ticks only on the bottom plot, never on top
    data_vline()            vertical reference line that stops at the curve
    align_negative_ticks()  shift "-" labels so their digits line up with positive ones
    finish()                apply the per-axes rules in one call
    legend_below()          figure legend under the lowest x label, measured after layout
    place_label()           put a label next to a point at the first spot that touches nothing
    find_overlaps()         list every text touching a line, marker or other text
    allow_overlap()         mark a text that is meant to sit on data (e.g. inside a filled shape)
    save()                  check overlaps, then save pdf + png with a tight bounding box

Usage::

    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # a nicefig.py copy next to the script
    import nicefig as nf

    colors = nf.setup()
    fig, ax = plt.subplots()
    ...
    nf.finish(ax)
    nf.smart_legend(ax)
    nf.save(fig, "figures/my_plot")
"""

import itertools

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation

import niceplots

# Line-end labels closer than this many text heights are treated as colliding
_LABEL_GAP = 1.1


def setup(style="doumont-light", latex=True):
    """Apply the niceplots style plus our defaults and return the colour dict.

    latex=True (default) sets every piece of text in LaTeX's Computer Modern, matching
    a paper set in Computer Modern / Latin Modern:
    - if `latex` and `dvipng` are installed, matplotlib typesets all text with real
      LaTeX (text.usetex, lmodern + amsmath);
    - otherwise text uses CMU Serif (Computer Modern, bundled with niceplots) and maths
      uses mathtext's Computer Modern ("cm"), which needs no LaTeX install.
    latex=False keeps the niceplots sans-serif look.

    Returns
    -------
    dict
        niceplots.get_colors(): names ("Blue", "Red", ...) -> hex, plus "Axis", "Text", ...
    """
    plt.style.use(niceplots.get_style(style))
    plt.rcParams["axes.grid"] = False
    plt.rcParams["xtick.top"] = False
    plt.rcParams["ytick.right"] = False
    plt.rcParams["legend.frameon"] = False
    if latex:
        plt.rcParams["axes.labelweight"] = "normal"
        plt.rcParams["axes.unicode_minus"] = False   # "-" inside maths is already a true minus in Computer Modern
        if usetex_available():
            plt.rcParams["text.usetex"] = True
            plt.rcParams["font.family"] = "serif"
            plt.rcParams["text.latex.preamble"] = r"\usepackage[T1]{fontenc}\usepackage{lmodern}\usepackage{amsmath}"
        else:
            plt.rcParams["font.family"] = "serif"
            # cmr10 = TeX's own Computer Modern Roman; with use_mathtext it gives tick labels a true minus.
            # CMU Serif fills in any glyph cmr10 lacks.
            plt.rcParams["font.serif"] = ["cmr10", "CMU Serif"]
            plt.rcParams["mathtext.fontset"] = "cm"
            plt.rcParams["axes.formatter.use_mathtext"] = True   # tick numbers in maths: CM digits and a real minus
            plt.rcParams["mathtext.default"] = "normal"   # LaTeX math: italic letters, upright digits
    return niceplots.get_colors()


def usetex_available():
    """True if a LaTeX install that matplotlib's text.usetex can drive is on the PATH."""
    import shutil

    return all(shutil.which(exe) for exe in ("latex", "dvipng"))


def ylabel(ax, text, **kwargs):
    """Set a y label that reads horizontally (rotation 0), placed left of the tick labels."""
    ax.set_ylabel(text, rotation=0, ha="right", va="center", **kwargs)


def _fix_ylabel_rotation(ax):
    """Keep the existing y-label text but make it horizontal."""
    lab = ax.yaxis.label
    if lab.get_text():
        lab.set_rotation(0)
        lab.set_horizontalalignment("right")
        lab.set_verticalalignment("center")


def _labelled_lines(ax, lines=None):
    lines = ax.get_lines() if lines is None else lines
    return [line for line in lines if not line.get_label().startswith("_")]


def _lines_cross(a, b):
    """True if two lines intersect (or cannot be compared safely)."""
    xa, ya = np.asarray(a.get_xdata(), float), np.asarray(a.get_ydata(), float)
    xb, yb = np.asarray(b.get_xdata(), float), np.asarray(b.get_ydata(), float)
    # Non-monotonic x (loops, spirals) cannot be compared by interpolation: assume crossing
    for x in (xa, xb):
        if x.size < 2 or not (np.all(np.diff(x) > 0) or np.all(np.diff(x) < 0)):
            return True
    if xa[0] > xa[-1]:
        xa, ya = xa[::-1], ya[::-1]
    if xb[0] > xb[-1]:
        xb, yb = xb[::-1], yb[::-1]
    lo, hi = max(xa[0], xb[0]), min(xa[-1], xb[-1])
    if lo >= hi:
        return False
    x = np.union1d(xa[(xa >= lo) & (xa <= hi)], xb[(xb >= lo) & (xb <= hi)])
    d = np.interp(x, xa, ya) - np.interp(x, xb, yb)
    # Touching (e.g. a shared start point) is not crossing; only a change of side is
    d = d[np.isfinite(d) & (d != 0)]
    return d.size > 0 and np.any(np.sign(d) != np.sign(d[0]))


def _ends_collide(ax, annotations):
    """True if any two line-end labels sit closer than _LABEL_GAP text heights."""
    if len(annotations) < 2:
        return False
    ax.figure.canvas.draw()
    boxes = [ann.get_window_extent() for ann in annotations]
    ys = sorted(box.y0 for box in boxes)
    height = max(box.height for box in boxes)
    return any(b - a < _LABEL_GAP * height for a, b in zip(ys, ys[1:]))


def smart_legend(ax, lines=None, ncol=None, force=None):
    """Label lines directly when they are separate, otherwise use a legend below the plot.

    Rule: separate lines -> name at the end of each line, in the line's colour
    (niceplots.label_line_ends). Crossing lines, or ends too close to label
    cleanly -> frameless legend centred below the axes, never boxed, never a
    tall column on the right.

    Call this AFTER setting axis limits.

    Parameters
    ----------
    force : {None, "ends", "below"}
        Override the automatic choice.

    Returns
    -------
    list of annotations, or the Legend
    """
    lines = _labelled_lines(ax, lines)
    if not lines:
        return None

    use_ends = force == "ends"
    if force is None:
        use_ends = not any(_lines_cross(a, b) for a, b in itertools.combinations(lines, 2))

    if use_ends:
        annotations = niceplots.label_line_ends(ax, lines)
        if force == "ends" or not _ends_collide(ax, annotations):
            return annotations
        for ann in annotations:
            ann.remove()

    # Below the x label: anchor to the bottom of everything drawn on the axes
    fig = ax.figure
    fig.canvas.draw()
    bottom = ax.get_tightbbox().transformed(ax.transAxes.inverted()).y0
    ncol = ncol or (len(lines) if len(lines) <= 5 else int(np.ceil(len(lines) / 2)))
    return ax.legend(
        handles=lines,
        loc="upper center",
        bbox_to_anchor=(0.5, bottom - 0.02),
        ncol=ncol,
        frameon=False,
        handlelength=1.2,
        handletextpad=0.4,
        columnspacing=1.0,
    )


def diverging_cmap(low="Blue", high="Red", style=None):
    """Two sequential ramps meeting at white: niceplots Blue <- white -> niceplots Red."""
    colors = niceplots.get_colors(style)
    return mcolors.LinearSegmentedColormap.from_list(
        "nice_diverging", [colors[low][:7], "#ffffff", colors[high][:7]]
    )


def color_scale(data, center=0.0, sequential=None, diverging=None):
    """Pick the colour map and normalisation for a field.

    - Data on both sides of `center` (e.g. pressure perturbation, eigenmode,
      sensitivity): diverging map, symmetric about `center` so white = center.
    - One-signed data (e.g. Mach number, density): sequential map (parula).

    Returns
    -------
    cmap, norm
    """
    data = np.asarray(data, float)
    lo, hi = np.nanmin(data), np.nanmax(data)
    if center is not None and lo < center < hi:
        half = max(hi - center, center - lo)
        cmap = diverging if diverging is not None else diverging_cmap()
        return cmap, mcolors.Normalize(center - half, center + half)
    cmap = sequential if sequential is not None else niceplots.parula_map
    return cmap, mcolors.Normalize(lo, hi)


def colorbar(ax, mappable, label=None, ticks=None, nticks=5, extend="both", width=0.04, pad=0.04, fmt=None):
    """Vertical colour bar exactly as tall as the axes, with ticks at both ends.

    - The bar spans the axes height, so its top is flush with the top of the plot
      (also when the axes use aspect="equal").
    - Ticks run from the bottom-most value (vmin) to the top-most value (vmax).
    - extend="both" gives the pointed (diamond-like) ends; pass extend="neither"
      for a plain rectangle. For contourf the ends come from the contour call
      itself: use ax.contourf(..., extend="both").
    - The label sits above the bar, horizontal.

    Save with bbox_inches="tight" (nf.save does) so the bar is not cropped.
    """
    fig = ax.figure
    cax = ax.inset_axes([1 + pad, 0, width, 1])
    cb = fig.colorbar(mappable, cax=cax, extend=extend, extendfrac=0.06)
    # The coloured bar's own range (contour levels can differ from norm.vmin/vmax)
    vmin, vmax = cb.ax.get_ylim()
    if ticks is None:
        ticks = np.linspace(vmin, vmax, nticks)
    cb.set_ticks(ticks)
    if fmt is not None:
        cb.ax.yaxis.set_major_formatter(fmt)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=4, which="both")
    cb.minorticks_off()
    if label:
        cb.ax.set_title(label, loc="left", fontsize=plt.rcParams["axes.labelsize"], pad=10)
    return cb


def stack_shared_x(axes, xlabel=None):
    """Vertically stacked plots sharing x: only the bottom plot carries x ticks/labels.

    No plot gets ticks along the top edge.
    """
    axes = list(np.ravel(axes))
    for i, ax in enumerate(axes):
        niceplots.adjust_spines(ax, outward=True)
        ax.tick_params(top=False, labeltop=False)
        if i < len(axes) - 1:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(bottom=False, labelbottom=False)
    if xlabel:
        axes[-1].set_xlabel(xlabel)
    axes[0].figure.align_ylabels(axes)
    return axes


def data_vline(ax, x, y_top, y_bottom=None, **kwargs):
    """Vertical marker that runs from the x axis up to the curve, not across the whole plot."""
    if y_bottom is None:
        y_bottom = ax.get_ylim()[0]
    kwargs.setdefault("color", niceplots.get_colors()["Axis"])
    kwargs.setdefault("lw", 1.0)
    kwargs.setdefault("ls", "--")
    return ax.vlines(x, y_bottom, y_top, **kwargs)


def allow_overlap(text):
    """Mark a text as intentionally drawn on top of data (e.g. a name written inside a filled shape)."""
    text._nf_allow_overlap = True
    return text


def _densify(verts, step=1.0):
    """Points every ~step pixels along a polyline given in display coordinates (NaNs break it)."""
    pts = []
    for a, b in zip(verts[:-1], verts[1:]):
        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
            continue
        n = max(int(np.hypot(*(b - a)) / step), 1)
        pts.append(a + np.linspace(0.0, 1.0, n + 1)[:, None] * (b - a))
    return np.concatenate(pts) if pts else np.empty((0, 2))


def _data_points(ax):
    """(name, points in display coords, hit radius in px) for every line and marker set in the axes."""
    from matplotlib.collections import LineCollection, PathCollection
    from matplotlib.contour import ContourSet

    out = []
    for line in ax.get_lines():
        if not line.get_visible() or len(line.get_xydata()) == 0:
            continue
        name = line.get_label() if not line.get_label().startswith("_") else "a line"
        if line.get_linestyle() not in ("None", "", " "):
            path = line.get_transform().transform_path(line.get_path())
            out.append((name, _densify(path.vertices), 0.5 * line.get_linewidth() * ax.figure.dpi / 72))
        if line.get_marker() not in (None, "None", "", " "):
            xy = line.get_transform().transform(line.get_xydata())
            out.append((name + " marker", xy, 0.5 * line.get_markersize() * ax.figure.dpi / 72))
    for coll in ax.collections:
        if not coll.get_visible() or isinstance(coll, ContourSet):
            continue
        if isinstance(coll, LineCollection):
            tr = coll.get_transform()
            pts = [_densify(tr.transform_path(p).vertices) for p in coll.get_paths()]
            if pts:
                out.append(("a line", np.concatenate(pts), 1.0))
        elif isinstance(coll, PathCollection) and len(coll.get_offsets()):
            xy = coll.get_offset_transform().transform(coll.get_offsets())
            size = np.sqrt(np.max(coll.get_sizes())) if len(coll.get_sizes()) else 6.0
            out.append(("a marker", xy, 0.5 * size * ax.figure.dpi / 72))
    return out


def _text_issues(ax, text, renderer, pad=2.0, data=None):
    """Everything a text touches in its axes: lines, markers, other texts, tick and axis labels."""
    if getattr(text, "_nf_allow_overlap", False) or not text.get_visible() or not text.get_text().strip():
        return []
    if hasattr(text, "update_positions"):   # an annotation's offset text is only placed at draw time
        text.update_positions(renderer)
    box = Text.get_window_extent(text, renderer).padded(pad)   # text only, not an annotation's leader line
    issues = []
    for name, pts, rad in data if data is not None else _data_points(ax):
        if len(pts) == 0:
            continue
        b = box.padded(rad)
        hit = (pts[:, 0] >= b.x0) & (pts[:, 0] <= b.x1) & (pts[:, 1] >= b.y0) & (pts[:, 1] <= b.y1)
        if hit.any():
            issues.append(name)
    others = [t for t in ax.texts if t is not text] + [ax.xaxis.label, ax.yaxis.label]
    others += ax.get_xticklabels() + ax.get_yticklabels()
    for t in others:
        if t.get_visible() and t.get_text().strip() and box.overlaps(Text.get_window_extent(t, renderer)):
            issues.append(f'text "{t.get_text()}"')
    return issues


def find_overlaps(fig, pad=2.0):
    """List every text (labels, annotations, line-end names) that touches a line, a marker or other text.

    Texts marked with allow_overlap() are skipped. Returns a list of strings; empty means clean.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    found = []
    for ax in fig.axes:
        data = _data_points(ax)
        for t in ax.texts:
            for what in _text_issues(ax, t, renderer, pad, data):
                found.append(f'"{t.get_text()}" touches {what}')
    # legends (axes or figure level) must clear every axis label, tick label and free text
    legends = [lg for lg in fig.legends] + [ax.get_legend() for ax in fig.axes if ax.get_legend() is not None]
    for lg in legends:
        # the drawn entries (texts and handles), not the legend's invisible border padding
        parts = [t.get_window_extent(renderer) for t in lg.get_texts()]
        parts += [h.get_window_extent(renderer) for h in lg.legend_handles if h is not None and hasattr(h, "get_window_extent")]
        parts = [b for b in parts if np.all(np.isfinite(b.get_points()))]   # scatter handles report an empty inf box
        for ax in fig.axes:
            texts = [ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels() + list(ax.texts)
            for t in texts:
                if not (t.get_visible() and t.get_text().strip()):
                    continue
                tb = Text.get_window_extent(t, renderer)
                if any(b.padded(pad).overlaps(tb) for b in parts):
                    found.append(f'legend touches "{t.get_text()}"')
                    break
    return found


def freeze_layout(fig):
    """Run the layout engine once and then fix the axes positions.

    With constrained layout every new label can resize the axes, which moves data that
    a label was placed against. Freezing keeps what place_label checked true at save time.
    """
    if fig.get_layout_engine() is not None:
        fig.canvas.draw()
        fig.set_layout_engine("none")


def legend_below(fig, handles=None, labels=None, gap=6, **kwargs):
    """Figure legend centred under all axes, just below the lowest x label / tick labels.

    Measured after the layout is final (it freezes it), so equal-aspect axes or late labels
    cannot push the x label into the legend. Frameless; kwargs go to fig.legend (ncol, ...).
    """
    freeze_layout(fig)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bottom = min(ax.get_tightbbox(renderer).y0 for ax in fig.axes if ax.get_visible())
    y = (bottom - gap * fig.dpi / 72) / fig.bbox.height
    kwargs.setdefault("frameon", False)
    if handles is not None:
        kwargs["handles"] = handles
    if labels is not None:
        kwargs["labels"] = labels
    return fig.legend(loc="upper center", bbox_to_anchor=(0.5, y), bbox_transform=fig.transFigure, **kwargs)


def place_label(ax, text, xy, radii=(6, 12, 20, 30, 45), dirs=None, leader=False, warn=True, **kwargs):
    """Annotate `text` near the data point `xy`, at the first position that touches nothing.

    Tries the directions `dirs` (unit steps such as (1, 0) = right, (-1, -1) = down-left;
    default: all 8, diagonals first) at increasing distances `radii` (points) and keeps
    the first clean spot, else the one with the fewest collisions (and warns).
    leader=True draws a thin line from the label to `xy`: use it with larger radii when the
    point sits where several lines meet, so the label can move into open space.
    `xy` may also be a list of candidate points (e.g. several points along the line being
    labelled); they are tried in order and the first clean spot wins.
    Call it AFTER limits, aspect and all data are set; it freezes the layout (freeze_layout).
    kwargs go to ax.annotate.
    """
    fig = ax.figure
    freeze_layout(fig)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    data = _data_points(ax)
    dirs = dirs or [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
    if leader:
        color = kwargs.get("color", plt.rcParams["text.color"])
        kwargs.setdefault("arrowprops", dict(arrowstyle="-", lw=0.6, color=color, shrinkA=2, shrinkB=1))
    anchors = [tuple(p) for p in np.atleast_2d(np.asarray(xy, dtype=float))]
    best, best_n = None, None
    for anchor, r, (dx, dy) in itertools.product(anchors, radii, dirs):
        ha = "left" if dx > 0 else "right" if dx < 0 else "center"
        va = "bottom" if dy > 0 else "top" if dy < 0 else "center"
        ann = ax.annotate(text, anchor, xytext=(dx * r, dy * r), textcoords="offset points", ha=ha, va=va, **kwargs)
        n = len(_text_issues(ax, ann, renderer, data=data))
        if n == 0:
            if best is not None:
                best.remove()
            return ann
        if best_n is None or n < best_n:
            if best is not None:
                best.remove()
            best, best_n = ann, n
        else:
            ann.remove()
    if warn:
        print(f'nicefig: no clean spot for "{text}"; placed with {best_n} collision(s), adjust by hand')
    return best


def _strip_math(s):
    """Tick text without $...$ and \\mathdefault{...} wrappers, e.g. '$\\mathdefault{-0.5}$' -> '-0.5'."""
    return s.replace("$", "").replace("\\mathdefault{", "").replace("{", "").replace("}", "")


def align_negative_ticks(ax, which="both"):
    """Shift negative tick labels so the digits line up with positive ones.

    Centre-aligned labels (x axis): negatives move left by half a minus-sign
    width, so the digits sit centred on the tick. Left-aligned labels (colour
    bars): positives move right by one minus width, so all digits share a
    column and the minus signs never touch the tick marks. Right-aligned
    labels already line up. Call LAST, after limits and ticks are final.
    """
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes = {"x": [ax.xaxis], "y": [ax.yaxis], "both": [ax.xaxis, ax.yaxis]}[which]
    for axis in axes:
        labels = [lab for lab in axis.get_ticklabels() if lab.get_text()]
        is_neg = [_strip_math(lab.get_text())[:1] in ("-", "−") for lab in labels]
        if not any(is_neg):
            continue
        minus = "−" if plt.rcParams["axes.unicode_minus"] else "-"
        probe = Text(0, 0, f"$\\mathdefault{{{minus}}}$" if "$" in labels[0].get_text() else minus)
        probe.set_fontproperties(labels[0].get_fontproperties())
        probe.set_figure(fig)
        width_in = probe.get_window_extent(renderer).width / fig.dpi
        for lab, neg in zip(labels, is_neg):
            ha = lab.get_horizontalalignment()
            if ha == "center" and neg:
                dx = -0.5 * width_in
            elif ha == "left" and not neg:
                dx = width_in
            else:
                continue
            lab.set_transform(lab.get_transform() + ScaledTranslation(dx, 0, fig.dpi_scale_trans))


def finish(ax, outward=True):
    """Per-axes clean-up: Doumont spines, no grid, no top/right ticks, horizontal y label."""
    niceplots.adjust_spines(ax, outward=outward)
    ax.grid(False)
    ax.tick_params(top=False, right=False, labeltop=False, labelright=False)
    _fix_ylabel_rotation(ax)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_rotation(0)


_OT1_BAD = set('<>{}_|"\\')


def lint_text(fig):
    """Flag characters that TeX's Computer Modern text font cannot show outside maths.

    As in real LaTeX, < > { } _ | " and backslash typed as plain text come out as other
    glyphs (e.g. "<x>" -> "¡x¿"); they must be written inside $...$ (e.g. "$<$", "$\\{a\\}$").
    """
    import re

    msgs = []
    for t in fig.findobj(Text):
        s = t.get_text()
        if not s or not t.get_visible():
            continue
        plain = re.sub(r"(?<!\\)\$.*?(?<!\\)\$", "", s)   # drop $...$ parts
        bad = sorted(set(plain) & _OT1_BAD)
        if bad:
            msgs.append(f'"{s}": put {" ".join(bad)} inside $...$')
    return msgs


def save(fig, path, formats=("pdf", "png"), dpi=300, check=True):
    """Save in several formats with a tight box (keeps line-end labels and colour bars).

    check=True runs find_overlaps first and prints every text that touches a line, a
    marker or other text; check="strict" refuses to save until they are fixed.
    """
    if check:
        for msg in lint_text(fig):
            print(f"nicefig: TEXT in {path}: {msg}")
        issues = find_overlaps(fig)
        for msg in issues:
            print(f"nicefig: OVERLAP in {path}: {msg}")
        if issues and check == "strict":
            raise RuntimeError(f"{len(issues)} overlapping label(s) in {path}; fix them or mark with nf.allow_overlap()")
    niceplots.save_figs(fig, path, list(formats), format_kwargs={"png": {"dpi": dpi}}, bbox_inches="tight")
