"""
notebook.py
The lab notebook (logbook): a Markdown file that carries lessons from one
campaign to the next.

Every run of optimize_agents.py, GP or Claude, appends one entry:

    ## <date time> | module <m> | amp <n> (HDU <n+1>) | <optimizer> | <N> measurements (<k> new) | best F = ... at ...

    **Run facts** (recorded by the code): config, images, times, best points,
    signal and noise statistics.

    <Claude's analysis, for Claude runs>

Claude campaigns also read the notebook at the start, as prior knowledge.
logbook.py reads it and adds operator entries.
"""

import os
from datetime import datetime

import numpy as np

import bo_core as bo

# Older entries are left out of Claude's prompt (not the file) beyond this size.
DEFAULT_NOTEBOOK_MAX_CHARS = 30000

PREAMBLE = ("# Claude lab notebook\n\n"
            "Written by the optimizer at the end of each campaign and read by "
            "Claude at the start of the next one. Edit or delete entries freely.\n")

# Below this gain (ADU) an image has no usable LED signal.
NO_SIGNAL_GAIN = 1000


def load_notebook(path: str, max_chars: int = DEFAULT_NOTEBOOK_MAX_CHARS) -> str:
    """Notebook text for the prompt ('' if none). Keeps the newest entries."""
    if not path or not os.path.exists(path):
        return ""
    with open(path) as f:
        text = f.read().strip()
    if len(text) > max_chars:
        cut = text.find("\n## ", len(text) - max_chars)
        text = ("[older entries omitted]\n" +
                (text[cut + 1:] if cut != -1 else text[-max_chars:]))
    return text


def append_notebook_entry(path: str, header: str, body: str):
    # The code writes the "## " header; drop any heading the body starts with.
    lines = body.strip().splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
    body = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    with open(path, "a") as f:
        if new_file:
            f.write(PREAMBLE)
        f.write(f"\n## {header}\n\n{body.strip()}\n")


def amp_label(amplifier) -> str:
    """Config amplifier value (FITS HDU index) -> 'amp N (HDU N+1)'."""
    return f"amp {amplifier - 1} (HDU {amplifier})" if amplifier is not None else ""


def format_point(x_norm, param_cfgs) -> str:
    return ", ".join(
        f"{p['name']}={round(bo.from_normalized(v, *p['bounds']), p.get('precision', 2))}"
        for v, p in zip(x_norm, param_cfgs))


def make_entry(records, param_cfgs, module, amplifier, optimizer, config_name,
               t_start, t_end, x0=None, y0=None, lessons="", status=""):
    """
    Header and body of the entry for one run.

    records : this run's measurements, dicts with keys x (normalized point),
              F, stats (image statistics, may be empty) and image (file name)
    x0, y0  : warm-start measurements, if the run was resumed
    lessons : Claude's analysis (Claude runs), appended after the facts
    status  : e.g. "interrupted (OverloadedError)"
    """
    xs = [list(x) for x in (x0 or [])] + [r["x"] for r in records]
    ys = [float(y) for y in (y0 or [])] + [r["F"] for r in records]
    best = int(np.argmin(ys))
    fields = [f"{datetime.now():%Y-%m-%d %H:%M}", f"module {module or '?'}"]
    if amplifier is not None:
        fields.append(amp_label(amplifier))
    fields += [optimizer, f"{len(xs)} measurements ({len(records)} new)",
               f"best F = {ys[best]:.5g} at {format_point(xs[best], param_cfgs)}"]
    if status:
        fields.append(status)
    header = " | ".join(fields)

    facts = ["**Run facts** (recorded by the code)"]
    images = [r["image"] for r in records if r.get("image")]
    span = f"{t_start:%H:%M}-{t_end:%H:%M}" if t_start and t_end else ""
    facts.append("- " + "; ".join(x for x in (
        f"Optimizer: {optimizer}",
        f"config: {config_name}" if config_name else "",
        f"images {images[0]} to {images[-1]}" if images else "",
        span,
        f"resumed from {len(x0)} earlier measurements" if x0 else "",
    ) if x) + ".")
    order = sorted(range(len(records)), key=lambda i: records[i]["F"])[:3]
    if order:
        r = records[order[0]]
        line = (f"- Best F this run: {r['F']:.4g} at ({format_point(r['x'], param_cfgs)})"
                + (f", image {r['image']}" if r.get("image") else ""))
        others = [f"{records[i]['F']:.4g} at ({format_point(records[i]['x'], param_cfgs)})"
                  for i in order[1:]]
        facts.append(line + (". Next: " + "; ".join(others) if others else "") + ".")
    gains = [r["stats"]["gain"] for r in records if "gain" in r.get("stats", {})]
    if gains:
        n_low = sum(g < NO_SIGNAL_GAIN for g in gains)
        facts.append(f"- Signal (gain, ADU): median {np.median(gains):.0f}, "
                     f"max {max(gains):.0f}; {n_low} of {len(gains)} images below "
                     f"{NO_SIGNAL_GAIN} (no usable signal).")
    noise = [r["stats"]["noise_overscan"] for r in records
             if "noise_overscan" in r.get("stats", {})]
    if noise:
        facts.append(f"- Overscan noise (ADU): median {np.median(noise):.0f}, "
                     f"range {min(noise):.0f}-{max(noise):.0f}.")
    body = "\n".join(facts)
    if lessons:
        lines = lessons.strip().splitlines()
        while lines and lines[0].lstrip().startswith("#"):   # stray heading
            lines.pop(0)
        body += "\n\n" + "\n".join(lines).strip()
    return header, body
