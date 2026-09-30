"""
protocol.py
Message format shared by all agents.

Every message is a plain, JSON-serializable dict so it can travel over a
multiprocessing queue today and over a socket, a log file, or an LLM tool
call later without changing the agents themselves.

Request
-------
    {"id": 7, "kind": "acquire", "sender": "optimizer",
     "time": "2026-09-30T12:00:00", "payload": {...}}

Reply
-----
    {"id": 8, "kind": "reply", "sender": "acquisition", "reply_to": 7,
     "ok": true, "payload": {...}, "error": null}

Request kinds
-------------
    acquisition agent : "initial_exposure", "acquire"
    objective agent   : "evaluate"
    any agent         : "shutdown"
"""

import itertools
import json
from datetime import datetime

_ids = itertools.count(1)

SHUTDOWN = "shutdown"
READY    = "ready"
REPLY    = "reply"


def _now() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def make_request(kind: str, sender: str, payload: dict = None) -> dict:
    return {
        "id":      next(_ids),
        "kind":    kind,
        "sender":  sender,
        "time":    _now(),
        "payload": payload or {},
    }


def make_reply(request: dict, sender: str, ok: bool,
               payload: dict = None, error: str = None) -> dict:
    return {
        "id":       next(_ids),
        "kind":     REPLY,
        "sender":   sender,
        "reply_to": request["id"] if request else None,
        "time":     _now(),
        "ok":       ok,
        "payload":  payload or {},
        "error":    error,
    }


class MessageLog:
    """Append-only JSONL record of every message exchanged (optional)."""

    def __init__(self, path: str = None):
        self._fh = open(path, "a") if path else None

    def write(self, direction: str, agent: str, message: dict):
        if self._fh is None:
            return
        self._fh.write(json.dumps({"direction": direction, "agent": agent,
                                   **message}) + "\n")
        self._fh.flush()

    def close(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None
