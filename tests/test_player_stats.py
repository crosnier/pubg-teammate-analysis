##########
# Unit Test for Player Stats API
# fromn root of project: `python -m unittest discover tests`
##########

import unittest
from unittest.mock import patch, AsyncMock
from api.player_stats import fetch_player_stats, PlayerNotFoundError

MOCK_PLAYER_ID = "account.mocked123"
MOCK_STATS = {"mock": "stats_json_data"}

class TestPlayerStatsQuery(unittest.IsolatedAsyncioTestCase):

    @patch("api.player_stats.update_player_index")
    @patch("api.player_stats.player_api_queue.request", new_callable=AsyncMock)
    async def test_fetch_player_stats(self, mock_request, mock_update_index):
        # --- Mock the rate-limited queue's responses ---
        mock_request.side_effect = [
            # First call: get player ID
            {"data": [{"id": MOCK_PLAYER_ID}]},
            # Second call: get player stats
            MOCK_STATS
        ]

        stats, player_id = await fetch_player_stats("FakePlayer")

        self.assertEqual(player_id, MOCK_PLAYER_ID)
        self.assertEqual(stats, MOCK_STATS)
        self.assertEqual(mock_request.call_count, 2)
        mock_update_index.assert_called_once_with(account_id=MOCK_PLAYER_ID, playername="FakePlayer")

    @patch("api.player_stats.player_api_queue.request", new_callable=AsyncMock)
    async def test_raises_player_not_found_on_empty_data(self, mock_request):
        # The real API returns an empty "data" list (not a 404) for a name
        # that doesn't resolve to any player - must not fall through to an
        # IndexError on data[0].
        mock_request.return_value = {"data": []}

        with self.assertRaises(PlayerNotFoundError):
            await fetch_player_stats("NotARealPlayerName")

if __name__ == '__main__':
    unittest.main()
