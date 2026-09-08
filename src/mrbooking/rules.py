"""Business rule engine (Section 6, BR1-BR16)."""
from __future__ import annotations

import datetime as _dt
import re

from .config import Config
from .errors import RuleViolation
from .models import Booking, Room
from .storage import Store

BOOKER_ID_RE = re.compile(r"^[a-z0-9]{3,20}$")


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _duration_minutes(start: str, end: str) -> int:
    return _to_minutes(end) - _to_minutes(start)


def _overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return _to_minutes(a_start) < _to_minutes(b_end) and _to_minutes(b_start) < _to_minutes(a_end)


def _active_bookings_for_room_date(store: Store, room: str, date: str) -> list[Booking]:
    return [
        b for b in store.bookings
        if b.status == "active" and b.room.strip().lower() == room.strip().lower() and b.date == date
    ]


def _active_bookings_for_booker_date(store: Store, booker: str, date: str) -> list[Booking]:
    return [b for b in store.bookings if b.status == "active" and b.booked_by == booker and b.date == date]


def _find_room(store: Store, name: str) -> Room | None:
    for r in store.rooms:
        if r.name.strip().lower() == name.strip().lower():
            return r
    return None


def _room_closed(store: Store, room: str, date: str) -> bool:
    return any(c.room.strip().lower() == room.strip().lower() and c.date == date for c in store.closures)


def check_new_booking(candidate: dict, store: Store, config: Config, now: _dt.datetime) -> None:
    room = _find_room(store, candidate["room"])
    if room is not None:
        for existing in _active_bookings_for_room_date(store, candidate["room"], candidate["date"]):
            if _overlaps(candidate["start"], candidate["end"], existing.start, existing.end):
                raise RuleViolation("BR1", "Overlaps an existing booking in this room.")
    duration = _duration_minutes(candidate["start"], candidate["end"])
    if duration < config.min_booking_minutes or duration > config.max_booking_minutes:
        raise RuleViolation("BR2", "Booking length must be within the configured minimum and maximum.")
    if _to_minutes(candidate["start"]) % config.slot_minutes != 0 or _to_minutes(candidate["end"]) % config.slot_minutes != 0:
        raise RuleViolation("BR3", "Start and end times must fall on a quarter hour.")
    if _to_minutes(candidate["start"]) < _to_minutes(config.opening_time) or _to_minutes(candidate["end"]) > _to_minutes(config.closing_time):
        raise RuleViolation("BR4", "Booking must fall within opening hours.")
    if room is not None:
        if candidate["attendees"] < 1 or candidate["attendees"] > room.capacity:
            raise RuleViolation("BR5", "Attendees must be between 1 and the room capacity.")
    date_val = candidate["date"]
    start_val = candidate["start"]
    booking_dt = _dt.datetime.strptime(date_val + " " + start_val, "%Y-%m-%d %H:%M")
    if booking_dt < now:
        raise RuleViolation("BR6", "Booking may not be made for a date and time in the past.")
    booked_by_val = candidate["booked_by"]
    existing_for_booker = _active_bookings_for_booker_date(store, booked_by_val, date_val)
    if len(existing_for_booker) >= config.daily_booking_limit_per_person:
        raise RuleViolation("BR7", "Daily booking limit for this person has been reached.")
    if _room_closed(store, candidate["room"], date_val):
        raise RuleViolation("BR9", "Room is closed on this date.")
    if not BOOKER_ID_RE.match(booked_by_val):
        raise RuleViolation("BR13", "Booker id must be 3-20 lower-case letters or digits, no spaces or punctuation.")


def check_amendment(candidate: dict, existing: Booking, store: Store, config: Config, now: _dt.datetime) -> None:
    room = _find_room(store, candidate["room"])
    date_val = candidate["date"]
    start_val = candidate["start"]
    end_val = candidate["end"]
    booked_by_val = candidate["booked_by"]
    if room is not None:
        for other in _active_bookings_for_room_date(store, candidate["room"], date_val):
            if other.id == existing.id:
                continue
            if _overlaps(start_val, end_val, other.start, other.end):
                raise RuleViolation("BR1", "Overlaps an existing booking in this room.")
    duration = _duration_minutes(start_val, end_val)
    if duration < config.min_booking_minutes or duration > config.max_booking_minutes:
        raise RuleViolation("BR2", "Booking length must be within the configured minimum and maximum.")
    if _to_minutes(start_val) % config.slot_minutes != 0 or _to_minutes(end_val) % config.slot_minutes != 0:
        raise RuleViolation("BR3", "Start and end times must fall on a quarter hour.")
    if _to_minutes(start_val) < _to_minutes(config.opening_time) or _to_minutes(end_val) > _to_minutes(config.closing_time):
        raise RuleViolation("BR4", "Booking must fall within opening hours.")
    if room is not None:
        if candidate["attendees"] < 1 or candidate["attendees"] > room.capacity:
            raise RuleViolation("BR5", "Attendees must be between 1 and the room capacity.")
    booking_dt = _dt.datetime.strptime(date_val + " " + start_val, "%Y-%m-%d %H:%M")
    if booking_dt < now:
        raise RuleViolation("BR6", "Booking may not be made for a date and time in the past.")
    others_for_booker = []
    for b in _active_bookings_for_booker_date(store, booked_by_val, date_val):
        if b.id != existing.id:
            others_for_booker.append(b)
    if len(others_for_booker) >= config.daily_booking_limit_per_person:
        raise RuleViolation("BR7", "Daily booking limit for this person has been reached.")
    if _room_closed(store, candidate["room"], date_val):
        raise RuleViolation("BR9", "Room is closed on this date.")
    current_start_dt = _dt.datetime.strptime(existing.date + " " + existing.start, "%Y-%m-%d %H:%M")
    cutoff_seconds = config.cancel_amend_cutoff_minutes * 60
    if (current_start_dt - now).total_seconds() <= cutoff_seconds:
        raise RuleViolation("BR11", "Booking may only be amended more than the cutoff before its start time.")
    unchanged = (
        candidate["room"].strip().lower() == existing.room.strip().lower()
        and date_val == existing.date
        and start_val == existing.start
        and end_val == existing.end
        and candidate["attendees"] == existing.attendees
    )
    if unchanged:
        raise RuleViolation("BR16", "Amendment does not change any field.")


