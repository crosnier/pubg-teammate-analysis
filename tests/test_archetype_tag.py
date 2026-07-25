##########
# Unit Test for Archetype Tag (combined tempo + range + weapon signature)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.archetype_tag import compute_archetype_tag

ME = "account.me"
RIVAL = "account.rival"


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def match_start(base="2026-07-22T00:00:00.000Z"):
    return {"_T": "LogMatchStart", "_D": base}


def damage_event(attacker_id, victim_id, seconds_after_start):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "_D": f"2026-07-22T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


def kill_event(killer_id, victim_id, weapon_causer, distance_m, seconds_after_start):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": False,
        "killer": {"accountId": killer_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "killerDamageInfo": {"damageCauserName": weapon_causer, "distance": distance_m * 100},
        "_D": f"2026-07-22T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


class TestComputeArchetypeTag(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_combines_all_three_signals_with_short_tag(self):
        # 8 fast, close-range AR kills across 8 matches -> Hot-Drop Headhunter,
        # Close-Range, AR -> short_tag "Close-Range/Aggressive"
        for i in range(8):
            self._write_match(f"match-{i}", [
                match_start(),
                create_event(ME),
                damage_event(ME, RIVAL, 20),
                kill_event(ME, RIVAL, "WeapAK47_C", 15, 25),
            ])

        result = compute_archetype_tag(ME, telemetry_dir=self.tmpdir.name, match_ids=[f"match-{i}" for i in range(8)])

        self.assertEqual(result["tempo"]["tempo_tag"], "Hot-Drop Headhunter")
        self.assertEqual(result["range"]["range_bucket"], "Close-Range")
        self.assertEqual(result["weapon"]["signature"], "AR")
        self.assertEqual(result["short_tag"], "Close-Range/Aggressive")
        self.assertEqual(result["matches_analyzed"], 8)

    def test_short_tag_none_when_signals_lack_data(self):
        self._write_match("match-1", [match_start(), create_event(ME)])

        result = compute_archetype_tag(ME, telemetry_dir=self.tmpdir.name, match_ids=["match-1"])

        self.assertIsNone(result["range"]["range_bucket"])
        self.assertIsNone(result["short_tag"])

    def test_passive_temperament_for_slow_roll_patient(self):
        for i in range(8):
            self._write_match(f"slow-{i}", [
                match_start(),
                create_event(ME),
                damage_event(ME, RIVAL, 900),
                kill_event(ME, RIVAL, "WeapKar98k_C", 80, 910),
            ])

        result = compute_archetype_tag(ME, telemetry_dir=self.tmpdir.name, match_ids=[f"slow-{i}" for i in range(8)])

        self.assertEqual(result["tempo"]["tempo_tag"], "Slow-Roll Patient")
        self.assertIn("Passive", result["short_tag"])

    def test_team_mode_match_ids_scopes_range_and_weapon_but_not_tempo(self):
        # 8 team-mode matches: fast Close-Range AR kills.
        for i in range(8):
            self._write_match(f"team-{i}", [
                match_start(),
                create_event(ME),
                damage_event(ME, RIVAL, 20),
                kill_event(ME, RIVAL, "WeapAK47_C", 15, 25),
            ])
        # 8 additional solo-mode matches: also fast (same tempo), but
        # Long-Range SR kills - would flip Range/Weapon if not excluded.
        for i in range(8):
            self._write_match(f"solo-{i}", [
                match_start(),
                create_event(ME),
                damage_event(ME, RIVAL, 20),
                kill_event(ME, RIVAL, "WeapKar98k_C", 200, 25),
            ])

        all_ids = [f"team-{i}" for i in range(8)] + [f"solo-{i}" for i in range(8)]
        team_ids = [f"team-{i}" for i in range(8)]

        result = compute_archetype_tag(
            ME, telemetry_dir=self.tmpdir.name, match_ids=all_ids, team_mode_match_ids=team_ids,
        )

        # Tempo stays on the full (unscoped) match set - 16 fast matches either way.
        self.assertEqual(result["tempo"]["tempo_tag"], "Hot-Drop Headhunter")
        self.assertEqual(result["tempo"]["matches_analyzed"], 16)
        # Range/Weapon reflect only the 8 team-mode matches, not all 16.
        self.assertEqual(result["range"]["range_bucket"], "Close-Range")
        self.assertEqual(result["weapon"]["signature"], "AR")
        self.assertEqual(result["range"]["kills_analyzed"], 8)


if __name__ == '__main__':
    unittest.main()
