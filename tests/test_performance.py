"""TC10: no operation may take longer than two seconds on a file of 10,000
bookings. Bookings are seeded directly into the store (bypassing the rule
engine, which is already exercised elsewhere) purely to build a realistic
10,000-row data file quickly; the timings below measure real operations
running against that file through the normal service/report code paths."""
import time
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking import reports
from mrbooking.models import Booking
from mrbooking.storage import save

BUDGET_SECONDS = 2.0


def seed_10000_bookings(svc):
    rooms = [r.name for r in svc.store.rooms]
    bookers = ["booker%03d" % i for i in range(200)]
    slots = ["08:00", "08:15", "08:30", "08:45", "09:00", "09:15", "09:30", "09:45"]
    count = 0
    day = 1
    while count < 10000:
        date = "2026-%02d-%02d" % (1 + (day // 28) % 12, 1 + (day % 28))
        for room in rooms:
            for i, slot in enumerate(slots):
                if count >= 10000:
                    break
                end_h, end_m = slot.split(":")
                end = "%02d:%02d" % (int(end_h), int(end_m) + 15) if int(end_m) < 45 else "%02d:00" % (int(end_h) + 1)
                svc.store.bookings.append(Booking(
                    id=svc.store.next_id, room=room, date=date, start=slot, end=end,
                    attendees=1, booked_by=bookers[count % len(bookers)], status="active",
                ))
                svc.store.next_id += 1
                count += 1
        day += 1
    save(svc.data_path, svc.store)


class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        seed_10000_bookings(self.svc)
        self.assertEqual(len(self.svc.store.bookings), 10000)

    def test_TC10_list_bookings_for_date(self):
        start = time.perf_counter()
        self.svc.list_bookings_for_date("2026-02-02")
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)

    def test_TC10_report_utilisation(self):
        start = time.perf_counter()
        reports.room_utilisation(self.svc.store, "2026-02-02", self.svc.config)
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)

    def test_TC10_report_range(self):
        start = time.perf_counter()
        reports.room_utilisation_range(self.svc.store, "2026-01-01", "2026-06-30", self.svc.config)
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)

    def test_TC10_create_booking(self):
        start = time.perf_counter()
        self.svc.create_booking("Huddle", "2026-12-25", "09:00", "10:00", 2, "rsingh")
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)

    def test_TC10_free_periods(self):
        start = time.perf_counter()
        self.svc.free_periods("Huddle", "2026-02-02")
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)

    def test_TC10_load_from_disk(self):
        from mrbooking.storage import load
        start = time.perf_counter()
        load(self.svc.data_path)
        self.assertLess(time.perf_counter() - start, BUDGET_SECONDS)


if __name__ == "__main__":
    unittest.main()
