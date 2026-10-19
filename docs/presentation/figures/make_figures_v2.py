"""
Figures for the second version of the presentation (GP vs Claude comparison),
from the run logs in ../data.

    cd docs/presentation/figures && python3 make_figures_v2.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches
import matplotlib.colors
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


FOUR, SIX = "#eb6834", "#1baf7a"          # validated categorical slots 2, 3


def fig_four_vs_six(four, six, name):
    """Claude with 4 vs 6 parameters (same amplifier, LED only): F and signal."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 3.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1.15, 1]})
    for d, color, label, dx in ((four, FOUR, "4 parameters (Oct 2)", -0.12),
                                (six, SIX, "6 parameters (Oct 14)", 0.12)):
        pos, neg = d[d.gain > 0], d[d.gain <= 0]
        a1.scatter(pos.iteration + dx, pos.F, s=14, color=color, edgecolor="white",
                   linewidth=0.5, zorder=3)
        a1.scatter(neg.iteration + dx, neg.F, s=14, facecolor="white", edgecolor=color,
                   linewidth=1.0, zorder=3)
        best = np.minimum.accumulate(np.where(d.gain > 0, d.F, np.inf))
        a1.step(d.iteration, best, where="post", color=color, linewidth=1.6, zorder=2,
                label=label)
        a1.text(d.iteration.iloc[-1] + 0.8, best[-1], f"{best[-1]:.2f}", color=INK,
                fontsize=7, va="center")
        a2.scatter(d.iteration + dx, d.gain, s=12, color=color, edgecolor="white",
                   linewidth=0.4, zorder=3)
    for a in (a1, a2):
        shade(a)
        a.axvline(30.5, color=MUTED, linewidth=0.8, linestyle="--")
        a.grid(axis="y", color=GRID, linewidth=0.6)
        a.set_xlim(0.5, 53)
    a1.set_yscale("log")
    a1.set_ylabel("F (log)")
    a1.legend(fontsize=7, frameon=False, loc="upper right")
    a2.axhline(0, color=MUTED, linewidth=0.8)
    a2.set_ylim(-2500, 5000)
    a2.text(31, 4300, "4-parameter run ends", fontsize=6.5, color=MUTED)
    a2.set_ylabel("gain (ADU)")
    a2.set_xlabel("image")
    a2.set_xticks([1, 8, 20, 30, 40, 50])
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


def fig_hh_hl(six, name):
    """How Claude moved the horizontal clock levels, and the signal it got."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 3.4), sharex=True)
    for a in (a1, a2):
        shade(a)
        a.grid(axis="y", color=GRID, linewidth=0.6)
    a1.plot(six.iteration, six.hh, color=GP, marker="o", markersize=2.5,
            linewidth=0.9, label="hh (high level)")
    a1.plot(six.iteration, six.hl, color=CLAUDE, marker="o", markersize=2.5,
            linewidth=0.9, label="hl (low level)")
    for y, c in ((-2, GP), (-4.5, CLAUDE)):
        a1.axhline(y, color=c, linewidth=0.8, linestyle=":")
    a1.text(50.6, -2, "script\ndefault", fontsize=6, color=MUTED, va="center")
    a1.set_ylabel("voltage (V)")
    a1.set_ylim(-11, 11)
    a1.legend(fontsize=7, frameon=False, loc="upper right", ncol=2)
    a2.scatter(six.iteration, six.gain, s=12, color=SIX, edgecolor="white", linewidth=0.4)
    a2.axhline(0, color=MUTED, linewidth=0.8)
    a2.set_ylim(-2500, 5000)
    a2.set_ylabel("gain (ADU)")
    a2.set_xlabel("image")
    a2.set_xticks([1, 8, 20, 30, 40, 50])
    a2.set_xlim(0.5, 53)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


# Raw images (amplifier 3 = HDU 4), regions as in config "detector"
HDU = 4
ACTIVE, OVERSCAN = ((2, 30), (16, 56)), ((2, 30), (89, 98))
VMIN, VMAX = -1500, 4500


def read_amp(day, filename):
    import fitsio
    im = fitsio.read(os.path.join(DATA, "images", day, filename), ext=HDU).astype(float)
    (r0, r1), (c0, c1) = OVERSCAN
    return im - np.median(im[r0:r1, c0:c1])       # ADU above the overscan level


def ramp(color, n):
    """n steps of one hue, light to dark (later images darker)."""
    rgb = np.array(matplotlib.colors.to_rgb(color))
    return [tuple(1 - (1 - rgb) * f) for f in np.linspace(0.35, 1.0, n)]


def draw_regions(ax):
    for ((r0, r1), (c0, c1)), ls in ((ACTIVE, "-"), (OVERSCAN, "--")):
        ax.add_patch(matplotlib.patches.Rectangle((c0 - 0.5, r0 - 0.5), c1 - c0, r1 - r0,
                     fill=False, edgecolor="#f2c14e", linewidth=0.9, linestyle=ls))


def fig_filmstrip(table, day, iterations, color, name):
    """Selected images along Claude's path, same display scale, plus column profiles."""
    rows = [table[table.iteration == i].iloc[0] for i in iterations]
    colors = ramp(color, len(rows))
    fig = plt.figure(figsize=(6.6, 3.7))
    gs = fig.add_gridspec(2, len(rows), height_ratios=[1.25, 1], hspace=0.55, wspace=0.08)
    for k, r in enumerate(rows):
        ax = fig.add_subplot(gs[0, k])
        im = ax.imshow(read_amp(day, r.filename), cmap="gray", vmin=VMIN, vmax=VMAX,
                       origin="lower", interpolation="nearest", aspect="auto")
        draw_regions(ax)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True); sp.set_color(colors[k]); sp.set_linewidth(2.2)
        tag = "Sobol" if r.iteration <= N_SOBOL else "guided"
        ax.set_title(f"image {int(r.iteration)} ({tag})\nF {r.F:.2f}   gain {r.gain:.0f}",
                     fontsize=6.8, color=INK)
    cax = fig.add_axes([0.875, 0.50, 0.012, 0.36])
    cb = fig.colorbar(im, cax=cax)
    cb.ax.tick_params(labelsize=6)
    cb.set_label("ADU above overscan", fontsize=6.5)
    ax = fig.add_subplot(gs[1, :])
    (r0, r1), (c0, c1) = ACTIVE
    ax.axvspan(c0 - 0.5, c1 - 0.5, color=SHADE, zorder=0)
    ax.axvspan(OVERSCAN[1][0] - 0.5, OVERSCAN[1][1] - 0.5, color=SHADE, zorder=0)
    ax.text((c0 + c1) / 2, 0.97, "active region", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=6.5, color=MUTED)
    ax.text(93.5, 0.97, "overscan", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=6.5, color=MUTED)
    for k, r in enumerate(rows):
        prof = np.median(read_amp(day, r.filename)[r0:r1], axis=0)
        ax.plot(np.arange(prof.size), prof, color=colors[k], linewidth=1.4,
                label=f"image {int(r.iteration)}")
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xlim(-0.5, 99.5)
    ax.set_xlabel("column")
    ax.set_ylabel("ADU, median of\nactive rows")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.legend(fontsize=6.5, frameon=False, ncol=len(rows), loc="upper right",
              bbox_to_anchor=(1.0, 1.32))
    fig.subplots_adjust(left=0.11, right=0.86, top=0.90, bottom=0.12)
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


