"""F41-F44: smallest-room suggestion, under-occupancy warning, day
timeline, single-op room move."""
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking.errors import RuleViolation


class TestSuggestRoom(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))

    def test_F41_suggests_smallest_fitting_free_room(self):
        room = self.svc.suggest_room("2026-03-02", "09:00", "10:00", 2)
        self.assertIn(room.name, ("Focus 1", "Focus 2"))
        self.assertEqual(room.capacity, 2)

    def test_F41_skips_rooms_too_small(self):
        room = self.svc.suggest_room("2026-03-02", "09:00", "10:00", 5)
        self.assertEqual(room.name, "Huddle")

    def test_F41_skips_occupied_room(self):
        self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "10:00", 1, "rsingh")
        self.svc.create_booking("Focus 2", "2026-03-02", "09:00", "10:00", 1, "mbaker")
        room = self.svc.suggest_room("2026-03-02", "09:00", "10:00", 2)
        self.assertEqual(room.name, "Huddle")

    def test_F41_skips_closed_room(self):
        self.svc.close_room("Focus 1", "2026-03-05")
        room = self.svc.suggest_room("2026-03-05", "09:00", "10:00", 2)
        self.assertEqual(room.name, "Focus 2")

    def test_F41_returns_none_when_nothing_fits(self):
        room = self.svc.suggest_room("2026-03-02", "09:00", "10:00", 99)
        self.assertIsNone(room)

    def test_F41_bad_time_window_refused_not_crashed(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.suggest_room("2026-03-02", "10:00", "09:00", 2)
        self.assertEqual(ctx.exception.rule_id, "F26")

    def test_F41_zero_attendees_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.suggest_room("2026-03-02", "09:00", "10:00", 0)
        self.assertEqual(ctx.exception.rule_id, "BR5")


class TestUnderOccupancyWarning(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))

    def test_F42_warns_below_half(self):
        self.assertTrue(self.svc.is_under_occupied("Boardroom", 2))

    def test_F42_no_warning_at_exactly_half(self):
        # capacity 14, half is 7 -- "fewer than half" means 7 is NOT a warning.
        self.assertFalse(self.svc.is_under_occupied("Boardroom", 7))

    def test_F42_no_warning_above_half(self):
        self.assertFalse(self.svc.is_under_occupied("Boardroom", 10))

    def test_F42_booking_still_accepted_despite_low_occupancy(self):
        b = self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(b.attendees, 2)
        self.assertTrue(self.svc.is_under_occupied(b.room, b.attendees))


class TestDayTimeline(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))

    def test_F43_timeline_one_row_per_room(self):
        from mrbooking import reports
        rows = reports.day_timeline(self.svc.store, "2026-03-02", self.svc.config)
        self.assertEqual(len(rows), 4)
        names = {r["room"] for r in rows}
        self.assertEqual(names, {"Focus 1", "Focus 2", "Huddle", "Boardroom"})

    def test_F43_occupied_cells_marked(self):
        from mrbooking import reports
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        rows = {r["room"]: r for r in reports.day_timeline(self.svc.store, "2026-03-02", self.svc.config)}
        huddle_line = rows["Huddle"]["line"]
        # 08:00-20:00 at 30-min resolution: index 2 covers 09:00-09:30, should be occupied.
        self.assertEqual(huddle_line[2], "#")
        self.assertEqual(huddle_line[0], ".")

    def test_F43_closed_room_flagged(self):
        from mrbooking import reports
        self.svc.close_room("Focus 1", "2026-03-05")
        rows = {r["room"]: r for r in reports.day_timeline(self.svc.store, "2026-03-05", self.svc.config)}
        self.assertTrue(rows["Focus 1"]["closed"])


class TestMoveBooking(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        self.b = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")

    def test_F44_move_keeps_identifier(self):
        moved = self.svc.move_booking(self.b.id, "Focus 1")
        self.assertEqual(moved.id, self.b.id)
        self.assertEqual(moved.room, "Focus 1")
        self.assertEqual(moved.start, "09:00")
        self.assertEqual(moved.end, "10:00")

    def test_F44_old_slot_becomes_free(self):
        self.svc.move_booking(self.b.id, "Focus 1")
        new_booking = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        self.assertIsNotNone(new_booking.id)

    def test_F44_move_to_same_room_refused_as_noop(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.move_booking(self.b.id, "Huddle")
        self.assertEqual(ctx.exception.rule_id, "BR16")

    def test_F44_move_to_too_small_room_refused(self):
        big_booking = self.svc.create_booking("Boardroom", "2026-03-02", "11:00", "12:00", 5, "tokafor")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.move_booking(big_booking.id, "Focus 1")  # capacity 2, booking has 5 attendees
        self.assertEqual(ctx.exception.rule_id, "BR5")

    def test_F44_move_to_occupied_room_refused(self):
        self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "10:00", 1, "mbaker")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.move_booking(self.b.id, "Focus 1")
        self.assertEqual(ctx.exception.rule_id, "BR1")


if __name__ == "__main__":
    unittest.main()
