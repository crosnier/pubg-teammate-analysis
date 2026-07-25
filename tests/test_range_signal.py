##########
# Unit Test for Range Signal (Archetype Tag - range axis)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.range_signal import compute_range_signal, CLOSE_RANGE_MAX_METERS, MID_RANGE_MAX_METERS

ME = "account.me"
RIVAL = "account.rival"


def kill_event(killer_id, victim_id, distance_m, is_suicide=False,
               killer_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "type": killer_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "killerDamageInfo": {"distance": distance_m * 100},
    }


class TestComputeRangeSignal(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_bucket_assignment(self):
        cases = [
            ("close", [5, 8, 10, 12, 15, 18, 20, 22], "Close-Range"),
            ("mid", [25, 27, 30, 32, 33, 35, 36, 38], "Mid-Range"),
            ("long", [50, 80, 100, 120, 150, 200, 250, 300], "Long-Range"),
            ("close_range_boundary_inclusive", [CLOSE_RANGE_MAX_METERS] * 8, "Close-Range"),
            ("mid_range_boundary_inclusive", [MID_RANGE_MAX_METERS] * 8, "Mid-Range"),
        ]
        for name, distances, expected_bucket in cases:
            with self.subTest(case=name):
                self._write_match(name, [kill_event(ME, RIVAL, d) for d in distances])

                result = compute_range_signal(ME, telemetry_dir=self.tmpdir.name, match_ids={name})

                self.assertEqual(result["range_bucket"], expected_bucket)
                self.assertEqual(result["kills_analyzed"], 8)

    def test_uses_median_not_mean_to_resist_outliers(self):
        # 7 close kills + 1 extreme long-range outlier: median stays close-range,
        # a mean-based calculation would get dragged into Mid/Long-Range instead.
        events = [kill_event(ME, RIVAL, 10) for _ in range(7)] + [kill_event(ME, RIVAL, 600)]
        self._write_match("m1", events)

        result = compute_range_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["range_bucket"], "Close-Range")
        self.assertEqual(result["median_distance_m"], 10)

    def test_none_below_minimum_kills(self):
        events = [kill_event(ME, RIVAL, 10) for _ in range(5)]
        self._write_match("m1", events)

        result = compute_range_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result["range_bucket"])
        self.assertIsNone(result["median_distance_m"])
        self.assertEqual(result["kills_analyzed"], 5)

    def test_ignores_suicides_and_non_user_kills(self):
        events = [kill_event(ME, RIVAL, 10) for _ in range(8)] + [
            kill_event(ME, ME, 500, is_suicide=True),
            kill_event(ME, RIVAL, 500, victim_type="user_ai"),
        ]
        self._write_match("m1", events)

        result = compute_range_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["kills_analyzed"], 8)
        self.assertEqual(result["range_bucket"], "Close-Range")

    def test_aggregates_across_multiple_matches(self):
        self._write_match("m1", [kill_event(ME, RIVAL, 10) for _ in range(4)])
        self._write_match("m2", [kill_event(ME, RIVAL, 15) for _ in range(4)])

        result = compute_range_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["kills_analyzed"], 8)
        self.assertEqual(result["range_bucket"], "Close-Range")


if __name__ == '__main__':
    unittest.main()
