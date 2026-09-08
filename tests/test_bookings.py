"""F1, F2, F4, F5, F9, F10, BR1-BR9, BR13, F25-F28."""
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking.errors import NotFoundError, RuleViolation


class TestCreateBooking(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service())

    def test_F1_valid_booking_is_accepted(self):
        b = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 4, "rsingh")
        self.assertEqual(b.room, "Huddle")
        listed = self.svc.list_bookings_for_date("2026-03-02")
        self.assertIn(b.id, [x.id for x in listed])

    def test_BR1_overlap_refused(self):
        self.svc.create_booking("Huddle", "2026-03-02", "10:00", "11:00", 2, "rsingh")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "10:30", "11:30", 2, "tokafor")
        self.assertEqual(ctx.exception.rule_id, "BR1")

    def test_BR1_touching_bookings_accepted(self):
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        b2 = self.svc.create_booking("Huddle", "2026-03-02", "10:00", "11:00", 2, "tokafor")
        self.assertIsNotNone(b2.id)

    def test_BR2_below_minimum_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "09:00", "09:10", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR2")

    def test_BR2_exactly_15_minutes_accepted(self):
        b = self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 1, "rsingh")
        self.assertIsNotNone(b.id)

    def test_BR2_exactly_4_hours_accepted(self):
        b = self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "13:00", 4, "rsingh")
        self.assertIsNotNone(b.id)

    def test_BR2_above_maximum_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "13:15", 4, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR2")

    def test_BR3_not_on_quarter_hour_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "09:07", "09:37", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR3")

    def test_BR4_starts_before_opening_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "07:45", "09:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR4")

    def test_BR4_ends_exactly_at_closing_accepted(self):
        b = self.svc.create_booking("Huddle", "2026-03-02", "19:00", "20:00", 2, "rsingh")
        self.assertIsNotNone(b.id)

    def test_BR4_ends_after_closing_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "19:30", "20:30", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR4")

    def test_BR5_over_capacity_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 3, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR5")

    def test_BR5_exactly_at_capacity_accepted(self):
        b = self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 14, "rsingh")
        self.assertEqual(b.attendees, 14)

    def test_BR6_past_booking_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-02-01", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR6")

    def test_BR7_fourth_booking_same_day_refused(self):
        self.svc.create_booking("Focus 1", "2026-03-02", "09:00", "09:15", 1, "rsingh")
        self.svc.create_booking("Focus 2", "2026-03-02", "09:15", "09:30", 1, "rsingh")
        self.svc.create_booking("Huddle", "2026-03-02", "09:30", "09:45", 1, "rsingh")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Boardroom", "2026-03-02", "09:45", "10:00", 1, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR7")

    def test_BR9_closed_room_refused(self):
        self.svc.close_room("Huddle", "2026-03-05")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-05", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR9")

    def test_BR13_bad_booker_id_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "R Singh")
        self.assertEqual(ctx.exception.rule_id, "BR13")

    def test_F25_missing_field_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F25")

    def test_F25_wrong_type_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", "two", "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F25")

    def test_F26_end_before_start_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "10:00", "09:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F26")

    def test_F26_end_equals_start_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "10:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F26")

    def test_F27_nonexistent_date_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-02-30", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F27")

    def test_F28_unknown_room_refused(self):
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Not A Room", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "F28")

    def test_F2_refusal_names_the_rule(self):
        self.svc.create_booking("Huddle", "2026-03-02", "10:00", "11:00", 2, "rsingh")
        with self.assertRaises(RuleViolation) as ctx:
            self.svc.create_booking("Huddle", "2026-03-02", "10:30", "11:30", 2, "tokafor")
        self.assertTrue(ctx.exception.rule_id.startswith("BR") or ctx.exception.rule_id.startswith("F"))


class TestListAndRetrieve(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service())

    def test_F4_list_by_date_ordered_by_room_then_start(self):
        self.svc.create_booking("Huddle", "2026-03-02", "13:00", "14:00", 4, "rsingh")
        self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 4, "mbaker")
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 4, "tokafor")
        items = self.svc.list_bookings_for_date("2026-03-02")
        rooms_starts = [(b.room, b.start) for b in items]
        self.assertEqual(rooms_starts, sorted(rooms_starts, key=lambda t: (t[0].lower(), t[1])))

    def test_F5_list_by_room_and_date(self):
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        items = self.svc.list_bookings_for_room_date("Huddle", "2026-03-02")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].room, "Huddle")

    def test_F9_get_booking_by_id(self):
        b = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        fetched = self.svc.get_booking(b.id)
        self.assertEqual(fetched.id, b.id)

    def test_F9_get_missing_booking_raises(self):
        with self.assertRaises(NotFoundError):
            self.svc.get_booking(99999)

    def test_F10_list_by_booker_and_date(self):
        self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.svc.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        items = self.svc.list_bookings_for_booker_date("rsingh", "2026-03-02")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].booked_by, "rsingh")


class TestCancel(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service())

    def test_F3_cancel_by_id(self):
        b = self.svc.create_booking("Huddle", "2026-03-05", "09:00", "10:00", 2, "rsingh")
        cancelled = self.svc.cancel_booking(b.id)
        self.assertEqual(cancelled.status, "cancelled")

    def test_BR8_cancel_within_cutoff_refused(self):
        early_svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        b = early_svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        late_svc = make_service(now="2026-03-02 08:35", tmp_dir=early_svc.data_dir)
        with self.assertRaises(RuleViolation) as ctx:
            late_svc.cancel_booking(b.id)
        self.assertEqual(ctx.exception.rule_id, "BR8")

    def test_AC11_cancelled_slot_becomes_available(self):
        b = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.svc.cancel_booking(b.id)
        b2 = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "tokafor")
        self.assertNotEqual(b.id, b2.id)


if __name__ == "__main__":
    unittest.main()
