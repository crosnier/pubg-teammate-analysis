##########
# Unit Test for Headline Number (confidence-gated "so-what" stat picker)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.headline_number import compute_headline_number, MIN_MATCHES_FOR_CANDIDATE

ME = "account.me"
RIVAL = "account.rival"
TEAMMATE = "account.teammate"


def match_start(day):
    return {"_T": "LogMatchStart", "_D": f"2026-07-{day:02d}T00:00:00.000Z"}


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def kill_event(killer_id, victim_id, distance_m=10, killer_type="user", victim_type="user",
               is_suicide=False, dbno_id=-1):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "dBNOId": dbno_id,
        "killer": {"accountId": killer_id, "type": killer_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "killerDamageInfo": {"distance": distance_m * 100},
    }


def damage_event(attacker_id, victim_id, damage, attacker_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": attacker_type},
        "victim": {"accountId": victim_id, "type": victim_type},
        "damage": damage,
    }


def revive_event(reviver_id, victim_id):
    return {"_T": "LogPlayerRevive", "reviver": {"accountId": reviver_id}, "victim": {"accountId": victim_id}}


def groggy_event(attacker_id, victim_id, dbno_id, attacker_type="user", victim_type="user"):
    return {
        "_T": "LogPlayerMakeGroggy",
        "dBNOId": dbno_id,
        "attacker": {"accountId": attacker_id, "type": attacker_type},
        "victim": {"accountId": victim_id, "type": victim_type},
    }


class TestComputeHeadlineNumber(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, day, events):
        match_id = f"match-{day}"
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump([match_start(day), create_event(ME)] + events, f)
        return match_id

    def test_below_minimum_matches_falls_back_to_kill_count(self):
        for day in range(1, MIN_MATCHES_FOR_CANDIDATE - 1):
            self._write_match(day, [kill_event(ME, RIVAL)])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "fallback_kill_count")
        self.assertIsNone(result["score"])
        self.assertIn("kills over your last", result["headline"])

    def test_no_matches_reports_not_enough_data(self):
        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["headline"], "Not enough data yet")
        self.assertEqual(result["matches_analyzed"], 0)

    def test_stable_close_range_win_rate_selected(self):
        # Wins every close-range fight, consistently, across enough matches -
        # a clean, stable rate signal.
        # Always dies (never kills) at close range - a clean, consistently
        # one-sided rate signal. Deliberately the "loses every time" shape
        # rather than "wins every time": a win is itself a real kill, which
        # would also feed the kills-before-death candidate and make the two
        # signals move together instead of isolating this one.
        for day in range(1, 13):
            self._write_match(day, [kill_event(RIVAL, ME, distance_m=8)])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "close_range_win_rate")
        self.assertIn("0%", result["headline"])

    def test_unstable_pattern_direction_flip_is_rejected(self):
        # First half all wins, second half all losses at close range - the
        # stability gate should reject this even though the raw win rate
        # (50%) might otherwise look plausible; nothing else clears the bar
        # either, so it falls back.
        for day in range(1, 7):
            self._write_match(day, [kill_event(ME, RIVAL, distance_m=8)])
        for day in range(7, 13):
            self._write_match(day, [kill_event(RIVAL, ME, distance_m=8)])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertNotEqual(result["stat_key"], "close_range_win_rate")

    def test_knockdown_conversion_links_via_dbno_id(self):
        # One knockdown resolved via a matching-dBNOId kill (converted),
        # the rest resolved via revive (not converted) - exercises the
        # kill-side of the dBNOId linkage, not just the revive-only path
        # covered separately below. The single converting kill is placed
        # on day 1 so it lands entirely in the first stability-check half,
        # keeping kills-before-death's own reading unstable (excluded)
        # rather than competing with this candidate.
        events = [groggy_event(ME, RIVAL, dbno_id=1), kill_event(ME, RIVAL, distance_m=999, dbno_id=1)]
        self._write_match(1, events)
        for day in range(2, 13):
            events = [groggy_event(ME, RIVAL, dbno_id=100 + day), revive_event(TEAMMATE, RIVAL)]
            events[1]["dBNOId"] = 100 + day
            self._write_match(day, events)

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "knockdown_conversion_rate")
        self.assertIn("1/12", result["headline"])

    def test_knockdown_resolved_by_revive_counts_as_not_converted(self):
        for day in range(1, 13):
            events = [
                groggy_event(ME, RIVAL, dbno_id=200 + day),
                revive_event(TEAMMATE, RIVAL),
            ]
            events[1]["dBNOId"] = 200 + day
            self._write_match(day, events)

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        # Every knockdown was saved by a revive - 0% conversion is a stable
        # (if unflattering) pattern and should still be surfaced, not hidden.
        self.assertEqual(result["stat_key"], "knockdown_conversion_rate")
        self.assertIn("0%", result["headline"])

    def test_revives_per_match_counted(self):
        for day in range(1, 13):
            self._write_match(day, [revive_event(ME, TEAMMATE), kill_event(RIVAL, ME, distance_m=500)])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "revives")
        self.assertIn("1.0 revives", result["headline"])

    def test_damage_excludes_self_and_bot_damage(self):
        for day in range(1, 13):
            self._write_match(day, [
                damage_event(ME, RIVAL, 50),
                damage_event(ME, ME, 20),
                damage_event(ME, RIVAL, 30, victim_type="user_ai"),
            ])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "damage")
        self.assertIn("50 damage", result["headline"])

    def test_highest_scoring_eligible_candidate_wins(self):
        # A consistently one-sided close-range rate (0% win rate every
        # match) should beat a damage signal that's eligible and stable
        # but too noisy (wide swings match to match) to score as highly.
        damage_values = [0, 300, 0, 280, 0, 260, 0, 290, 0, 270, 0, 300]
        for day in range(1, 13):
            events = [
                kill_event(RIVAL, ME, distance_m=8),
                damage_event(ME, RIVAL, damage_values[day - 1]),
            ]
            self._write_match(day, events)

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["stat_key"], "close_range_win_rate")

    def test_states_sample_size_inline(self):
        for day in range(1, 13):
            self._write_match(day, [kill_event(ME, RIVAL, distance_m=8)])

        result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)

        self.assertIn(str(result["matches_analyzed"]), result["headline"])

    def test_possessive_defaults_to_your_but_is_overridable(self):
        # squad.py renders teammate cards with possessive="their" - "your"
        # would misattribute the teammate's own stats to the running user.
        for day in range(1, MIN_MATCHES_FOR_CANDIDATE - 1):
            self._write_match(day, [kill_event(ME, RIVAL)])

        default_result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name)
        their_result = compute_headline_number(ME, telemetry_dir=self.tmpdir.name, possessive="their")

        self.assertIn("your last", default_result["headline"])
        self.assertIn("their last", their_result["headline"])


if __name__ == '__main__':
    unittest.main()
