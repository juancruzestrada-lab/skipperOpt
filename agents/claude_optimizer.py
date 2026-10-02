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

Every decision (proposed point, a summary of Claude's thinking as returned
by the API, tokens used and a cost estimate) is appended to <run>_claude_decisions.jsonl next to
the progress CSV. The prompt deliberately does not ask Claude to write its
reasoning into the answer: Opus 5.5 declines such requests
("reasoning_extraction"), so the explanation comes from the summarized
thinking blocks instead.

Lab notebook
------------
The caller (agents/optimizer.py) passes the notebook text in as prior
knowledge (notebook_text) and, with lessons=True, Claude writes its
analysis of the campaign at the end; it is returned in
result.specs["lessons"] and the caller adds it to the notebook entry. See
agents/notebook.py.

Needs `python3 -m pip install anthropic` and an API key in ANTHROPIC_API_KEY (or an
`ant auth login` profile).
"""

import json
import os
import time
from datetime import datetime

import numpy as np
from skopt.sampler import Sobol
from skopt.space import Space
from skopt.utils import create_result

import bo_core as bo

from .notebook import amp_label

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
{setup}
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
{notes}{notebook}
Reply with the next point to measure."""

NOTEBOOK_SECTION = """
Lab notebook from previous campaigns on this setup (entries written at the \
end of earlier campaigns and by the operator; oldest first). The notebook is \
append-only: entries are never changed afterwards, so when a later entry \
corrects an earlier one, the later entry applies. \
Use it as prior knowledge, not as ground truth: conditions such as \
temperature, cabling or firmware may have changed since, so when the \
current measurements disagree with it, trust the current measurements. \
Each entry header names the module and, when recorded, the amplifier: an \
entry for a different amplifier describes a different readout channel. \
Entries marked "operator note" were written by the lab operator and are \
first-hand observations. Every entry starts with run facts recorded by the \
code; entries from GP or reference runs contain only those facts.

{text}
"""

NOTEBOOK_REQUEST = """The campaign is finished. Write a lab-notebook entry for future campaigns \
on this setup. Measurements of this campaign:
{table}

Cover, concisely (about 150-300 words, plain Markdown, no top-level heading):
- the best region found, with parameter values and F, and how reproducible it looked
- regions or settings that gave broken or useless images, and how that showed \
in the statistics (e.g. negative gain, very large overscan noise)
- which parameters F was most and least sensitive to
- concrete suggestions for the next campaign (bounds, starting points, what to test)
Record only what these measurements and earlier notebook entries support."""


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


# Temporary API errors (rate limit, server error, overloaded) and network
# problems are retried with growing waits, up to about 15 minutes in total,
# so a busy API does not end a campaign. Other errors (bad key, bad request)
# are raised immediately.
_RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
_RETRY_WAITS  = [15, 30, 60, 120, 180, 240, 300]   # seconds
_sleep        = time.sleep


def _is_temporary(err: Exception) -> bool:
    if getattr(err, "status_code", None) in _RETRY_STATUS:
        return True
    return type(err).__name__ in ("APIConnectionError", "APITimeoutError")


def _create_with_retry(client, **params):
    for wait in _RETRY_WAITS + [None]:
        try:
            return client.beta.messages.create(**params)
        except Exception as err:
            if wait is None or not _is_temporary(err):
                raise
            print(f"  Claude API temporarily unavailable ({type(err).__name__}); "
                  f"retrying in {wait} s...")
            _sleep(wait)


