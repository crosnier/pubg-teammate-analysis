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


def create_event(account_id, timestamp="2026-01-01T00:00:00.000Z", team_id=1, name=None):
    character = {"accountId": account_id, "type": "user", "teamId": team_id}
    if name:
        character["name"] = name
    return {"_T": "LogPlayerCreate", "_D": timestamp, "character": character}


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
        self.assertEqual(
            brief["death_info"],
            {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.9},
        )

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


class TestSquadStatusAtDeath(unittest.TestCase):

    def test_none_when_player_survives_to_match_end(self):
        events = [
            match_start_event(),
            create_event(ME, name="Me"),
            create_event("account.mate", name="Mate"),
            match_end_event([match_end_entry(ME, 1)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertIsNone(brief["squad_status"])

    def test_none_when_no_other_teammates(self):
        events = [
            match_start_event(),
            create_event(ME, name="Me"),
            kill_event(KILLER, "Rival", ME, "WeapAUG_C", 2000.0, "2026-01-01T00:05:00.000Z"),
            match_end_event([match_end_entry(ME, 30)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertIsNone(brief["squad_status"])

    def test_classifies_each_teammate_relative_to_players_death(self):
        # Player (ME) dies at 00:10:00. Teammates:
        #  - "AliveMate" never dies -> still alive
        #  - "SameFightMate" dies 20s before ME (inside the 30s window) -> same fight
        #  - "EarlierMate" dies 5 minutes before ME -> unrelated, eliminated earlier
        events = [
            match_start_event(),
            create_event(ME, name="Me"),
            create_event("account.alive", name="AliveMate"),
            create_event("account.samefight", name="SameFightMate"),
            create_event("account.earlier", name="EarlierMate"),
            kill_event(KILLER, "Rival", "account.earlier", "WeapAUG_C", 1000.0, "2026-01-01T00:05:00.000Z"),
            kill_event(KILLER, "Rival", "account.samefight", "WeapAUG_C", 1000.0, "2026-01-01T00:09:40.000Z"),
            kill_event(KILLER, "Rival", ME, "WeapAUG_C", 2000.0, "2026-01-01T00:10:00.000Z"),
            match_end_event([match_end_entry(ME, 5)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        by_name = {s["name"]: s for s in brief["squad_status"]}
        self.assertEqual(by_name["AliveMate"]["status"], "alive")
        self.assertEqual(by_name["SameFightMate"]["status"], "same_engagement")
        self.assertEqual(by_name["SameFightMate"]["seconds_before"], 20.0)
        self.assertEqual(by_name["EarlierMate"]["status"], "eliminated_earlier")
        self.assertEqual(by_name["EarlierMate"]["seconds_before"], 300.0)

    def test_ignores_teammates_on_a_different_team(self):
        events = [
            match_start_event(),
            create_event(ME, name="Me", team_id=1),
            create_event("account.other", name="NotMyTeammate", team_id=2),
            kill_event(KILLER, "Rival", ME, "WeapAUG_C", 2000.0, "2026-01-01T00:05:00.000Z"),
            match_end_event([match_end_entry(ME, 20)]),
        ]

        brief = compute_last_match_brief(ME, "match-1", events)

        self.assertIsNone(brief["squad_status"])


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
        # Defensive check: even if a candidate ID turns out not to actually
        # contain the player (shouldn't happen in practice, since
        # candidate_match_ids comes from the player's own API data), it's
        # still excluded rather than trusted blindly.
        self._write_match("with-me", "2026-01-01T00:00:00.000Z", ME)
        self._write_match("without-me", "2026-06-01T00:00:00.000Z", KILLER)

        match_id, events = find_latest_match_for_player(
            ME, ["with-me", "without-me"], telemetry_dir=self.tmpdir.name
        )

        self.assertEqual(match_id, "with-me")

    def test_ignores_cached_matches_not_in_the_candidate_list(self):
        self._write_match("mine", "2026-01-01T00:00:00.000Z", ME)
        self._write_match("someone-elses-more-recent", "2026-06-01T00:00:00.000Z", KILLER)

        match_id, events = find_latest_match_for_player(ME, ["mine"], telemetry_dir=self.tmpdir.name)

        self.assertEqual(match_id, "mine")

    def test_skips_candidate_matches_not_yet_cached(self):
        self._write_match("cached", "2026-01-01T00:00:00.000Z", ME)

        match_id, events = find_latest_match_for_player(
            ME, ["cached", "not-cached-yet"], telemetry_dir=self.tmpdir.name
        )

        self.assertEqual(match_id, "cached")

    def test_picks_latest_among_matches_player_appears_in(self):
        self._write_match("older", "2026-01-01T00:00:00.000Z", ME)
        self._write_match("newer", "2026-03-01T00:00:00.000Z", ME)

        match_id, events = find_latest_match_for_player(ME, ["older", "newer"], telemetry_dir=self.tmpdir.name)

        self.assertEqual(match_id, "newer")

    def test_no_matches_returns_none(self):
        match_id, events = find_latest_match_for_player(ME, [], telemetry_dir=self.tmpdir.name)

        self.assertIsNone(match_id)
        self.assertIsNone(events)


if __name__ == '__main__':
    unittest.main()
