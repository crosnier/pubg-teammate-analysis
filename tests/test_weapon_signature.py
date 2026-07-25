##########
# Unit Test for Weapon Signature (Archetype Tag)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.weapon_signature import compute_weapon_signature

ME = "account.me"
RIVAL = "account.rival"


def kill_event(killer_id, victim_id, weapon_causer, is_suicide=False,
               killer_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "type": killer_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "killerDamageInfo": {"damageCauserName": weapon_causer},
    }


class TestComputeWeaponSignature(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_signature_and_wildcard_determination(self):
        cases = [
            ("clear_lead", [("WeapAK47_C", 9), ("WeapMP5K_C", 1)], False, "AR"),
            ("under_share_threshold", [("WeapAK47_C", 4), ("WeapMP5K_C", 3), ("WeapKar98k_C", 3)], True, None),
            ("within_gap_threshold", [("WeapAK47_C", 10), ("WeapMP5K_C", 9), ("WeapKar98k_C", 1)], True, None),
            ("clear_gap_and_share", [("WeapAK47_C", 5), ("WeapMP5K_C", 1), ("WeapKar98k_C", 1), ("WeapVector_C", 1)], False, "AR"),
        ]
        for name, weapon_counts, expect_wildcard, expect_signature in cases:
            with self.subTest(case=name):
                events = [kill_event(ME, RIVAL, weapon) for weapon, count in weapon_counts for _ in range(count)]
                self._write_match(name, events)

                result = compute_weapon_signature(ME, telemetry_dir=self.tmpdir.name, match_ids={name})

                self.assertEqual(result["is_wildcard"], expect_wildcard)
                if expect_wildcard:
                    self.assertIn("Wildcard", result["signature"])
                else:
                    self.assertEqual(result["signature"], expect_signature)

    def test_excludes_non_gun_kills(self):
        events = [kill_event(ME, RIVAL, "WeapAK47_C") for _ in range(8)] + \
                 [kill_event(ME, RIVAL, "ProjGrenade_C") for _ in range(20)]
        self._write_match("m1", events)

        result = compute_weapon_signature(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["kills_analyzed"], 8)
        self.assertEqual(result["signature"], "AR")

    def test_none_when_below_minimum_kills(self):
        events = [kill_event(ME, RIVAL, "WeapAK47_C") for _ in range(5)]
        self._write_match("m1", events)

        result = compute_weapon_signature(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result["signature"])
        self.assertIsNone(result["is_wildcard"])

    def test_excludes_suicides_and_non_user_kills(self):
        events = [
            kill_event(ME, RIVAL, "WeapAK47_C") for _ in range(8)
        ] + [
            kill_event(ME, ME, "WeapAK47_C", is_suicide=True),
            kill_event(ME, RIVAL, "WeapAK47_C", victim_type="user_ai"),
        ]
        self._write_match("m1", events)

        result = compute_weapon_signature(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["kills_analyzed"], 8)


if __name__ == '__main__':
    unittest.main()
