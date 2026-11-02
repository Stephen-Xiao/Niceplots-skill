# niceplots Claude skill

A [Claude Code](https://claude.com/claude-code) skill that makes every matplotlib figure follow
the lab's style: [MDO Lab niceplots](https://github.com/mdolab/niceplots) plus our rules (LaTeX
Computer Modern text, no label touching a line or other text, labels at line ends or a frameless
legend below, horizontal y labels, flush colour bars, sequential or diverging colour maps).

## Use it

1. Install the plotting packages once, in the Python environment you plot with:
   ```
   pip install niceplots matplotlib scipy
   ```
2. Open Claude Code anywhere inside this repository. The skill loads automatically when you ask
   for a plot, or force it with:
   ```
   /niceplots plot P7 against time for TR 0.85 and 0.80
   ```

Nothing else to install: Claude Code picks up skills from `.claude/skills/` in the repository.

## Use the helpers without Claude

`nicefig.py` is plain Python. Copy it next to your script and import it:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nicefig as nf

colors = nf.setup()
# ... plot with matplotlib ...
nf.finish(ax)
nf.smart_legend(ax)
nf.save(fig, "figures/my_plot")   # checks overlaps and LaTeX characters, writes .pdf and .png
```

## Files

| File | What it is |
|---|---|
| `SKILL.md` | The rules Claude follows (also a readable style guide) |
| `nicefig.py` | The Python helpers |
| `reference.md` | Every niceplots function and its arguments |
| `examples/demo.py` | Four example figures: `python examples/demo.py out_dir` |
