---
name: niceplots
description: Make every Python/matplotlib figure in MDO Lab niceplots style and the lab's figure rules (all text in LaTeX Computer Modern, no label ever touching a line or other text, direct line labels or frameless legend below, horizontal y labels, math-symbol labels, flush colour bars with end ticks, sequential vs diverging colour maps, aligned negative numbers, no needless lines). Use whenever creating, editing, restyling or reviewing any plot, graph, chart, contour, colour bar, legend or paper figure in Python.
---

# Plotting with niceplots

All figures use [niceplots](https://github.com/mdolab/niceplots) (MDO Lab) for the
style, plus `nicefig.py` (this folder) for the rules niceplots does not enforce.
Full niceplots API: `reference.md`. Worked example: `examples/demo.py`.

## Setup (every script)

The helpers are `nicefig.py` in this skill's folder (the folder this SKILL.md is in; when the
skill is shared through a repository it is `.claude/skills/niceplots/` at the repository root).
Scripts import a **copy that sits next to them**, so they run on any machine, cluster or CI
without the skill installed:

1. Copy this folder's `nicefig.py` into the script's folder (once per folder; copy it again after
   the skill is updated so the copies stay current).
2. Start the script with:

```python
import os, sys
import matplotlib.pyplot as plt
import numpy as np
import niceplots
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # the nicefig.py copy next to this script
import nicefig as nf

colors = nf.setup()          # niceplots doumont-light + our rcParams + LaTeX text; dict "Blue", "Red", "Axis", ...
```

- Python environment: needs `niceplots`, `matplotlib`, `scipy` and `numpy`. If `import niceplots`
  fails, run `pip install niceplots` in that environment. If the user has a known plotting
  environment (in their notes or memory), use it; if an environment fails to import scipy or
  niceplots, try another one rather than repairing the user's simulation environment.
- Scripts that need a simulation code (e.g. ADflow) should save their data (npz/csv) and
  plot in a separate script in the plotting environment.
- Use `nf.setup("doumont-dark")` / `"james-light"` / `"james-dark"` only if asked.

## The rules

### 0. Everything in LaTeX
- `nf.setup()` sets **all** text (labels, ticks, legends, annotations, colour-bar labels) in
  LaTeX's Computer Modern, matching papers set in Computer Modern / Latin Modern (lmodern),
  such as the AIAA journal template:
  - if a LaTeX install with `latex` and `dvipng` is on the PATH, matplotlib typesets every
    string with real LaTeX (`text.usetex`, lmodern + amsmath);
  - otherwise (the case on this Mac) text uses `cmr10`, TeX's own Computer Modern Roman
    (CMU Serif fills any missing glyph), maths uses mathtext's Computer Modern with LaTeX's
    rules (italic letters, upright digits), and tick numbers are set in maths so negatives
    get a true minus sign. No install needed.
- Write every symbol, variable and unit exponent in maths: `"$x$ (mm)"`, `r"$\theta_A = 31^\circ 36'$"`,
  `r"$A_E = 875$ mm$^2$"`, `r"$\sigma$ (1/s)"`, `r"$\mathrm{TR}_\mathrm{eff}$"`. Use `\mathrm{}` for
  multi-letter names inside maths (TR, eff, max). Plain words stay plain text.
- **As in real LaTeX, `< > { } _ | "` and backslash cannot be typed as plain text** (the
  Computer Modern text font shows `<x>` as `¡x¿`). Put them in maths: `"$<$"`, `r"$\{a\}$"`,
  `"$a_b$"`. `nf.save` prints `nicefig: TEXT ...` for any such string; fix every one.
- Write strings so they also compile under real LaTeX: escape `%` as `\%`, `&` as `\&`, `#` as `\#`,
  `_` outside maths as `\_`; use `--` for ranges; no Unicode symbols (write `$\sim$`, `$\pm$`,
  `$\times$`, `$^\circ$`, not ~ ± × °).
- `nf.setup(latex=False)` returns to the niceplots sans-serif look only if asked.

### 1. Legends
- **Lines that do not cross:** no legend. Put each name at the end of its line,
  in the line's colour (`niceplots.label_line_ends`). Leave room on the right.
- **Lines that cross, or too many to label cleanly:** a legend **without a box**,
  placed **below the plot** (or otherwise outside it), in rows, never a tall
  10-entry column on the right.
- `nf.smart_legend(ax)` chooses automatically. Call it after setting the axis limits.
  Override with `force="ends"` or `force="below"`.
- A legend shared by several panels goes under them with `nf.legend_below(fig, handles=..., ncol=...)`,
  called last: it measures the final layout, so the x label can never run into the legend.
- A short label written next to a curve inside the plot (`ax.annotate`, coloured
  like the line) is also fine. Never use a boxed legend.

### 2. Labels and text
- **Rotation 0 everywhere.** The y-axis label reads horizontally, left of the tick labels:
  `nf.ylabel(ax, "$C_p$")`. `nf.finish(ax)` turns an existing rotated label horizontal
  and keeps its text. Tick labels are never rotated either.
- **Symbols in math mode.** Coordinates and variables are symbols: `"$x$"`, `"$y$"`,
  `"$t$ (ms)"`, `"$p/p_0$"`, `r"$\sigma$ (1/s)"`, `"$x_1$"`. Never plain `x`, `p/p0` or `sigma`.
  Units stay outside the `$...$`, in parentheses.
