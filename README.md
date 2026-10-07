# skipperOpt

Bayesian optimization of Skipper-CCD operating parameters with an LTA readout.

## Two ways to run

| Driver | What it is |
|---|---|
| `optimize_sensor_LTA.py` | Original single-process driver. |
| `optimize_agents.py` | Same optimization, split into three agents running in separate processes. |

Both take the same options and config and write the same output files:

```bash
python3 optimize_agents.py --config config_skipper.json
python3 optimize_agents.py --config config_skipper.json --amplifier 2
python3 optimize_agents.py --config config_skipper.json --resume images/skipper/ai/<date>/gp_results.csv
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
python3 -m pip install anthropic
# Replace the text in quotes with your own key from
# https://platform.claude.com (API Keys). It starts with sk-ant-
export ANTHROPIC_API_KEY='sk-ant-REPLACE-WITH-YOUR-KEY'
python3 optimize_agents.py --config config_skipper_claude.json
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
from earlier campaigns. The lab notebook gives it that memory, and gives you
a record of every run:

- **Every run adds an entry**, GP or Claude, also when it is interrupted
  (marked `interrupted (...)`). The header gives date, module, amplifier,
  optimizer, number of measurements and the best point; the body starts with
  **run facts** recorded by the code: config, images, times, best three
  points, signal (gain) and overscan-noise statistics, and how many images had
  negative gain.
- **Claude runs** add Claude's analysis below the facts: best region, settings
  that gave broken images, which parameters mattered, suggestions.
- **Claude reads the notebook** at the start of each campaign as prior
  knowledge, with the instruction to trust current measurements over old
  entries, and is told which amplifier is in use. Only the newest ~30,000
  characters are sent.
- File: `<output_base>/<module>/claude_notebook.md` (one per module). Options
  in the `optimizer` block: `"notebook": "<path>"` for another file,
  `"notebook": false` to turn it off, `"notebook_read": false` to keep writing
  entries but not show the notebook to Claude (used by
  `config_compare_claude.json` for a fair comparison).
- It is a plain Markdown file and **append-only**: past entries are never
  changed. To correct an entry, add a new one saying what it corrects;
  Claude is told that later entries take precedence.

Reading and adding entries from the command line (`logbook.py`):

```bash
python3 logbook.py list                       # one line per entry
python3 logbook.py show                       # latest entry; "show 3 5" or "show all"
python3 logbook.py search dropout             # entries containing a word
python3 logbook.py add -m "LED replaced, gain back to 1e5 ADU" --amp 3
python3 logbook.py add --amp 3                # write the entry in your editor ($EDITOR, default nano)
```

The notebook is located from `config_skipper_claude.json` (or `--config`,
or `--notebook <path>`). Your entries are headed `operator note`, with the
amplifier if given (`--amp` is the amplifier number 0-3); Claude is told to
treat them as first-hand observations. Claude's own entries now also record
the amplifier, and each campaign tells Claude which amplifier is in use.

Code: `agents/claude_optimizer.py`. The acquisition and objective agents are
unchanged.

### Adding an LLM supervisor later

Every agent answers `handle({"kind": ..., "payload": {...}})` with a JSON
dict, and each request kind maps to one `on_<kind>()` method. Those methods
can be exposed as tools to a Claude agent (e.g. via the Claude Agent SDK)
without changing the agents, for example a supervisor that reads the
`stats` from each evaluation and flags bad images before they reach the
optimizer.

## Optimized parameters

Each entry of `"parameters"` in the config is one optimized dimension
(`name`, `command_type`, `lta_var`, `bounds`, `precision`, and a `_comment`
that Claude reads as the parameter's description). With
`optimize_agents.py`, `lta_var` may also be a **list**: the one value is then
sent to every listed LTA variable. The Claude and comparison configs use this
for the horizontal clocks, as in `voltage_skp_lta_v2.sh`:

- `hh` -> `h1ah h1bh h2ch h3ah h3bh` (bounds -2.9 to -1.1 V)
- `hl` -> `h1al h1bl h2cl h3al h3bl` (bounds -9.9 to -3.6 V)

The bounds keep the script's ordering constraints (th > hh > tl, hh > sh,
tl > hl > sl, sh > hl) with the other clock voltages at the script's values.
The original `optimize_sensor_LTA.py` does not understand the list form; use
it only with configs whose `lta_var` entries are single names (such as
`config_skipper.json`).

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
python3 optimize_agents.py --config config_compare_reference.json
python3 optimize_agents.py --config config_compare_gp.json
python3 optimize_agents.py --config config_compare_reference.json
python3 optimize_agents.py --config config_compare_claude.json
python3 optimize_agents.py --config config_compare_reference.json
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
python3 -m pip install scikit-optimize pandas matplotlib pytest anthropic
python3 -m pytest tests -v
```
