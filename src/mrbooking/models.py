"""Domain models: Room, Booking, Closure."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Room:
    name: str
    capacity: int

    def to_dict(self) -> dict:
        return {"name": self.name, "capacity": self.capacity}

    @staticmethod
    def from_dict(d: dict) -> "Room":
        return Room(name=d["name"], capacity=d["capacity"])


@dataclass
class Booking:
    id: int
    room: str
    date: str          # YYYY-MM-DD
    start: str          # HH:MM
    end: str            # HH:MM
    attendees: int
    booked_by: str
    status: str = "active"   # "active" or "cancelled" (G3: cancelled excluded from reports)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "room": self.room,
            "date": self.date,
            "start": self.start,
            "end": self.end,
            "attendees": self.attendees,
            "booked_by": self.booked_by,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: dict) -> "Booking":
        return Booking(
            id=d["id"],
            room=d["room"],
            date=d["date"],
            start=d["start"],
            end=d["end"],
            attendees=d["attendees"],
            booked_by=d["booked_by"],
            status=d.get("status", "active"),
        )


@dataclass
class Closure:
    room: str
    date: str

    def to_dict(self) -> dict:
        return {"room": self.room, "date": self.date}

    @staticmethod
    def from_dict(d: dict) -> "Closure":
        return Closure(room=d["room"], date=d["date"])
