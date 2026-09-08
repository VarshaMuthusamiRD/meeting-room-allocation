"""Persistence layer (F6/F29-F31/TC4/TC8).

Single human-readable JSON file. Saves are atomic (write to a temp file then
os.replace) so an interruption mid-save cannot leave the data file unreadable
(F29). Before every save a timestamped backup of the current file is taken,
retaining the 3 most recent (F31). On load the structure is validated; a
corrupted or hand-edited file is reported clearly rather than crashing or
silently proceeding (F30).
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import FORMAT_VERSION
from .errors import DataFileError
from .models import Booking, Closure, Room, WaitlistEntry

REQUIRED_KEYS = {"format_version", "next_id", "rooms", "bookings", "closures"}
BACKUP_RETAIN = 3


@dataclass
class Store:
    rooms: list[Room] = field(default_factory=list)
    bookings: list[Booking] = field(default_factory=list)
    closures: list[Closure] = field(default_factory=list)
    waitlist: list[WaitlistEntry] = field(default_factory=list)
    next_id: int = 1
    format_version: int = FORMAT_VERSION

    def to_dict(self) -> dict:
        return {
            "format_version": self.format_version,
            "next_id": self.next_id,
            "rooms": [r.to_dict() for r in self.rooms],
            "bookings": [b.to_dict() for b in self.bookings],
            "closures": [c.to_dict() for c in self.closures],
            "waitlist": [w.to_dict() for w in self.waitlist],
        }


def _validate_structure(data: object) -> None:
    if not isinstance(data, dict):
        raise DataFileError("Data file is not a JSON object.")
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise DataFileError(f"Data file is missing required keys: {sorted(missing)}")
    if not isinstance(data["next_id"], int) or data["next_id"] < 1:
        raise DataFileError("Data file 'next_id' must be a positive integer.")
    if not isinstance(data["format_version"], int):
        raise DataFileError("Data file 'format_version' must be an integer.")
    if data["format_version"] > FORMAT_VERSION:
        raise DataFileError(
            f"Data file format_version {data['format_version']} is newer than this "
            f"software supports ({FORMAT_VERSION})."
        )
    for key, item_keys in (
        ("rooms", {"name", "capacity"}),
        ("bookings", {"id", "room", "date", "start", "end", "attendees", "booked_by"}),
        ("closures", {"room", "date"}),
    ):
        if not isinstance(data[key], list):
            raise DataFileError(f"Data file '{key}' must be a list.")
        for i, item in enumerate(data[key]):
            if not isinstance(item, dict):
                raise DataFileError(f"Data file '{key}[{i}]' must be an object.")
            missing_item = item_keys - set(item.keys())
            if missing_item:
                raise DataFileError(
                    f"Data file '{key}[{i}]' is missing fields: {sorted(missing_item)}"
                )
    # "waitlist" (F47) is optional: files written before F47 existed do not have
    # it, and must still load cleanly (additive schema change, no format_version
    # bump needed -- see ASSUMPTIONS.md). When present, it is validated the same
    # way as the other collections.
    if "waitlist" in data:
        if not isinstance(data["waitlist"], list):
            raise DataFileError("Data file 'waitlist' must be a list.")
        waitlist_keys = {"id", "room", "date", "start", "end", "attendees", "booked_by"}
        for i, item in enumerate(data["waitlist"]):
            if not isinstance(item, dict):
                raise DataFileError(f"Data file 'waitlist[{i}]' must be an object.")
            missing_item = waitlist_keys - set(item.keys())
            if missing_item:
                raise DataFileError(
                    f"Data file 'waitlist[{i}]' is missing fields: {sorted(missing_item)}"
                )


def load(path: Path) -> Store:
    if not path.exists():
        return Store()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        raise DataFileError(f"Could not read data file {path}: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DataFileError(f"Data file {path} is not valid JSON: {e}") from e
    _validate_structure(data)
    return Store(
        rooms=[Room.from_dict(r) for r in data["rooms"]],
        bookings=[Booking.from_dict(b) for b in data["bookings"]],
        closures=[Closure.from_dict(c) for c in data["closures"]],
        waitlist=[WaitlistEntry.from_dict(w) for w in data.get("waitlist", [])],
        next_id=data["next_id"],
        format_version=data["format_version"],
    )


def _rotate_backups(path: Path) -> None:
    if not path.exists():
        return
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    import datetime as _dt

    stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup_path = backup_dir / f"{path.stem}.{stamp}{path.suffix}"
    shutil.copy2(path, backup_path)

    backups = sorted(backup_dir.glob(f"{path.stem}.*{path.suffix}"))
    while len(backups) > BACKUP_RETAIN:
        oldest = backups.pop(0)
        oldest.unlink(missing_ok=True)


def _replace_with_retry(tmp_name: str, path: Path, attempts: int = 5) -> None:
    """os.replace can transiently fail on Windows with WinError 32 ("the
    process cannot access the file") when antivirus or search indexing
    briefly holds a read lock on a just-written file. This is not a real
    conflict -- the file is not actually in concurrent use by this program
    (TC1/TC6 assume a single desk process) -- so a short bounded retry
    resolves it without weakening the atomicity guarantee (F29): the file
    is still only ever replaced by a single, complete os.replace call."""
    import time

    for attempt in range(attempts):
        try:
            os.replace(tmp_name, path)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.05 * (attempt + 1))


def save(path: Path, store: Store) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_backups(path)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        _replace_with_retry(tmp_name, path)
    finally:
        # Best-effort cleanup only: if os.replace succeeded, tmp_name is
        # already gone. If it raised, that original error is what the
        # caller needs to see -- a failure here must never mask it.
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except OSError:
            pass


def list_backups(path: Path) -> list[Path]:
    backup_dir = path.parent / "backups"
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob(f"{path.stem}.*{path.suffix}"))


def restore_from_backup(path: Path, backup_path: Path) -> None:
    """F40: restore the data file from a chosen backup."""
    if not backup_path.exists():
        raise DataFileError(f"Backup {backup_path} does not exist.")
    # Validate the backup before overwriting the live file.
    with open(backup_path, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    _validate_structure(data)
    shutil.copy2(backup_path, path)
