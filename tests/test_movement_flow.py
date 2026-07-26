##########
# Unit Test for Movement Flow (Map Drop Zone + Flow, issue #44)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.movement_flow import (
    compute_flow_read_from_events,
    compute_flow_signal,
    MIN_MATCHES_FOR_SIGNAL,
    MIN_POSITIONS_FOR_MATCH_READING,
    ZONE_CENTER_MAX_FRACTION,
    BALANCED_MAX_FRACTION,
)

ME = "account.me"
ZONE_X, ZONE_Y, ZONE_RADIUS = 400000, 400000, 500000


def player_create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id}}


def zone_event(elapsed_time, radius=ZONE_RADIUS, x=ZONE_X, y=ZONE_Y):
    return {
        "_T": "LogGameStatePeriodic",
        "gameState": {
            "elapsedTime": elapsed_time,
            "safetyZonePosition": {"x": x, "y": y},
            "safetyZoneRadius": radius,
        },
    }


def position_event(account_id, elapsed_time, x, y, char_type="user"):
    return {
        "_T": "LogPlayerPosition",
        "elapsedTime": elapsed_time,
        "character": {"accountId": account_id, "type": char_type, "location": {"x": x, "y": y, "z": 0}},
    }


def positions_at_fraction(account_id, fraction, count=MIN_POSITIONS_FOR_MATCH_READING):
    # All positions due-east of zone center at `fraction` of the radius.
    offset = fraction * ZONE_RADIUS
    return [position_event(account_id, t * 10, ZONE_X + offset, ZONE_Y) for t in range(count)]


class TestComputeFlowReadFromEvents(unittest.TestCase):

    def test_none_when_player_absent(self):
        events = [zone_event(0)]
        self.assertIsNone(compute_flow_read_from_events(ME, events))

    def test_none_when_no_zone_data(self):
        events = [player_create_event(ME)] + positions_at_fraction(ME, 0.1)
        self.assertIsNone(compute_flow_read_from_events(ME, events))

    def test_none_below_minimum_positions(self):
        events = [player_create_event(ME), zone_event(0)] + positions_at_fraction(
            ME, 0.1, count=MIN_POSITIONS_FOR_MATCH_READING - 1
        )
        self.assertIsNone(compute_flow_read_from_events(ME, events))

    def test_bucket_assignment(self):
        cases = [
            ("center", 0.1, "Zone Center"),
            ("balanced", 0.35, "Balanced Rotator"),
            ("edge", 0.8, "Zone Edge"),
            ("center_boundary_inclusive", ZONE_CENTER_MAX_FRACTION, "Zone Center"),
            ("balanced_boundary_inclusive", BALANCED_MAX_FRACTION, "Balanced Rotator"),
        ]
        for name, fraction, expected_bucket in cases:
            with self.subTest(case=name):
                events = [player_create_event(ME), zone_event(0)] + positions_at_fraction(ME, fraction)
                result = compute_flow_read_from_events(ME, events)
                self.assertEqual(result["flow_bucket"], expected_bucket)
                self.assertEqual(result["positions_analyzed"], MIN_POSITIONS_FOR_MATCH_READING)

    def test_ignores_other_players_and_bots(self):
        events = [
            player_create_event(ME),
            zone_event(0),
            *positions_at_fraction("account.rival", 0.9),
            *[position_event(ME, t * 10, ZONE_X, ZONE_Y, char_type="user_ai") for t in range(5)],
            *positions_at_fraction(ME, 0.1),
        ]
        result = compute_flow_read_from_events(ME, events)
        self.assertEqual(result["flow_bucket"], "Zone Center")

    def test_uses_zone_snapshot_at_or_before_position_time(self):
        # A position at t=25 sits at offset 180000 from zone center. Three
        # candidate snapshots give three different buckets depending on
        # which one gets picked (radius 500000 -> Balanced, 200000 -> Edge,
        # 800000 -> Center) - only the t=20/radius=200000 one (the most
        # recent snapshot at or before t=25) is correct.
        events = [
            player_create_event(ME),
            zone_event(0, radius=500000),
            zone_event(20, radius=200000),
            zone_event(30, radius=800000),
        ] + [position_event(ME, 25, ZONE_X + 180000, ZONE_Y) for _ in range(MIN_POSITIONS_FOR_MATCH_READING)]
        result = compute_flow_read_from_events(ME, events)
        self.assertEqual(result["flow_bucket"], "Zone Edge")


class TestComputeFlowSignal(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_none_below_minimum_matches(self):
        for i in range(MIN_MATCHES_FOR_SIGNAL - 1):
            self._write_match(f"m{i}", [player_create_event(ME), zone_event(0)] + positions_at_fraction(ME, 0.1))

        result = compute_flow_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result["flow_tag"])
        self.assertEqual(result["matches_analyzed"], MIN_MATCHES_FOR_SIGNAL - 1)

    def test_most_frequent_bucket_wins(self):
        for i in range(6):
            self._write_match(f"c{i}", [player_create_event(ME), zone_event(0)] + positions_at_fraction(ME, 0.1))
        for i in range(2):
            self._write_match(f"e{i}", [player_create_event(ME), zone_event(0)] + positions_at_fraction(ME, 0.9))

        result = compute_flow_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["flow_tag"], "Zone Center")
        self.assertEqual(result["matches_analyzed"], MIN_MATCHES_FOR_SIGNAL)


if __name__ == '__main__':
    unittest.main()
