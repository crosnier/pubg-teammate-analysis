##########
# Unit Test for shared telemetry loading (issue #30)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.telemetry_cache import load_telemetry_events, select_telemetry_events


class TestLoadTelemetryEvents(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_loads_only_requested_matches(self):
        self._write_match("m1", [{"_T": "LogMatchStart"}])
        self._write_match("m2", [{"_T": "LogMatchStart"}])
        self._write_match("m3", [{"_T": "LogMatchStart"}])

        result = load_telemetry_events(["m1", "m3"], telemetry_dir=self.tmpdir.name)

        self.assertEqual(set(result.keys()), {"m1", "m3"})

    def test_skips_match_ids_not_yet_cached(self):
        self._write_match("m1", [{"_T": "LogMatchStart"}])

        result = load_telemetry_events(["m1", "not-cached"], telemetry_dir=self.tmpdir.name)

        self.assertEqual(set(result.keys()), {"m1"})


class TestSelectTelemetryEvents(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_falls_back_to_disk_when_no_preloaded_cache_given(self):
        self._write_match("m1", [{"_T": "LogMatchStart", "tag": "m1"}])
        self._write_match("m2", [{"_T": "LogMatchStart", "tag": "m2"}])

        result = select_telemetry_events(match_ids={"m1"}, telemetry_dir=self.tmpdir.name)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0]["tag"], "m1")

    def test_uses_preloaded_cache_without_touching_disk(self):
        # Deliberately point telemetry_dir at an empty directory - if this
        # ever fell through to a disk read instead of using events_by_match,
        # it would return nothing rather than the pre-loaded events.
        events_by_match = {"m1": [{"_T": "LogMatchStart", "tag": "m1"}]}

        result = select_telemetry_events(
            match_ids={"m1"}, telemetry_dir=self.tmpdir.name, events_by_match=events_by_match
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0]["tag"], "m1")

    def test_preloaded_cache_filters_by_match_ids_even_as_a_superset(self):
        # events_by_match may be a wider union built by a caller sharing it
        # across signals with different match_id scopes (see
        # archetype_tag.py) - match_ids must still filter it down.
        events_by_match = {
            "m1": [{"_T": "LogMatchStart", "tag": "m1"}],
            "m2": [{"_T": "LogMatchStart", "tag": "m2"}],
        }

        result = select_telemetry_events(match_ids={"m1"}, events_by_match=events_by_match)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0]["tag"], "m1")

    def test_preloaded_cache_with_no_match_ids_returns_everything(self):
        events_by_match = {
            "m1": [{"_T": "LogMatchStart", "tag": "m1"}],
            "m2": [{"_T": "LogMatchStart", "tag": "m2"}],
        }

        result = select_telemetry_events(match_ids=None, events_by_match=events_by_match)

        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