def fig_best_pair(four, six, name):
    """Best image of the 4- and 6-parameter runs, same scale, and their profiles."""
    picks = [("Oct-02-2026", four.loc[four[four.gain > 0].F.idxmin()], FOUR, "4 parameters"),
             ("Oct-14-2026", six.loc[six[six.gain > 0].F.idxmin()], SIX, "6 parameters")]
    fig = plt.figure(figsize=(6.6, 2.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.5], wspace=0.35)
    (r0, r1), _ = ACTIVE
    axp = fig.add_subplot(gs[0, 2])
    for k, (day, r, color, label) in enumerate(picks):
        ax = fig.add_subplot(gs[0, k])
        img = read_amp(day, r.filename)
        im = ax.imshow(img, cmap="gray", vmin=VMIN, vmax=VMAX, origin="lower",
                       interpolation="nearest", aspect="auto")
        draw_regions(ax)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True); sp.set_color(color); sp.set_linewidth(2.2)
        ax.set_title(f"{label}: image {int(r.iteration)}\nF {r.F:.2f}   gain {r.gain:.0f}",
                     fontsize=7, color=INK)
        axp.plot(np.median(img[r0:r1], axis=0), color=color, linewidth=1.4, label=label)
    axp.axhline(0, color=MUTED, linewidth=0.8)
    axp.axvspan(ACTIVE[1][0] - 0.5, ACTIVE[1][1] - 0.5, color=SHADE, zorder=0)
    axp.axvspan(OVERSCAN[1][0] - 0.5, OVERSCAN[1][1] - 0.5, color=SHADE, zorder=0)
    axp.set_xlabel("column")
    axp.set_ylabel("ADU, median of active rows")
    axp.grid(axis="y", color=GRID, linewidth=0.6)
    axp.legend(fontsize=6.5, frameon=False)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.82, bottom=0.17)
    fig.savefig(os.path.join(HERE, name))
    plt.close(fig)


if __name__ == "__main__":
    gp = load("Oct-02-2026_results-skipper-004")
    cl = load("Oct-02-2026_results-skipper-005")
    fig_compare_per_image(gp, cl, "compare_per_image.pdf")
    fig_trajectories(gp, cl, "compare_trajectories.pdf")
    fig_shot_noise("shot_noise.pdf")
    six = load("Oct-14-2026_results-skipper-001")
    fig_four_vs_six(cl, six, "four_vs_six.pdf")
    fig_hh_hl(six, "hh_hl.pdf")
    fig_filmstrip(cl, "Oct-02-2026", [1, 4, 11, 25, 28], FOUR, "images_oct02.pdf")
    fig_filmstrip(six, "Oct-14-2026", [1, 4, 13, 30, 50], SIX, "images_oct14.pdf")
    fig_best_pair(cl, six, "images_best.pdf")
    print("figures written")