- **Negative numbers aligned.** Call `nf.align_negative_ticks(ax)` (and on
  `cb.ax` with `which="y"` for colour bars) as the **last** step before saving, so
  the digits of `-0.5` and `0.5` line up and minus signs never touch tick marks.

### 3. Remove unnecessary lines
- No grid, no top/right spines, no box around the axes. Use outward Doumont spines:
  `nf.finish(ax)` (calls `niceplots.adjust_spines`).
- No full-height vertical (or horizontal) reference lines. If a marker is needed,
  draw it from the axis **only up to the data**: `nf.data_vline(ax, x0, y_at_x0)`,
  or replace it with an annotation or point on the curve.
- Ticks only on the left and bottom. **Never ticks along the top.**
- Stacked plots with the same x: only the bottom plot has x ticks and the x label:
  `nf.stack_shared_x(axes, xlabel="$t$ (ms)")`.

### 4. Colour maps
- **Data of one sign** (Mach, density, |u|): sequential map. Default
  `niceplots.parula_map`.
- **Signed data around a reference** (perturbations, eigenmodes, sensitivities, Δp):
  diverging map built from two sequential ramps in opposite directions meeting at
  white, symmetric about the reference so white = 0.
- `cmap, norm = nf.color_scale(data, center=0.0)` picks the right one.
- Line colours come from the niceplots cycle (`colors["Blue"]`, ...). Don't use rainbow/jet.

### 5. Colour bars
- `cb = nf.colorbar(ax, mappable, label=r"$\Delta p$")`:
  - same height as the plot, so **its top is flush with the top of the axes**;
  - **ticks run from the bottom-most to the top-most value** of the bar;
  - **pointed ("diamond") ends** by default. For `contourf`, pass `extend="both"` to
    `contourf` itself;
  - label horizontal, above the bar; no outline.
- Pick contour levels with round ends, e.g. `levels=np.linspace(-1.5, 1.5, 31)`,
  so the end ticks are round numbers.

### 6. No label touches anything
- **No text may touch a line, a marker, another text, a tick label or an axis label.** This
  includes dashed guide lines and leader lines of other labels. (Text written *inside* a filled
  shape, such as "cowl" on the cowl, is fine: fills are not checked.)
- **Place every free label with `nf.place_label(ax, text, xy, ...)`**, never with a fixed
  `xytext` offset. It tries 8 directions at growing distances and keeps the first spot that
  touches nothing. Call it **after** limits, aspect and all data are drawn.
  - `dirs=[(1, 0), (0, 1), ...]` sets which directions to try first (e.g. keep a tap name
    in the open duct with `dirs=[(0, -1), (-1, -1), (1, -1)]`).
  - Where several lines meet (e.g. a cowl lip), pass `leader=True` with larger `radii`
    and a list of candidate anchor points along the line, so the label moves into open space
    with a thin leader line: `nf.place_label(ax, lab, [p_mid, p_35, p_65], radii=(18, 28, 40), leader=True)`.
- `nf.place_label` freezes the layout (`nf.freeze_layout`) so labels checked now stay clear
  at save time.
- `nf.save` runs `nf.find_overlaps(fig)` and prints `nicefig: OVERLAP ...` for every collision,
  including a legend entry touching an axis label or tick label.
  **A figure is not finished while any OVERLAP line prints.** Fix it with `place_label`, never
  by ignoring it. Only a text deliberately drawn on data may be exempted with `nf.allow_overlap(text)`.

### 7. Saving
- `nf.save(fig, "path/name")` checks overlaps, then writes `name.pdf` + `name.png` (300 dpi)
  with a tight box, so line-end labels and colour bars are not cut off.
  `check="strict"` refuses to save while overlaps remain.

## Workflow

1. `nf.setup()`, then build the figure with plain matplotlib (`plt.subplots`, `ax.plot`, ...).
   Pass `clip_on=False` on lines that touch the axis limits.
2. Labels: `ax.set_xlabel("$x$ (mm)")`, `nf.ylabel(ax, "$C_p$")`, maths for all symbols (rule 0).
3. Set limits and ticks. Prefer ticks at the data ends (`ax.set_xticks([...])`).
4. `nf.finish(ax)` on every axes (or `nf.stack_shared_x(axes)` for stacks).
5. `nf.smart_legend(ax)` / `nf.colorbar(...)`.
6. Free labels and annotations with `nf.place_label(...)` (rule 6).
7. `nf.align_negative_ticks(ax)` last, then `nf.save(...)`. **Read its output: zero OVERLAP lines.**
8. **Look at the PNG** (Read it) and check it against the checklist before showing it to the user.

## Checklist before handing over a figure
- [ ] all text in LaTeX Computer Modern; every symbol in `$...$` (letters italic, digits upright)
- [ ] `nf.save` printed no OVERLAP and no TEXT line, and on the PNG no text touches a line, marker or text
- [ ] No boxed legend; labels at line ends or legend below/outside
- [ ] y label horizontal; nothing rotated
- [ ] no grid, no top/right spines, no top ticks, no full-height guide lines
- [ ] stacked plots: x ticks only on the bottom
- [ ] sequential map for one-signed data, symmetric diverging map for signed data
- [ ] colour bar flush with the plot top, end ticks at both ends, pointed ends
- [ ] negative numbers aligned with positive ones
- [ ] nothing cut off at the figure edge
