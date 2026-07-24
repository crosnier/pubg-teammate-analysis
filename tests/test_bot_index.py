##########
# Unit Test for Bot Index persistence
# from root of project: `python -m unittest discover tests`
##########

import unittest
from unittest.mock import patch

from api.bot_index import update_bot_index

BOTS = {"account.bot1": "BotName123"}


class TestUpdateBotIndex(unittest.TestCase):

    @patch("api.bot_index.save_bot_index")
    @patch("api.bot_index.load_bot_index", return_value={})
    def test_adds_new_bot_entry(self, mock_load, mock_save):
        update_bot_index(BOTS, "match-1")

        saved_index = mock_save.call_args.args[0]
        entry = saved_index["account.bot1"]
        self.assertEqual(entry["playername"], "BotName123")
        self.assertEqual(entry["matches_seen"], ["match-1"])
        self.assertEqual(entry["times_seen"], 1)
        self.assertEqual(entry["first_seen"], entry["last_seen"])

    @patch("api.bot_index.save_bot_index")
    @patch("api.bot_index.load_bot_index")
    def test_repeat_encounter_appends_match_and_increments_count(self, mock_load, mock_save):
        mock_load.return_value = {
            "account.bot1": {
                "playername": "BotName123",
                "first_seen": "2026-01-01",
                "last_seen": "2026-01-01",
                "matches_seen": ["match-1"],
                "times_seen": 1,
            }
        }

        update_bot_index(BOTS, "match-2")

        saved_index = mock_save.call_args.args[0]
        entry = saved_index["account.bot1"]
        self.assertEqual(entry["matches_seen"], ["match-1", "match-2"])
        self.assertEqual(entry["times_seen"], 2)
        self.assertEqual(entry["first_seen"], "2026-01-01")

    @patch("api.bot_index.save_bot_index")
    @patch("api.bot_index.load_bot_index")
    def test_same_match_seen_twice_does_not_duplicate(self, mock_load, mock_save):
        mock_load.return_value = {
            "account.bot1": {
                "playername": "BotName123",
                "first_seen": "2026-01-01",
                "last_seen": "2026-01-01",
                "matches_seen": ["match-1"],
                "times_seen": 1,
            }
        }

        update_bot_index(BOTS, "match-1")

        saved_index = mock_save.call_args.args[0]
        entry = saved_index["account.bot1"]
        self.assertEqual(entry["matches_seen"], ["match-1"])
        self.assertEqual(entry["times_seen"], 1)


if __name__ == '__main__':
    unittest.main()
