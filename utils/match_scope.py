# ==============================
# utils/match_scope.py
# ==============================
import json
import os
from datetime import datetime, timedelta, timezone

TELEMETRY_DIR = "match-telemetry"

# Which of a player's own cached matches feed the Archetype Tag signals.
# Operational tuning knobs (not fixed design constants), so they're env
# configurable - see .env.example. Recent play is a better behavioral
# signal than a match from months ago, but too few matches makes any
# signal unreliable, hence the widening window.
#
# Defaults kept at 50 deliberately, not a placeholder (see issue #30):
# tempo/range/weapon used to each independently re-parse the same match
# files, fixed by sharing one parse pass per match across all three (see
# utils/telemetry_cache.py) - a real ~2.2x speedup, but real cached
# telemetry files run large enough (median ~36MB) that the per-match
# JSON-parse cost alone is still the dominant factor. At 250 matches
# that's ~110s+ for Archetype Tag alone, before combat_stats.py/
# headline_number.py/drop_zone.py/movement_flow.py each separately
# re-parse the same matches again (that redundancy is real but out of
# #30's scope, which named only tempo/range/weapon). Raise only with
# that wait time in mind - env-configurable, see .env.example.
MAX_MATCHES = int(os.getenv("ARCHETYPE_MAX_MATCHES", 50))
MIN_MATCHES_TARGET = int(os.getenv("ARCHETYPE_MIN_MATCHES_TARGET", 50))
INITIAL_WINDOW_DAYS = int(os.getenv("ARCHETYPE_INITIAL_WINDOW_DAYS", 30))
WINDOW_INCREMENT_DAYS = int(os.getenv("ARCHETYPE_WINDOW_INCREMENT_DAYS", 30))
MAX_WINDOW_DAYS = int(os.getenv("ARCHETYPE_MAX_WINDOW_DAYS", 90))


def _parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_match_dates(candidate_match_ids, telemetry_dir):
    """Yield (match_id, match_start) for this player's own matches that are cached.

    candidate_match_ids is the player's authoritative match list, straight
    from the PUBG player-stats API response (see main.py) - not every
    cached telemetry file. The shared telemetry cache holds many matches
    belonging to other players entirely (see README), so this only ever
    opens the specific files that are actually this player's own, rather
    than scanning and checking presence across the whole cache. Not every
    candidate match is guaranteed to be cached yet (telemetry fetches are
    rate-limited per run), so missing files are skipped rather than erroring.
    """
    for match_id in candidate_match_ids:
        path = os.path.join(telemetry_dir, f"{match_id}-telemetry.json")
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            events = json.load(f)
        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event or not start_event.get("_D"):
            continue
        yield match_id, _parse_timestamp(start_event["_D"])


def select_scoped_match_ids(candidate_match_ids, telemetry_dir=TELEMETRY_DIR, now=None):
    """Pick which of a player's own cached matches feed the Archetype Tag.

    Starts with a recency window of INITIAL_WINDOW_DAYS, widening by
    WINDOW_INCREMENT_DAYS until either MIN_MATCHES_TARGET matches are found
    (defaults to matching MAX_MATCHES - keep widening until there's enough
    to fill the cap, or MAX_WINDOW_DAYS is reached) then caps the result at
    MAX_MATCHES (most recent first).
    """
    now = now or datetime.now(timezone.utc)
    dated_matches = sorted(_load_match_dates(candidate_match_ids, telemetry_dir), key=lambda m: m[1], reverse=True)

    window_days = INITIAL_WINDOW_DAYS
    in_window = []
    while True:
        cutoff = now - timedelta(days=window_days)
        in_window = [match_id for match_id, started in dated_matches if started >= cutoff]
        if len(in_window) >= MIN_MATCHES_TARGET or window_days >= MAX_WINDOW_DAYS:
            break
        window_days = min(window_days + WINDOW_INCREMENT_DAYS, MAX_WINDOW_DAYS)

    return in_window[:MAX_MATCHES]
