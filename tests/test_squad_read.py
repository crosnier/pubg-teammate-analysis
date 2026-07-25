##########
# Unit Test for Squad Read (synergy line + "opens first" bolstering)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.squad_read import compute_synergy_line, compute_engagement_lead, compute_squad_read, BOLSTER_WINDOW

ME = "account.me"
MATE = "account.mate"
RIVAL = "account.rival"
MATE_NAME = "DanucD"


def match_start(day):
    return {"_T": "LogMatchStart", "_D": f"2026-07-{day:02d}T00:00:00.000Z"}


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def damage_event(attacker_id, victim_id, seconds_after_start):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "_D": f"2026-07-01T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


class TestComputeSynergyLine(unittest.TestCase):

    def test_missing_data_returns_none(self):
        self.assertIsNone(compute_synergy_line(None, "Aggressive", "Mate", "Close-Range", "Aggressive"))
        self.assertIsNone(compute_synergy_line("Close-Range", None, "Mate", "Close-Range", "Aggressive"))

    def test_cases(self):
        cases = [
            (
                "identical_aggressive",
                ("Close-Range", "Aggressive", "Close-Range", "Aggressive"),
                "matching aggressive playstyles",
            ),
            (
                "identical_passive",
                ("Long-Range", "Passive", "Long-Range", "Passive"),
                "matching passive playstyles",
            ),
            (
                "identical_balanced",
                ("Mid-Range", "Balanced", "Mid-Range", "Balanced"),
                "closely matched playstyles",
            ),
            (
                "same_temperament_self_closer",
                ("Close-Range", "Balanced", "Long-Range", "Balanced"),
                "you get into the fight up close",
            ),
            (
                "same_temperament_teammate_closer",
                ("Long-Range", "Balanced", "Close-Range", "Balanced"),
                f"{MATE_NAME} gets into the fight up close",
            ),
            (
                "same_range_self_faster",
                ("Mid-Range", "Aggressive", "Mid-Range", "Balanced"),
                "you tend to commit sooner",
            ),
            (
                "same_range_teammate_faster",
                ("Mid-Range", "Balanced", "Mid-Range", "Aggressive"),
                f"{MATE_NAME} tends to commit sooner",
            ),
            (
                "aligned_self_pushes",
                ("Close-Range", "Aggressive", "Long-Range", "Passive"),
                "classic push-and-cover: you push in",
            ),
            (
                "aligned_teammate_pushes",
                ("Long-Range", "Passive", "Close-Range", "Aggressive"),
                f"classic push-and-cover: {MATE_NAME} pushes in",
            ),
            (
                "misaligned",
                ("Long-Range", "Aggressive", "Close-Range", "Passive"),
                "an unusual mix",
            ),
        ]
        for name, (self_range, self_temp, mate_range, mate_temp), expected_substring in cases:
            with self.subTest(case=name):
                result = compute_synergy_line(self_range, self_temp, MATE_NAME, mate_range, mate_temp)
                self.assertIn(expected_substring, result)


class TestComputeEngagementLead(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.match_ids = []

    def _write_shared_match(self, day, self_contact_seconds, mate_contact_seconds):
        events = [
            match_start(day),
            create_event(ME),
            create_event(MATE),
            damage_event(ME, RIVAL, self_contact_seconds),
            damage_event(MATE, RIVAL, mate_contact_seconds),
        ]
        match_id = f"match-{day}"
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)
        self.match_ids.append(match_id)

    def test_none_below_bolster_window(self):
        for day in range(1, BOLSTER_WINDOW - 1):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=50)

        result = compute_engagement_lead(ME, MATE, MATE_NAME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result)

    def test_none_when_no_leader_clears_threshold(self):
        # 4-4 split across 8 matches - neither reaches the 5-of-8 bar.
        for day in range(1, 5):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=50)
        for day in range(5, 9):
            self._write_shared_match(day, self_contact_seconds=50, mate_contact_seconds=10)

        result = compute_engagement_lead(ME, MATE, MATE_NAME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result)

    def test_teammate_opens_first_bolstered(self):
        for day in range(1, 7):
            self._write_shared_match(day, self_contact_seconds=100, mate_contact_seconds=10)
        for day in range(7, 9):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=100)

        result = compute_engagement_lead(ME, MATE, MATE_NAME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn(MATE_NAME, result)
        self.assertIn("6 of your last 8", result)

    def test_self_opens_first_bolstered(self):
        for day in range(1, 6):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=100)
        for day in range(6, 9):
            self._write_shared_match(day, self_contact_seconds=100, mate_contact_seconds=10)

        result = compute_engagement_lead(ME, MATE, MATE_NAME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn("you've opened", result)
        self.assertIn("5 of your last 8", result)

    def test_uses_most_recent_window_only(self):
        # 10 shared matches total: oldest 2 favor ME, most recent 8 favor MATE 5-3.
        # Only the most recent 8 should count, so MATE should be the bolstered leader.
        for day in range(1, 3):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=100)
        for day in range(3, 8):
            self._write_shared_match(day, self_contact_seconds=100, mate_contact_seconds=10)
        for day in range(8, 11):
            self._write_shared_match(day, self_contact_seconds=10, mate_contact_seconds=100)

        result = compute_engagement_lead(ME, MATE, MATE_NAME, self.match_ids, telemetry_dir=self.tmpdir.name)

        self.assertIn(MATE_NAME, result)


class TestComputeSquadRead(unittest.TestCase):

    def test_combines_synergy_and_shared_match_intersection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self_archetype = {"range": {"range_bucket": "Close-Range"}, "temperament": "Aggressive"}
            teammate_archetype = {"range": {"range_bucket": "Long-Range"}, "temperament": "Passive"}

            result = compute_squad_read(
                ME, self_archetype, {"match-a", "match-b", "match-c"},
                MATE, MATE_NAME, teammate_archetype, {"match-b", "match-c", "match-d"},
                telemetry_dir=tmpdir,
            )

            self.assertIn("classic push-and-cover", result["synergy_line"])
            self.assertEqual(result["shared_matches_analyzed"], 2)


if __name__ == '__main__':
    unittest.main()
