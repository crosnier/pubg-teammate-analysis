# ==============================
# utils/tempo_signal.py
# ==============================
from datetime import datetime

from utils.last_match_brief import player_present_in_match
from utils.telemetry_cache import select_telemetry_events

TELEMETRY_DIR = "match-telemetry"

# Bucket thresholds in seconds from LogMatchStart to first real-player
# contact, and the window after that contact within which a kill still
# reads as "quick". Calibrated against 101,194 real (player, match)
# time-to-first-contact readings and 56,385 contact-to-kill gap readings
# across 1,636 cached matches (including top-30 ranked PC-NA leaderboard
# players) - quartile splits of the real distribution:
# p25=128s, p50=222s, p75=494s for contact; p60=~30s for the kill gap
# (loosely - "quick" should mean faster than typical, not merely not-slow).
VERY_FAST_CONTACT_SECONDS = 130
SHORT_DELAY_SECONDS = 220
MODERATE_DELAY_SECONDS = 490
QUICK_KILL_WINDOW_SECONDS = 30

# Minimum matches with a valid reading before naming a tempo tag -
# matches range_signal.py/weapon_signature.py's MIN_KILLS_FOR_SIGNAL=8,
# grounded in Epstein's aggregation principle (single-occasion behavioral
# reliability is low; ~8+ occasions is where aggregated reliability
# becomes meaningfully informative, per Spearman-Brown).
MIN_MATCHES_FOR_SIGNAL = 8

TEMPO_BUCKET_ORDER = [
    "Hot-Drop Headhunter",
    "Early Skirmisher",
    "Quick-Gear Striker",
    "Calculated Pusher",
    "Slow-Roll Patient",
]


def _parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compute_time_to_first_contact_from_events(account_id, telemetry_events):
    """Return this match's tempo reading for one player, or None if unplayed.

    Tempo is driven by time-to-first-contact: elapsed time from
    LogMatchStart to the player's first LogPlayerTakeDamage event where
    they're the attacker against a real (non-bot, non-NPC) player - this
    covers both damage-only pokes and kills, since a kill is damage that
    finished the job. Environmental/self damage is excluded because it
    has no real opponent on the other end.

    A match the player never appears in returns None rather than a
    "Slow-Roll Patient" reading - telemetry caching is shared across
    players, so the cache holds many matches unrelated to this account.
    """
    if not player_present_in_match(account_id, telemetry_events):
        return None

    start_event = next((e for e in telemetry_events if e.get("_T") == "LogMatchStart"), None)
    if not start_event or not start_event.get("_D"):
        return None
    match_start = _parse_timestamp(start_event["_D"])

    contact_seconds = None
    for event in telemetry_events:
        if event.get("_T") != "LogPlayerTakeDamage":
            continue
        attacker = event.get("attacker") or {}
        victim = event.get("victim") or {}
        if attacker.get("accountId") != account_id or attacker.get("type") != "user":
            continue
        if victim.get("type") != "user" or victim.get("accountId") == account_id:
            continue
        elapsed = (_parse_timestamp(event["_D"]) - match_start).total_seconds()
        if contact_seconds is None or elapsed < contact_seconds:
            contact_seconds = elapsed

    if contact_seconds is None:
        return {"contact_seconds": None, "quick_kill": False, "tempo_bucket": "Slow-Roll Patient"}

    kill_seconds = None
    for event in telemetry_events:
        if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
            continue
        killer = event.get("killer") or {}
        victim = event.get("victim") or {}
        if killer.get("accountId") != account_id or killer.get("type") != "user":
            continue
        if victim.get("type") != "user" or victim.get("accountId") == account_id:
            continue
        elapsed = (_parse_timestamp(event["_D"]) - match_start).total_seconds()
        if kill_seconds is None or elapsed < kill_seconds:
            kill_seconds = elapsed

    quick_kill = kill_seconds is not None and (kill_seconds - contact_seconds) <= QUICK_KILL_WINDOW_SECONDS

    if contact_seconds <= VERY_FAST_CONTACT_SECONDS:
        bucket = "Hot-Drop Headhunter" if quick_kill else "Early Skirmisher"
    elif contact_seconds <= SHORT_DELAY_SECONDS:
        bucket = "Quick-Gear Striker"
    elif contact_seconds <= MODERATE_DELAY_SECONDS:
        bucket = "Calculated Pusher"
    else:
        bucket = "Slow-Roll Patient"

    return {"contact_seconds": contact_seconds, "quick_kill": quick_kill, "tempo_bucket": bucket}


def compute_tempo_signal(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR, events_by_match=None):
    """Aggregate the tempo half of the Archetype Tag across cached matches.

    Overall tag is the most frequent per-match bucket, ties broken by
    bucket priority (fastest-tempo bucket first) rather than arbitrarily.
    Requires MIN_MATCHES_FOR_SIGNAL matches before naming a tag - a
    single match is not a reliable read on tempo.

    events_by_match, if given (see utils/telemetry_cache.py), reuses
    telemetry already parsed by a caller sharing it across multiple
    signals (see archetype_tag.py) instead of re-reading from disk.
    """
    per_match = []
    for events in select_telemetry_events(match_ids, telemetry_dir, events_by_match):
        reading = compute_time_to_first_contact_from_events(account_id, events)
        if reading is not None:
            per_match.append(reading)

    bucket_counts = {}
    for reading in per_match:
        bucket = reading["tempo_bucket"]
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    if bucket_counts and len(per_match) >= MIN_MATCHES_FOR_SIGNAL:
        max_count = max(bucket_counts.values())
        tied = [b for b, c in bucket_counts.items() if c == max_count]
        tempo_tag = next(b for b in TEMPO_BUCKET_ORDER if b in tied)
    else:
        tempo_tag = None

    return {
        "tempo_tag": tempo_tag,
        "matches_analyzed": len(per_match),
        "matches_with_contact": sum(1 for r in per_match if r["contact_seconds"] is not None),
        "bucket_counts": bucket_counts,
    }
