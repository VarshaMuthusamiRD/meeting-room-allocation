"""F11-F16, BR10-BR16."""
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking.errors import RuleViolation


class TestAmend(unittest.TestCase):
    def setUp(self):
        self.early = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        self.b = self.early.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.svc = make_service(now="2026-03-01 09:00", tmp_dir=self.early.data_dir)

    def test_F11_amend_time(self):
        updated = self.svc.amend_booking(self.b.id, start="10:00", end="11:00")
        self.assertEqual(updated.start, "10:00")
        self.assertEqual(updated.end, "11:00")

    def test_F12_amended_booking_reapplies_rules(self):
        self.svc.create_booking("Huddle", "2026-03-02", "11:00", "12:00", 2, "tokafor")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.amend_booking(self.b.id, start="11:30", end="12:30")
        self.assertEqual(ctx.exception.rule_id, "BR1")

    def test_BR10_amendment_does_not_conflict_with_own_previous_slot(self):
        updated = self.svc.amend_booking(self.b.id, start="09:15", end="10:15")
        self.assertEqual(updated.start, "09:15")

    def test_BR11_amend_within_cutoff_refused(self):
        late_svc = make_service(now="2026-03-02 08:35", tmp_dir=self.early.data_dir)
        with self.assertRaises(RuleViolation) as ctx:
            late_svc.amend_booking(self.b.id, start="10:00", end="11:00")
        self.assertEqual(ctx.exception.rule_id, "BR11")

    def test_BR16_noop_amendment_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.amend_booking(self.b.id, room="Huddle", date="2026-03-02", start="09:00", end="10:00", attendees=2)
        self.assertEqual(ctx.exception.rule_id, "BR16")

    def test_amend_over_capacity_refused_BR5(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.amend_booking(self.b.id, attendees=99)
        self.assertEqual(ctx.exception.rule_id, "BR5")


class TestRoomAdmin(unittest.TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_F13_add_room(self):
        r = self.svc.add_room("Huddle", 6)
        self.assertEqual(r.capacity, 6)

    def test_F14_list_rooms(self):
        self.svc.add_room("Huddle", 6)
        self.svc.add_room("Boardroom", 14)
        names = [r.name for r in self.svc.list_rooms()]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_BR12_duplicate_name_case_insensitive_refused(self):
        self.svc.add_room("Huddle", 6)
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.add_room("  huddle  ", 8)
        self.assertEqual(ctx.exception.rule_id, "BR12")

    def test_BR15_capacity_zero_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.add_room("Tiny", 0)
        self.assertEqual(ctx.exception.rule_id, "BR15")

    def test_BR15_capacity_51_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.add_room("Huge", 51)
        self.assertEqual(ctx.exception.rule_id, "BR15")

    def test_F15_close_room(self):
        self.svc.add_room("Huddle", 6)
        closure = self.svc.close_room("Huddle", "2026-03-05")
        self.assertEqual(closure.room, "Huddle")

    def test_BR14_close_room_with_bookings_refused(self):
        early = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        early.create_booking("Huddle", "2026-03-05", "09:00", "10:00", 2, "rsingh")
        with self.assertRaises(RuleViolation) as ctx:
            early.close_room("Huddle", "2026-03-05")
        self.assertEqual(ctx.exception.rule_id, "BR14")

    def test_F16_free_periods_exclude_bookings(self):
        early = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        early.create_booking("Huddle", "2026-03-05", "09:00", "10:00", 2, "rsingh")
        periods = early.free_periods("Huddle", "2026-03-05")
        self.assertIn(("08:00", "09:00"), periods)
        self.assertIn(("10:00", "20:00"), periods)
        for start, end in periods:
            h1, m1 = start.split(":")
            h2, m2 = end.split(":")
            length = (int(h2) * 60 + int(m2)) - (int(h1) * 60 + int(m1))
            self.assertGreaterEqual(length, 15)

    def test_G12_closed_room_has_no_free_periods(self):
        early = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        early.close_room("Huddle", "2026-03-05")
        periods = early.free_periods("Huddle", "2026-03-05")
        self.assertEqual(periods, [])


if __name__ == "__main__":
    unittest.main()
