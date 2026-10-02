"""
Tests for logbook.py (reading the lab notebook and adding operator entries).

    python3 -m pytest tests -v
"""

import io
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import logbook   # noqa: E402

NOTEBOOK = """# Claude lab notebook

Written by the Claude optimizer at the end of each campaign and read at the start of the next one. Edit or delete entries freely.

## 2026-10-01 09:13 | module skipper | 30 measurements (30 new) | best F = 0.018867 at Vdd=-14.5

**Best region.** Tight cluster.

## 2026-10-02 15:15 | module skipper | 30 measurements (30 new) | best F = 0.0072334 at Vdd=-17.5

Signal decay and dropout after image 13.
"""


@pytest.fixture
def nb(tmp_path):
    path = tmp_path / "claude_notebook.md"
    path.write_text(NOTEBOOK)
    return str(path)


def run(capsys, *argv):
    logbook.main(list(argv))
    return capsys.readouterr().out


def test_list_and_show(nb, capsys):
    out = run(capsys, "--notebook", nb, "list")
    assert "2 entries" in out
    assert "[ 1] 2026-10-01 09:13 | module skipper" in out
    assert "Signal decay" in run(capsys, "--notebook", nb, "show")       # latest
    out = run(capsys, "--notebook", nb, "show", "1")
    assert "Tight cluster" in out and "Signal decay" not in out
    out = run(capsys, "--notebook", nb, "show", "all")
    assert "Tight cluster" in out and "Signal decay" in out
    with pytest.raises(SystemExit):
        run(capsys, "--notebook", nb, "show", "7")


def test_search(nb, capsys):
    out = run(capsys, "--notebook", nb, "search", "DROPOUT")
    assert "[2]" in out and "Tight cluster" not in out
    assert "No entries" in run(capsys, "--notebook", nb, "search", "xyz")


def test_add_message(nb, capsys):
    out = run(capsys, "--notebook", nb, "add", "-m", "LED replaced.",
              "--amp", "3", "--title", "hardware")
    assert "| amp 3 (HDU 4) | operator note | hardware" in out
    header, body = logbook.read_entries(nb)[-1]
    assert header.endswith("| amp 3 (HDU 4) | operator note | hardware")
    assert body == "LED replaced."
    assert len(logbook.read_entries(nb)) == 3
    with pytest.raises(SystemExit):
        run(capsys, "--notebook", nb, "add", "-m", "x", "--amp", "4")


def test_add_from_stdin_and_editor(nb, capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", io.StringIO("from a pipe\n"))
    run(capsys, "--notebook", nb, "add", "-m", "-")
    assert logbook.read_entries(nb)[-1][1] == "from a pipe"

    fake_editor = tmp_path / "ed.py"
    fake_editor.write_text("import sys\nopen(sys.argv[1], 'a').write('written in editor\\n')\n")
    monkeypatch.setenv("EDITOR", f"{sys.executable} {fake_editor}")
    run(capsys, "--notebook", nb, "add")
    assert logbook.read_entries(nb)[-1][1] == "written in editor"


def test_empty_entry_is_rejected(nb, capsys):
    with pytest.raises(SystemExit):
        run(capsys, "--notebook", nb, "add", "-m", "   ")
    assert len(logbook.read_entries(nb)) == 2


def test_new_notebook_from_config(tmp_path, capsys, monkeypatch):
    cfg = {"module": "mod9", "image": {"output_base": str(tmp_path / "images")},
           "optimizer": {"type": "claude"}}
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    run(capsys, "--config", str(cfg_path), "add", "-m", "first note", "--amp", "1")
    path = tmp_path / "images" / "mod9" / "claude_notebook.md"
    text = path.read_text()
    assert text.startswith("# Claude lab notebook")
    assert "| module mod9 | amp 1 (HDU 2) | operator note" in text
    # optimizer.notebook overrides the default location
    cfg["optimizer"]["notebook"] = str(tmp_path / "other.md")
    cfg_path.write_text(json.dumps(cfg))
    run(capsys, "--config", str(cfg_path), "add", "-m", "second")
    assert (tmp_path / "other.md").exists()
