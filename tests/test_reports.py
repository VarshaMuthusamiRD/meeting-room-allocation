"""F17-F24, verified against the exact worked examples in Appendix B."""
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking import reports


def load_appendix_a(svc):
    svc.create_booking("Huddle", "2026-03-02", "09:00", "10:30", 5, "rsingh")
    svc.create_booking("Huddle", "2026-03-02", "13:00", "14:00", 4, "rsingh")
    svc.create_booking("Huddle", "2026-03-02", "16:15", "17:00", 6, "tokafor")
    svc.create_booking("Boardroom", "2026-03-02", "08:00", "12:00", 12, "mbaker")
    svc.create_booking("Boardroom", "2026-03-02", "12:00", "16:00", 14, "mbaker")
    svc.create_booking("Boardroom", "2026-03-02", "16:00", "20:00", 9, "tokafor")
    svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 1, "rsingh")
    return svc


class TestReportsAppendixB(unittest.TestCase):
    def setUp(self):
        self.svc = load_appendix_a(with_sample_rooms(make_service(now="2026-03-01 08:00")))
        self.store = self.svc.store
        self.config = self.svc.config

    def test_F17_room_utilisation_matches_appendix_b(self):
        rows = {r["room"]: r for r in reports.room_utilisation(self.store, "2026-03-02", self.config)}
        self.assertEqual(rows["Focus 1"]["booked_minutes"], 15)
        self.assertEqual(rows["Focus 1"]["utilisation_pct"], 2.1)
        self.assertEqual(rows["Focus 2"]["booked_minutes"], 0)
        self.assertEqual(rows["Focus 2"]["utilisation_pct"], 0.0)
        self.assertEqual(rows["Huddle"]["booked_minutes"], 195)
        self.assertEqual(rows["Huddle"]["utilisation_pct"], 27.1)
        self.assertEqual(rows["Boardroom"]["booked_minutes"], 720)
        self.assertEqual(rows["Boardroom"]["utilisation_pct"], 100.0)

    def test_G4_empty_room_still_listed(self):
        rows = {r["room"] for r in reports.room_utilisation(self.store, "2026-03-02", self.config)}
        self.assertIn("Focus 2", rows)

    def test_F18_minutes_and_count_per_room(self):
        rows = {r["room"]: r for r in reports.room_minutes_and_count(self.store, "2026-03-02")}
        self.assertEqual(rows["Huddle"]["booking_count"], 3)
        self.assertEqual(rows["Huddle"]["booked_minutes"], 195)
        self.assertEqual(rows["Boardroom"]["booking_count"], 3)

    def test_F19_seat_utilisation_matches_appendix_b(self):
        result = reports.seat_utilisation(self.store, "2026-03-02", self.config)
        self.assertEqual(result["seat_minutes_booked"], 9375)
        self.assertEqual(result["seat_minutes_available"], 17280)
        self.assertEqual(result["seat_utilisation_pct"], 54.3)

    def test_F20_peak_period_matches_appendix_b(self):
        result = reports.peak_period(self.store, "2026-03-02", self.config)
        self.assertEqual(result["start"], "09:00")
        self.assertEqual(result["end"], "10:00")
        self.assertEqual(result["rooms_in_use"], 3)

    def test_F21_under_occupancy_empty_for_sample_data(self):
        result = reports.under_occupied_bookings(self.store, "2026-03-02")
        self.assertEqual(result, [])

    def test_F21_under_occupancy_detects_added_boardroom_booking(self):
        self.svc.create_booking("Boardroom", "2026-03-03", "09:00", "10:00", 2, "mbaker")
        result = reports.under_occupied_bookings(self.store, "2026-03-03")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["room"], "Boardroom")
        self.assertEqual(result[0]["attendees"], 2)

    def test_F23_per_booker_report(self):
        rows = {r["booker"]: r for r in reports.per_booker_report(self.store, "2026-03-02")}
        self.assertEqual(rows["rsingh"]["booking_count"], 3)
        self.assertEqual(rows["rsingh"]["total_minutes"], 90 + 60 + 15)
        self.assertEqual(rows["mbaker"]["booking_count"], 2)
        self.assertEqual(rows["tokafor"]["booking_count"], 2)

    def test_F24_empty_minutes_matches_appendix_b(self):
        rows = {r["room"]: r for r in reports.empty_minutes(self.store, "2026-03-02", self.config)}
        self.assertEqual(rows["Focus 1"]["empty_minutes"], 705)
        self.assertEqual(rows["Focus 2"]["empty_minutes"], 720)
        self.assertEqual(rows["Huddle"]["empty_minutes"], 525)
        self.assertEqual(rows["Boardroom"]["empty_minutes"], 0)
        for r in rows.values():
            self.assertEqual(r["booked_minutes"] + r["empty_minutes"], 720)

    def test_F22_range_average_utilisation(self):
        rows = {r["room"]: r for r in reports.room_utilisation_range(self.store, "2026-03-02", "2026-03-03", self.config)}
        self.assertEqual(rows["Boardroom"]["days"], 2)
        self.assertGreater(rows["Boardroom"]["average_utilisation_pct"], 0)

    def test_G8_closed_room_reads_zero_pct_with_full_available_minutes(self):
        self.svc.close_room("Focus 2", "2026-03-10")
        rows = {r["room"]: r for r in reports.room_utilisation(self.store, "2026-03-10", self.config)}
        self.assertEqual(rows["Focus 2"]["utilisation_pct"], 0.0)
        self.assertEqual(rows["Focus 2"]["available_minutes"], 720)
        self.assertTrue(rows["Focus 2"]["closed"])

    def test_G3_cancelled_booking_excluded_from_utilisation(self):
        b = self.svc.create_booking("Focus 2", "2026-03-04", "09:00", "10:00", 1, "rsingh")
        self.svc.cancel_booking(b.id)
        rows = {r["room"]: r for r in reports.room_utilisation(self.store, "2026-03-04", self.config)}
        self.assertEqual(rows["Focus 2"]["booked_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
