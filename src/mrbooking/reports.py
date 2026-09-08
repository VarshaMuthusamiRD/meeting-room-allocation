"""Reporting and analysis (F17-F24, Appendix B).

Every percentage is rounded to one decimal place using standard
half-up rounding via Decimal, matching Appendix B exactly (e.g. 195/720
must read 27.1, never 27.08 or 27).
"""
from __future__ import annotations

import datetime as _dt
from decimal import ROUND_HALF_UP, Decimal

from .config import Config
from .storage import Store

OPENING_MINUTES_PER_DAY = 720  # 08:00-20:00, fixed by the RFP glossary (Appendix C)


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    value = (Decimal(numerator) / Decimal(denominator)) * Decimal(100)
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _available_minutes(config: Config) -> int:
    return _to_minutes(config.closing_time) - _to_minutes(config.opening_time)


def _active_for_date(store: Store, date: str):
    return [b for b in store.bookings if b.status == "active" and b.date == date]


def _room_capacity(store: Store, room_name: str) -> int:
    for r in store.rooms:
        if r.name.strip().lower() == room_name.strip().lower():
            return r.capacity
    return 0


def room_utilisation(store: Store, date: str, config: Config) -> list[dict]:
    """F17/F7: utilisation percentage per room, one decimal place. G4/G8: every
    room is listed, including empty and closed ones."""
    available = _available_minutes(config)
    bookings = _active_for_date(store, date)
    results = []
    for room in sorted(store.rooms, key=lambda r: r.name.lower()):
        booked = sum(
            _to_minutes(b.end) - _to_minutes(b.start)
            for b in bookings
            if b.room.strip().lower() == room.name.strip().lower()
        )
        closed = any(
            c.room.strip().lower() == room.name.strip().lower() and c.date == date
            for c in store.closures
        )
        results.append({
            "room": room.name,
            "booked_minutes": booked,
            "available_minutes": available,
            "utilisation_pct": _pct(booked, available),
            "closed": closed,
        })
    return results


def room_minutes_and_count(store: Store, date: str) -> list[dict]:
    """F18/F8: total minutes booked and number of bookings, per room, for a date."""
    bookings = _active_for_date(store, date)
    results = []
    for room in sorted(store.rooms, key=lambda r: r.name.lower()):
        room_bookings = [b for b in bookings if b.room.strip().lower() == room.name.strip().lower()]
        booked = sum(_to_minutes(b.end) - _to_minutes(b.start) for b in room_bookings)
        results.append({
            "room": room.name,
            "booking_count": len(room_bookings),
            "booked_minutes": booked,
        })
    return results


def seat_utilisation(store: Store, date: str, config: Config) -> dict:
    """F19: seat-minutes booked as a percentage of seat-minutes available."""
    available_minutes = _available_minutes(config)
    bookings = _active_for_date(store, date)
    seat_minutes_booked = sum(
        b.attendees * (_to_minutes(b.end) - _to_minutes(b.start)) for b in bookings
    )
    seat_minutes_available = sum(r.capacity * available_minutes for r in store.rooms)
    return {
        "seat_minutes_booked": seat_minutes_booked,
        "seat_minutes_available": seat_minutes_available,
        "seat_utilisation_pct": _pct(seat_minutes_booked, seat_minutes_available),
    }


