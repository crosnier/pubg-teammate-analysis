##########
# Unit Test for Tempo Signal (Archetype Tag - time-to-first-contact)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.tempo_signal import compute_time_to_first_contact_from_events, compute_tempo_signal

ME = "account.me"
RIVAL = "account.rival"


def match_start(seconds_offset=0, base="2026-07-22T00:00:00.000Z"):
    return {"_T": "LogMatchStart", "_D": base}


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def damage_event(attacker_id, victim_id, seconds_after_start,
                  attacker_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": attacker_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "_D": f"2026-07-22T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


def kill_event(killer_id, victim_id, seconds_after_start, is_suicide=False,
               killer_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "type": killer_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "_D": f"2026-07-22T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


class TestComputeTimeToFirstContact(unittest.TestCase):

    def test_hot_drop_headhunter_on_fast_contact_and_quick_kill(self):
        events = [
            match_start(),
            create_event(ME),
            damage_event(ME, RIVAL, 30),
            kill_event(ME, RIVAL, 45),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["contact_seconds"], 30)
        self.assertTrue(result["quick_kill"])
        self.assertEqual(result["tempo_bucket"], "Hot-Drop Headhunter")

    def test_early_skirmisher_on_fast_contact_without_quick_kill(self):
        events = [
            match_start(),
            create_event(ME),
            damage_event(ME, RIVAL, 30),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertFalse(result["quick_kill"])
        self.assertEqual(result["tempo_bucket"], "Early Skirmisher")

    def test_bucket_assignment_by_contact_delay(self):
        cases = [
            ("quick_gear_striker_short_delay", 200, "Quick-Gear Striker"),
            ("calculated_pusher_moderate_delay", 450, "Calculated Pusher"),
            ("slow_roll_patient_long_delay", 900, "Slow-Roll Patient"),
        ]
        for name, delay_seconds, expected_bucket in cases:
            with self.subTest(case=name):
                events = [match_start(), create_event(ME), damage_event(ME, RIVAL, delay_seconds)]

                result = compute_time_to_first_contact_from_events(ME, events)

                self.assertEqual(result["tempo_bucket"], expected_bucket)

    def test_slow_roll_patient_when_no_contact_at_all(self):
        events = [match_start(), create_event(ME)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result["contact_seconds"])
        self.assertEqual(result["tempo_bucket"], "Slow-Roll Patient")

    def test_none_when_match_never_started(self):
        events = [create_event(ME), damage_event(ME, RIVAL, 30)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result)

    def test_none_when_player_never_appears_in_match(self):
        """The bug fix: a match the player never played shouldn't count as
        a Slow-Roll Patient reading just because there's no contact from
        them - telemetry caching is shared, so unrelated matches sit in
        the same directory."""
        events = [match_start(), create_event(RIVAL), damage_event(RIVAL, "account.someone_else", 20)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result)

    def test_ignores_self_damage_and_environmental_damage(self):
        events = [
            match_start(),
            create_event(ME),
            damage_event(ME, ME, 10),
            kill_event(ME, RIVAL, 40),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result["contact_seconds"])

    def test_ignores_damage_against_bots(self):
        events = [
            match_start(),
            create_event(ME),
            damage_event(ME, RIVAL, 15, victim_type="user_ai"),
            damage_event(ME, RIVAL, 250),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["contact_seconds"], 250)

    def test_kill_outside_quick_kill_window_does_not_count(self):
        events = [
            match_start(),
            create_event(ME),
            damage_event(ME, RIVAL, 10),
            kill_event(ME, RIVAL, 200),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertFalse(result["quick_kill"])
        self.assertEqual(result["tempo_bucket"], "Early Skirmisher")


class TestComputeTempoSignal(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_aggregates_most_common_bucket_across_matches(self):
        for i in range(6):
            self._write_match(f"slow-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 900)])
        for i in range(2):
            self._write_match(f"hot-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(signal["tempo_tag"], "Slow-Roll Patient")
        self.assertEqual(signal["matches_analyzed"], 8)
        self.assertEqual(signal["matches_with_contact"], 8)

    def test_ties_break_toward_faster_bucket(self):
        for i in range(4):
            self._write_match(f"slow-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 900)])
        for i in range(4):
            self._write_match(f"hot-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(signal["tempo_tag"], "Hot-Drop Headhunter")

    def test_no_tempo_tag_when_no_matches_cached(self):
        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(signal["tempo_tag"])
        self.assertEqual(signal["matches_analyzed"], 0)

    def test_no_tempo_tag_below_minimum_matches(self):
        for i in range(7):
            self._write_match(f"hot-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(signal["tempo_tag"])
        self.assertEqual(signal["matches_analyzed"], 7)

    def test_excludes_matches_the_player_never_played(self):
        for i in range(8):
            self._write_match(f"mine-{i}", [match_start(), create_event(ME), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])
        self._write_match("unrelated-match", [match_start(), create_event(RIVAL), damage_event(RIVAL, "account.other", 20)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(signal["matches_analyzed"], 8)
        self.assertEqual(signal["tempo_tag"], "Hot-Drop Headhunter")


if __name__ == '__main__':
    unittest.main()
