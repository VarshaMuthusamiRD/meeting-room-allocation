"""F34-F40: startup self-check, version reporting, config-driven behaviour,
scriptable exit codes, usage message, injectable time, backup restore."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.helpers import make_service, with_sample_rooms

from mrbooking import SOFTWARE_VERSION, FORMAT_VERSION
from mrbooking.cli import main


def run_cli(args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(args)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0
    return code, out.getvalue(), err.getvalue()


class TestOperability(unittest.TestCase):
    def test_F34_check_on_fresh_data_dir_succeeds(self):
        tmp = Path(tempfile.mkdtemp())
        code, out, err = run_cli(["--data-dir", str(tmp), "check"])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_F34_check_on_corrupted_file_fails_clearly(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        svc.data_path.write_text("{not valid json", encoding="utf-8")
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "check"])
        self.assertEqual(code, 1)
        self.assertIn("FAILED", err)

    def test_F36_version_reports_software_and_format_version(self):
        tmp = Path(tempfile.mkdtemp())
        code, out, err = run_cli(["--data-dir", str(tmp), "version"])
        self.assertEqual(code, 0)
        self.assertIn(SOFTWARE_VERSION, out)
        self.assertIn(str(FORMAT_VERSION), out)

    def test_F37_success_exit_code_is_zero(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "--now", "2026-03-01 08:00",
                                   "book", "Huddle", "2026-03-02", "09:00", "10:00", "2", "rsingh"])
        self.assertEqual(code, 0)

    def test_F37_failure_exit_code_is_nonzero(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "--now", "2026-03-01 08:00",
                                   "book", "NoSuchRoom", "2026-03-02", "09:00", "10:00", "2", "rsingh"])
        self.assertEqual(code, 1)
        self.assertIn("F28", err)

    def test_F38_usage_lists_every_operation(self):
        code, out, err = run_cli(["-h"])
        for op in ["book", "cancel", "get", "list-date", "list-room", "list-booker",
                   "amend", "add-room", "list-rooms", "close-room", "free-periods",
                   "version", "check", "report-utilisation", "report-minutes",
                   "report-seat-utilisation", "report-peak", "report-under-occupied",
                   "report-range", "report-booker", "report-empty",
                   "list-backups", "restore-backup"]:
            self.assertIn(op, out)

    def test_F39_now_override_changes_reported_refusal(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "--now", "2020-01-01 08:00",
                                   "book", "Huddle", "2026-03-02", "09:00", "10:00", "2", "rsingh"])
        self.assertEqual(code, 0)  # 2026 is in the future relative to 2020, so accepted

    def test_F40_restore_backup_via_cli(self):
        svc = with_sample_rooms(make_service(now="2026-03-01 08:00"))
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "list-backups"])
        self.assertEqual(code, 0)
        svc.add_room("Extra", 4)
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "list-backups"])
        self.assertEqual(code, 0)
        backup_lines = [l for l in out.strip().splitlines() if l]
        self.assertTrue(len(backup_lines) >= 1)
        code, out, err = run_cli(["--data-dir", str(svc.data_dir), "restore-backup", backup_lines[0]])
        self.assertEqual(code, 0)
        data = json.loads(svc.data_path.read_text(encoding="utf-8"))
        names = [r["name"] for r in data["rooms"]]
        self.assertNotIn("Extra", names)


if __name__ == "__main__":
    unittest.main()
