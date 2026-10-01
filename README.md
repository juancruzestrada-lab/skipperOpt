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

### Lab notebook: carrying lessons between campaigns

Each API call starts from scratch, so on its own Claude remembers nothing
from earlier campaigns. The lab notebook gives it that memory:

- At the end of every Claude campaign, Claude writes a short entry: best
  region, settings that gave broken images and how they showed in the
  statistics, which parameters mattered, suggestions for the next run. The
  code adds a header with the date, module, number of measurements and the
  best point. Entries are appended to
  `<output_base>/<module>/claude_notebook.md` (one notebook per module,
  shared by all dates).
- At the start of every Claude campaign the notebook is loaded into Claude's
  instructions as prior knowledge, with the instruction to trust current
  measurements over old entries when they disagree (temperature, cabling or
  firmware may have changed). Only the newest ~30,000 characters are sent.
- It is a plain Markdown file: read it, correct it, add your own notes,
  delete entries that no longer apply.
- Set `"notebook": "<path>"` in the `optimizer` block for another location
  (e.g. one notebook per detector), or `"notebook": false` to turn it off.
- If writing the entry fails, the campaign's results are saved anyway.
  Interrupted campaigns write no entry.

Code: `agents/claude_optimizer.py`. The acquisition and objective agents are
unchanged.

### Adding an LLM supervisor later

Every agent answers `handle({"kind": ..., "payload": {...}})` with a JSON
dict, and each request kind maps to one `on_<kind>()` method. Those methods
can be exposed as tools to a Claude agent (e.g. via the Claude Agent SDK)
without changing the agents, for example a supervisor that reads the
`stats` from each evaluation and flags bad images before they reach the
optimizer.

## GP vs. Claude comparison on one amplifier

Three ready-made configs, all for amplifier 1 (`"amplifier": 2`: the value is
the FITS HDU index, one higher than the amplifier number):

| Config | What it does |
|---|---|
| `config_compare_reference.json` | 3 images at a fixed reference point (bounds collapsed to one value) |
| `config_compare_gp.json` | GP, 30 images: 8 Sobol + 22 guided |
| `config_compare_claude.json` | Claude, 30 images: 8 Sobol + 22 guided, lab notebook off |

Run them back to back in one session:

```bash
python optimize_agents.py --config config_compare_reference.json
python optimize_agents.py --config config_compare_gp.json
python optimize_agents.py --config config_compare_reference.json
python optimize_agents.py --config config_compare_claude.json
python optimize_agents.py --config config_compare_reference.json
```

The three reference checks should agree; if they do not, the detector state
changed during the comparison. Optimizer type `"dummy"` cannot be used for
fixed-point runs: `bo_core` passes it `n_initial_points`, which
`dummy_minimize` does not accept.

## Tests

`tests/` runs both drivers against simulated hardware (`tests/fake_hw`: a
fake `lta.sh`, ESP32 and `fitsio`) and checks they give identical results,
including warm restart, and checks the Claude optimizer with a fake
Claude client (no network or API key needed):

```bash
pip install scikit-optimize pandas matplotlib pytest anthropic
python -m pytest tests -v
```
