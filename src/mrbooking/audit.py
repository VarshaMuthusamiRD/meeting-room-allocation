"""Append-only audit log (F32/TC12/G10).

Every accepted or refused attempt (booking, amendment, cancellation) is
recorded with a timestamp, the request, and the rule id when refused. The
file is only ever opened in append mode -- the program never rewrites or
truncates it.
"""
from __future__ import annotations

import json
from pathlib import Path


def record(path: Path, *, timestamp: str, operation: str, request: dict,
           outcome: str, rule_id: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": timestamp,
        "operation": operation,
        "request": request,
        "outcome": outcome,  # "accepted" or "refused"
        "rule_id": rule_id,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries
