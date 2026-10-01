"""
Tests for the Claude optimizer (agents/claude_optimizer.py) using a fake
Claude client: no network, no API key.

    python -m pytest tests -v
"""

import glob
import json
import os
import subprocess
import sys

import pandas as pd
import pytest
from skopt.space import Real

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests", "fake_hw")]

import bo_core as bo                                   # noqa: E402
import agents.claude_optimizer as co                    # noqa: E402
from agents.claude_optimizer import claude_minimize    # noqa: E402

PARAMS = [
    {"name": "Vdd", "bounds": [-23, -10], "precision": 1},
    {"name": "delay", "bounds": [10, 30], "precision": 0},
]
OBJ = {"max_baseline": 1000, "penalties": []}
SPACE = [Real(-1.0, 1.0, name=f"x{i}") for i in range(len(PARAMS))]


def quadratic(x):
    vdd = bo.from_normalized(x[0], -23, -10)
    delay = bo.from_normalized(x[1], 10, 30)
    return (vdd + 17) ** 2 + 0.1 * (delay - 18) ** 2


class APIError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class FakeClient:
    """Returns scripted replies (or raises scripted errors) and records requests."""

    def __init__(self, points, errors=()):
        self.points, self.requests = list(points), []
        self.errors = list(errors)
        self.beta = self
        self.messages = self

    def create(self, **params):
        self.requests.append(params)
        if self.errors:
            raise self.errors.pop(0)
        reply = {"next_point": self.points.pop(0)}
        from types import SimpleNamespace as NS
        return NS(stop_reason="end_turn", stop_details=None,
                  content=[NS(type="text", text=json.dumps(reply))])


def test_loop_callbacks_and_result(tmp_path):
    client = FakeClient([{"Vdd": -17, "delay": 18}, {"Vdd": -99, "delay": 50}])
    seen = []
    log = tmp_path / "decisions.jsonl"
    res = claude_minimize(quadratic, SPACE, n_calls=6, param_cfgs=PARAMS,
                          obj_cfg=OBJ, n_initial_points=4, random_state=1,
                          callback=lambda r: seen.append(len(r.x_iters)),
                          decision_log=str(log), client=client)

    assert seen == [1, 2, 3, 4, 5, 6]
    assert len(client.requests) == 2
    # Claude's first proposal is the true optimum.
    assert res.fun == pytest.approx(0.0, abs=1e-9)
    assert res.x == pytest.approx([bo.to_normalized(-17, -23, -10),
                                   bo.to_normalized(18, 10, 30)])
    # Out-of-bounds proposal is clipped to the bounds.
    assert res.x_iters[-1] == pytest.approx([-1.0, 1.0])
    assert [json.loads(l)["iteration"] for l in open(log)] == [5, 6]
    assert all("thinking_summary" in json.loads(l) for l in open(log))

    # Results save exactly like a skopt run.
    bo.save_results(res, str(tmp_path) + "/", "Oct-01-2026_results-t-000",
                    "claude", PARAMS)
    df = pd.read_csv(tmp_path / "gp_results.csv")
    assert list(df.columns) == ["param_0", "param_1", "objective"]
    assert len(df) == 6


def test_request_contents():
    client = FakeClient([{"Vdd": -15, "delay": 20}])
    stats = []

    def func(x):
        stats.append({"noise_overscan": 3.2, "noise_active": 9.0,
                      "charge_overscan": 1000.0, "charge_active": 1100.0,
                      "gain": 100.0})
        return quadratic(x)

    claude_minimize(func, SPACE, n_calls=3, param_cfgs=PARAMS, obj_cfg=OBJ,
                    n_initial_points=2, random_state=1, observations=stats,
                    notes="Vdd above -12 V is unsafe.", client=client)

    (req,) = client.requests
    assert req["model"] == "claude-opus-5-5"
    assert req["fallbacks"] == "default"
    assert req["output_config"]["effort"] == "high"
    assert req["thinking"] == {"type": "adaptive", "display": "summarized"}
    schema = req["output_config"]["format"]["schema"]
    assert schema["required"] == ["next_point"]
    assert schema["properties"]["next_point"]["required"] == ["Vdd", "delay"]
    system = req["system"][0]["text"]
    assert "- Vdd: [-23, -10]" in system and "unsafe" in system
    # Asking for reasoning in the answer gets declined as reasoning_extraction.
    assert "reasoning" not in system.lower()
    user = req["messages"][0]["content"]
    assert "Measurements so far (2)" in user and "3.2" in user
    assert "Measurements left in this campaign, including the next one: 1" in user


def test_usage_and_cost(tmp_path, capsys):
    from types import SimpleNamespace as NS

    class UsageClient(FakeClient):
        def create(self, **params):
            r = super().create(**params)
            r.model = params["model"]
            r.usage = NS(input_tokens=1000, output_tokens=2000,
                         cache_creation_input_tokens=3000,
                         cache_read_input_tokens=4000)
            return r

    log = tmp_path / "decisions.jsonl"
    client = UsageClient([{"Vdd": -17, "delay": 18}, {"Vdd": -16, "delay": 19}])
    res = claude_minimize(quadratic, SPACE, n_calls=3, param_cfgs=PARAMS,
                          obj_cfg=OBJ, n_initial_points=1, random_state=1,
                          decision_log=str(log), client=client)

    # Opus 5.5: $4 in, $20 out, $5 cache write, $0.20 cache read per MTok.
    per_request = (1000 * 4 + 2000 * 20 + 3000 * 5 + 4000 * 0.20) / 1e6
    entries = [json.loads(l) for l in open(log)]
    assert [e["cost_usd"] for e in entries] == pytest.approx([per_request] * 2)
    assert entries[0]["usage"]["cache_read_input_tokens"] == 4000
    assert res.specs["usage"]["requests"] == 2
    assert res.specs["usage"]["output_tokens"] == 4000
    assert res.specs["usage"]["cost_usd_estimate"] == pytest.approx(2 * per_request)
    out = capsys.readouterr().out
    assert "Claude tokens: 8000 in, 2000 out" in out
    assert "Claude usage: 2 requests, 16000 input tokens (8000 from cache)" in out