# Standard list prices, USD per million tokens:
# (input, output, cache write (5-minute), cache read). Estimates only; the
# Console's Usage and Cost pages are authoritative. Thinking tokens are
# billed as output and are included in output_tokens.
PRICES_PER_MTOK = {
    "claude-opus-5-5":   (4.00, 20.00, 5.00, 0.20),
    "claude-opus-5":     (5.00, 25.00, 6.25, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-haiku-4-5":  (1.00,  5.00, 1.25, 0.10),
}
_USAGE_FIELDS = ("input_tokens", "output_tokens",
                 "cache_creation_input_tokens", "cache_read_input_tokens")


def _usage_of(response) -> dict:
    usage = getattr(response, "usage", None)
    return {k: int(getattr(usage, k, 0) or 0) for k in _USAGE_FIELDS}


def estimate_cost(model: str, usage: dict):
    """USD estimate for the given token counts, or None for unknown models."""
    matches = [m for m in PRICES_PER_MTOK if model.startswith(m)]
    if not matches:
        return None
    p_in, p_out, p_write, p_read = PRICES_PER_MTOK[max(matches, key=len)]
    return (usage["input_tokens"] * p_in
            + usage["output_tokens"] * p_out
            + usage["cache_creation_input_tokens"] * p_write
            + usage["cache_read_input_tokens"] * p_read) / 1e6


def _fmt_cost(cost) -> str:
    return f"≈ ${cost:.3f}" if cost is not None else "cost unknown for this model"


def _request(client, model, effort, max_tokens, system, user, schema=None):
    """One Claude request. Returns (final text, thinking summary, accounting)."""
    output_config = {"effort": effort}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    response = _create_with_retry(
        client,
        model=model,
        max_tokens=max_tokens,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "adaptive", "display": "summarized"},
        output_config=output_config,
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude's reply was cut off; raise optimizer.max_tokens.")
    text = [b.text for b in response.content if b.type == "text"][-1]
    thinking = "\n".join(
        b.thinking for b in response.content
        if b.type == "thinking" and getattr(b, "thinking", "")
    )
    # A refusal fallback can answer with another model; price what ran.
    served_by = getattr(response, "model", None)
    served_by = served_by if isinstance(served_by, str) else model
    usage = _usage_of(response)
    return text, thinking, {"served_by": served_by, "usage": usage,
                            "cost_usd": estimate_cost(served_by, usage)}


def _ask_claude(client, model, effort, max_tokens, system, schema, user):
    text, thinking, accounting = _request(client, model, effort, max_tokens,
                                          system, user, schema)
    decision = json.loads(text)
    decision["thinking_summary"] = thinking
    decision.update(accounting)
    return decision


def claude_minimize(func, dimensions, n_calls, param_cfgs, obj_cfg,
                    n_initial_points=8, random_state=None, callback=None,
                    x0=None, y0=None, observations=None,
                    model=DEFAULT_MODEL, effort=DEFAULT_EFFORT, notes="",
                    max_tokens=16000, decision_log=None, client=None,
                    notebook_text="", lessons=False, module="", amplifier=None):
    """
    Minimize func over dimensions with Claude choosing the points.

    Parameters mirror skopt.gp_minimize where they overlap. Extra:
    param_cfgs, obj_cfg : config["parameters"], config["objective"]
    observations : list that the caller appends one stats dict to per
                   evaluation (optional; shown to Claude when present)
    client       : anthropic.Anthropic instance (created if None)
    notebook_text: lab notebook text, given to Claude as prior knowledge
    lessons      : at the end, ask Claude for a notebook entry analysing the
                   campaign; returned in result.specs["lessons"]
    module       : detector/module name
    amplifier    : config "amplifier" value (FITS HDU index); recorded as
                   amplifier number HDU-1 in the prompt and notebook headers
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

    setup = (f"\nCurrent setup: module {module or '?'}, {amp_label(amplifier)}.\n"
             if amplifier is not None else "")
    system = SYSTEM_PROMPT.format(
        setup=setup,
        parameters=_describe_parameters(param_cfgs),
        objective=_describe_objective(obj_cfg),
        notes=f"\nNotes from the operator:\n{notes}\n" if notes else "",
        notebook=(NOTEBOOK_SECTION.format(text=notebook_text)
                  if notebook_text else ""),
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
    total_usage = dict.fromkeys(_USAGE_FIELDS, 0)
    total_cost  = 0.0
    n_requests  = 0

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

        n_requests += 1
        for k in _USAGE_FIELDS:
            total_usage[k] += decision["usage"][k]
        if total_cost is not None:
            total_cost = (None if decision["cost_usd"] is None
                          else total_cost + decision["cost_usd"])
        u = decision["usage"]
        print(f"  Claude tokens: {u['input_tokens'] + u['cache_creation_input_tokens'] + u['cache_read_input_tokens']} in, "
              f"{u['output_tokens']} out, {_fmt_cost(decision['cost_usd'])}; "
              f"campaign so far {_fmt_cost(total_cost)}")
        if decision_log:
            with open(decision_log, "a") as f:
                f.write(json.dumps({
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "iteration": len(Xi) + 1, "model": model, **decision,
                }) + "\n")
        result = record(x_norm)

    if lessons and Xi:
        try:
            text, _, accounting = _request(
                client, model, effort, max_tokens, system,
                NOTEBOOK_REQUEST.format(
                    table=_history_table(Xi, yi, stats, param_cfgs, n_prior)))
            n_requests += 1
            for k in _USAGE_FIELDS:
                total_usage[k] += accounting["usage"][k]
            if total_cost is not None:
                total_cost = (None if accounting["cost_usd"] is None
                              else total_cost + accounting["cost_usd"])
            specs["lessons"] = text
        except Exception as err:
            print(f"\nWARNING: Claude could not write its notebook analysis ({err}); "
                  "the entry will contain the run facts only.")

    if n_requests:
        total_in = (total_usage["input_tokens"]
                    + total_usage["cache_creation_input_tokens"]
                    + total_usage["cache_read_input_tokens"])
        print(f"\nClaude usage: {n_requests} requests, {total_in} input tokens "
              f"({total_usage['cache_read_input_tokens']} from cache), "
              f"{total_usage['output_tokens']} output tokens, "
              f"{_fmt_cost(total_cost)} (estimate; see the Console for actual spend)")
    specs["usage"] = {"requests": n_requests, **total_usage,
                      "cost_usd_estimate": total_cost}

    if result is None:
        result = create_result(Xi, yi, space, rng, specs)
    return result


def build_claude_call(opt_cfg: dict, space: list, objective_fn, callback,
                      param_cfgs: list, obj_cfg: dict, observations: list,
                      decision_log: str, x0=None, y0=None,
                      notebook_text: str = "", lessons: bool = False,
                      module: str = "", amplifier: int = None):
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
        "notebook_text":    notebook_text,
        "lessons":          lessons,
        "module":           module,
        "amplifier":        amplifier,
    }
    for key in _CLAUDE_KEYS:
        if key in opt_cfg:
            kwargs[key] = opt_cfg[key]
    return claude_minimize, kwargs
