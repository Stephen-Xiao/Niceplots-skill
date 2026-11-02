import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # the skill folder
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nicefig as nf

out = sys.argv[1] if len(sys.argv) > 1 else "."
colors = nf.setup()

# 1. separate lines -> labels at line ends
fig, ax = plt.subplots(figsize=(7, 4.5))
t = np.linspace(0, 10, 200)
for k in range(4):
    ax.plot(t, (k + 1) * (1 - np.exp(-t / 3)), label=f"$k = {k+1}$", clip_on=False)
ax.set_xlim(0, 10); ax.set_ylim(0, 4)
ax.set_xlabel("$t$ (ms)"); nf.ylabel(ax, "$p/p_0$")
nf.finish(ax); r = nf.smart_legend(ax); print("separate ->", type(r).__name__)
nf.save(fig, f"{out}/1_separate")

# 2. crossing lines, negative values -> legend below
fig, ax = plt.subplots(figsize=(7, 4.5))
x = np.linspace(-2, 2, 200)
for k in range(5):
    ax.plot(x, np.sin(2 * x + k), label=f"Case {k+1}")
ax.set_xlim(-2, 2); ax.set_ylim(-1, 1)
ax.set_xticks([-2, -1, 0, 1, 2]); ax.set_yticks([-1, -0.5, 0, 0.5, 1])
ax.set_xlabel("$x$ (mm)"); ax.set_ylabel("$C_p$")   # deliberately rotated; finish() fixes
nf.finish(ax); r = nf.smart_legend(ax); print("crossing ->", type(r).__name__)
nf.data_vline(ax, 0.5, np.sin(1.0))
nf.align_negative_ticks(ax)
nf.save(fig, f"{out}/2_crossing")

# 3. signed field -> diverging map + flush colour bar
X, Y = np.meshgrid(np.linspace(-1, 1, 200), np.linspace(-1, 1, 200))
F = np.sin(3 * X) * np.cos(2 * Y) * 1.7
fig, ax = plt.subplots(figsize=(7, 5.5))
cmap, norm = nf.color_scale(F)
cs = ax.contourf(X, Y, F, levels=31, cmap=cmap, norm=norm, extend="both")
ax.set_aspect("equal"); ax.set_xlabel("$x$"); nf.ylabel(ax, "$y$")
nf.finish(ax)
cb = nf.colorbar(ax, cs, label=r"$\Delta p$")
nf.align_negative_ticks(cb.ax, "y"); nf.align_negative_ticks(ax)
nf.save(fig, f"{out}/3_field")

# 4. stacked, shared x
fig, axes = plt.subplots(3, 1, figsize=(7, 6), sharex=True)
for i, a in enumerate(axes):
    a.plot(t, np.sin(t * (i + 1)), color=list(colors.values())[i])
    nf.ylabel(a, f"$C_{i+1}$")
nf.stack_shared_x(axes, xlabel="$t$ (ms)")
nf.save(fig, f"{out}/4_stacked")
print("ok")
