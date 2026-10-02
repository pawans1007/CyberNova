
import tempfile
import unittest
from pathlib import Path

from cybersecurity.lab_manager import LabManager
from cybersecurity.scan_history import ScanHistory


class TestLabManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_dir.name) / "test_cybernova.db"
        )
        self.lab = LabManager(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_target(self):
        result = self.lab.add_target(
            "192.168.1.10",
            "Test machine",
        )
        self.assertEqual(result, "192.168.1.10/32")

    def test_target_persists_after_restart(self):
        self.lab.add_target(
            "192.168.1.0/24",
            "Local network",
        )

        restarted_lab = LabManager(self.database_path)

        self.assertIn(
            "192.168.1.0/24",
            restarted_lab.list_targets(),
        )

    def test_authorized_target(self):
        self.lab.add_target("192.168.1.0/24")

        self.assertTrue(
            self.lab.is_authorized("192.168.1.15")
        )

    def test_unauthorized_target(self):
        self.lab.add_target("192.168.1.0/24")

        self.assertFalse(
            self.lab.is_authorized("10.0.0.5")
        )

    def test_duplicate_registration(self):
        self.lab.add_target("192.168.1.10")

        with self.assertRaises(ValueError):
            self.lab.add_target("192.168.1.10")

    def test_public_target_rejected(self):
        with self.assertRaises(ValueError):
            self.lab.add_target("8.8.8.8")

    def test_remove_target(self):
        self.lab.add_target("192.168.1.10")

        self.assertTrue(
            self.lab.remove_target("192.168.1.10")
        )

        self.assertFalse(
            self.lab.is_authorized("192.168.1.10")
        )


class TestScanHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_dir.name) / "test_history.db"
        )
        self.history = ScanHistory(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_scan(self):
        scan_id = self.history.start_scan("127.0.0.1")

        self.assertIsInstance(scan_id, int)

        scan = self.history.get_scan(scan_id)

        self.assertEqual(scan["target"], "127.0.0.1")
        self.assertEqual(scan["status"], "running")

    def test_complete_scan(self):
        scan_id = self.history.start_scan("127.0.0.1")

        updated = self.history.complete_scan(
            scan_id,
            summary="Test scan completed",
            json_report="sample.json",
            text_report="sample.txt",
        )

        self.assertTrue(updated)

        scan = self.history.get_scan(scan_id)

        self.assertEqual(scan["status"], "completed")
        self.assertEqual(
            scan["summary"],
            "Test scan completed",
        )
        self.assertEqual(
            scan["json_report"],
            "sample.json",
        )
        self.assertEqual(
            scan["text_report"],
            "sample.txt",
        )

    def test_fail_scan(self):
        scan_id = self.history.start_scan("127.0.0.1")

        updated = self.history.fail_scan(
            scan_id,
            "Nmap was not found",
        )

        self.assertTrue(updated)

        scan = self.history.get_scan(scan_id)

        self.assertEqual(scan["status"], "failed")
        self.assertEqual(
            scan["error"],
            "Nmap was not found",
        )

    def test_list_scans(self):
        first_id = self.history.start_scan("127.0.0.1")
        second_id = self.history.start_scan("192.168.1.10")

        scans = self.history.list_scans()

        self.assertEqual(len(scans), 2)
        self.assertEqual(scans[0]["id"], second_id)
        self.assertEqual(scans[1]["id"], first_id)

    def test_delete_scan(self):
        scan_id = self.history.start_scan("127.0.0.1")

        self.assertTrue(
            self.history.delete_scan(scan_id)
        )

        self.assertIsNone(
            self.history.get_scan(scan_id)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)