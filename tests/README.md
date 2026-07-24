# Testing Standard

Match the test type to what's actually being verified. The goal is
high-value coverage, not a pile of narrow tests that are slow to maintain
for marginal benefit. Nothing in this suite should ever make a real call to
the PUBG API - that risks rate limits and account bans, and belongs to a
manual smoke test, not automation.

## Unit tests (bulk of the suite)

Pure computation or parsing with no I/O: telemetry-derived stat tallying,
rate-limiter throttling math, filename/URL/response parsing, display
formatting helpers. Cheap to write, run in milliseconds, and pinpoint the
exact broken function when they fail. Mock time/sleep rather than actually
waiting (see `test_rate_limiter.py`).

Examples: `test_combat_stats.py`, `test_display_stats_by_mode.py`,
`test_display_match_history.py`, `test_player_index.py`,
`test_telemetry_fetcher.py`.

## Integration tests (mocked, narrow set)

Module wiring where two pieces have to agree on a contract - e.g.
`player_stats.py` calling through `rate_limiter.py`. Mock the network
boundary (`aiohttp`), assert the right calls happened with the right args.
Don't re-test logic already covered by that module's own unit tests here -
just the handoff.

Example: `test_player_stats.py`.

## End-to-end / live smoke test

A single documented manual run (`python main.py <player>`) against the real
API. Expected once per PR that touches API-facing behavior (anything under
`api/`, or code that changes what gets sent to or parsed from a live
response) - not part of the automated suite.

## Running the suite

```bash
python -m unittest discover tests
```

Requires a `.env` with `PUBG_API_KEY` set (see main README) -
`api/telemetry_fetcher.py` raises at import time if it's missing, which
means importing it for unit tests also requires the key to be present even
though those tests don't make network calls.

## Audit notes (as of the #17 pass)

Existing tests already matched the standard - no miscategorized or
duplicate tests found. Gaps filled in this pass: `normalize_filename`
(`player_index.py`), `format_number` (`display_stats_by_mode.py`),
`extract_match_ids_by_mode` (`display_match_history.py`), and
`get_telemetry_url` (`telemetry_fetcher.py`) were pure-logic functions
previously exercised only by manual runs.

While auditing `format_number`, found that the `"Time Survived (min)"` row
doesn't convert seconds to minutes like the other two survival-time rows do
- the case-sensitive substring check (`"TimeSurvived"` vs. the actual key
`"timeSurvived"`) doesn't match. Documented in
`test_display_stats_by_mode.py`, tracked as a separate bug rather than
fixed here.
