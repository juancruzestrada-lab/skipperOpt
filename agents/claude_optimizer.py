"""
claude_optimizer.py
Claude as the optimizer: a drop-in replacement for gp_minimize.

claude_minimize() has the same calling convention and returns the same kind
of OptimizeResult as skopt's minimizers, so the progress callback,
gp_results.csv, the .pkl dumps, warm restart and the convergence plot all
work unchanged. Select it in the config with:

    "optimizer": {
        "type": "claude",
        "n_calls": 30,
        "n_initial_points": 8,
        "random_state": 15,
        "model": "claude-opus-5-5",
        "effort": "high",
        "notes": "Anything Claude should know about this detector."
    }

Loop
----
1. Space-filling start: n_initial_points Sobol points (same generator family
   as the GP runs), skipped on warm restart.
2. Each following iteration Claude gets the full history (parameters in
   physical units, F, and the image statistics from the objective agent),
   reasons about it, and returns the next point to measure as JSON.
3. The point is clipped to the bounds, measured, and appended to the history.

Every decision (proposed point + a summary of Claude's thinking, as
returned by the API) is appended to <run>_claude_decisions.jsonl next to
the progress CSV. The prompt deliberately does not ask Claude to write its
reasoning into the answer: Opus 5.5 declines such requests
("reasoning_extraction"), so the explanation comes from the summarized
thinking blocks instead.

Needs `pip install anthropic` and an API key in ANTHROPIC_API_KEY (or an
`ant auth login` profile).
"""

import json
from datetime import datetime

import numpy as np
from skopt.sampler import Sobol
from skopt.space import Space
from skopt.utils import create_result

import bo_core as bo

DEFAULT_MODEL  = "claude-opus-5-5"
DEFAULT_EFFORT = "high"

# Keys of config["optimizer"] used by claude_minimize (everything else ignored).
_CLAUDE_KEYS = {"model", "effort", "notes", "max_tokens"}


SYSTEM_PROMPT = """\
You are the optimizer in a closed-loop tuning campaign for a Skipper-CCD \
read out by an LTA controller. Each measurement: the CCD is exposed to an \
LED for a fixed time, the operating parameters below are set, an image is \
read out, and a scalar objective F is computed from it. Lower F is better. \
Each measurement takes real lab time, so choose every point deliberately.

Your job each turn: look at all measurements so far and choose the single \
next parameter set to measure, trading off exploiting the best region \
against exploring regions you know little about. F is noisy; differences \
smaller than the scatter between similar points are not meaningful, and \
re-measuring a promising point is allowed when it would resolve that.

Parameters (physical units, inclusive bounds; values are rounded to the \
given number of decimals before being applied):
{parameters}

Objective:
{objective}

Image statistics reported with each measurement (ADU):
- noise_overscan: std of the overscan region (read noise proxy)
- noise_active: std of the exposed active region
- charge_overscan / charge_active: medians of those regions
- gain: charge_active - charge_overscan (LED signal; scales with amplifier gain)
{notes}
Reply with the next point to measure."""


def _describe_parameters(param_cfgs: list) -> str:
    lines = []
    for p in param_cfgs:
        lo, hi = p["bounds"]
        desc = p.get("_comment", "")
        lines.append(f"- {p['name']}: [{lo}, {hi}], {p.get('precision', 2)} "
                     f"decimals. {desc}".rstrip())
    return "\n".join(lines)


def _describe_objective(obj_cfg: dict) -> str:
    text = ("F = min(|noise_overscan / gain|, max_baseline) + penalties, "
            f"with max_baseline = {obj_cfg.get('max_baseline', 1000)}. "
            "This is approximately the read noise in units of the LED "
            "signal, so it tracks noise in electrons.")
    active = [p for p in obj_cfg.get("penalties", []) if not p.get("_disabled")]
    if active:
        text += " Active penalties: " + "; ".join(
            f"{p['type']} (coefficient {p.get('coefficient', 1.0)}, "
            f"power {p.get('power', 1.0)}, params {p.get('params', {})})"
            for p in active)
    else:
        text += " No penalty terms are active."
    return text


def _output_schema(param_cfgs: list) -> dict:
    return {
        "type": "object",
        "properties": {
            "next_point": {
                "type": "object",
                "properties": {p["name"]: {"type": "number"} for p in param_cfgs},
                "required": [p["name"] for p in param_cfgs],
                "additionalProperties": False,
            },
        },
        "required": ["next_point"],
        "additionalProperties": False,
    }


