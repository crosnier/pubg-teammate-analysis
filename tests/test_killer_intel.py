##########
# Unit Test for Killer Intel (solo.py's replacement for squad status)
# from root of project: `python -m unittest discover tests`
##########

import unittest

from utils.killer_intel import compute_killer_intel, format_killer_intel

ME = "account.me"
KILLER = "account.killer"
OTHER_VICTIM = "account.other"


def match_start(timestamp="2026-01-01T00:00:00.000Z"):
    return {"_T": "LogMatchStart", "_D": timestamp}


def match_end(entries):
    return {"_T": "LogMatchEnd", "characters": entries}


def match_end_entry(account_id, ranking):
    return {"character": {"accountId": account_id, "ranking": ranking}}


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def damage_event(attacker_id, victim_id, seconds_after_start):
    return {
        "_T": "LogPlayerTakeDamage",
        "attacker": {"accountId": attacker_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "_D": f"2026-01-01T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


def kill_event(killer_id, victim_id, seconds_after_start, is_suicide=False):
    return {
        "_T": "LogPlayerKillV2",
        "isSuicide": is_suicide,
        "killer": {"accountId": killer_id, "type": "user"},
        "victim": {"accountId": victim_id, "type": "user"},
        "_D": f"2026-01-01T00:{seconds_after_start // 60:02d}:{seconds_after_start % 60:02d}.000Z",
    }


class TestComputeKillerIntel(unittest.TestCase):

    def test_none_when_no_death_info(self):
        self.assertIsNone(compute_killer_intel([], None))

    def test_none_when_killer_account_id_missing(self):
        death_info = {"killed_by": "Rival", "weapon": "AUG", "distance_m": 20.0}
        self.assertIsNone(compute_killer_intel([], death_info))

    def test_counts_killer_kills_excluding_suicide_and_self(self):
        events = [
            match_start(),
            damage_event(KILLER, ME, 10),
            kill_event(KILLER, OTHER_VICTIM, 20),
            kill_event(KILLER, ME, 30),
            {"_T": "LogPlayerKillV2", "isSuicide": True, "killer": {"accountId": KILLER, "type": "user"},
             "victim": {"accountId": KILLER, "type": "user"}, "_D": "2026-01-01T00:00:40.000Z"},
        ]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertEqual(intel["kill_count"], 2)
        self.assertEqual(intel["killer_name"], "Rival")

    def test_engagement_pace_early_for_fast_contact(self):
        events = [match_start(), create_event(KILLER), damage_event(KILLER, ME, 10)]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertEqual(intel["engagement_pace"], "early")

    def test_engagement_pace_late_for_slow_contact(self):
        events = [match_start(), create_event(KILLER), damage_event(KILLER, ME, 600)]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertEqual(intel["engagement_pace"], "late")

    def test_engagement_pace_unknown_when_killer_never_seen_elsewhere(self):
        # No LogPlayerCreate for the killer at all - compute_time_to_first_contact_from_events
        # can't confirm the killer was even present in the cached event stream.
        events = [match_start()]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertEqual(intel["engagement_pace"], "unknown")

    def test_final_rank_from_match_end(self):
        events = [
            match_start(),
            damage_event(KILLER, ME, 10),
            match_end([match_end_entry(KILLER, 3)]),
        ]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertEqual(intel["final_rank"], 3)

    def test_final_rank_none_when_killer_not_in_match_end(self):
        events = [match_start(), damage_event(KILLER, ME, 10), match_end([match_end_entry(ME, 5)])]
        death_info = {"killed_by": "Rival", "killer_account_id": KILLER, "weapon": "AUG", "distance_m": 20.0}

        intel = compute_killer_intel(events, death_info)

        self.assertIsNone(intel["final_rank"])


class TestFormatKillerIntel(unittest.TestCase):

    def test_none_passthrough(self):
        self.assertIsNone(format_killer_intel(None))

    def test_zero_kills_phrased_without_kill_count(self):
        result = format_killer_intel({
            "killer_name": "Rival", "kill_count": 0, "engagement_pace": "late", "final_rank": None,
        })
        self.assertIn("no other confirmed kills", result)

    def test_singular_kill_phrasing(self):
        result = format_killer_intel({
            "killer_name": "Rival", "kill_count": 1, "engagement_pace": "early", "final_rank": None,
        })
        self.assertIn("1 kill this match", result)
        self.assertNotIn("1 kills", result)

    def test_plural_kill_phrasing_and_rank(self):
        result = format_killer_intel({
            "killer_name": "Rival", "kill_count": 4, "engagement_pace": "mid", "final_rank": 2,
        })
        self.assertIn("4 kills this match", result)
        self.assertIn("finish #2", result)


if __name__ == '__main__':
    unittest.main()