def peak_period(store: Store, date: str, config: Config) -> dict:
    """F20: the clock hour in which the most rooms are simultaneously in use."""
    bookings = _active_for_date(store, date)
    open_min = _to_minutes(config.opening_time)
    close_min = _to_minutes(config.closing_time)
    best_hour = None
    best_count = -1
    hour = open_min
    while hour < close_min:
        hour_end = hour + 60
        rooms_in_use = set()
        for b in bookings:
            b_start = _to_minutes(b.start)
            b_end = _to_minutes(b.end)
            if b_start < hour_end and hour < b_end:
                rooms_in_use.add(b.room.strip().lower())
        count = len(rooms_in_use)
        if count > best_count:
            best_count = count
            best_hour = hour
        hour += 60
    if best_hour is None:
        return {"start": config.opening_time, "end": config.opening_time, "rooms_in_use": 0}
    return {
        "start": "%02d:%02d" % (best_hour // 60, best_hour % 60),
        "end": "%02d:%02d" % ((best_hour + 60) // 60, (best_hour + 60) % 60),
        "rooms_in_use": best_count,
    }


def under_occupied_bookings(store: Store, date: str) -> list[dict]:
    """F21: bookings using fewer than half the seats in their room."""
    bookings = _active_for_date(store, date)
    results = []
    for b in bookings:
        capacity = _room_capacity(store, b.room)
        if capacity > 0 and b.attendees < capacity / 2.0:
            results.append({
                "id": b.id, "room": b.room, "start": b.start, "end": b.end,
                "attendees": b.attendees, "capacity": capacity,
            })
    return results


def room_utilisation_range(store: Store, start_date: str, end_date: str, config: Config) -> list[dict]:
    """F22: room utilisation across a range of dates, showing each room average."""
    start_dt = _dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = _dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    dates = []
    cursor = start_dt
    while cursor <= end_dt:
        dates.append(cursor.strftime("%Y-%m-%d"))
        cursor += _dt.timedelta(days=1)
    per_room_totals: dict[str, list[float]] = {r.name: [] for r in store.rooms}
    for d in dates:
        for row in room_utilisation(store, d, config):
            per_room_totals.setdefault(row["room"], []).append(row["utilisation_pct"])
    results = []
    for room in sorted(store.rooms, key=lambda r: r.name.lower()):
        values = per_room_totals.get(room.name, [])
        average = sum(values) / len(values) if values else 0.0
        results.append({"room": room.name, "average_utilisation_pct": round(average, 1), "days": len(dates)})
    return results


def per_booker_report(store: Store, date: str) -> list[dict]:
    """F23: per booker, number of bookings and total minutes held, for a date."""
    bookings = _active_for_date(store, date)
    totals: dict[str, dict] = {}
    for b in bookings:
        entry = totals.setdefault(b.booked_by, {"booker": b.booked_by, "booking_count": 0, "total_minutes": 0})
        entry["booking_count"] += 1
        entry["total_minutes"] += _to_minutes(b.end) - _to_minutes(b.start)
    return sorted(totals.values(), key=lambda e: e["booker"])


def empty_minutes(store: Store, date: str, config: Config) -> list[dict]:
    """F24: total minutes each room stood empty during opening hours."""
    available = _available_minutes(config)
    results = []
    for row in room_utilisation(store, date, config):
        results.append({
            "room": row["room"],
            "booked_minutes": row["booked_minutes"],
            "empty_minutes": available - row["booked_minutes"],
            "total_minutes": available,
        })
    return results


def day_timeline(store: Store, date: str, config: Config, resolution_minutes: int = 30) -> list[dict]:
    """F43: a text timeline of a day, one row per room. '#' marks a cell
    that overlaps a booking, '.' marks a free cell; closed rooms are flagged."""
    open_min = _to_minutes(config.opening_time)
    close_min = _to_minutes(config.closing_time)
    bookings = _active_for_date(store, date)
    results = []
    for room in sorted(store.rooms, key=lambda r: r.name.lower()):
        room_bookings = [b for b in bookings if b.room.strip().lower() == room.name.strip().lower()]
        closed = any(
            c.room.strip().lower() == room.name.strip().lower() and c.date == date
            for c in store.closures
        )
        cells = []
        cursor = open_min
        while cursor < close_min:
            cell_end = cursor + resolution_minutes
            occupied = any(
                _to_minutes(b.start) < cell_end and cursor < _to_minutes(b.end)
                for b in room_bookings
            )
            cells.append("#" if occupied else ".")
            cursor = cell_end
        results.append({"room": room.name, "line": "".join(cells), "closed": closed})
    return results
