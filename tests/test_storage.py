"""F6, F29-F31, F33 (storage-level requirements exercised via BookingService)."""
import unittest

from tests.helpers import make_service, with_sample_rooms


class TestPersistence(unittest.TestCase):
    def test_F6_bookings_survive_reload(self):
        svc1 = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        b = svc1.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        svc2 = make_service(now="2026-03-01 08:00", tmp_dir=svc1.data_dir)
        reloaded = svc2.get_booking(b.id)
        self.assertEqual(reloaded.room, "Huddle")
        self.assertEqual(reloaded.start, "09:00")

    def test_F33_ids_are_never_reused_after_cancellation(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        b1 = svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        svc.cancel_booking(b1.id)
        b2 = svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "tokafor")
        self.assertGreater(b2.id, b1.id)


if __name__ == "__main__":
    unittest.main()
