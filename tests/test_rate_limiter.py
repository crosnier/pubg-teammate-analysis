##########
# Unit Test for Request Queue / Rate Limiter
# from root of project: `python -m unittest discover tests`
##########

import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.rate_limiter import RateLimitedQueue


def make_mock_session(headers, json_data):
    response = MagicMock()
    response.headers = headers
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value=json_data)

    response_cm = MagicMock()
    response_cm.__aenter__ = AsyncMock(return_value=response)
    response_cm.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.closed = False
    session.request = MagicMock(return_value=response_cm)
    return session


class TestRateLimitedQueue(unittest.IsolatedAsyncioTestCase):

    async def test_updates_state_from_response_headers(self):
        queue = RateLimitedQueue(default_limit_per_minute=10)
        session = make_mock_session(
            headers={"X-RateLimit-Limit": "10", "X-RateLimit-Remaining": "9", "X-RateLimit-Reset": "1700000000"},
            json_data={"ok": True},
        )
        queue._session = session

        result = await queue.request("GET", "https://api.pubg.com/shards/steam/players")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(queue._limit, 10)
        self.assertEqual(queue._remaining, 9)
        self.assertEqual(queue._reset_at, 1700000000.0)

    async def test_pauses_when_remaining_is_zero(self):
        queue = RateLimitedQueue(default_limit_per_minute=10)
        queue._remaining = 0
        queue._reset_at = time.time() + 5

        with patch("api.rate_limiter.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await queue._wait_for_slot()

        mock_sleep.assert_awaited_once()
        waited = mock_sleep.call_args.args[0]
        self.assertGreater(waited, 0)
        self.assertLessEqual(waited, 5)

    async def test_throttles_to_default_interval_without_headers(self):
        queue = RateLimitedQueue(default_limit_per_minute=60)  # 1 req/sec
        queue._last_request_at = time.time()

        with patch("api.rate_limiter.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await queue._wait_for_slot()

        mock_sleep.assert_awaited_once()
        waited = mock_sleep.call_args.args[0]
        self.assertGreater(waited, 0)
        self.assertLessEqual(waited, 1)

    async def test_no_wait_when_remaining_available(self):
        queue = RateLimitedQueue(default_limit_per_minute=10)
        queue._remaining = 5
        queue._reset_at = time.time() + 60
        queue._last_request_at = time.time() - 60

        with patch("api.rate_limiter.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await queue._wait_for_slot()

        mock_sleep.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
