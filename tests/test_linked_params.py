"""
Parameters whose lta_var is a list (e.g. "hh" -> h1ah, h1bh, h2ch, h3ah,
h3bh): one optimized value sent to every listed LTA variable.

    python3 -m pytest tests -v
"""

import glob
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE_HW = os.path.join(REPO, "tests", "fake_hw")
sys.path[:0] = [REPO, FAKE_HW]

from agents.acquisition import expand_linked   # noqa: E402

HH = ["h1ah", "h1bh", "h2ch", "h3ah", "h3bh"]
HL = ["h1al", "h1bl", "h2cl", "h3al", "h3bl"]


def test_expand_linked():
    cfgs = [{"name": "Vr", "lta_var": "vr"},
            {"name": "hh", "lta_var": ["h1ah", "h2ch"]}]
    out, xs = expand_linked(cfgs, [0.1, -0.5])
    assert [c["lta_var"] for c in out] == ["vr", "h1ah", "h2ch"]
    assert [c["name"] for c in out] == ["Vr", "hh (h1ah)", "hh (h2ch)"]
    assert out[0] is cfgs[0]                       # single-variable entries untouched
    assert list(xs) == [0.1, -0.5, -0.5]


def test_hh_hl_set_all_phases(tmp_path):
    with open(os.path.join(REPO, "config_compare_gp.json")) as f:
        cfg = json.load(f)
    names = [p["name"] for p in cfg["parameters"]]
    assert names[-2:] == ["hh", "hl"]
    cfg["exposure_time"] = 0
    cfg["image"]["output_base"] = str(tmp_path / "images")
    cfg["optimizer"].update({"n_calls": 3, "n_initial_points": 3})

    # Wrap the fake LTA to record every command it receives.
    calls = tmp_path / "lta_calls.log"
    wrapper = tmp_path / "lta.sh"
    wrapper.write_text(f'#!/bin/sh\necho "$@" >> {calls}\nexec {sys.executable} '
                       f'{os.path.join(FAKE_HW, "fake_lta.py")} "$@"\n')
    wrapper.chmod(0o755)
    cfg["lta"]["script"] = str(wrapper)
    (tmp_path / "cfg.json").write_text(json.dumps(cfg))

    env = dict(os.environ, PYTHONPATH=os.pathsep.join([FAKE_HW, REPO]),
               FAKE_LTA_STATE=str(tmp_path / "state.json"), MPLBACKEND="Agg")
    proc = subprocess.run([sys.executable, "optimize_agents.py", "--config",
                           str(tmp_path / "cfg.json"), "--amplifier", "1"],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    sets = [l.split()[1:] for l in calls.read_text().splitlines() if l.split()[1:2] == ["set"]]
    per_image = {}
    for _, var, val in sets:
        per_image.setdefault(var, []).append(float(val))
    for group, (lo, hi) in ((HH, (-10, 10)), (HL, (-10, 10))):
        values = np.array([per_image[v] for v in group])      # 5 vars x 3 images
        assert values.shape == (5, 3)
        assert np.all(values == values[0])                    # same value on every phase
        assert np.all((values >= lo) & (values <= hi))

    (progress,) = glob.glob(str(tmp_path / "images" / "skipper" / "ai" / "*" / "*_results-skipper-*.csv"))
    cols = pd.read_csv(progress).columns
    assert "hh (current)" in cols and "hl (current)" in cols
