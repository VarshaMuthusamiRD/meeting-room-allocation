"""TC7, TC9, F35, F39: injectable clock and externally configurable behaviour."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import make_service, with_sample_rooms

from mrbooking.clock import Clock
from mrbooking.config import Config
from mrbooking.errors import RuleViolation
from mrbooking.service import BookingService


class TestInjectableClock(unittest.TestCase):
    def test_TC7_F39_fixed_now_makes_BR6_reproducible(self):
        svc_a = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc_b = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        with self.assertRaises(RuleViolation) as ctx_a:
            svc_a.create_booking("Huddle", "2026-02-01", "09:00", "10:00", 2, "rsingh")
        with self.assertRaises(RuleViolation) as ctx_b:
            svc_b.create_booking("Huddle", "2026-02-01", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx_a.exception.rule_id, ctx_b.exception.rule_id)
        self.assertEqual(ctx_a.exception.rule_id, "BR6")


class TestConfigDriven(unittest.TestCase):
    def test_TC9_F35_opening_hours_come_from_config_not_code(self):
        tmp_dir = Path(tempfile.mkdtemp())
        config_path = tmp_dir / "config.json"
        config_path.write_text(json.dumps({
            "opening_time": "10:00",
            "closing_time": "18:00",
            "min_booking_minutes": 15,
            "max_booking_minutes": 240,
            "daily_booking_limit_per_person": 3,
            "slot_minutes": 15,
            "min_free_period_minutes": 15,
            "cancel_amend_cutoff_minutes": 60,
        }), encoding="utf-8")
        config = Config.load(config_path)
        clock = Clock.from_iso("2026-03-01 08:00")
        svc = BookingService(data_dir=tmp_dir / "data", config=config, clock=clock)
        svc.add_room("Huddle", 6)
        # 09:00 is before the configured 10:00 opening -- must be refused under BR4.
        with self.assertRaises(RuleViolation) as ctx:
            svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        self.assertEqual(ctx.exception.rule_id, "BR4")
        # 10:00-11:00 is within the configured hours -- accepted.
        b = svc.create_booking("Huddle", "2026-03-02", "10:00", "11:00", 2, "rsingh")
        self.assertIsNotNone(b.id)

    def test_AC39_config_change_takes_effect_without_code_change(self):
        default_config = Config()
        self.assertEqual(default_config.opening_time, "08:00")
        custom_config = Config(opening_time="06:00", closing_time="22:00")
        self.assertEqual(custom_config.opening_time, "06:00")


if __name__ == "__main__":
    unittest.main()
