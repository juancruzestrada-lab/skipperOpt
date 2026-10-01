"""
Figures for the presentation, from the run logs in ../data.

    cd docs/presentation/figures && python make_figures.py
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

CAMPAIGNS = [   # run id, label, series colour (validated categorical slots 1-3)
    ("002", "Campaign 1", "#2a78d6"),
    ("003", "Campaign 2", "#eb6834"),
    ("004", "Campaign 3: amplifier not working", "#1baf7a"),
]
N_SOBOL = 8
BROKEN_GAIN = 1000          # gain below this: no usable signal
INK, MUTED, GRID = "#222222", "#6b6b6b", "#e4e4e4"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def load(run):
    d = pd.read_csv(os.path.join(DATA, f"Oct-01-2026_results-skipper-{run}.csv"))
    stats = [m["payload"]["stats"]
             for m in map(json.loads, open(os.path.join(
                 DATA, f"Oct-01-2026_results-skipper-{run}_messages.jsonl")))
             if m.get("direction") == "recv" and m.get("sender") == "objective"
             and "stats" in m.get("payload", {})]
    d = pd.concat([d, pd.DataFrame(stats)], axis=1)
    d["broken"] = d["gain"] < BROKEN_GAIN
    return d


def fig_per_image():
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), sharey=True)
    for ax, (run, label, color) in zip(axes, CAMPAIGNS):
        d = load(run)
        ax.axvspan(0.5, N_SOBOL + 0.5, color="#f1f1ef", zorder=0)
        ok, bad = d[~d.broken], d[d.broken]
        ax.scatter(ok.iteration, ok["F (current)"], s=16, color=color,
                   edgecolor="white", linewidth=0.8, zorder=3)
        ax.scatter(bad.iteration, bad["F (current)"], s=18, marker="x",
                   color=MUTED, linewidth=1.1, zorder=3)
        ax.step(d.iteration, np.minimum.accumulate(d["F (current)"]),
                where="post", color=color, linewidth=1.6, zorder=2)
        best = d.loc[d["F (current)"].idxmin()]
        ax.annotate(f"best {best['F (current)']:.3g}", (best.iteration, best["F (current)"]),
                    xytext=(0, 9 if best["F (current)"] < 0.5 else -14),
                    textcoords="offset points", ha="center",
                    fontsize=7, color=INK)
        ax.set_yscale("log")
        ax.set_ylim(0.01, 2000)
        ax.set_xlim(0.5, 30.5)
        ax.set_xticks([1, 8, 15, 22, 30])
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_title(label, fontsize=8.5, color=INK, loc="left")
        ax.set_xlabel("image")
        ax.text(4.5, 1100, "Sobol", ha="center", fontsize=6.5, color=MUTED)
        ax.text(19.5, 1100, "Claude", ha="center", fontsize=6.5, color=MUTED)
        if run == "002":
            ax.annotate("signal dropout\n(images 11-18)", (14.5, 25), fontsize=6.5,
                        color=MUTED, ha="center")
    axes[0].set_ylabel("F  (log scale, lower is better)")
    fig.tight_layout(w_pad=1.0)
    fig.savefig(os.path.join(HERE, "per_image_F.pdf"))
    plt.close(fig)


def fig_vdd_vdrain():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 3.0), sharex=True, sharey=True)
    for ax, (run, label, color) in zip(axes, CAMPAIGNS[:2]):
        d = load(run)
        lo, hi = -23.5, -9.5
        ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=0.8, linestyle="--", zorder=1)
        ax.fill_between([lo, hi], [lo, hi], [hi, hi], color="#f1f1ef", zorder=0)
        ax.text(-22.8, -11.0, "Vdrain less negative\nthan Vdd", fontsize=6.5,
                color=MUTED, va="top")
        claude = d[d.iteration > N_SOBOL]
        ax.plot(claude["Vdd (current)"], claude["Vdrain (current)"], color=color,
                linewidth=0.6, alpha=0.5, zorder=2)
        ok, bad = d[~d.broken], d[d.broken]
        sob = ok[ok.iteration <= N_SOBOL]
        cl = ok[ok.iteration > N_SOBOL]
        ax.scatter(sob["Vdd (current)"], sob["Vdrain (current)"], s=22,
                   facecolor="white", edgecolor=color, linewidth=1.1, zorder=3,
                   label="Sobol start")
        ax.scatter(cl["Vdd (current)"], cl["Vdrain (current)"], s=16, color=color,
                   edgecolor="white", linewidth=0.6, zorder=4, label="Claude")
        ax.scatter(bad["Vdd (current)"], bad["Vdrain (current)"], s=20, marker="x",
                   color=MUTED, linewidth=1.1, zorder=5, label="no signal (gain < 1000)")
        best = d.loc[d["F (current)"].idxmin()]
        ax.annotate(f"best F = {best['F (current)']:.3g}",
                    (best["Vdd (current)"], best["Vdrain (current)"]),
                    xytext=(-62, 26), textcoords="offset points", fontsize=7,
                    color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal")
        ax.set_title(label, fontsize=8.5, color=INK, loc="left")
        ax.set_xlabel("Vdd (V)")
        ax.grid(color=GRID, linewidth=0.6)
    axes[0].set_ylabel("Vdrain (V)")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=7,
               frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(w_pad=1.5, rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "vdd_vdrain.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig_per_image()
    fig_vdd_vdrain()
    print("figures written")
