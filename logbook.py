"""
logbook.py
Read the lab notebook (logbook) and add your own entries.

The notebook is the Markdown file the Claude optimizer reads at the start of
every campaign and adds to at the end of one. Entries you add here are
marked "operator note" so Claude treats them as first-hand observations.

Usage
-----
    python3 logbook.py list                         one line per entry
    python3 logbook.py show                         the latest entry
    python3 logbook.py show 3 5                     entries 3 and 5 (numbers from "list")
    python3 logbook.py show all                     every entry
    python3 logbook.py search dropout               entries containing a word
    python3 logbook.py add -m "LED replaced, signal back to 1e5 ADU" --amp 3
    python3 logbook.py add --amp 3                  write the entry in your editor
    python3 logbook.py edit                         open the whole notebook in your editor

The notebook is found from a config file, as the optimizer does
(<output_base>/<module>/claude_notebook.md, or optimizer.notebook if set):
    python3 logbook.py --config config_skipper_claude.json list
or given directly:
    python3 logbook.py --notebook path/to/claude_notebook.md list
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

PREAMBLE = ("# Claude lab notebook\n\n"
            "Written by the Claude optimizer at the end of each campaign and "
            "read at the start of the next one. Edit or delete entries freely.\n")

DEFAULT_CONFIGS = ("config_skipper_claude.json", "config_skipper.json")


# ---------------------------------------------------------------------------
# Locating and parsing the notebook
# ---------------------------------------------------------------------------

def notebook_from_config(path: str) -> tuple:
    """(notebook path, module) as the optimizer would use them."""
    with open(path) as f:
        cfg = json.load(f)
    module = cfg.get("module", "")
    custom = cfg.get("optimizer", {}).get("notebook")
    if isinstance(custom, str) and custom:
        return custom, module
    base = cfg.get("image", {}).get("output_base", "images")
    return os.path.join(base, module, "claude_notebook.md"), module


def parse(text: str) -> tuple:
    """Split the notebook into (preamble, [(header, body), ...])."""
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    entries = []
    for part in parts[1:]:
        header, _, body = part.partition("\n")
        entries.append((header.strip(), body.strip()))
    return parts[0], entries


def read_entries(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return parse(f.read())[1]


def select(entries: list, which: list) -> list:
    """Entry numbers are 1-based, as printed by `list`."""
    if not which:
        return [(len(entries), entries[-1])] if entries else []
    if which == ["all"]:
        return list(enumerate(entries, 1))
    chosen = []
    for w in which:
        n = len(entries) if w == "last" else int(w)
        if not 1 <= n <= len(entries):
            sys.exit(f"No entry {w}: the notebook has {len(entries)} entries.")
        chosen.append((n, entries[n - 1]))
    return chosen


def print_entry(n: int, header: str, body: str):
    print(f"[{n}] ## {header}\n")
    print(body if body else "(no text)")
    print()


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def editor() -> list:
    return (os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano").split()


def text_from_editor() -> str:
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tmp:
        tmp.write("\n# Write your logbook entry above. Lines starting with '#' "
                  "are ignored.\n")
        name = tmp.name
    try:
        subprocess.call(editor() + [name])
        with open(name) as f:
            lines = [l.rstrip("\n") for l in f if not l.startswith("#")]
    finally:
        os.unlink(name)
    return "\n".join(lines).strip()


def add_entry(path: str, body: str, module: str = "", amp: int = None,
              title: str = "", when: datetime = None) -> str:
    when = when or datetime.now()
    fields = [f"{when:%Y-%m-%d %H:%M}"]
    if module:
        fields.append(f"module {module}")
    if amp is not None:
        fields.append(f"amp {amp} (HDU {amp + 1})")
    fields.append("operator note")
    if title:
        fields.append(title)
    header = " | ".join(fields)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new_file = not os.path.exists(path)
    with open(path, "a") as f:
        if new_file:
            f.write(PREAMBLE)
        f.write(f"\n## {header}\n\n{body.strip()}\n")
    return header


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read the Claude lab notebook and add operator entries.")
    where = parser.add_mutually_exclusive_group()
    where.add_argument("--notebook", help="Path of the notebook file.")
    where.add_argument("--config", help="Campaign config; the notebook is "
                       "found the same way the optimizer finds it.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="One line per entry.")
    p = sub.add_parser("show", help="Print entries (default: the latest).")
    p.add_argument("which", nargs="*", help='Entry numbers, "last" or "all".')
    p = sub.add_parser("search", help="Entries containing a text (case-insensitive).")
    p.add_argument("text")
    p = sub.add_parser("add", help="Add an operator entry.")
    p.add_argument("-m", "--message", help="Entry text. Without it your "
                   "editor opens; use '-' to read from standard input.")
    p.add_argument("--amp", type=int, help="Amplifier number, 0-3 "
                   "(config value is one higher).")
    p.add_argument("--title", default="", help="Short title for the header.")
    sub.add_parser("edit", help="Open the whole notebook in your editor.")
    args = parser.parse_args(argv)

    module = ""
    if args.notebook:
        path = args.notebook
    else:
        config = args.config or next((c for c in DEFAULT_CONFIGS if os.path.exists(c)), None)
        if config is None:
            sys.exit("No config found; use --config or --notebook.")
        path, module = notebook_from_config(config)

    if args.command == "list":
        entries = read_entries(path)
        print(f"{path}: {len(entries)} entries")
        for n, (header, _) in enumerate(entries, 1):
            print(f"[{n:>2}] {header}")

    elif args.command == "show":
        entries = read_entries(path)
        if not entries:
            sys.exit(f"{path}: no entries yet.")
        for n, (header, body) in select(entries, args.which):
            print_entry(n, header, body)

    elif args.command == "search":
        needle = args.text.lower()
        hits = [(n, e) for n, e in enumerate(read_entries(path), 1)
                if needle in (e[0] + "\n" + e[1]).lower()]
        if not hits:
            print(f'No entries contain "{args.text}".')
        for n, (header, body) in hits:
            print_entry(n, header, body)

    elif args.command == "add":
        if args.amp is not None and not 0 <= args.amp <= 3:
            sys.exit("--amp is the amplifier number, 0-3.")
        if args.message == "-":
            body = sys.stdin.read()
        elif args.message is not None:
            body = args.message
        else:
            body = text_from_editor()
        if not body.strip():
            sys.exit("Empty entry, nothing added.")
        header = add_entry(path, body, module=module, amp=args.amp, title=args.title)
        print(f"Added to {path}:\n## {header}")

    elif args.command == "edit":
        if not os.path.exists(path):
            sys.exit(f"{path} does not exist yet.")
        subprocess.call(editor() + [path])


if __name__ == "__main__":
    main()
