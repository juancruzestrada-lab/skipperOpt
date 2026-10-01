# skipperOpt

Bayesian optimization of Skipper-CCD operating parameters with an LTA readout.

## Two ways to run

| Driver | What it is |
|---|---|
| `optimize_sensor_LTA.py` | Original single-process driver. |
| `optimize_agents.py` | Same optimization, split into three agents running in separate processes. |

Both take the same options and config and write the same output files:

```bash
python optimize_agents.py --config config_skipper.json
python optimize_agents.py --config config_skipper.json --amplifier 2
python optimize_agents.py --config config_skipper.json --resume images/skipper/ai/<date>/gp_results.csv
```

## The agents

```
                 acquire(x_norm) ──►  AcquisitionAgent   (ESP32 LED + LTA)
OptimizerAgent   ◄── image_path          expose → set parameters → read
(skopt + CSV)
                 evaluate(image_path) ►  ObjectiveAgent    (no hardware)
                 ◄── F, stats                read → stats → F
```

- **AcquisitionAgent** (`agents/acquisition.py`) is the only one that touches
  hardware. Each request: expose, set the parameters, read out, and report
  the new image path.
- **ObjectiveAgent** (`agents/objective.py`) computes F from that image with
  `image_analysis`, and also returns the image statistics (noise, charge, gain).
- **OptimizerAgent** (`agents/optimizer.py`) runs `gp_minimize` (or forest /
  gbrt / dummy) through `bo_core` exactly as before. The function skopt calls
  just sends one request to each of the other two agents.

`bo_core.py`, `image_analysis.py`, `lta_control.py` and the config are
unchanged and shared by both drivers.

Messages are plain JSON dicts (`agents/protocol.py`). Each run also writes
`<run>_messages.jsonl` next to the progress CSV with every request and reply,
which is handy for debugging (turn off with `--no-message-log`).

If an agent raises an error, the run stops with that agent's traceback and
the other agent processes are shut down.

`gp_results.csv` is rewritten after every iteration (not only at the end),
so a run that stops early for any reason can be continued with
`--resume <output dir>/gp_results.csv`.

## Claude as the optimizer

Set the optimizer type to `"claude"` (see `config_skipper_claude.json`) and
Claude chooses the points instead of the Gaussian process:

```bash
pip install anthropic
# Replace the text in quotes with your own key from
# https://platform.claude.com (API Keys). It starts with sk-ant-
export ANTHROPIC_API_KEY='sk-ant-REPLACE-WITH-YOUR-KEY'
python optimize_agents.py --config config_skipper_claude.json
```

- The first `n_initial_points` are a Sobol design, as in the GP runs; after
  that, each iteration Claude sees every measurement so far (parameters in
  physical units, F, and the image statistics noise/charge/gain), explains
  its choice, and returns the next point as JSON. Points are clipped to
  the bounds.
- `model` (default `claude-opus-5-5`), `effort` (`low` … `max`, default
  `high`) and free-text `notes` for Claude go in the `optimizer` block.
- Each proposed point and a summary of Claude's thinking (returned by the
  API) are printed and saved to `<run>_claude_decisions.jsonl`. The prompt
  never asks Claude to write out its reasoning in the answer: Opus 5.5
  declines that as `reasoning_extraction`.
- Progress CSV, `gp_results.csv`, warm restart (`--resume`), the `.pkl`
  dump and the convergence plot work exactly as with `gp`, so GP and Claude
  campaigns can be compared directly or resumed from one another.
- Cost is one API call per guided iteration (22 calls for the example).
  Each iteration prints the tokens used and a cost estimate plus the running
  campaign total; the end of the run prints a summary. The same numbers are
  saved per iteration in `<run>_claude_decisions.jsonl` and in the result
  `.pkl` (`specs["usage"]`). Estimates use list prices; the Console's Usage
  and Cost pages show what was actually billed.
- If the API is temporarily unavailable (overloaded, rate limited, server
  or network error), the request is retried with growing waits for up to
  about 15 minutes before the run stops. A bad key or bad request stops
  the run immediately.

Code: `agents/claude_optimizer.py`. The acquisition and objective agents are
unchanged.

### Adding an LLM supervisor later

Every agent answers `handle({"kind": ..., "payload": {...}})` with a JSON
dict, and each request kind maps to one `on_<kind>()` method. Those methods
can be exposed as tools to a Claude agent (e.g. via the Claude Agent SDK)
without changing the agents, for example a supervisor that reads the
`stats` from each evaluation and flags bad images before they reach the
optimizer.

## Tests

`tests/` runs both drivers against simulated hardware (`tests/fake_hw`: a
fake `lta.sh`, ESP32 and `fitsio`) and checks they give identical results,
including warm restart, and checks the Claude optimizer with a fake
Claude client (no network or API key needed):

```bash
pip install scikit-optimize pandas matplotlib pytest anthropic
python -m pytest tests -v
```