def check_cancellation(booking: Booking, config: Config, now: _dt.datetime) -> None:
    start_dt = _dt.datetime.strptime(booking.date + " " + booking.start, "%Y-%m-%d %H:%M")
    cutoff_seconds = config.cancel_amend_cutoff_minutes * 60
    if (start_dt - now).total_seconds() <= cutoff_seconds:
        raise RuleViolation("BR8", "Booking may only be cancelled more than the cutoff before its start time.")


def check_add_room(name: str, capacity: int, store: Store, config: Config) -> None:
    if _find_room(store, name) is not None:
        raise RuleViolation("BR12", "A room with this name already exists, ignoring case and spacing.")
    if capacity < 1 or capacity > 50:
        raise RuleViolation("BR15", "Room capacity must be between 1 and 50.")


def check_close_room(room: str, date: str, store: Store) -> None:
    if _active_bookings_for_room_date(store, room, date):
        raise RuleViolation("BR14", "Room has existing bookings on this date; cancel them first.")


def free_rooms(store: Store, date: str, start: str, end: str) -> list[Room]:
    """F41 support: rooms that are open (not closed) and have no overlapping
    active booking for the given date/start/end window."""
    candidates = []
    for room in store.rooms:
        if _room_closed(store, room.name, date):
            continue
        conflict = False
        for existing in _active_bookings_for_room_date(store, room.name, date):
            if _overlaps(start, end, existing.start, existing.end):
                conflict = True
                break
        if not conflict:
            candidates.append(room)
    return candidates


def check_waitlist_entry(candidate: dict, store: Store, config: Config, now: _dt.datetime) -> None:
    """F47: a waitlist entry is deliberately allowed to be for a slot that is
    already taken -- that is the whole point of a waitlist -- so BR1 (overlap)
    is not checked here. BR7 (daily booking limit) is also not checked: a
    waitlist entry does not hold a room, so it should not count against the
    limit on active bookings a person can hold. Every other applicable rule
    (duration, quarter-hour, opening hours, capacity, not in the past, room
    not closed, booker id format) still applies, in the same fixed BR-numeric
    order used everywhere else (G7)."""
    room = _find_room(store, candidate["room"])
    duration = _duration_minutes(candidate["start"], candidate["end"])
    if duration < config.min_booking_minutes or duration > config.max_booking_minutes:
        raise RuleViolation("BR2", "Booking length must be within the configured minimum and maximum.")
    if _to_minutes(candidate["start"]) % config.slot_minutes != 0 or \
       _to_minutes(candidate["end"]) % config.slot_minutes != 0:
        raise RuleViolation("BR3", "Start and end times must fall on a quarter hour.")
    if _to_minutes(candidate["start"]) < _to_minutes(config.opening_time) or \
       _to_minutes(candidate["end"]) > _to_minutes(config.closing_time):
        raise RuleViolation("BR4", "Booking must fall within opening hours.")
    if room is not None:
        if candidate["attendees"] < 1 or candidate["attendees"] > room.capacity:
            raise RuleViolation("BR5", "Attendees must be between 1 and the room capacity.")
    booking_dt = _dt.datetime.strptime(candidate["date"] + " " + candidate["start"], "%Y-%m-%d %H:%M")
    if booking_dt < now:
        raise RuleViolation("BR6", "Booking may not be made for a date and time in the past.")
    if _room_closed(store, candidate["room"], candidate["date"]):
        raise RuleViolation("BR9", "Room is closed on this date.")
    if not BOOKER_ID_RE.match(candidate["booked_by"]):
        raise RuleViolation("BR13", "Booker id must be 3-20 lower-case letters or digits, no spaces or punctuation.")
