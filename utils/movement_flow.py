# ==============================
# utils/movement_flow.py
# ==============================
"""
Map Drop Zone + Flow (issue #44), "Flow" half: where a player tends to sit
relative to the shrinking safe zone over the course of a match, mined from
LogPlayerPosition + LogGameStatePeriodic.

Unlike the Drop Zone half (utils/drop_zone.py), this signal is
**map-agnostic** - it never needs named POI data, since it only measures
relative geometry (distance from the player to the safe zone's own center,
as a fraction of the safe zone's own radius). That means Flow works on
every map immediately, including ones Drop Zone can't classify yet
(Taego, Miramar, etc.) - a deliberate scope difference, not an oversight.

Researched before building, not guessed:
- LogPlayerPosition pings fire every 10 in-game seconds per player for as
  long as they're alive, with a `location` matching LogParachuteLanding's
  coordinate system.
- LogGameStatePeriodic fires on the same ~10s cadence with
  `safetyZonePosition` + `safetyZoneRadius` - trivial to align by
  `elapsedTime` (take the most recent zone snapshot at or before a given
  position's timestamp). Early-match snapshots before the first circle is
  announced have `safetyZoneRadius == 0` and are skipped.
- Calibrated 2026-07-25 against 6,570 real (player, match) samples across
  80 cached matches (random sample, seed 3): each sample is that player's
  MEDIAN (distance-to-zone-center / zone-radius) ratio across all of their
  position pings in one match. Population percentiles: p10=0.134,
  p25=0.210, p33=0.256, p50=0.371, p67=0.457, p75=0.506, p90=0.634 - used
  a tertile split (p33/p67) the same way range_signal.py did, rather than
  picking round numbers.
"""
import glob
import json
import math
import os
import statistics

from utils.last_match_brief import player_present_in_match

TELEMETRY_DIR = "match-telemetry"

# Tertile-split bucket thresholds on (distance-to-zone-center / zone-radius),
# calibrated against the real distribution above (p33=0.256, p67=0.457,
# rounded slightly for a readable constant).
ZONE_CENTER_MAX_FRACTION = 0.26
BALANCED_MAX_FRACTION = 0.46

MIN_POSITIONS_FOR_MATCH_READING = 5
MIN_MATCHES_FOR_SIGNAL = 8

FLOW_BUCKET_ORDER = ["Zone Center", "Balanced Rotator", "Zone Edge"]


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def _bucket_for_fraction(median_fraction):
    if median_fraction <= ZONE_CENTER_MAX_FRACTION:
        return "Zone Center"
    if median_fraction <= BALANCED_MAX_FRACTION:
        return "Balanced Rotator"
    return "Zone Edge"


def compute_flow_read_from_events(account_id, events):
    """Return this match's zone-relative flow reading for one player, or
    None if there's nothing usable (player absent, or too few position
    pings/zone snapshots to trust a median).
    """
    if not player_present_in_match(account_id, events):
        return None

    zone_by_time = {}
    for event in events:
        if event.get("_T") != "LogGameStatePeriodic":
            continue
        game_state = event["gameState"]
        if game_state["safetyZoneRadius"] <= 0:
            continue
        zone_by_time[game_state["elapsedTime"]] = (
            game_state["safetyZonePosition"]["x"],
            game_state["safetyZonePosition"]["y"],
            game_state["safetyZoneRadius"],
        )
    if not zone_by_time:
        return None
    zone_times = sorted(zone_by_time)

    fractions = []
    for event in events:
        if event.get("_T") != "LogPlayerPosition":
            continue
        character = event.get("character") or {}
        if character.get("accountId") != account_id or character.get("type") != "user":
            continue

        position_time = event["elapsedTime"]
        zone_time = next((t for t in reversed(zone_times) if t <= position_time), None)
        if zone_time is None:
            continue

        zone_x, zone_y, zone_radius = zone_by_time[zone_time]
        location = character["location"]
        distance = math.hypot(location["x"] - zone_x, location["y"] - zone_y)
        fractions.append(distance / zone_radius)

    if len(fractions) < MIN_POSITIONS_FOR_MATCH_READING:
        return None

    median_fraction = statistics.median(fractions)
    return {
        "median_zone_fraction": median_fraction,
        "flow_bucket": _bucket_for_fraction(median_fraction),
        "positions_analyzed": len(fractions),
    }


def compute_flow_signal(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR):
    """Aggregate per-match flow reads into a "how do you sit relative to
    the zone" signal - most frequent bucket across matches, same
    mode-based approach as compute_tempo_signal/compute_drop_zone_signal.
    Requires MIN_MATCHES_FOR_SIGNAL matches with a usable reading before
    naming a tag.
    """
    per_match = []
    for events in _load_telemetry_files(match_ids, telemetry_dir):
        reading = compute_flow_read_from_events(account_id, events)
        if reading is not None:
            per_match.append(reading)

    bucket_counts = {}
    for reading in per_match:
        bucket = reading["flow_bucket"]
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    if bucket_counts and len(per_match) >= MIN_MATCHES_FOR_SIGNAL:
        max_count = max(bucket_counts.values())
        tied = [b for b, c in bucket_counts.items() if c == max_count]
        flow_tag = next(b for b in FLOW_BUCKET_ORDER if b in tied)
    else:
        flow_tag = None

    return {
        "flow_tag": flow_tag,
        "matches_analyzed": len(per_match),
        "bucket_counts": bucket_counts,
    }