def test_cost_estimate_by_model():
    u = {"input_tokens": 1_000_000, "output_tokens": 0,
         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    assert co.estimate_cost("claude-opus-5-5", u) == pytest.approx(4.0)
    assert co.estimate_cost("claude-opus-5", u) == pytest.approx(5.0)
    assert co.estimate_cost("claude-haiku-4-5-20251001", u) == pytest.approx(1.0)
    assert co.estimate_cost("some-future-model", u) is None


def test_temporary_api_errors_are_retried(monkeypatch):
    waits = []
    monkeypatch.setattr(co, "_sleep", waits.append)
    client = FakeClient([{"Vdd": -17, "delay": 18}],
                        errors=[APIError(529), APIError(500)])
    res = claude_minimize(quadratic, SPACE, n_calls=2, param_cfgs=PARAMS,
                          obj_cfg=OBJ, n_initial_points=1, random_state=1,
                          client=client)
    assert waits == [15, 30]
    assert len(client.requests) == 3
    assert len(res.x_iters) == 2


def test_permanent_api_errors_are_not_retried(monkeypatch):
    waits = []
    monkeypatch.setattr(co, "_sleep", waits.append)
    client = FakeClient([], errors=[APIError(401)])
    with pytest.raises(APIError):
        claude_minimize(quadratic, SPACE, n_calls=2, param_cfgs=PARAMS,
                        obj_cfg=OBJ, n_initial_points=1, random_state=1,
                        client=client)
    assert waits == []


def test_retries_give_up_eventually(monkeypatch):
    waits = []
    monkeypatch.setattr(co, "_sleep", waits.append)
    client = FakeClient([], errors=[APIError(529)] * 20)
    with pytest.raises(APIError):
        claude_minimize(quadratic, SPACE, n_calls=2, param_cfgs=PARAMS,
                        obj_cfg=OBJ, n_initial_points=1, random_state=1,
                        client=client)
    assert waits == co._RETRY_WAITS


def test_warm_start_skips_initial_design():
    client = FakeClient([{"Vdd": -17, "delay": 18}, {"Vdd": -16, "delay": 18}])
    x0 = [[0.0, 0.0], [0.5, -0.5]]
    y0 = [quadratic(x) for x in x0]
    res = claude_minimize(quadratic, SPACE, n_calls=2, param_cfgs=PARAMS,
                          obj_cfg=OBJ, x0=x0, y0=y0, client=client)
    assert len(res.x_iters) == 4
    assert res.x_iters[:2] == x0
    assert "Measurements so far (2)" in client.requests[0]["messages"][0]["content"]


def run_claude_campaign(tmp_path, n_calls, extra_env=None, resume=None):
    with open(os.path.join(REPO, "config_skipper.json")) as f:
        cfg = json.load(f)
    fake_hw = os.path.join(REPO, "tests", "fake_hw")
    cfg["lta"]["script"]        = os.path.join(fake_hw, "fake_lta.py")
    cfg["exposure_time"]        = 0
    cfg["image"]["output_base"] = str(tmp_path / "images")
    cfg["optimizer"] = {"type": "claude", "n_calls": n_calls,
                        "n_initial_points": 4, "random_state": 15}
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))

    env = dict(os.environ, MPLBACKEND="Agg",
               FAKE_LTA_STATE=str(tmp_path / "state.json"),
               PYTHONPATH=os.pathsep.join(
                   [os.path.join(REPO, "tests", "fake_claude"), fake_hw, REPO]),
               **(extra_env or {}))
    cmd = [sys.executable, "optimize_agents.py", "--config", str(cfg_path)]
    if resume:
        cmd += ["--resume", resume]
    return subprocess.run(cmd, cwd=REPO, env=env, capture_output=True,
                          text=True, timeout=300)


def test_interrupted_claude_run_can_be_resumed(tmp_path):
    # Claude fails permanently on its 3rd request: 4 Sobol + 2 guided points done.
    proc = run_claude_campaign(tmp_path, 8, {"FAKE_CLAUDE_FAIL_AFTER": "2"})
    assert proc.returncode != 0
    assert "fake permanent API failure" in proc.stderr
    (out,) = glob.glob(str(tmp_path / "images" / "skipper" / "ai" / "*"))
    saved = os.path.join(out, "gp_results.csv")
    assert len(pd.read_csv(saved)) == 6

    proc = run_claude_campaign(tmp_path, 2, resume=saved)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Loaded 6 prior evaluations" in proc.stdout
    assert len(pd.read_csv(saved)) == 8


def test_agents_end_to_end_with_claude(tmp_path):
    proc = run_claude_campaign(tmp_path, 6)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Starting CLAUDE optimization" in proc.stdout
    assert proc.stdout.count("Claude proposes:") == 2
    assert "Claude usage: 2 requests" in proc.stdout
    assert proc.stdout.count("(summary): Step from measurement") == 2

    (out,) = glob.glob(str(tmp_path / "images" / "skipper" / "ai" / "*"))
    assert len(pd.read_csv(os.path.join(out, "gp_results.csv"))) == 6
    (decisions,) = glob.glob(os.path.join(out, "*_claude_decisions.jsonl"))
    assert len(open(decisions).readlines()) == 2
    assert glob.glob(os.path.join(out, "*_claude_result.pkl"))
