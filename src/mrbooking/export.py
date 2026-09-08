"""F46: export a day's bookings to a file the accountant can open.

CSV is the obvious choice: no third-party dependency (TC3, stdlib csv
module), plain text so it stays readable if the format ever needs
inspecting by hand (in the spirit of TC4), and it opens directly in any
spreadsheet application without conversion.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .storage import Store

CSV_HEADER = ["id", "room", "date", "start", "end", "attendees", "booked_by"]


def day_bookings_rows(store: Store, date: str) -> list[list]:
    bookings = [b for b in store.bookings if b.status == "active" and b.date == date]
    bookings = sorted(bookings, key=lambda b: (b.room.lower(), b.start))
    return [
        [b.id, b.room, b.date, b.start, b.end, b.attendees, b.booked_by]
        for b in bookings
    ]


def write_day_csv(store: Store, date: str, output_path: Path) -> int:
    """Writes the day's active bookings to output_path as CSV. Returns the
    number of bookings written."""
    rows = day_bookings_rows(store, date)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)
    return len(rows)