def _history_table(Xi, yi, stats, param_cfgs, n_prior) -> str:
    names = [p["name"] for p in param_cfgs]
    stat_keys = ["noise_overscan", "noise_active", "charge_overscan",
                 "charge_active", "gain"]
    header = ["#"] + names + ["F"] + stat_keys
    rows = [" | ".join(header)]
    for i, (x, y) in enumerate(zip(Xi, yi)):
        phys = [round(bo.from_normalized(v, *p["bounds"]), p.get("precision", 2))
                for v, p in zip(x, param_cfgs)]
        j = i - n_prior
        st = stats[j] if 0 <= j < len(stats) else {}
        cells = [str(i + 1)] + [str(v) for v in phys] + [f"{y:.5g}"]
        cells += [f"{st[k]:.4g}" if k in st else "-" for k in stat_keys]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def _ask_claude(client, model, effort, max_tokens, system, schema, user):
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": effort,
                       "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude's reply was cut off; raise optimizer.max_tokens.")
    text = [b.text for b in response.content if b.type == "text"][-1]
    decision = json.loads(text)
    decision["thinking_summary"] = "\n".join(
        b.thinking for b in response.content
        if b.type == "thinking" and getattr(b, "thinking", "")
    )
    return decision


def claude_minimize(func, dimensions, n_calls, param_cfgs, obj_cfg,
                    n_initial_points=8, random_state=None, callback=None,
                    x0=None, y0=None, observations=None,
                    model=DEFAULT_MODEL, effort=DEFAULT_EFFORT, notes="",
                    max_tokens=16000, decision_log=None, client=None):
    """
    Minimize func over dimensions with Claude choosing the points.

    Parameters mirror skopt.gp_minimize where they overlap. Extra:
    param_cfgs, obj_cfg : config["parameters"], config["objective"]
    observations : list that the caller appends one stats dict to per
                   evaluation (optional; shown to Claude when present)
    client       : anthropic.Anthropic instance (created if None)
    """
    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    space     = Space(dimensions)
    callbacks = callback if isinstance(callback, list) else [callback] if callback else []
    stats     = observations if observations is not None else []

    Xi = [list(map(float, x)) for x in x0] if x0 else []
    yi = [float(y) for y in y0] if y0 else []
    n_prior = len(Xi)

    system = SYSTEM_PROMPT.format(
        parameters=_describe_parameters(param_cfgs),
        objective=_describe_objective(obj_cfg),
        notes=f"\nNotes from the operator:\n{notes}\n" if notes else "",
    )
    schema = _output_schema(param_cfgs)
    specs  = {"function": "claude_minimize",
              "args": {"n_calls": n_calls, "n_initial_points": n_initial_points,
                       "random_state": random_state, "model": model,
                       "effort": effort}}
    rng    = np.random.RandomState(random_state)

    def record(x):
        Xi.append(list(map(float, x)))
        yi.append(float(func(Xi[-1])))
        result = create_result(Xi, yi, space, rng, specs)
        for cb in callbacks:
            cb(result)
        return result

    # 1. Space-filling start (skipped on warm restart, like gp_minimize).
    n_init = 0 if x0 else min(n_initial_points, n_calls)
    initial = (Sobol().generate(space.dimensions, n_init, random_state=random_state)
               if n_init else [])
    result = None
    for x in initial:
        result = record(x)

    # 2. Claude-guided iterations.
    for _ in range(n_calls - n_init):
        remaining = n_calls - (len(Xi) - n_prior)
        user = (
            f"Measurements so far ({len(Xi)}):\n"
            f"{_history_table(Xi, yi, stats, param_cfgs, n_prior)}\n\n"
            f"Measurements left in this campaign, including the next one: "
            f"{remaining}. Choose the next point."
        )
        decision = _ask_claude(client, model, effort, max_tokens,
                               system, schema, user)

        x_norm = []
        for p in param_cfgs:
            lo, hi = p["bounds"]
            v = float(np.clip(decision["next_point"][p["name"]], lo, hi))
            x_norm.append(float(np.clip(bo.to_normalized(v, lo, hi), -1.0, 1.0)))

        point = ", ".join(f"{p['name']}={decision['next_point'][p['name']]}"
                          for p in param_cfgs)
        print(f"Claude proposes: {point}")
        if decision["thinking_summary"]:
            print(f"Claude's thinking (summary): {decision['thinking_summary']}")
        if decision_log:
            with open(decision_log, "a") as f:
                f.write(json.dumps({
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "iteration": len(Xi) + 1, "model": model, **decision,
                }) + "\n")
        result = record(x_norm)

    if result is None:
        result = create_result(Xi, yi, space, rng, specs)
    return result


def build_claude_call(opt_cfg: dict, space: list, objective_fn, callback,
                      param_cfgs: list, obj_cfg: dict, observations: list,
                      decision_log: str, x0=None, y0=None):
    """Same contract as bo_core.build_optimizer_call, for type 'claude'."""
    kwargs = {
        "func":             objective_fn,
        "dimensions":       space,
        "n_calls":          int(opt_cfg["n_calls"]),
        "n_initial_points": int(opt_cfg.get("n_initial_points", 8)),
        "random_state":     opt_cfg.get("random_state", 42),
        "callback":         [callback],
        "param_cfgs":       param_cfgs,
        "obj_cfg":          obj_cfg,
        "observations":     observations,
        "decision_log":     decision_log,
        "x0":               x0,
        "y0":               y0,
    }
    for key in _CLAUDE_KEYS:
        if key in opt_cfg:
            kwargs[key] = opt_cfg[key]
    return claude_minimize, kwargs
