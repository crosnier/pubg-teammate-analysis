# ==============================
# api/rate_limiter.py
# ==============================
import os
import time
import asyncio
import logging

import aiohttp

logger = logging.getLogger("rate_limiter")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

DEFAULT_LIMIT_PER_MINUTE = int(os.getenv("PUBG_RATE_LIMIT_PER_MINUTE", 10))


class RateLimitedQueue:
    """Serializes requests to rate-limited PUBG API endpoints.

    Falls back to a configurable default rate (requests/minute) until the
    API's X-RateLimit-* response headers are seen, then throttles against
    the reported Limit/Remaining/Reset instead.
    """

    def __init__(self, default_limit_per_minute=DEFAULT_LIMIT_PER_MINUTE):
        self._lock = asyncio.Lock()
        self._session = None
        self._limit = default_limit_per_minute
        self._remaining = None
        self._reset_at = None
        self._last_request_at = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _wait_for_slot(self):
        if self._remaining is not None and self._remaining <= 0 and self._reset_at:
            wait_time = self._reset_at - time.time()
            if wait_time > 0:
                logger.info(f"Rate limit exhausted, pausing queue for {wait_time:.1f}s until reset")
                await asyncio.sleep(wait_time)
            return

        if self._last_request_at is not None:
            min_interval = 60.0 / self._limit
            elapsed = time.time() - self._last_request_at
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.info(f"Throttling to {self._limit}/min, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

    def _update_from_headers(self, headers):
        limit = headers.get("X-RateLimit-Limit")
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")

        if limit is not None:
            self._limit = int(limit)
        if remaining is not None:
            self._remaining = int(remaining)
        if reset is not None:
            self._reset_at = float(reset)

    async def request(self, method, url, headers=None, **kwargs):
        async with self._lock:
            logger.info(f"Queued {method} {url}")
            await self._wait_for_slot()

            session = await self._get_session()
            async with session.request(method, url, headers=headers, **kwargs) as response:
                self._update_from_headers(response.headers)
                self._last_request_at = time.time()
                response.raise_for_status()
                data = await response.json()

            logger.info(
                f"Released {method} {url} "
                f"(remaining={self._remaining}, limit={self._limit})"
            )
            return data


# Shared queue for all rate-limited endpoints (/players, /seasons).
# /matches and telemetry URLs are not rate-limited and must bypass this queue.
player_api_queue = RateLimitedQueue()
