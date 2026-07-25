##########
# Unit Test for Request Queue / Rate Limiter
# from root of project: `python -m unittest discover tests`
##########

import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.rate_limiter import RateLimitedQueue, SAFETY_MARGIN


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
        queue = RateLimitedQueue(default_limit_per_minute=60)  # paced to 60*SAFETY_MARGIN/min
        queue._last_request_at = time.time()

        with patch("api.rate_limiter.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await queue._wait_for_slot()

        mock_sleep.assert_awaited_once()
        waited = mock_sleep.call_args.args[0]
        expected_interval = 60.0 / (60 * SAFETY_MARGIN)
        self.assertGreater(waited, 0)
        self.assertLessEqual(waited, expected_interval)

    async def test_pacing_applies_safety_margin_below_reported_limit(self):
        # A bare 10/min limit should be paced to 10*SAFETY_MARGIN/min, not
        # the full 10 - guards against normal timing jitter tripping the
        # API's own 429 threshold right at the documented ceiling.
        queue = RateLimitedQueue(default_limit_per_minute=10)
        queue._last_request_at = time.time()

        with patch("api.rate_limiter.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await queue._wait_for_slot()

        waited = mock_sleep.call_args.args[0]
        full_rate_interval = 60.0 / 10
        self.assertGreater(waited, full_rate_interval)

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
