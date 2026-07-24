##########
# Unit Test for Bot Detection
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.bot_detection import detect_bots, find_latest_match


def player_create_event(account_id, name, char_type="user", timestamp="2026-01-01T00:00:00.000Z"):
    return {
        "_T": "LogPlayerCreate",
        "_D": timestamp,
        "character": {"accountId": account_id, "name": name, "type": char_type},
    }


def match_start_event(timestamp):
    return {"_T": "LogMatchStart", "_D": timestamp}


class TestDetectBots(unittest.TestCase):

    def test_identifies_ai_players_only(self):
        events = [
            player_create_event("account.human", "RealPlayer", char_type="user"),
            player_create_event("account.bot", "BotName123", char_type="user_ai"),
        ]

        bots = detect_bots(events)

        self.assertEqual(bots, {"account.bot": "BotName123"})

    def test_no_bots_returns_empty_dict(self):
        events = [player_create_event("account.human", "RealPlayer")]

        self.assertEqual(detect_bots(events), {})

    def test_ignores_events_without_account_id(self):
        events = [{"_T": "LogPlayerCreate", "character": {"type": "user_ai", "name": "NoId"}}]

        self.assertEqual(detect_bots(events), {})


class TestFindLatestMatch(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, timestamp, extra_events=None):
        events = [match_start_event(timestamp)] + (extra_events or [])
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_returns_match_with_latest_timestamp(self):
        self._write_match("older-match", "2026-01-01T00:00:00.000Z")
        self._write_match("newer-match", "2026-06-15T00:00:00.000Z")

        match_id, events = find_latest_match(telemetry_dir=self.tmpdir.name)

        self.assertEqual(match_id, "newer-match")
        self.assertTrue(any(e.get("_T") == "LogMatchStart" for e in events))

    def test_skips_files_without_match_start(self):
        path = os.path.join(self.tmpdir.name, "no-start-telemetry.json")
        with open(path, "w") as f:
            json.dump([{"_T": "LogPlayerCreate"}], f)

        match_id, events = find_latest_match(telemetry_dir=self.tmpdir.name)

        self.assertIsNone(match_id)
        self.assertIsNone(events)

    def test_empty_directory_returns_none(self):
        match_id, events = find_latest_match(telemetry_dir=self.tmpdir.name)

        self.assertIsNone(match_id)
        self.assertIsNone(events)


if __name__ == '__main__':
    unittest.main()
