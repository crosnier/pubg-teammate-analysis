##########
# Unit Test for Last Match Brief
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.last_match_brief import (
    compute_last_match_brief,
    find_latest_match_for_player,
    player_present_in_match,
)

ME = "account.me"
KILLER = "account.killer"


def match_start_event(timestamp="2026-01-01T00:00:00.000Z"):
    return {"_T": "LogMatchStart", "_D": timestamp}


def match_end_event(entries):
    return {"_T": "LogMatchEnd", "characters": entries}


def match_end_entry(account_id, ranking):
    return {"character": {"accountId": account_id, "ranking": ranking}}


def create_event(account_id, timestamp="2026-01-01T00:00:00.000Z"):
    return {"_T": "LogPlayerCreate", "_D": timestamp, "character": {"accountId": account_id, "type": "user"}}


def kill_event(killer_id, killer_name, victim_id, weapon, distance_cm, timestamp, is_suicide=False):
    return {
        "_T": "LogPlayerKillV2",
        "_D": timestamp,
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "name": killer_name, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "killerDamageInfo": {"damageCauserName": weapon, "distance": distance_cm},
    }


class TestComputeLastMatchBrief(unittest.TestCase):

    def test_death_populates_time_alive_and_death_info(self):
        events = [
            match_start_event("2026-01-01T00:00:00.000Z"),
            create_event(ME),
            kill_event(KILLER, "Rival", ME, "WeapAUG_C", 2090.0, "2026-01-01T00:05:00.000Z"),
            match_end_event([match_end_entry(ME, 42)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertEqual(brief["round_rank"], 42)
        self.assertEqual(brief["time_alive_seconds"], 300)
        self.assertEqual(brief["kill_count"], 0)
        self.assertIsNone(brief["most_used_weapon"])
        self.assertEqual(brief["death_info"], {"killed_by": "Rival", "weapon": "AUG", "distance_m": 20.9})

    def test_survivor_has_no_death_info_and_uses_match_end_time(self):
        events = [
            match_start_event("2026-01-01T00:00:00.000Z"),
            create_event(ME),
            kill_event(ME, "Me", "account.victim1", "WeapVSS_C", 1000.0, "2026-01-01T00:10:00.000Z"),
            kill_event(ME, "Me", "account.victim2", "WeapVSS_C", 1500.0, "2026-01-01T00:12:00.000Z"),
            match_end_event([match_end_entry(ME, 1)]),
        ]
        events[-1]["_D"] = "2026-01-01T00:25:00.000Z"

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertEqual(brief["round_rank"], 1)
        self.assertEqual(brief["time_alive_seconds"], 1500)
        self.assertEqual(brief["kill_count"], 2)
        self.assertEqual(brief["most_used_weapon"], "VSS")
        self.assertIsNone(brief["death_info"])

    def test_most_used_weapon_picks_highest_count(self):
        events = [
            match_start_event(),
            create_event(ME),
            kill_event(ME, "Me", "account.v1", "WeapAKM_C", 500.0, "2026-01-01T00:01:00.000Z"),
            kill_event(ME, "Me", "account.v2", "WeapAKM_C", 500.0, "2026-01-01T00:02:00.000Z"),
            kill_event(ME, "Me", "account.v3", "WeapKar98k_C", 500.0, "2026-01-01T00:03:00.000Z"),
            match_end_event([match_end_entry(ME, 3)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertEqual(brief["most_used_weapon"], "AKM")


class TestPlayerPresentInMatch(unittest.TestCase):

    def test_true_when_account_has_create_event(self):
        self.assertTrue(player_present_in_match(ME, [create_event(ME)]))

    def test_false_when_absent(self):
        self.assertFalse(player_present_in_match(ME, [create_event(KILLER)]))


class TestFindLatestMatchForPlayer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, timestamp, account_id):
        events = [match_start_event(timestamp), create_event(account_id, timestamp)]
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_only_considers_matches_player_appears_in(self):
        self._write_match("with-me", "2026-01-01T00:00:00.000Z", ME)
        self._write_match("without-me", "2026-06-01T00:00:00.000Z", KILLER)

        match_id, events = find_latest_match_for_player(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(match_id, "with-me")

    def test_picks_latest_among_matches_player_appears_in(self):
        self._write_match("older", "2026-01-01T00:00:00.000Z", ME)
        self._write_match("newer", "2026-03-01T00:00:00.000Z", ME)

        match_id, events = find_latest_match_for_player(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(match_id, "newer")

    def test_no_matches_returns_none(self):
        match_id, events = find_latest_match_for_player(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(match_id)
        self.assertIsNone(events)


if __name__ == '__main__':
    unittest.main()
