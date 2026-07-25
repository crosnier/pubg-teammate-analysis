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
            damage_event(ME, RIVAL, 30),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertFalse(result["quick_kill"])
        self.assertEqual(result["tempo_bucket"], "Early Skirmisher")

    def test_quick_gear_striker_on_short_delay(self):
        events = [match_start(), damage_event(ME, RIVAL, 200)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["tempo_bucket"], "Quick-Gear Striker")

    def test_calculated_pusher_on_moderate_delay(self):
        events = [match_start(), damage_event(ME, RIVAL, 450)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["tempo_bucket"], "Calculated Pusher")

    def test_slow_roll_patient_on_long_delay(self):
        events = [match_start(), damage_event(ME, RIVAL, 900)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["tempo_bucket"], "Slow-Roll Patient")

    def test_slow_roll_patient_when_no_contact_at_all(self):
        events = [match_start()]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result["contact_seconds"])
        self.assertEqual(result["tempo_bucket"], "Slow-Roll Patient")

    def test_none_when_match_never_started(self):
        events = [damage_event(ME, RIVAL, 30)]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result)

    def test_ignores_self_damage_and_environmental_damage(self):
        events = [
            match_start(),
            damage_event(ME, ME, 10),
            kill_event(ME, RIVAL, 40),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertIsNone(result["contact_seconds"])

    def test_ignores_damage_against_bots(self):
        events = [
            match_start(),
            damage_event(ME, RIVAL, 15, victim_type="user_ai"),
            damage_event(ME, RIVAL, 250),
        ]

        result = compute_time_to_first_contact_from_events(ME, events)

        self.assertEqual(result["contact_seconds"], 250)

    def test_kill_outside_quick_kill_window_does_not_count(self):
        events = [
            match_start(),
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
        self._write_match("match1", [match_start(), damage_event(ME, RIVAL, 900)])
        self._write_match("match2", [match_start(), damage_event(ME, RIVAL, 950)])
        self._write_match("match3", [match_start(), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(signal["tempo_tag"], "Slow-Roll Patient")
        self.assertEqual(signal["matches_analyzed"], 3)
        self.assertEqual(signal["matches_with_contact"], 3)

    def test_ties_break_toward_faster_bucket(self):
        self._write_match("match1", [match_start(), damage_event(ME, RIVAL, 900)])
        self._write_match("match2", [match_start(), damage_event(ME, RIVAL, 30), kill_event(ME, RIVAL, 40)])

        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(signal["tempo_tag"], "Hot-Drop Headhunter")

    def test_no_tempo_tag_when_no_matches_cached(self):
        signal = compute_tempo_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(signal["tempo_tag"])
        self.assertEqual(signal["matches_analyzed"], 0)


if __name__ == '__main__':
    unittest.main()
