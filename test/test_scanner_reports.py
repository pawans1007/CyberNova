import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from cybersecurity.scanner import NmapScanner
from cybersecurity.report_generator import ReportGenerator


SAMPLE_XML = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <address addr="127.0.0.1" addrtype="ipv4"/>
        <hostnames>
            <hostname name="localhost" type="PTR"/>
        </hostnames>
        <ports>
            <port protocol="tcp" portid="80">
                <state state="open"/>
                <service name="http" product="Test Server" version="1.0"/>
            </port>
        </ports>
    </host>
</nmaprun>
"""


class FakeLabManager:
    def __init__(self, authorized=True):
        self.authorized = authorized

    def is_authorized(self, target):
        return self.authorized


class TestNmapScanner(unittest.TestCase):

    def setUp(self):
        self.lab_manager = FakeLabManager()
        self.scanner = NmapScanner(
            self.lab_manager,
            timeout=10,
        )

    def test_invalid_target(self):
        result = self.scanner.scan("not-an-ip")

        self.assertFalse(result["success"])
        self.assertIn("Invalid target", result["error"])

    def test_unauthorized_target(self):
        self.lab_manager.authorized = False

        result = self.scanner.scan("127.0.0.1")

        self.assertFalse(result["success"])
        self.assertIn("not registered", result["error"])

    def test_broad_network_rejected(self):
        result = self.scanner.scan("192.168.0.0/16")

        self.assertFalse(result["success"])
        self.assertIn("/24", result["error"])

    @patch("cybersecurity.scanner.shutil.which", return_value=None)
    def test_nmap_not_installed(self, mock_which):
        result = self.scanner.scan("127.0.0.1")

        self.assertFalse(result["success"])
        self.assertIn("Nmap was not found", result["error"])

    @patch("cybersecurity.scanner.subprocess.run")
    @patch("cybersecurity.scanner.shutil.which", return_value="nmap")
    def test_successful_scan(self, mock_which, mock_run):
        mock_run.return_value = Mock(
            returncode=0,
            stdout=SAMPLE_XML,
            stderr="",
        )

        result = self.scanner.scan("127.0.0.1")

        self.assertTrue(result["success"])
        self.assertEqual(result["target"], "127.0.0.1/32")
        self.assertIn("<nmaprun>", result["xml"])
        mock_run.assert_called_once()

    @patch("cybersecurity.scanner.subprocess.run")
    @patch("cybersecurity.scanner.shutil.which", return_value="nmap")
    def test_scan_timeout(self, mock_which, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="nmap",
            timeout=10,
        )

        result = self.scanner.scan("127.0.0.1")

        self.assertFalse(result["success"])
        self.assertIn("timeout", result["error"].lower())


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.reports_dir = Path(self.temp_dir.name)
        self.generator = ReportGenerator(
            reports_dir=self.reports_dir,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_valid_xml(self):
        result = self.generator.parse_nmap_xml(SAMPLE_XML)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["hosts"]), 1)

        host = result["hosts"][0]
        self.assertEqual(host["status"], "up")
        self.assertEqual(host["addresses"][0]["address"], "127.0.0.1")
        self.assertEqual(host["ports"][0]["port"], "80")
        self.assertEqual(host["ports"][0]["state"], "open")

    def test_parse_invalid_xml(self):
        result = self.generator.parse_nmap_xml("<invalid")

        self.assertFalse(result["success"])
        self.assertIn("Invalid Nmap XML", result["error"])

    def test_parse_empty_xml(self):
        result = self.generator.parse_nmap_xml("")

        self.assertFalse(result["success"])
        self.assertIn("empty", result["error"].lower())

    def test_unexpected_xml_root(self):
        result = self.generator.parse_nmap_xml("<root/>")

        self.assertFalse(result["success"])

    def test_save_report(self):
        scan_result = {
            "success": True,
            "target": "127.0.0.1",
            "xml": SAMPLE_XML,
        }

        result = self.generator.save_report(scan_result)

        self.assertTrue(result["success"])
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["text_path"]).exists())

        text = Path(result["text_path"]).read_text(
            encoding="utf-8"
        )

        self.assertIn("CyberNova Nmap Scan Report", text)
        self.assertIn("127.0.0.1", text)
        self.assertIn("80", text)

    def test_cannot_save_failed_scan(self):
        result = self.generator.save_report({
            "success": False,
            "error": "Scan failed",
        })

        self.assertFalse(result["success"])
        self.assertIn("unsuccessful scan", result["error"])

    def test_unique_report_filenames(self):
        scan_result = {
            "success": True,
            "target": "127.0.0.1",
            "xml": SAMPLE_XML,
        }

        first = self.generator.save_report(scan_result)
        second = self.generator.save_report(scan_result)

        self.assertTrue(first["success"])
        self.assertTrue(second["success"])
        self.assertNotEqual(
            first["json_path"],
            second["json_path"],
        )


if __name__ == "__main__":
    unittest.main()
