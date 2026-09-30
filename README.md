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
including warm restart:

```bash
pip install scikit-optimize pandas matplotlib pytest
python -m pytest tests -v
```
