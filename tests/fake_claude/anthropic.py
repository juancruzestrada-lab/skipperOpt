"""
Stand-in for the anthropic SDK (tests only).

Answers each request with a point 10% of the way from the best measurement
so far toward the middle of the bounds, read back from the history table
in the prompt, so runs are deterministic and need no network or API key. With
FAKE_CLAUDE_FAIL_AFTER=N set, every request after the N-th fails.
"""
import json
import os
from types import SimpleNamespace

calls = []


def _propose(params):
    system = params["system"][0]["text"]
    names, bounds = [], []
    for line in system.splitlines():
        if line.startswith("- ") and ": [" in line:
            name, rest = line[2:].split(": [", 1)
            lo, hi = rest.split("]", 1)[0].split(",")
            names.append(name)
            bounds.append((float(lo), float(hi)))
    rows = [r.split(" | ") for r in params["messages"][0]["content"].splitlines()
            if r[:1].isdigit()]
    best = min(rows, key=lambda r: float(r[len(names) + 1]))
    point = {n: float(best[i + 1]) + 0.1 * ((lo + hi) / 2 - float(best[i + 1]))
             for i, (n, (lo, hi)) in enumerate(zip(names, bounds))}
    return (f"Step from measurement #{best[0]} toward the centre.",
            {"next_point": point})


class _Messages:
    def create(self, **params):
        calls.append(params)
        fail_after = os.environ.get("FAKE_CLAUDE_FAIL_AFTER")
        if fail_after is not None and len(calls) > int(fail_after):
            raise RuntimeError("fake permanent API failure")
        summary, answer = _propose(params)
        return SimpleNamespace(stop_reason="end_turn", stop_details=None,
                               content=[SimpleNamespace(type="thinking",
                                                        thinking=summary),
                                        SimpleNamespace(type="text",
                                                        text=json.dumps(answer))])


class Anthropic:
    def __init__(self, *args, **kwargs):
        self.beta = SimpleNamespace(messages=_Messages())
