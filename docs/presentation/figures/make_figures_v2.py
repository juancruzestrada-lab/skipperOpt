"""
Figures for the second version of the presentation (GP vs Claude comparison),
from the run logs in ../data.

    cd docs/presentation/figures && python3 make_figures_v2.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

GP, CLAUDE = "#2a78d6", "#eb6834"          # validated categorical slots 1, 2 (+ 3 below)
INK, MUTED, GRID, SHADE = "#222222", "#6b6b6b", "#e4e4e4", "#f1f1ef"
N_SOBOL = 8
PARAMS = [("Vdd", "Vdd (V)"), ("Vdrain", "Vdrain (V)"), ("Vr", "Vr (V)"),
          ("delay_H_overlap", "delay (clk)")]
BOUNDS = {"Vdd": (-23, -10), "Vdrain": (-23, -10), "Vr": (-8, -5),
          "delay_H_overlap": (10, 30)}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def load(prefix):
    d = pd.read_csv(os.path.join(DATA, prefix + ".csv"))
    d.columns = [c.replace(" (current)", "") for c in d.columns]
    stats = [m["payload"]["stats"]
             for m in map(json.loads, open(os.path.join(DATA, prefix + "_messages.jsonl")))
             if m.get("direction") == "recv" and m.get("sender") == "objective"
             and "stats" in m.get("payload", {})]
    return pd.concat([d, pd.DataFrame(stats)], axis=1)


def shade(ax):
    ax.axvspan(0.5, N_SOBOL + 0.5, color=SHADE, zorder=0)


def fig_compare_per_image(gp, cl, name):
    """F (log) and signal per image, GP and Claude overlaid."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 3.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1.15, 1]})
    for d, color, label, dx in ((gp, GP, "GP", -0.12), (cl, CLAUDE, "Claude", 0.12)):
        pos, neg = d[d.gain > 0], d[d.gain <= 0]
        a1.scatter(pos.iteration + dx, pos.F, s=16, color=color, edgecolor="white",
                   linewidth=0.6, zorder=3)
        a1.scatter(neg.iteration + dx, neg.F, s=16, facecolor="white", edgecolor=color,
                   linewidth=1.0, zorder=3)
        best = np.minimum.accumulate(np.where(d.gain > 0, d.F, np.inf))
        a1.step(d.iteration, best, where="post", color=color, linewidth=1.6, zorder=2)
        a2.scatter(d.iteration + dx, d.gain, s=14, color=color, edgecolor="white",
                   linewidth=0.5, zorder=3)
        a1.text(30.6, best[-1], f"{label}  {best[-1]:.2f}", color=INK,
                fontsize=7, va="center")
    for a in (a1, a2):
        shade(a)
        a.grid(axis="y", color=GRID, linewidth=0.6)
        a.set_xlim(0.5, 33.5)
    a1.set_yscale("log")
    a1.set_ylabel("F (log)")
    a1.text(4.5, a1.get_ylim()[1] * 0.6, "Sobol", ha="center", fontsize=6.5, color=MUTED)
    a1.text(19.5, a1.get_ylim()[1] * 0.6, "guided", ha="center", fontsize=6.5, color=MUTED)
    a2.axhline(0, color=MUTED, linewidth=0.8)
    a2.set_ylabel("gain (ADU)")
    a2.set_xlabel("image")
    a2.set_xticks([1, 8, 15, 22, 30])
    handles = [plt.Line2D([], [], marker="o", ls="", color=GP, label="GP"),
               plt.Line2D([], [], marker="o", ls="", color=CLAUDE, label="Claude"),
               plt.Line2D([], [], marker="o", ls="", mfc="white", mec=MUTED,
                          label="negative gain (open)"),
               plt.Line2D([], [], color=MUTED, lw=1.6, label="best so far, gain > 0")]
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


def fig_trajectories(gp, cl, name):
    """Each parameter per image: how GP and Claude move through the space."""
    fig, axes = plt.subplots(2, 2, figsize=(6.4, 3.4), sharex=True)
    for ax, (col, label) in zip(axes.flat, PARAMS):
        shade(ax)
        lo, hi = BOUNDS[col]
        for y in (lo, hi):
            ax.axhline(y, color=MUTED, linewidth=0.6, linestyle=":")
        ax.plot(gp.iteration, gp[col], color=GP, linewidth=0.9, marker="o",
                markersize=2.5, label="GP")
        ax.plot(cl.iteration, cl[col], color=CLAUDE, linewidth=0.9, marker="o",
                markersize=2.5, label="Claude")
        ax.set_ylabel(label)
        ax.set_ylim(lo - 0.08 * (hi - lo), hi + 0.08 * (hi - lo))
        ax.grid(axis="y", color=GRID, linewidth=0.6)
    for ax in axes[1]:
        ax.set_xlabel("image")
        ax.set_xticks([1, 8, 15, 22, 30])
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels + [], loc="upper center", ncol=2, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


def fig_shot_noise(name):
    """Excess active-region variance vs signal: real light follows var = k * S."""
    leak = load("Oct-01-2026_results-skipper-003")
    led = load("Oct-02-2026_results-skipper-005")
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    for d, color, label in ((leak, "#1baf7a", "Oct 1 (light leaks)"),
                            (led, CLAUDE, "Oct 2 (LED only, Claude run)")):
        g = d[d.gain > 900]
        ax.scatter(g.gain, g.noise_active ** 2 - g.noise_overscan ** 2, s=14,
                   color=color, edgecolor="white", linewidth=0.5, label=label, zorder=3)
    s = np.array([5e2, 5e4])
    for k, ls in ((144, "-"), (204, "--")):
        ax.plot(s, k * s, color=MUTED, linewidth=0.8, linestyle=ls, zorder=2)
        ax.text(s[1], k * s[1], f" {k} ADU/e$^-$", fontsize=6.5, color=MUTED, va="center")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("signal: gain (ADU)")
    ax.set_ylabel("excess variance (ADU$^2$)")
    ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_xlim(5e2, 2e5)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


if __name__ == "__main__":
    gp = load("Oct-02-2026_results-skipper-004")
    cl = load("Oct-02-2026_results-skipper-005")
    fig_compare_per_image(gp, cl, "compare_per_image.pdf")
    fig_trajectories(gp, cl, "compare_trajectories.pdf")
    fig_shot_noise("shot_noise.pdf")
    print("figures written")
