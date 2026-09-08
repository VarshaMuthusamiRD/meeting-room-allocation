"""Day-19 edge-case and input-fuzzing sweep. Every value reaching the system
is assumed wrong: missing, empty, wrong type, absurdly long, negative, a
nonexistent date, an end before a start. The system must refuse cleanly
(RuleViolation) rather than crash with an unhandled exception."""
import unittest

from tests.helpers import make_service, with_sample_rooms

from mrbooking.errors import RuleViolation

BAD_INPUTS = [
    None,
    "",
    "   ",
    123,
    12.5,
    True,
    [],
    {},
    "x" * 10000,
    -1,
    "not-a-date",
    "2026-13-40",
    "09:99",
    "09:00:00",
]


class TestInputFuzzing(unittest.TestCase):
    def setUp(self):
        self.svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))

    def _assert_refused_not_crashed(self, **kwargs):
        base = dict(room="Huddle", date="2026-03-02", start="09:00", end="10:00", attendees=2, booked_by="rsingh")
        base.update(kwargs)
        try:
            self.svc.create_booking(**base)
        except RuleViolation:
            return  # correctly refused
        except Exception as e:  # pragma: no cover - failing this is the point of the sweep
            self.fail("Unhandled exception for input %r: %r" % (kwargs, e))

    def test_fuzz_room_field(self):
        for bad in BAD_INPUTS:
            self._assert_refused_not_crashed(room=bad)

    def test_fuzz_date_field(self):
        for bad in BAD_INPUTS:
            self._assert_refused_not_crashed(date=bad)

    def test_fuzz_start_field(self):
        for bad in BAD_INPUTS:
            self._assert_refused_not_crashed(start=bad)

    def test_fuzz_end_field(self):
        for bad in BAD_INPUTS:
            self._assert_refused_not_crashed(end=bad)

    def test_fuzz_attendees_field(self):
        for bad in [None, "", "two", -1, -100, 3.5, [], {}, "x" * 100]:
            self._assert_refused_not_crashed(attendees=bad)

    def test_fuzz_booked_by_field(self):
        for bad in BAD_INPUTS:
            self._assert_refused_not_crashed(booked_by=bad)

    def test_fuzz_negative_attendees_refused_not_crashed(self):
        self._assert_refused_not_crashed(attendees=-5)

    def test_fuzz_absurdly_long_room_name_refused_not_crashed(self):
        self._assert_refused_not_crashed(room="Z" * 5000)

    def test_fuzz_end_before_start_refused_not_crashed(self):
        self._assert_refused_not_crashed(start="10:00", end="09:00")

    def test_fuzz_nonexistent_date_refused_not_crashed(self):
        self._assert_refused_not_crashed(date="2026-02-30")

    def test_fuzz_amend_bad_inputs_do_not_crash(self):
        b = self.svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        for bad in BAD_INPUTS:
            try:
                self.svc.amend_booking(b.id, start=bad)
            except RuleViolation:
                continue
            except Exception as e:
                self.fail("Unhandled exception amending with %r: %r" % (bad, e))

    def test_fuzz_add_room_bad_capacity_does_not_crash(self):
        for bad in [None, "", "six", -1, 0, 3.5, [], {}, "x" * 100]:
            try:
                self.svc.add_room("Room-%r" % (bad,), bad)
            except RuleViolation:
                continue
            except Exception as e:
                self.fail("Unhandled exception adding room with capacity %r: %r" % (bad, e))


if __name__ == "__main__":
    unittest.main()
