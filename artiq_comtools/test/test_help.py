"""Generic tests for frontend commands."""
import subprocess
import sys
import unittest


class TestFrontends(unittest.TestCase):
    def test_help(self):
        """Test --help as a simple smoke test against catastrophic breakage."""
        commands = [
            "ctlmgr", "influxdb", "influxdb_schedule"
        ]

        for command in commands:
            subprocess.check_call(
                [sys.executable, "-m", "artiq_comtools.artiq_" + command, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT)
