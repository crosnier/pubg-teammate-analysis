##########
# Unit Test for Environment Doctor
# from root of project: `python -m unittest discover tests`
##########

import os
import sys
import tempfile
import unittest
from unittest import mock

import doctor


class TestCheckPythonVersion(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_version_file(self, version):
        path = os.path.join(self.tmpdir.name, ".python-version")
        with open(path, "w") as f:
            f.write(version)
        return path

    def test_passes_when_version_matches(self):
        actual = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        path = self._write_version_file(actual)

        ok, message = doctor.check_python_version(version_file=path)

        self.assertTrue(ok)

    def test_fails_when_major_minor_mismatches(self):
        path = self._write_version_file("99.99.99")

        ok, message = doctor.check_python_version(version_file=path)

        self.assertFalse(ok)
        self.assertIn("99.99", message)

    def test_passes_when_only_patch_version_differs(self):
        # A different patch/micro version shouldn't fail the check - only
        # a major/minor mismatch risks missing dependency compatibility.
        actual_major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
        path = self._write_version_file(f"{actual_major_minor}.999")

        ok, message = doctor.check_python_version(version_file=path)

        self.assertTrue(ok)

    def test_passes_when_no_version_file_present(self):
        ok, message = doctor.check_python_version(version_file=os.path.join(self.tmpdir.name, "missing"))

        self.assertTrue(ok)


class TestCheckPackages(unittest.TestCase):

    def test_passes_when_all_installed(self):
        ok, message = doctor.check_packages(packages=["os", "sys"])

        self.assertTrue(ok)

    def test_fails_and_lists_missing_packages(self):
        ok, message = doctor.check_packages(packages=["os", "definitely_not_a_real_package"])

        self.assertFalse(ok)
        self.assertIn("definitely_not_a_real_package", message)


class TestCheckEnvFile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_fails_when_file_missing(self):
        ok, message = doctor.check_env_file(env_path=os.path.join(self.tmpdir.name, ".env"))

        self.assertFalse(ok)

    def test_fails_when_key_missing(self):
        path = os.path.join(self.tmpdir.name, ".env")
        with open(path, "w") as f:
            f.write("SOME_OTHER_VAR=value\n")

        ok, message = doctor.check_env_file(env_path=path)

        self.assertFalse(ok)
        self.assertIn("PUBG_API_KEY", message)

    def test_fails_when_key_present_but_empty(self):
        path = os.path.join(self.tmpdir.name, ".env")
        with open(path, "w") as f:
            f.write("PUBG_API_KEY=\n")

        ok, message = doctor.check_env_file(env_path=path)

        self.assertFalse(ok)

    def test_passes_when_key_set(self):
        path = os.path.join(self.tmpdir.name, ".env")
        with open(path, "w") as f:
            f.write("PUBG_API_KEY=abc123\n")

        ok, message = doctor.check_env_file(env_path=path)

        self.assertTrue(ok)


class TestCheckDataDirs(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_creates_missing_directories(self):
        ok, message = doctor.check_data_dirs(dirs=["foo", "bar"], base_dir=self.tmpdir.name)

        self.assertTrue(ok)
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir.name, "foo")))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir.name, "bar")))
        self.assertIn("foo", message)

    def test_reports_no_creation_when_already_present(self):
        os.makedirs(os.path.join(self.tmpdir.name, "foo"))

        ok, message = doctor.check_data_dirs(dirs=["foo"], base_dir=self.tmpdir.name)

        self.assertTrue(ok)
        self.assertNotIn("Created", message)


class TestCheckApiHeartbeat(unittest.TestCase):
    """Mocks the network boundary - never calls the real PUBG API in tests."""

    def test_passes_on_status_200(self):
        with mock.patch("doctor._ping_pubg_api", return_value=200):
            ok, message = doctor.check_api_heartbeat()

        self.assertTrue(ok)

    def test_fails_on_non_200_status(self):
        with mock.patch("doctor._ping_pubg_api", return_value=503):
            ok, message = doctor.check_api_heartbeat()

        self.assertFalse(ok)
        self.assertIn("503", message)

    def test_fails_when_request_raises(self):
        with mock.patch("doctor._ping_pubg_api", side_effect=ConnectionError("no route to host")):
            ok, message = doctor.check_api_heartbeat()

        self.assertFalse(ok)
        self.assertIn("no route to host", message)


if __name__ == '__main__':
    unittest.main()
