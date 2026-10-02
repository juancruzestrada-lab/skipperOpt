# Notes for Claude

- The lab machine runs Python as `python3` (there is no `python`). Always write
  commands as `python3 ...` and `python3 -m pip install ...`.
- The four original modules (`optimize_sensor_LTA.py`, `bo_core.py`,
  `image_analysis.py`, `lta_control.py`) are the user's code; change them only
  when asked.
- The config `amplifier` value is the FITS HDU index: amplifier N (numbered
  0-3) is `"amplifier": N+1`, because HDU 0 of the .fz file is empty.
- Tests: `python3 -m pytest tests` (simulated hardware and a fake Claude; no
  hardware, network or API key needed).
- The lab notebook (`claude_notebook.md`, read and appended with `logbook.py`)
  is append-only. Never edit or delete past entries, and never suggest doing
  so; corrections are added as new entries.
