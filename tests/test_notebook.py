"""
Tests for agents/notebook.py (entry format and loading).

    python3 -m pytest tests -v
"""

import os
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests", "fake_hw")]

from agents import notebook as nb   # noqa: E402

PARAMS = [{"name": "Vdd", "bounds": [-23, -10], "precision": 1},
          {"name": "delay", "bounds": [10, 30], "precision": 0}]


def rec(x, F, gain, noise=700, image="optimize_1.fz"):
    return {"x": x, "F": F, "image": image,
            "stats": {"gain": gain, "noise_overscan": noise}}


def test_make_entry_facts_and_header():
    records = [rec([0.0, 0.0], 0.5, 1400, image="optimize_10.fz"),
               rec([-0.2, 0.4], 0.02, 30000, 650, "optimize_11.fz"),
               rec([0.5, -0.5], 0.9, -300, 900, "optimize_12.fz")]
    header, body = nb.make_entry(
        records, PARAMS, "skipper", 4, "gp", "config_compare_gp.json",
        datetime(2026, 10, 2, 16, 9), datetime(2026, 10, 2, 16, 18))
    assert "| module skipper | amp 3 (HDU 4) | gp | 3 measurements (3 new) | best F = 0.02 at Vdd=-17.8, delay=24" in header
    assert body.startswith("**Run facts** (recorded by the code)")
    assert "Optimizer: gp; config: config_compare_gp.json; images optimize_10.fz to optimize_12.fz; 16:09-16:18." in body
    assert "Best F this run: 0.02 at (Vdd=-17.8, delay=24.0), image optimize_11.fz. Next: 0.5 at" in body
    assert "Signal (gain = active minus overscan median, ADU): median 1400, max 30000; 1 of 3 images with negative gain." in body
    assert "Overscan noise (ADU): median 700, range 650-900." in body


def test_make_entry_resumed_interrupted_with_lessons():
    header, body = nb.make_entry(
        [rec([0.0, 0.0], 0.3, 5000)], PARAMS, "skipper", None, "claude", "",
        None, None, x0=[[0.1, 0.1]], y0=[0.1],
        lessons="## Stray heading\n\n- Lesson.", status="interrupted (KeyboardInterrupt)")
    assert "| claude | 2 measurements (1 new) | best F = 0.1 at" in header
    assert header.endswith("| interrupted (KeyboardInterrupt)")
    assert "amp" not in header
    assert "resumed from 1 earlier measurements" in body
    assert body.endswith("- Lesson.") and "Stray heading" not in body


def test_append_creates_file_and_strips_heading(tmp_path):
    path = tmp_path / "sub" / "nb.md"
    nb.append_notebook_entry(str(path), "2026-10-02 | x", "# heading\n\ntext")
    text = path.read_text()
    assert text.startswith("# Claude lab notebook")
    assert text.endswith("\n## 2026-10-02 | x\n\ntext\n")


def test_load_notebook_keeps_newest_entries(tmp_path):
    path = tmp_path / "nb.md"
    path.write_text("# Claude lab notebook\n" +
                    "".join(f"\n## entry {i}\n\n" + "x" * 100 + "\n" for i in range(10)))
    text = nb.load_notebook(str(path), max_chars=400)
    assert text.startswith("[older entries omitted]")
    assert "## entry 9" in text and "## entry 0" not in text
    assert nb.load_notebook(str(tmp_path / "missing.md")) == ""
