"""Shared test fixtures."""
from __future__ import annotations

import datetime as _dt
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mrbooking.clock import Clock
from mrbooking.config import Config
from mrbooking.service import BookingService


def make_service(now: str = "2026-03-01 08:00", tmp_dir: Path | None = None) -> BookingService:
    data_dir = tmp_dir or Path(tempfile.mkdtemp())
    config = Config()
    clock = Clock.from_iso(now)
    svc = BookingService(data_dir=data_dir, config=config, clock=clock)
    return svc


def with_sample_rooms(svc: BookingService) -> BookingService:
    svc.add_room("Focus 1", 2)
    svc.add_room("Focus 2", 2)
    svc.add_room("Huddle", 6)
    svc.add_room("Boardroom", 14)
    return svc
