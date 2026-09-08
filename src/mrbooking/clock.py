"""Injectable clock (TC7) so BR6/BR8/BR11 are reproducible in tests and demos."""
from __future__ import annotations

import datetime as _dt


class Clock:
    """Returns the current date/time. Overridable via --now on the CLI."""

    def __init__(self, fixed: _dt.datetime | None = None):
        self._fixed = fixed

    def now(self) -> _dt.datetime:
        return self._fixed if self._fixed is not None else _dt.datetime.now()

    @staticmethod
    def from_iso(value: str) -> "Clock":
        return Clock(fixed=_dt.datetime.strptime(value, "%Y-%m-%d %H:%M"))
