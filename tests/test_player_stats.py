##########
# Unit Test for Player Stats API 
# fromn root of project: `python -m unittest discover tests`
##########

import unittest
from unittest.mock import patch
from api.player_stats import fetch_player_stats

MOCK_PLAYER_ID = "account.mocked123"
MOCK_STATS = {"mock": "stats_json_data"}

class TestPlayerStatsQuery(unittest.TestCase):
    
    @patch("api.player_stats.requests.get")
    def test_fetch_player_stats(self, mock_get):
        # --- Mock /players endpoint ---
        mock_get.side_effect = [
            # First call: get player ID
            unittest.mock.Mock(status_code=200, json=lambda: {
                "data": [{"id": MOCK_PLAYER_ID}]
            }),
            # Second call: get player stats
            unittest.mock.Mock(status_code=200, json=lambda: MOCK_STATS)
        ]

        stats, player_id = fetch_player_stats("FakePlayer")
        
        self.assertEqual(player_id, MOCK_PLAYER_ID)
        self.assertEqual(stats, MOCK_STATS)
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main()