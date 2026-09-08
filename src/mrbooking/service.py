"""Service layer: orchestrates storage, rules, and the audit log for every
operation in F1-F16 (core booking, amendment, room administration).
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from . import FORMAT_VERSION
from .audit import record as audit_record
from .config import Config
from .errors import NotFoundError, RuleViolation
from .models import Booking, Closure, Room
from .rules import (
    check_add_room,
    check_amendment,
    check_cancellation,
    check_close_room,
    check_new_booking,
)
from .storage import Store, load, save

TIME_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuleViolation("F25", field_name + " is missing, empty, or the wrong type.")
    return value.strip()


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuleViolation("F25", field_name + " must be a whole number.")
    return value


def _validate_date(value: object) -> str:
    text = _require_text(value, "date")
    try:
        _dt.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise RuleViolation("F27", "Date does not exist in the calendar.") from None
    return text


def _validate_time(value: object, field_name: str) -> str:
    text = _require_text(value, field_name)
    if not TIME_RE.match(text):
        raise RuleViolation("F25", field_name + " is not a valid HH:MM time.")
    return text


class BookingService:
    def __init__(self, data_dir: Path, config: Config, clock):
        self.data_dir = Path(data_dir)
        self.data_path = self.data_dir / "bookings.json"
        self.audit_path = self.data_dir / "audit.log"
        self.config = config
        self.clock = clock
        self.store: Store = load(self.data_path)

    def _save(self) -> None:
        save(self.data_path, self.store)

    def _now(self) -> _dt.datetime:
        return self.clock.now()

    def _find_room_ci(self, name: str) -> Room | None:
        for r in self.store.rooms:
            if r.name.strip().lower() == name.strip().lower():
                return r
        return None

    def _audit(self, operation: str, request: dict, outcome: str, rule_id: str | None) -> None:
        audit_record(
            self.audit_path,
            timestamp=self._now().isoformat(timespec="seconds"),
            operation=operation,
            request=request,
            outcome=outcome,
            rule_id=rule_id,
        )

    # -- F1/F2: create a booking --------------------------------------
    def create_booking(self, room: object, date: object, start: object, end: object,
                        attendees: object, booked_by: object) -> Booking:
        request = {
            "room": room, "date": date, "start": start, "end": end,
            "attendees": attendees, "booked_by": booked_by,
        }
        try:
            room_name = _require_text(room, "room")
            date_val = _validate_date(date)
            start_val = _validate_time(start, "start")
            end_val = _validate_time(end, "end")
            attendees_val = _require_int(attendees, "attendees")
            booked_by_val = _require_text(booked_by, "booked_by")
            if end_val <= start_val:
                raise RuleViolation("F26", "End time must be later than start time.")
            if self._find_room_ci(room_name) is None:
                raise RuleViolation("F28", "Room is not in the room list.")
            candidate = {
                "room": room_name, "date": date_val, "start": start_val, "end": end_val,
                "attendees": attendees_val, "booked_by": booked_by_val,
            }
            check_new_booking(candidate, self.store, self.config, self._now())
        except RuleViolation as e:
            self._audit("create_booking", request, "refused", e.rule_id)
            raise
        booking = Booking(
            id=self.store.next_id, room=room_name, date=date_val, start=start_val,
            end=end_val, attendees=attendees_val, booked_by=booked_by_val, status="active",
        )
        self.store.bookings.append(booking)
        self.store.next_id += 1
        self._save()
        self._audit("create_booking", request, "accepted", None)
        return booking

    # -- F3: cancel a booking -------------------------------------------
    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        request = {"id": booking_id}
        try:
            check_cancellation(booking, self.config, self._now())
        except RuleViolation as e:
            self._audit("cancel_booking", request, "refused", e.rule_id)
            raise
        booking.status = "cancelled"
        self._save()
        self._audit("cancel_booking", request, "accepted", None)
        return booking

    # -- F9: retrieve a single booking -----------------------------------
    def get_booking(self, booking_id: int) -> Booking:
        for b in self.store.bookings:
            if b.id == booking_id:
                return b
        raise NotFoundError("No booking with id " + str(booking_id))

    # -- F4: list all bookings for a date, ordered by room then start ---
    def list_bookings_for_date(self, date: str) -> list[Booking]:
        items = [b for b in self.store.bookings if b.status == "active" and b.date == date]
        return sorted(items, key=lambda b: (b.room.lower(), b.start))

    # -- F5: list all bookings for a room on a date ----------------------
    def list_bookings_for_room_date(self, room: str, date: str) -> list[Booking]:
        items = [
            b for b in self.store.bookings
            if b.status == "active" and b.date == date and b.room.strip().lower() == room.strip().lower()
        ]
        return sorted(items, key=lambda b: b.start)

    # -- F10: list all bookings held by a booker on a date ---------------
    def list_bookings_for_booker_date(self, booker: str, date: str) -> list[Booking]:
        items = [b for b in self.store.bookings if b.status == "active" and b.date == date and b.booked_by == booker]
        return sorted(items, key=lambda b: b.start)

    # -- F11/F12: amend an existing booking ------------------------------
    def amend_booking(self, booking_id: int, room: object = None, date: object = None,
                       start: object = None, end: object = None, attendees: object = None) -> Booking:
        existing = self.get_booking(booking_id)
        request = {"id": booking_id, "room": room, "date": date, "start": start, "end": end, "attendees": attendees}
        try:
            room_name = _require_text(room, "room") if room is not None else existing.room
            date_val = _validate_date(date) if date is not None else existing.date
            start_val = _validate_time(start, "start") if start is not None else existing.start
            end_val = _validate_time(end, "end") if end is not None else existing.end
            attendees_val = _require_int(attendees, "attendees") if attendees is not None else existing.attendees
            if end_val <= start_val:
                raise RuleViolation("F26", "End time must be later than start time.")
            if self._find_room_ci(room_name) is None:
                raise RuleViolation("F28", "Room is not in the room list.")
            candidate = {
                "room": room_name, "date": date_val, "start": start_val, "end": end_val,
                "attendees": attendees_val, "booked_by": existing.booked_by,
            }
            check_amendment(candidate, existing, self.store, self.config, self._now())
        except RuleViolation as e:
            self._audit("amend_booking", request, "refused", e.rule_id)
            raise
        existing.room = room_name
        existing.date = date_val
        existing.start = start_val
        existing.end = end_val
        existing.attendees = attendees_val
        self._save()
        self._audit("amend_booking", request, "accepted", None)
        return existing

    # -- F13: add a room --------------------------------------------------
    def add_room(self, name: object, capacity: object) -> Room:
        request = {"name": name, "capacity": capacity}
        try:
            name_val = _require_text(name, "name")
            capacity_val = _require_int(capacity, "capacity")
            check_add_room(name_val, capacity_val, self.store, self.config)
        except RuleViolation as e:
            self._audit("add_room", request, "refused", e.rule_id)
            raise
        room = Room(name=name_val, capacity=capacity_val)
        self.store.rooms.append(room)
        self._save()
        self._audit("add_room", request, "accepted", None)
        return room

    # -- F14: list all rooms with capacities -------------------------------
    def list_rooms(self) -> list[Room]:
        return sorted(self.store.rooms, key=lambda r: r.name.lower())

    # -- F15: close a room for a date --------------------------------------
    def close_room(self, room: object, date: object) -> Closure:
        request = {"room": room, "date": date}
        try:
            room_name = _require_text(room, "room")
            date_val = _validate_date(date)
            if self._find_room_ci(room_name) is None:
                raise RuleViolation("F28", "Room is not in the room list.")
            check_close_room(room_name, date_val, self.store)
        except RuleViolation as e:
            self._audit("close_room", request, "refused", e.rule_id)
            raise
        closure = Closure(room=room_name, date=date_val)
        self.store.closures.append(closure)
        self._save()
        self._audit("close_room", request, "accepted", None)
        return closure

    # -- F16: free periods of at least the configured minimum length ------
    def free_periods(self, room: object, date: object) -> list[tuple[str, str]]:
        room_name = _require_text(room, "room")
        date_val = _validate_date(date)
        if self._find_room_ci(room_name) is None:
            raise RuleViolation("F28", "Room is not in the room list.")
        is_closed = any(
            c.room.strip().lower() == room_name.strip().lower() and c.date == date_val
            for c in self.store.closures
        )
        if is_closed:
            return []  # G12: a closed room has zero free periods.
        booked = self.list_bookings_for_room_date(room_name, date_val)
        open_start = self.config.opening_time
        open_end = self.config.closing_time

        def to_min(hhmm: str) -> int:
            h, m = hhmm.split(":")
            return int(h) * 60 + int(m)

        def to_hhmm(mins: int) -> str:
            return "%02d:%02d" % (mins // 60, mins % 60)

        cursor = to_min(open_start)
        end_of_day = to_min(open_end)
        free: list[tuple[str, str]] = []
        for b in booked:
            b_start = to_min(b.start)
            b_end = to_min(b.end)
            if b_start > cursor and (b_start - cursor) >= self.config.min_free_period_minutes:
                free.append((to_hhmm(cursor), to_hhmm(b_start)))
            cursor = max(cursor, b_end)
        if end_of_day > cursor and (end_of_day - cursor) >= self.config.min_free_period_minutes:
            free.append((to_hhmm(cursor), to_hhmm(end_of_day)))
        return free
