"""Command-line interface (TC5, F37, F38).

Single entry point. Every subcommand returns exit code 0 on success and 1 on
failure so a script can act on the result (F37). Run with no arguments, or
-h, to see the full usage message listing every operation (F38).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import FORMAT_VERSION, SOFTWARE_VERSION
from . import reports
from .clock import Clock
from .config import Config
from .errors import DataFileError, NotFoundError, RuleViolation
from .service import BookingService
from . import storage as storage_mod

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mrbooking",
        description="Meridian Coworking meeting room booking and utilisation service.",
    )
    p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="directory holding bookings.json, audit.log, backups/")
    p.add_argument("--config", default=None, help="path to config.json (defaults to project root)")
    p.add_argument("--now", default=None, help="override the current date and time, format: YYYY-MM-DD HH:MM (TC7)")

    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("book", help="create a booking (F1)")
    sp.add_argument("room")
    sp.add_argument("date")
    sp.add_argument("start")
    sp.add_argument("end")
    sp.add_argument("attendees", type=int)
    sp.add_argument("booked_by")

    sp = sub.add_parser("cancel", help="cancel a booking by id (F3)")
    sp.add_argument("id", type=int)

    sp = sub.add_parser("get", help="retrieve a single booking by id (F9)")
    sp.add_argument("id", type=int)

    sp = sub.add_parser("list-date", help="list all bookings for a date, ordered by room then start (F4)")
    sp.add_argument("date")

    sp = sub.add_parser("list-room", help="list all bookings for a room on a date (F5)")
    sp.add_argument("room")
    sp.add_argument("date")

    sp = sub.add_parser("list-booker", help="list bookings held by a booker on a date (F10)")
    sp.add_argument("booker")
    sp.add_argument("date")

    sp = sub.add_parser("amend", help="amend an existing booking (F11/F12)")
    sp.add_argument("id", type=int)
    sp.add_argument("--room")
    sp.add_argument("--date")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--attendees", type=int)

    sp = sub.add_parser("add-room", help="add a room with a name and capacity (F13)")
    sp.add_argument("name")
    sp.add_argument("capacity", type=int)

    sp = sub.add_parser("list-rooms", help="list all rooms with capacities (F14)")

    sp = sub.add_parser("close-room", help="mark a room closed for a date (F15)")
    sp.add_argument("room")
    sp.add_argument("date")

    sp = sub.add_parser("free-periods", help="show free periods of at least 15 minutes for a room/date (F16)")
    sp.add_argument("room")
    sp.add_argument("date")

    sp = sub.add_parser("version", help="report the software and data format version (F36)")

    sp = sub.add_parser("check", help="run a startup self-check on the data file (F34)")

    sp = sub.add_parser("report-utilisation", help="room utilisation percentage for a date (F17)")
    sp.add_argument("date")

    sp = sub.add_parser("report-minutes", help="total minutes booked and bookings per room, for a date (F18)")
    sp.add_argument("date")

    sp = sub.add_parser("report-seat-utilisation", help="seat utilisation for a date (F19)")
    sp.add_argument("date")

    sp = sub.add_parser("report-peak", help="peak period for a date (F20)")
    sp.add_argument("date")

    sp = sub.add_parser("report-under-occupied", help="bookings using fewer than half their room seats (F21)")
    sp.add_argument("date")

    sp = sub.add_parser("report-range", help="room utilisation averaged across a date range (F22)")
    sp.add_argument("start_date")
    sp.add_argument("end_date")

    sp = sub.add_parser("report-booker", help="per-booker bookings and minutes for a date (F23)")
    sp.add_argument("date")

    sp = sub.add_parser("report-empty", help="empty minutes per room for a date (F24)")
    sp.add_argument("date")

    sp = sub.add_parser("list-backups", help="list available data file backups")

    sp = sub.add_parser("restore-backup", help="restore the data file from a chosen backup (F40)")
    sp.add_argument("backup_path")

    return p


def _build_service(args) -> BookingService:
    config = Config.load(Path(args.config)) if args.config else Config.load()
    clock = Clock.from_iso(args.now) if args.now else Clock()
    return BookingService(data_dir=Path(args.data_dir), config=config, clock=clock)


def _fail(rule_id, message: str) -> int:
    prefix = ("[" + rule_id + "] ") if rule_id else ""
    print("REFUSED: " + prefix + message, file=sys.stderr)
    return 1


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print("software_version=" + SOFTWARE_VERSION)
        print("format_version=" + str(FORMAT_VERSION))
        return 0

    if args.command == "check":
        data_path = Path(args.data_dir) / "bookings.json"
        try:
            storage_mod.load(data_path)
        except DataFileError as e:
            print("DATA FILE CHECK FAILED: " + str(e), file=sys.stderr)
            return 1
        print("Data file OK: " + str(data_path))
        return 0

    try:
        svc = _build_service(args)
    except DataFileError as e:
        print("DATA FILE ERROR: " + str(e), file=sys.stderr)
        return 1

    try:
        if args.command == "book":
            b = svc.create_booking(args.room, args.date, args.start, args.end, args.attendees, args.booked_by)
            print("Booked #" + str(b.id) + ": " + b.room + " " + b.date + " " + b.start + "-" + b.end)
        elif args.command == "cancel":
            b = svc.cancel_booking(args.id)
            print("Cancelled #" + str(b.id))
        elif args.command == "get":
            b = svc.get_booking(args.id)
            print(b)
        elif args.command == "list-date":
            for b in svc.list_bookings_for_date(args.date):
                print(str(b.id) + "\t" + b.room + "\t" + b.start + "-" + b.end + "\t" + b.booked_by)
        elif args.command == "list-room":
            for b in svc.list_bookings_for_room_date(args.room, args.date):
                print(str(b.id) + "\t" + b.start + "-" + b.end + "\t" + b.booked_by)
        elif args.command == "list-booker":
            for b in svc.list_bookings_for_booker_date(args.booker, args.date):
                print(str(b.id) + "\t" + b.room + "\t" + b.start + "-" + b.end)
        elif args.command == "amend":
            b = svc.amend_booking(args.id, room=args.room, date=args.date, start=args.start, end=args.end, attendees=args.attendees)
            print("Amended #" + str(b.id) + ": " + b.room + " " + b.date + " " + b.start + "-" + b.end)
        elif args.command == "add-room":
            r = svc.add_room(args.name, args.capacity)
            print("Added room: " + r.name + " (capacity " + str(r.capacity) + ")")
        elif args.command == "list-rooms":
            for r in svc.list_rooms():
                print(r.name + "\t" + str(r.capacity))
        elif args.command == "close-room":
            c = svc.close_room(args.room, args.date)
            print("Closed " + c.room + " on " + c.date)
        elif args.command == "free-periods":
            for start, end in svc.free_periods(args.room, args.date):
                print(start + "-" + end)
        elif args.command == "report-utilisation":
            for row in reports.room_utilisation(svc.store, args.date, svc.config):
                print(row["room"] + "\t" + str(row["utilisation_pct"]) + "%\t" + str(row["booked_minutes"]) + "min")
        elif args.command == "report-minutes":
            for row in reports.room_minutes_and_count(svc.store, args.date):
                print(row["room"] + "\t" + str(row["booking_count"]) + " bookings\t" + str(row["booked_minutes"]) + "min")
        elif args.command == "report-seat-utilisation":
            row = reports.seat_utilisation(svc.store, args.date, svc.config)
            print(str(row["seat_utilisation_pct"]) + "%")
        elif args.command == "report-peak":
            row = reports.peak_period(svc.store, args.date, svc.config)
            print(row["start"] + "-" + row["end"] + "\t" + str(row["rooms_in_use"]) + " rooms")
        elif args.command == "report-under-occupied":
            for row in reports.under_occupied_bookings(svc.store, args.date):
                print(str(row["id"]) + "\t" + row["room"] + "\t" + str(row["attendees"]) + "/" + str(row["capacity"]))
        elif args.command == "report-range":
            for row in reports.room_utilisation_range(svc.store, args.start_date, args.end_date, svc.config):
                print(row["room"] + "\t" + str(row["average_utilisation_pct"]) + "% avg over " + str(row["days"]) + " days")
        elif args.command == "report-booker":
            for row in reports.per_booker_report(svc.store, args.date):
                print(row["booker"] + "\t" + str(row["booking_count"]) + " bookings\t" + str(row["total_minutes"]) + "min")
        elif args.command == "report-empty":
            for row in reports.empty_minutes(svc.store, args.date, svc.config):
                print(row["room"] + "\t" + str(row["empty_minutes"]) + "min empty")
        elif args.command == "list-backups":
            for b in storage_mod.list_backups(svc.data_path):
                print(str(b))
        elif args.command == "restore-backup":
            storage_mod.restore_from_backup(svc.data_path, Path(args.backup_path))
            print("Restored from " + args.backup_path)
        else:
            parser.print_usage()
            return 1
    except RuleViolation as e:
        return _fail(e.rule_id, e.message)
    except NotFoundError as e:
        return _fail(None, str(e))
    except DataFileError as e:
        return _fail(None, str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
