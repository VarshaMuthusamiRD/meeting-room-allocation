"""F45-F48: weekly utilisation summary, CSV export, waiting list, trend
comparison."""
import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import make_service, with_sample_rooms

from mrbooking import export as export_mod
from mrbooking import reports
from mrbooking.errors import NotFoundError, RuleViolation


def seed_appendix_a(svc):
    svc.create_booking("Huddle", "2026-03-02", "09:00", "10:30", 5, "rsingh")
    svc.create_booking("Huddle", "2026-03-02", "13:00", "14:00", 4, "rsingh")
    svc.create_booking("Huddle", "2026-03-02", "16:15", "17:00", 6, "tokafor")
    svc.create_booking("Boardroom", "2026-03-02", "08:00", "12:00", 12, "mbaker")
    svc.create_booking("Boardroom", "2026-03-02", "12:00", "16:00", 14, "mbaker")
    svc.create_booking("Boardroom", "2026-03-02", "16:00", "20:00", 9, "tokafor")
    svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 1, "rsingh")
    return svc


class TestWeeklySummary(unittest.TestCase):
    def test_F45_covers_seven_consecutive_dates(self):
        svc = seed_appendix_a(with_sample_rooms(make_service(now="2026-03-01 08:00")))
        summary = reports.weekly_utilisation_summary(svc.store, "2026-03-02", svc.config)
        self.assertEqual(summary["start_date"], "2026-03-02")
        self.assertEqual(summary["end_date"], "2026-03-08")
        self.assertEqual(len(summary["dates"]), 7)
        self.assertEqual(summary["dates"][0], "2026-03-02")
        self.assertEqual(summary["dates"][-1], "2026-03-08")

    def test_F45_per_date_matches_appendix_b_on_seeded_day(self):
        svc = seed_appendix_a(with_sample_rooms(make_service(now="2026-03-01 08:00")))
        summary = reports.weekly_utilisation_summary(svc.store, "2026-03-02", svc.config)
        day_rows = {r["room"]: r for r in summary["per_date"]["2026-03-02"]}
        self.assertEqual(day_rows["Boardroom"]["utilisation_pct"], 100.0)
        self.assertEqual(day_rows["Huddle"]["utilisation_pct"], 27.1)

    def test_F45_empty_week_reads_zero(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        summary = reports.weekly_utilisation_summary(svc.store, "2026-04-01", svc.config)
        for row in summary["average_by_room"]:
            self.assertEqual(row["average_utilisation_pct"], 0.0)


class TestExportCsv(unittest.TestCase):
    def test_F46_exports_active_bookings_as_csv(self):
        svc = seed_appendix_a(with_sample_rooms(make_service(now="2026-03-01 08:00")))
        out = Path(tempfile.mkdtemp()) / "day.csv"
        count = export_mod.write_day_csv(svc.store, "2026-03-02", out)
        self.assertEqual(count, 7)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["id", "room", "date", "start", "end", "attendees", "booked_by"])
        self.assertEqual(len(rows) - 1, 7)

    def test_F46_excludes_cancelled_bookings(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        b = svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        svc.cancel_booking(b.id)
        out = Path(tempfile.mkdtemp()) / "day.csv"
        count = export_mod.write_day_csv(svc.store, "2026-03-02", out)
        self.assertEqual(count, 0)

    def test_F46_empty_day_still_writes_header_only(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        out = Path(tempfile.mkdtemp()) / "day.csv"
        count = export_mod.write_day_csv(svc.store, "2026-03-09", out)
        self.assertEqual(count, 0)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows), 1)


