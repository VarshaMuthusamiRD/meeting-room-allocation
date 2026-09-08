"""Configuration loading (F35/TC9): opening hours, booking length limits, and the
per-person daily limit come from a config file, never hardcoded."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    opening_time: str = "08:00"
    closing_time: str = "20:00"
    min_booking_minutes: int = 15
    max_booking_minutes: int = 240
    daily_booking_limit_per_person: int = 3
    slot_minutes: int = 15  # quarter-hour granularity (BR3)
    min_free_period_minutes: int = 15  # F16
    cancel_amend_cutoff_minutes: int = 60  # BR8/BR11: must be strictly more than this

    @staticmethod
    def default_path() -> Path:
        return Path(__file__).resolve().parent.parent.parent / "config.json"

    @staticmethod
    def load(path: Path | None = None) -> "Config":
        path = path or Config.default_path()
        if not path.exists():
            return Config()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Config(
            opening_time=data.get("opening_time", "08:00"),
            closing_time=data.get("closing_time", "20:00"),
            min_booking_minutes=data.get("min_booking_minutes", 15),
            max_booking_minutes=data.get("max_booking_minutes", 240),
            daily_booking_limit_per_person=data.get("daily_booking_limit_per_person", 3),
            slot_minutes=data.get("slot_minutes", 15),
            min_free_period_minutes=data.get("min_free_period_minutes", 15),
            cancel_amend_cutoff_minutes=data.get("cancel_amend_cutoff_minutes", 60),
        )
