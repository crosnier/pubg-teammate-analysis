##########
# Unit Test for Squad Roster (coverage/distribution summary, N players)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.squad_roster import compute_squad_coverage_summary, compute_best_engagement_lead, compute_squad_roster

ME = "account.me"
MATE_A = "account.a"
MATE_B = "account.b"
MATE_C = "account.c"
RIVAL = "account.rival"


def archetype(range_bucket, temperament, tempo_tag="Quick-Gear Striker"):
    return {
        "range": {"range_bucket": range_bucket},
        "temperament": temperament,
        "tempo": {"tempo_tag": tempo_tag},
        "short_tag": f"{range_bucket}/{temperament}" if range_bucket and temperament else None,
    }


def member(name, account_id, range_bucket, temperament, match_ids=None):
    return {
        "name": name,
        "account_id": account_id,
        "archetype": archetype(range_bucket, temperament),
        "match_ids": match_ids or [],
    }


class TestComputeSquadCoverageSummary(unittest.TestCase):

    def test_none_when_fewer_than_two_profiled(self):
        members = [member("You", ME, "Close-Range", "Aggressive")]
        self.assertIsNone(compute_squad_coverage_summary(members))

    def test_none_when_a_member_lacks_data(self):
        members = [
            member("You", ME, "Close-Range", "Aggressive"),
            member("Mate", MATE_A, None, None),
        ]
        self.assertIsNone(compute_squad_coverage_summary(members))

    def test_balanced_squad_with_full_coverage_and_role_callouts(self):
        members = [
            member("You", ME, "Long-Range", "Passive"),
            member("DanucD", MATE_A, "Close-Range", "Aggressive"),
            member("Vacency", MATE_B, "Mid-Range", "Balanced"),
        ]
        result = compute_squad_coverage_summary(members)

        self.assertIn("Balanced squad", result)
        self.assertIn("You (support anchor)", result)
        self.assertIn("DanucD (entry fragger)", result)
        self.assertIn("Vacency cover", result)
        self.assertIn("No overlapping blind spots.", result)

    def test_all_aggressive_squad(self):
        members = [
            member("You", ME, "Close-Range", "Aggressive"),
            member("Mate", MATE_A, "Close-Range", "Aggressive"),
        ]
        result = compute_squad_coverage_summary(members)

        self.assertIn("All-Aggressive squad", result)

    def test_mixed_temperament_squad_uses_mixed_opener_not_generic_squad(self):
        # Aggressive + Balanced (no Passive) doesn't fit "Balanced squad"
        # (needs Aggressive+Passive) or "All-X squad" (needs one temperament) -
        # falls to the generic case, which should read "Mixed squad", not the
        # bare word "Squad" that collided with the "Squad Read:" print prefix.
        members = [
            member("You", ME, "Close-Range", "Aggressive"),
            member("Mate", MATE_A, "Mid-Range", "Balanced"),
        ]
        result = compute_squad_coverage_summary(members)

        self.assertIn("Mixed squad", result)

    def test_flags_missing_range_coverage(self):
        members = [
            member("You", ME, "Close-Range", "Aggressive"),
            member("Mate", MATE_A, "Mid-Range", "Balanced"),
        ]
        result = compute_squad_coverage_summary(members)

        self.assertIn("No one covers long-range", result)

    def test_leftover_balanced_members_grouped_by_range_span(self):
        members = [
            member("You", ME, "Close-Range", "Balanced"),
            member("Mate", MATE_A, "Long-Range", "Balanced"),
        ]
        result = compute_squad_coverage_summary(members)

        self.assertIn("You and Mate cover close-to-long", result)


class TestComputeBestEngagementLead(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, day, contact_by_account):
        events = [
            {"_T": "LogMatchStart", "_D": f"2026-07-{day:02d}T00:00:00.000Z"},
        ]
        for account_id in contact_by_account:
            events.append({"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}})
        for account_id, seconds in contact_by_account.items():
            events.append({
                "_T": "LogPlayerTakeDamage",
                "attacker": {"accountId": account_id, "type": "user"},
                "victim": {"accountId": RIVAL, "type": "user"},
                "_D": f"2026-07-{day:02d}T00:{seconds // 60:02d}:{seconds % 60:02d}.000Z",
            })
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_picks_the_strongest_teammate_comparison(self):
        match_ids_a = []
        match_ids_b = []
        # vs MATE_A: 5-of-8 leans "you" opened first
        for day in range(1, 6):
            mid = f"a-{day}"
            self._write_match(mid, day, {ME: 10, MATE_A: 100})
            match_ids_a.append(mid)
        for day in range(6, 9):
            mid = f"a-{day}"
            self._write_match(mid, day, {ME: 100, MATE_A: 10})
            match_ids_a.append(mid)

        # vs MATE_B: 8-of-8 - a stronger, more decisive pattern
        for day in range(1, 9):
            mid = f"b-{day}"
            self._write_match(mid, day, {ME: 10, MATE_B: 100})
            match_ids_b.append(mid)

        members = [
            member("You", ME, "Mid-Range", "Balanced"),
            member("MateA", MATE_A, "Mid-Range", "Balanced", match_ids=match_ids_a),
            member("MateB", MATE_B, "Mid-Range", "Balanced", match_ids=match_ids_b),
        ]
        members[0]["match_ids"] = match_ids_a + match_ids_b

        result = compute_best_engagement_lead(members, telemetry_dir=self.tmpdir.name)

        self.assertIn("you've opened", result)
        self.assertIn("8 of your last 8", result)

    def test_none_when_no_teammate_clears_the_bar(self):
        members = [
            member("You", ME, "Mid-Range", "Balanced", match_ids=["m1"]),
            member("Mate", MATE_A, "Mid-Range", "Balanced", match_ids=["m1"]),
        ]
        result = compute_best_engagement_lead(members, telemetry_dir=self.tmpdir.name)
        self.assertIsNone(result)


class TestComputeSquadRoster(unittest.TestCase):

    def test_roster_rows_include_you_and_teammates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            members = [
                member("You", ME, "Long-Range", "Passive"),
                member("DanucD", MATE_A, "Close-Range", "Aggressive"),
            ]
            result = compute_squad_roster(members, telemetry_dir=tmpdir)

            names = [row["name"] for row in result["roster_rows"]]
            self.assertEqual(names, ["You", "DanucD"])
            self.assertIsNotNone(result["coverage_summary"])


if __name__ == '__main__':
    unittest.main()
