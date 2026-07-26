# ==============================
# utils/range_signal.py
# ==============================
import statistics

from utils.telemetry_cache import select_telemetry_events

TELEMETRY_DIR = "match-telemetry"

# Range-axis bucket thresholds, in meters, applied to a player's MEDIAN
# real-player kill distance across cached matches. Median, not mean:
# kill distance is right-skewed (many close kills, a long tail of rare
# snipes), so mean is outlier-fragile - verified empirically that mean
# vs. median disagreed on bucket for 47.3% of 2,879 real players with 8+
# kills. Thresholds calibrated as a tertile split of per-player MEDIAN
# distance across 1,636 cached matches / 2,879 players with 8+ kills
# (33rd/67th percentile: 20.2m / 33.0m) - easy to retune here if the
# population shifts.
CLOSE_RANGE_MAX_METERS = 20
MID_RANGE_MAX_METERS = 33

MIN_KILLS_FOR_SIGNAL = 8


def _bucket_for_distance(median_distance_m):
    if median_distance_m <= CLOSE_RANGE_MAX_METERS:
        return "Close-Range"
    if median_distance_m <= MID_RANGE_MAX_METERS:
        return "Mid-Range"
    return "Long-Range"


def compute_range_signal(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR, events_by_match=None):
    """Range-axis half of the Archetype Tag: median real-player kill distance.

    Only kills against real players count (bots/NPCs have no bearing on a
    range preference). Requires MIN_KILLS_FOR_SIGNAL kills before a bucket
    is assigned, matching the design doc's confidence-gating philosophy -
    a small sample shouldn't produce a confident-sounding label.

    events_by_match, if given (see utils/telemetry_cache.py), reuses
    telemetry already parsed by a caller sharing it across multiple
    signals (see archetype_tag.py) instead of re-reading from disk.
    """
    distances = []

    for events in select_telemetry_events(match_ids, telemetry_dir, events_by_match):
        for event in events:
            if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
                continue
            killer = event.get("killer") or {}
            victim = event.get("victim") or {}
            if killer.get("accountId") != account_id or killer.get("type") != "user":
                continue
            if victim.get("type") != "user" or victim.get("accountId") == account_id:
                continue
            distance_m = (event.get("killerDamageInfo") or {}).get("distance", 0) / 100
            distances.append(distance_m)

    kills_analyzed = len(distances)
    if kills_analyzed < MIN_KILLS_FOR_SIGNAL:
        return {
            "range_bucket": None,
            "median_distance_m": None,
            "kills_analyzed": kills_analyzed,
        }

    median_distance_m = statistics.median(distances)
    return {
        "range_bucket": _bucket_for_distance(median_distance_m),
        "median_distance_m": round(median_distance_m, 1),
        "kills_analyzed": kills_analyzed,
    }
