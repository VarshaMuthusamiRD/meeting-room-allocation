"""F29-F32, TC12: atomic saves, backup rotation, corruption detection, audit log."""
import json
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import make_service, with_sample_rooms

from mrbooking import audit, storage
from mrbooking.errors import DataFileError


class TestAtomicSave(unittest.TestCase):
    def test_F29_failed_save_does_not_corrupt_existing_file(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        before = svc.data_path.read_text(encoding="utf-8")
        with mock.patch("mrbooking.storage.os.replace", side_effect=OSError("simulated interruption")):
            with self.assertRaises(OSError):
                storage.save(svc.data_path, svc.store)
        after = svc.data_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        json.loads(after)  # still valid JSON, still loadable

    def test_F29_no_stray_temp_files_after_successful_save(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        leftovers = list(svc.data_dir.glob(".tmp-*"))
        self.assertEqual(leftovers, [])


class TestCorruptionDetection(unittest.TestCase):
    def test_F30_invalid_json_reported_clearly(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.data_path.write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(DataFileError):
            storage.load(svc.data_path)

    def test_F30_missing_required_keys_reported_clearly(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.data_path.write_text(json.dumps({"rooms": []}), encoding="utf-8")
        with self.assertRaises(DataFileError):
            storage.load(svc.data_path)

    def test_F30_hand_edited_bad_field_type_reported_clearly(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        data = json.loads(svc.data_path.read_text(encoding="utf-8"))
        data["next_id"] = "not a number"
        svc.data_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(DataFileError):
            storage.load(svc.data_path)


class TestBackupRotation(unittest.TestCase):
    def test_F31_retains_three_most_recent_backups(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        for i in range(6):
            svc.add_room("Room%d" % i, 4)
        backups = storage.list_backups(svc.data_path)
        self.assertLessEqual(len(backups), 3)

    def test_F40_restore_from_backup(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        backups_before = storage.list_backups(svc.data_path)
        svc.add_room("Extra", 4)
        backups = storage.list_backups(svc.data_path)
        self.assertTrue(len(backups) >= 1)
        storage.restore_from_backup(svc.data_path, backups[0])
        restored = storage.load(svc.data_path)
        names = [r.name for r in restored.rooms]
        self.assertNotIn("Extra", names)


class TestAuditLog(unittest.TestCase):
    def test_F32_accepted_booking_logged(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        entries = audit.read_all(svc.audit_path)
        accepted = [e for e in entries if e["operation"] == "create_booking" and e["outcome"] == "accepted"]
        self.assertEqual(len(accepted), 1)

    def test_F32_refused_booking_logged_with_rule_id(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        try:
            svc.create_booking("Huddle", "2026-03-02", "09:30", "10:30", 2, "tokafor")
        except Exception:
            pass
        entries = audit.read_all(svc.audit_path)
        refused = [e for e in entries if e["outcome"] == "refused"]
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]["rule_id"], "BR1")

    def test_G10_amendment_logged(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        b = svc.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        svc.amend_booking(b.id, start="10:00", end="11:00")
        entries = audit.read_all(svc.audit_path)
        amend_entries = [e for e in entries if e["operation"] == "amend_booking"]
        self.assertEqual(len(amend_entries), 1)

    def test_TC12_audit_log_is_append_only_across_runs(self):
        svc1 = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc1.create_booking("Huddle", "2026-03-02", "09:00", "10:00", 2, "rsingh")
        first_count = len(audit.read_all(svc1.audit_path))
        svc2 = make_service(now="2026-03-01 09:00", tmp_dir=svc1.data_dir)
        svc2.create_booking("Boardroom", "2026-03-02", "09:00", "10:00", 2, "mbaker")
        entries = audit.read_all(svc1.audit_path)
        self.assertEqual(len(entries), first_count + 1)


if __name__ == "__main__":
    unittest.main()
