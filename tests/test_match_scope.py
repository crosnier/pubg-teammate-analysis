##########
# Unit Test for Match Scope (Archetype Tag data budget)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from utils.match_scope import (
    MAX_MATCHES,
    MIN_MATCHES_TARGET,
    INITIAL_WINDOW_DAYS,
    WINDOW_INCREMENT_DAYS,
    MAX_WINDOW_DAYS,
    select_scoped_match_ids,
)

ME = "account.me"
RIVAL = "account.rival"

NOW = datetime(2026, 7, 25, tzinfo=timezone.utc)


def create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id, "type": "user"}}


def match_start(days_ago):
    ts = (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {"_T": "LogMatchStart", "_D": ts}


class TestSelectScopedMatchIds(unittest.TestCase):
    """Fixture sizes are derived from the live MAX_MATCHES/MIN_MATCHES_TARGET
    constants (not hardcoded) so these tests stay correct as the data-budget
    defaults get tuned - see match_scope.py's own note on the current 50
    vs. intended-production 250 default."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, days_ago, present=True):
        events = [match_start(days_ago)]
        if present:
            events.append(create_event(ME))
        else:
            events.append(create_event(RIVAL))
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_excludes_matches_the_player_never_played(self):
        self._write_match("mine", days_ago=1, present=True)
        self._write_match("unrelated", days_ago=1, present=False)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(result, ["mine"])

    def test_returns_all_available_when_under_cap(self):
        """Fewer matches exist than the cap - widening exhausts the full
        window looking for more, but there's nothing further out, so the
        result is just everything that's there."""
        count = max(MIN_MATCHES_TARGET - 10, 1)
        for i in range(count):
            self._write_match(f"recent-{i}", days_ago=5)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(len(result), count)

    def test_caps_at_max_matches(self):
        count = MAX_MATCHES + 50
        for i in range(count):
            self._write_match(f"recent-{i}", days_ago=5)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(len(result), MAX_MATCHES)

    def test_most_recent_matches_kept_when_capped(self):
        count = MAX_MATCHES + 50
        for i in range(count):
            self._write_match(f"match-{i}", days_ago=count - i)  # highest index is most recent (1 day ago)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertIn(f"match-{count - 1}", result)
        self.assertNotIn("match-0", result)

    def test_widens_window_until_cap_reached(self):
        within_30 = max(MIN_MATCHES_TARGET // 10, 1)
        within_60 = MIN_MATCHES_TARGET + 20  # enough on its own to clear the target once window widens
        for i in range(within_30):
            self._write_match(f"within-30-{i}", days_ago=INITIAL_WINDOW_DAYS - 5)
        for i in range(within_60):
            self._write_match(f"within-60-{i}", days_ago=INITIAL_WINDOW_DAYS + WINDOW_INCREMENT_DAYS - 5)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(len(result), MAX_MATCHES)

    def test_widens_full_window_when_still_under_cap(self):
        within_30 = max(MIN_MATCHES_TARGET // 10, 1)
        within_60 = max(MIN_MATCHES_TARGET // 4, 1)
        for i in range(within_30):
            self._write_match(f"within-30-{i}", days_ago=INITIAL_WINDOW_DAYS - 5)
        for i in range(within_60):
            self._write_match(f"within-60-{i}", days_ago=INITIAL_WINDOW_DAYS + WINDOW_INCREMENT_DAYS - 5)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(len(result), within_30 + within_60)

    def test_stops_widening_at_max_window_even_if_sparse(self):
        for i in range(10):
            self._write_match(f"old-{i}", days_ago=MAX_WINDOW_DAYS - 5)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(len(result), 10)

    def test_matches_beyond_max_window_excluded_even_if_sparse(self):
        self._write_match("too-old", days_ago=MAX_WINDOW_DAYS + 1)

        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(result, [])

    def test_empty_when_no_matches_cached(self):
        result = select_scoped_match_ids(ME, telemetry_dir=self.tmpdir.name, now=NOW)

        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
