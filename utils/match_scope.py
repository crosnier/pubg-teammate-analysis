# ==============================
# utils/match_scope.py
# ==============================
import glob
import json
import os
from datetime import datetime, timedelta, timezone

from utils.last_match_brief import player_present_in_match

TELEMETRY_DIR = "match-telemetry"

# Which of a player's own cached matches feed the Archetype Tag signals.
# Operational tuning knobs (not fixed design constants), so they're env
# configurable - see .env.example. Recent play is a better behavioral
# signal than a match from months ago, but too few matches makes any
# signal unreliable, hence the widening window.
#
# Defaults set to 50 for now pending further performance investigation
# (real-cache benchmarking showed ~0.78s/match per signal, single-
# threaded) - the intended production default is 250, per the widening
# spec: 30-day window, +30 days at a time up to 90 days, until 250
# matches are found or the window maxes out. Revisit once the redundant
# per-signal file-parsing and match_scope's full-cache scan cost are
# addressed.
MAX_MATCHES = int(os.getenv("ARCHETYPE_MAX_MATCHES", 50))
MIN_MATCHES_TARGET = int(os.getenv("ARCHETYPE_MIN_MATCHES_TARGET", 50))
INITIAL_WINDOW_DAYS = int(os.getenv("ARCHETYPE_INITIAL_WINDOW_DAYS", 30))
WINDOW_INCREMENT_DAYS = int(os.getenv("ARCHETYPE_WINDOW_INCREMENT_DAYS", 30))
MAX_WINDOW_DAYS = int(os.getenv("ARCHETYPE_MAX_WINDOW_DAYS", 90))


def _parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_match_dates(account_id, telemetry_dir):
    """Yield (match_id, match_start) for every cached match the player appears in.

    Telemetry caching is shared across players (see README), so the cache
    holds many matches unrelated to this account - only matches the player
    actually appears in (via LogPlayerCreate) are candidates.
    """
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        with open(path, "r") as f:
            events = json.load(f)
        if not player_present_in_match(account_id, events):
            continue
        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event or not start_event.get("_D"):
            continue
        yield match_id, _parse_timestamp(start_event["_D"])


def select_scoped_match_ids(account_id, telemetry_dir=TELEMETRY_DIR, now=None):
    """Pick which of a player's own cached matches feed the Archetype Tag.

    Starts with a recency window of INITIAL_WINDOW_DAYS, widening by
    WINDOW_INCREMENT_DAYS until either MIN_MATCHES_TARGET matches are found
    (defaults to matching MAX_MATCHES - keep widening until there's enough
    to fill the cap, or MAX_WINDOW_DAYS is reached) then caps the result at
    MAX_MATCHES (most recent first).
    """
    now = now or datetime.now(timezone.utc)
    dated_matches = sorted(_load_match_dates(account_id, telemetry_dir), key=lambda m: m[1], reverse=True)

    window_days = INITIAL_WINDOW_DAYS
    in_window = []
    while True:
        cutoff = now - timedelta(days=window_days)
        in_window = [match_id for match_id, started in dated_matches if started >= cutoff]
        if len(in_window) >= MIN_MATCHES_TARGET or window_days >= MAX_WINDOW_DAYS:
            break
        window_days = min(window_days + WINDOW_INCREMENT_DAYS, MAX_WINDOW_DAYS)

    return in_window[:MAX_MATCHES]
