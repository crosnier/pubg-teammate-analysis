##########
# Unit Test for Solo Coaching Note (Squad Read's capstone stand-in for solo.py)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.solo_coaching import (
    compute_coaching_line,
    compute_map_line,
    MIN_MATCHES_FOR_MAP_SIGNAL,
)

ME = "account.me"
RIVAL = "account.rival"


def match_start(day, map_name="Baltic_Main"):
    return {"_T": "LogMatchStart", "_D": f"2026-07-{day:02d}T00:00:00.000Z", "mapName": map_name}


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def damage_event(attacker_id, victim_id, damage):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "damage": damage,
    }


class TestComputeCoachingLine(unittest.TestCase):

    def test_known_stat_keys_return_fixed_coaching_text(self):
        for stat_key in ("kills_before_death", "revives", "damage"):
            with self.subTest(stat_key=stat_key):
                result = compute_coaching_line({"stat_key": stat_key, "value": 5})
                self.assertIsNotNone(result)

    def test_close_range_win_rate_direction_changes_tone(self):
        winning = compute_coaching_line({"stat_key": "close_range_win_rate", "value": 0.8})
        losing = compute_coaching_line({"stat_key": "close_range_win_rate", "value": 0.2})
        self.assertIn("trust your instinct", winning)
        self.assertIn("disengaging earlier", losing)

    def test_knockdown_conversion_direction_changes_tone(self):
        converting = compute_coaching_line({"stat_key": "knockdown_conversion_rate", "value": 0.9})
        not_converting = compute_coaching_line({"stat_key": "knockdown_conversion_rate", "value": 0.1})
        self.assertIn("finish what you start", converting)
        self.assertIn("follow up faster", not_converting)

    def test_fallback_kill_count_has_no_coaching_line(self):
        result = compute_coaching_line({"stat_key": "fallback_kill_count", "value": None})
        self.assertIsNone(result)


class TestComputeMapLine(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.match_ids = []

    def _write_match(self, day, map_name, damage):
        events = [match_start(day, map_name), create_event(ME), damage_event(ME, RIVAL, damage)]
        match_id = f"match-{day}"
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)
        self.match_ids.append(match_id)

    def test_none_below_overall_minimum(self):
        for day in range(1, MIN_MATCHES_FOR_MAP_SIGNAL - 1):
            self._write_match(day, "Baltic_Main", damage=300)

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result)

    def test_none_when_no_single_map_clears_the_match_count_bar(self):
        # 12 matches total, but spread thin across maps - no single map has
        # MIN_MATCHES_FOR_MAP_SIGNAL matches of its own.
        maps = ["Baltic_Main", "Desert_Main", "Savage_Main"]
        for day in range(1, 13):
            self._write_match(day, maps[day % 3], damage=300)

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result)

    def test_none_when_deviation_too_small(self):
        for day in range(1, 9):
            self._write_match(day, "Baltic_Main", damage=300)
        for day in range(9, 17):
            self._write_match(day, "Desert_Main", damage=310)  # ~3% deviation, below threshold

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result)

    def test_surfaces_map_with_notably_higher_damage(self):
        # A third, small (< match-count bar) map bucket shifts the overall
        # mean so Baltic sits close to it (deviation stays under threshold)
        # while Desert clears it - avoids two equal-sized buckets landing
        # symmetrically either side of the mean, which would tie on |deviation|.
        for day in range(1, 9):
            self._write_match(day, "Baltic_Main", damage=500)
        for day in range(9, 17):
            self._write_match(day, "Desert_Main", damage=600)
        for day in range(17, 20):
            self._write_match(day, "Savage_Main", damage=100)

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn("Miramar", result)
        self.assertIn("above", result)

    def test_surfaces_map_with_notably_lower_damage(self):
        for day in range(1, 9):
            self._write_match(day, "Baltic_Main", damage=500)
        for day in range(9, 17):
            self._write_match(day, "Desert_Main", damage=200)
        for day in range(17, 20):
            self._write_match(day, "Savage_Main", damage=900)

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn("Miramar", result)
        self.assertIn("below", result)

    def test_unmapped_internal_name_falls_back_to_raw_string(self):
        for day in range(1, 9):
            self._write_match(day, "Baltic_Main", damage=500)
        for day in range(9, 17):
            self._write_match(day, "Unreleased_Test_Map", damage=600)
        for day in range(17, 20):
            self._write_match(day, "Savage_Main", damage=100)

        result = compute_map_line(ME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn("Unreleased_Test_Map", result)


if __name__ == '__main__':
    unittest.main()