class TestWaitlist(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))

    def test_F47_add_to_waitlist_for_a_taken_slot(self):
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        w = self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 3, "mbaker")
        self.assertEqual(w.room, "Huddle")
        self.assertEqual(w.status, "waiting")

    def test_F47_waitlist_does_not_hold_the_room(self):
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 3, "mbaker")
        listed = self.svc.list_bookings_for_room_date("Huddle", "2026-03-02")
        self.assertEqual(len(listed), 1)

    def test_F47_waitlist_still_enforces_capacity(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.add_to_waitlist("Focus 1", "2026-03-02", "09:00", "10:00", 5, "mbaker")
        self.assertEqual(ctx.exception.rule_id, "BR5")

    def test_F47_waitlist_still_enforces_booker_id_format(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 2, "M Baker")
        self.assertEqual(ctx.exception.rule_id, "BR13")

    def test_F47_waitlist_does_not_enforce_daily_limit(self):
        self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 1, "rsingh")
        self.svc.create_booking("Focus 2", "2026-03-02", "09:15", "09:30", 1, "rsingh")
        self.svc.create_booking("Huddle", "2026-03-02", "09:30", "09:45", 1, "rsingh")
        w = self.svc.add_to_waitlist("Boardroom", "2026-03-02", "10:00", "11:00", 2, "rsingh")
        self.assertIsNotNone(w.id)

    def test_F47_list_waitlist_for_room_date(self):
        self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 3, "tokafor")
        entries = self.svc.list_waitlist_for_room_date("Huddle", "2026-03-02")
        self.assertEqual(len(entries), 2)

    def test_F47_remove_from_waitlist(self):
        w = self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        removed = self.svc.remove_from_waitlist(w.id)
        self.assertEqual(removed.status, "removed")
        entries = self.svc.list_waitlist_for_room_date("Huddle", "2026-03-02")
        self.assertEqual(entries, [])

    def test_F47_remove_missing_entry_raises(self):
        with self.assertRaises(NotFoundError):
            self.svc.remove_from_waitlist(99999)

    def test_F47_waitlist_survives_reload(self):
        w = self.svc.add_to_waitlist("Huddle", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        svc2 = make_service(now="2026-03-01 08:00", tmp_dir=self.svc.data_dir)
        entries = svc2.list_waitlist_for_room_date("Huddle", "2026-03-02")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, w.id)


class TestBackwardCompatibleLoading(unittest.TestCase):
    def test_pre_F47_data_file_without_waitlist_key_still_loads(self):
        import json
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        data = json.loads(svc.data_path.read_text(encoding="utf-8"))
        self.assertIn("waitlist", data)
        del data["waitlist"]
        svc.data_path.write_text(json.dumps(data), encoding="utf-8")
        from mrbooking.storage import load
        store = load(svc.data_path)
        self.assertEqual(store.waitlist, [])


class TestTrendComparison(unittest.TestCase):
    def test_F48_flags_room_that_grew_busier(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-10", "09:00", "10:00", 2, "rsingh")
        svc.create_booking("Huddle", "2026-03-20", "09:00", "12:00", 2, "rsingh")
        rows = {r["room"]: r for r in reports.trend_comparison(
            svc.store, "2026-03-10", "2026-03-10", "2026-03-20", "2026-03-20", svc.config)}
        self.assertEqual(rows["Huddle"]["trend"], "busier")
        self.assertGreater(rows["Huddle"]["delta_pct"], 0)

    def test_F48_flags_room_that_grew_quieter(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-10", "09:00", "12:00", 2, "rsingh")
        svc.create_booking("Huddle", "2026-03-20", "09:00", "10:00", 2, "rsingh")
        rows = {r["room"]: r for r in reports.trend_comparison(
            svc.store, "2026-03-10", "2026-03-10", "2026-03-20", "2026-03-20", svc.config)}
        self.assertEqual(rows["Huddle"]["trend"], "quieter")
        self.assertLess(rows["Huddle"]["delta_pct"], 0)

    def test_F48_unchanged_room_flagged_unchanged(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        rows = {r["room"]: r for r in reports.trend_comparison(
            svc.store, "2026-03-10", "2026-03-10", "2026-03-20", "2026-03-20", svc.config)}
        self.assertEqual(rows["Focus 2"]["trend"], "unchanged")
        self.assertEqual(rows["Focus 2"]["delta_pct"], 0)


if __name__ == "__main__":
    unittest.main()
