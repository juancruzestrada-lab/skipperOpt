"""
End-to-end check that optimize_agents.py reproduces optimize_sensor_LTA.py.

Both drivers run against simulated hardware (tests/fake_hw: a fake lta.sh,
ESP32 and fitsio) and must produce identical optimization results, progress
CSVs and image files.

    python3 -m pytest tests -v
"""

import glob
import json
import os
import subprocess
import sys

import pandas as pd
import pytest

REPO    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE_HW = os.path.join(REPO, "tests", "fake_hw")


def run_driver(script, run_dir, n_calls, n_initial_points, resume=None):
    os.makedirs(run_dir)
    with open(os.path.join(REPO, "config_skipper.json")) as f:
        cfg = json.load(f)
    cfg["lta"]["script"]               = os.path.join(FAKE_HW, "fake_lta.py")
    cfg["exposure_time"]               = 0
    cfg["image"]["output_base"]        = os.path.join(run_dir, "images")
    cfg["optimizer"]["n_calls"]        = n_calls
    cfg["optimizer"]["n_initial_points"] = n_initial_points
    cfg_path = os.path.join(run_dir, "config.json")
    with open(cfg_path, "w") as f:
        json.dump(cfg, f)

    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join([FAKE_HW, REPO]),
               FAKE_LTA_STATE=os.path.join(run_dir, "lta_state.json"),
               MPLBACKEND="Agg")
    cmd = [sys.executable, os.path.join(REPO, script), "--config", cfg_path]
    if resume:
        cmd += ["--resume", resume]
    proc = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    (out_dir,) = glob.glob(os.path.join(run_dir, "images", "skipper", "ai", "*"))
    return out_dir, proc.stdout


def outputs(out_dir):
    (progress,) = glob.glob(os.path.join(out_dir, "*_results-skipper-*.csv"))
    return {
        "gp_results": pd.read_csv(os.path.join(out_dir, "gp_results.csv")),
        "progress":   pd.read_csv(progress),
        "images":     sorted(os.path.basename(p)
                             for p in glob.glob(os.path.join(out_dir, "*.fz"))),
    }


def assert_same(a, b):
    pd.testing.assert_frame_equal(a["gp_results"], b["gp_results"])
    pd.testing.assert_frame_equal(a["progress"], b["progress"])
    assert a["images"] == b["images"]


@pytest.fixture(scope="module")
def fresh_runs(tmp_path_factory):
    base = tmp_path_factory.mktemp("fresh")
    orig, _     = run_driver("optimize_sensor_LTA.py", str(base / "orig"), 8, 4)
    agents, log = run_driver("optimize_agents.py",     str(base / "agents"), 8, 4)
    return orig, agents, log


def test_fresh_run_matches_original(fresh_runs):
    orig, agents, _ = fresh_runs
    a, b = outputs(orig), outputs(agents)
    assert len(a["gp_results"]) == 8
    assert_same(a, b)


def test_message_log(fresh_runs):
    _, agents, _ = fresh_runs
    (log_path,) = glob.glob(os.path.join(agents, "*_messages.jsonl"))
    msgs = [json.loads(line) for line in open(log_path)]
    sent = [m["kind"] for m in msgs if m["direction"] == "send"]
    assert sent == ["initial_exposure"] + ["acquire", "evaluate"] * 8
    replies = [m for m in msgs if m["direction"] == "recv"]
    assert all(m["ok"] for m in replies)
    scores = [m["payload"]["F"] for m in replies if "F" in m["payload"]]
    gp = pd.read_csv(os.path.join(agents, "gp_results.csv"))
    assert scores == pytest.approx(list(gp["objective"]), rel=1e-12)


def test_resume_matches_original(fresh_runs, tmp_path):
    orig, _, _ = fresh_runs
    prior = os.path.join(orig, "gp_results.csv")
    a, _ = run_driver("optimize_sensor_LTA.py", str(tmp_path / "orig"), 3, 4, prior)
    b, _ = run_driver("optimize_agents.py",     str(tmp_path / "agents"), 3, 4, prior)
    assert len(outputs(a)["gp_results"]) == 8 + 3
    assert_same(outputs(a), outputs(b))


def test_agent_failure_stops_run(tmp_path):
    with open(os.path.join(REPO, "config_skipper.json")) as f:
        cfg = json.load(f)
    cfg["lta"]["script"]        = os.path.join(FAKE_HW, "fake_lta.py")
    cfg["exposure_time"]        = 0
    cfg["image"]["output_base"] = str(tmp_path / "images")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([FAKE_HW, REPO]),
               FAKE_LTA_STATE=str(tmp_path / "state.json"), MPLBACKEND="Agg")
    proc = subprocess.run(
        [sys.executable, "optimize_agents.py", "--config", str(cfg_path),
         "--amplifier", "5"],   # no such image extension
        cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0
    assert "objective agent failed" in proc.stderr
