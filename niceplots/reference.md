# niceplots API (v2.6.3, github.com/mdolab/niceplots)

`import niceplots`. Importing also registers its bundled fonts (CMU Bright, Computer Modern, Prompt).

## Style and colours
| Function | What it does |
|---|---|
| `get_style(styleName="doumont-light")` | Path to a style for `plt.style.use(...)` or `plt.style.context(...)`. niceplots styles: `doumont-light`, `doumont-dark`, `james-light`, `james-dark`. Any matplotlib style name passes through. |
| `get_colors(styleName=None)` | Dict of the current style's colours: `Yellow, Blue, Red, Green, Maroon, Orange, Purple, Cyan, Black` (doumont) plus `Axis, Background, Text, Label`. |
| `get_colors_list(styleName=None)` | The colour cycle as a list. |
| `get_available_styles()` | Names of the niceplots styles. |
| `parula_map`, `parula_map_r` | MATLAB-like parula colormap (sequential), and reversed. |

doumont-light sets: no top/right spines, `axes.xmargin/ymargin = 0`, CMU Bright font size 18,
bold axis labels, small tick labels, frameless legends, line width 2, constrained layout,
`savefig.dpi 600`, grey (#5a5758) axes and text.

## Helpers
| Function | What it does |
|---|---|
| `adjust_spines(ax=None, spines=["left","bottom"], outward=True)` | Keep only the listed spines, shift them outward 12 pt (Doumont look), ticks only on those sides. |
| `label_line_ends(ax, lines=None, labels=None, colors=None, x_offset_pts=6, y_offset_pts=0, **kw)` | Text label at the right end of each line in its colour. Call after setting limits. Lines with labels starting `_` are skipped. |
| `draggable_legend(axis=None, color_on=True, **kw)` | Coloured labels you can drag in an interactive window. |
| `horiz_bar(labels, times, header, nd=1, size=[5,0.5], color=None, includeBottomTicks=False)` | Doumont-style horizontal dot-bar chart of positive numbers. Returns `fig, axes`. |
| `stacked_plots(xlabel, xdata, data_dict_list, figsize=(12,10), outward=True, filename="stacks.png", xticks=None, cushion=0.1, colors=None, lines_only=False, line_scaler=1.0, xlim=None, dpi=200)` | Stack of plots sharing x with horizontal y labels; **saves the file itself**. `data_dict_list`: `{ylabel: ydata}` or `{ylabel: {"data":..., "ticks"/"limits":...}}`, or a list of such dicts for several series. |
| `plot_opt_prob(obj, xRange, yRange, ineqCon=None, eqCon=None, nPoints=51, optPoint=None, conStyle="shaded"/"hashed", ax=None, colors=None, cmap=None, levels=None, labelAxes=True)` | Contour plot of a 2D constrained optimisation problem (functions of `X, Y` arrays, constraints `g <= 0`, `h == 0`). |
| `plot_colored_line(x, y, c, cmap=None, fig=None, ax=None, addColorBar=False, cRange=None, cBarLabel=None, norm=None, **kw)` | Line coloured by a third variable (LineCollection). |
| `plot_nested_pie(data, colors=None, alphas=None, ax=None, innerKwargs=None, outerKwargs=None)` | Two-level pie from `{cat: {subcat: value}}`. |
| `plot_spline(x, y, ax=None, spline_type="non-overshoot"/"b-spline", num_interp_pts=100, spline_options={}, **plot_kw)` | Smooth curve through points (Akima, no overshoot, or B-spline). |
| `save_figs(fig, name, formats, format_kwargs=None, **kw)` | Save in several formats, e.g. `save_figs(fig, "out/f", ["pdf","png"], format_kwargs={"png": {"dpi": 400}}, bbox_inches="tight")`. |

## Idioms from the niceplots examples
- y label: `ax.set_ylabel("$x_2$", rotation="horizontal", ha="right")`
- marker on the plot: `ax.plot(x, y, "o", color=colors["Axis"], markeredgecolor="w", markersize=12, clip_on=False)`
- annotate a point: `ax.annotate("Local minimum", xy=pt, xytext=(-5, 10), textcoords="offset points", ha="center", fontsize="small")`
- ticks at meaningful values only: `ax.set_xticks([xmin, x_opt, xmax])`
- temporary style: `with plt.style.context(niceplots.get_style("james-dark")): ...`
