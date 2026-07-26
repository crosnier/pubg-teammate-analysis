# ==============================
# utils/drop_zone.py
# ==============================
"""
Map Drop Zone + Flow (issue #44), per-player half: classify a landing
coordinate against utils/map_regions_data.py's researched POI reference
data and aggregate across a player's cached matches into a "where do you
typically drop" read - the same shape as tempo_signal.py's most-frequent-
bucket approach.

All 4 ranked-rotation maps (Erangel, Miramar, Taego, Rondo) plus Vikendi
and Sanhok have real POI data as of this writing (see map_regions_data.py).
Any other map falls back to a "not yet supported" read rather than a crash
or a silently wrong guess, per issue #44's accuracy requirements -
MAP_POI_LOOKUP below is the single place that gates map support, so adding
a new map's data automatically supports it. Camp Jackal and Haven are
discontinued (not in PUBG's current map rotation as of 2026-07-26 - see
pubg.com's official Map Service Report) and are deliberately not planned
for POI data; they fall through the same graceful "not supported" path.

Ambiguity thresholds calibrated 2026-07-25 against 15,067 real
LogParachuteLanding events sampled from 204 cached Baltic_Main matches
(random sample, seed 42). Distribution of (second-nearest / nearest POI
distance) ratio: p10=1.17, p25=1.51, p50=2.90, p75=4.69, p90=7.38 - most
real landings (62.3% at ratio >= 2.0, ~75% at >= 1.5) sit well clear of
any boundary, confirming ambiguity is genuinely the minority tail rather
than the common case (POIs are spaced far enough apart on Erangel that a
confident nearest-POI read is usually correct). BETWEEN_RATIO=1.15 and
EDGE_RATIO=1.5 below split that tail into "genuinely between two POIs"
(~8-9% of landings, ratio < 1.15) vs. "near one POI's edge" (~15%,
1.15-1.5) vs. confident (~75%+, >= 1.5).
"""
import glob
import json
import math
import os
import statistics

from utils.last_match_brief import player_present_in_match
from utils.map_regions_data import (
    erangel_poi_world_coordinates,
    miramar_poi_world_coordinates,
    rondo_poi_world_coordinates,
    sanhok_poi_world_coordinates,
    taego_poi_world_coordinates,
    vikendi_poi_world_coordinates,
)

TELEMETRY_DIR = "match-telemetry"

# Map name -> {poi_name: (x_cm, y_cm)}. The only place map support is
# gated - a map absent here always falls back gracefully, never guesses.
MAP_POI_LOOKUP = {
    "Baltic_Main": erangel_poi_world_coordinates(),
    "Tiger_Main": taego_poi_world_coordinates(),
    "Desert_Main": miramar_poi_world_coordinates(),
    "DihorOtok_Main": vikendi_poi_world_coordinates(),
    "Savage_Main": sanhok_poi_world_coordinates(),
    "Neon_Main": rondo_poi_world_coordinates(),
}

# Ratio of second-nearest to nearest POI distance. Below BETWEEN_RATIO the
# landing is genuinely torn between two POIs ("between X and Y"); below
# EDGE_RATIO but above that it's a confident-ish nearest POI that's still
# close enough to a neighbor to caveat as "near the edge of X, <compass>";
# above EDGE_RATIO it's a plain confident single-POI read. Calibrated
# against the real ratio distribution (see module docstring) rather than
# guessed - most real landings cluster well above 2.0 (POIs are spaced far
# enough apart that ambiguity is the minority case), so these thresholds
# bite only on the genuinely boundary-adjacent tail.
BETWEEN_RATIO = 1.15
EDGE_RATIO = 1.5

MIN_MATCHES_FOR_SIGNAL = 8

_COMPASS_DIRECTIONS = [
    "north", "northeast", "east", "southeast",
    "south", "southwest", "west", "northwest",
]


def _compass_direction(from_xy, to_xy):
    """8-way compass direction of to_xy as seen from from_xy.

    Telemetry's coordinate convention is top-left origin, x-right, y-down
    (confirmed in map_regions_data.py's validation) - "south" is +y, not
    -y like a standard math y-axis.
    """
    dx = to_xy[0] - from_xy[0]
    dy = to_xy[1] - from_xy[1]
    angle = math.degrees(math.atan2(dx, -dy)) % 360  # 0=north, 90=east
    index = round(angle / 45) % 8
    return _COMPASS_DIRECTIONS[index]


def classify_landing(x, y, poi_coords):
    """Classify one (x, y) landing coordinate (cm) against a map's POI
    reference data. Returns a dict with a human-readable `description` and
    the structured nearest/second-nearest data behind it (kept structured,
    not just the sentence, per issue #44's "future visual map layer"
    requirement).
    """
    ranked = sorted(
        ((math.hypot(x - px, y - py), name, (px, py)) for name, (px, py) in poi_coords.items()),
    )
    nearest_dist, nearest_name, nearest_xy = ranked[0]
    second_dist, second_name, second_xy = ranked[1]
    ratio = (second_dist / nearest_dist) if nearest_dist > 0 else float("inf")

    if ratio < BETWEEN_RATIO:
        pair = sorted([nearest_name, second_name])
        description = f"between {pair[0]} and {pair[1]}"
        zone_key = f"between:{pair[0]}|{pair[1]}"
    elif ratio < EDGE_RATIO:
        direction = _compass_direction(nearest_xy, (x, y))
        description = f"near the edge of {nearest_name}, {direction}"
        zone_key = f"edge:{nearest_name}"
    else:
        direction = _compass_direction(nearest_xy, (x, y))
        description = f"near {nearest_name}, {direction}"
        zone_key = nearest_name

    return {
        "description": description,
        "zone_key": zone_key,
        "nearest_poi": nearest_name,
        "nearest_distance_m": round(nearest_dist / 100, 1),
        "second_nearest_poi": second_name,
        "second_nearest_distance_m": round(second_dist / 100, 1),
    }


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def compute_landing_read_from_events(account_id, events):
    """Return this match's landing classification for one player, or None
    if the player didn't land in this match (absent, or map unsupported).
    """
    if not player_present_in_match(account_id, events):
        return None

    start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
    map_name = start_event.get("mapName") if start_event else None
    poi_coords = MAP_POI_LOOKUP.get(map_name)
    if poi_coords is None:
        return {"supported_map": False, "map_name": map_name}

    landing_event = next(
        (
            e for e in events
            if e.get("_T") == "LogParachuteLanding"
            and (e.get("character") or {}).get("accountId") == account_id
            and (e.get("character") or {}).get("type") == "user"
        ),
        None,
    )
    if landing_event is None:
        return None

    location = landing_event["character"]["location"]
    result = classify_landing(location["x"], location["y"], poi_coords)
    result["supported_map"] = True
    result["map_name"] = map_name
    # Several POI names collide across maps (e.g. "School" exists on both
    # Erangel and Taego) - qualify zone_key with the map name so a player's
    # aggregate zone_counts never merges two physically different spots
    # that happen to share a name. classify_landing itself stays
    # map-agnostic (it only needs coordinates), this is the one place that
    # knows both the classification and the map, so it owns the prefix.
    result["zone_key"] = f"{map_name}||{result['zone_key']}"
    return result


def compute_drop_zone_signal(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR):
    """Aggregate per-match landing reads into a "where do you typically
    drop" signal - most frequent zone across matches, same mode-based
    approach as compute_tempo_signal. Requires MIN_MATCHES_FOR_SIGNAL
    landings on a supported map before naming a zone; a single landing
    isn't a reliable read on drop tendency.
    """
    supported_reads = []
    unsupported_maps = set()
    matches_analyzed = 0

    for events in _load_telemetry_files(match_ids, telemetry_dir):
        reading = compute_landing_read_from_events(account_id, events)
        if reading is None:
            continue
        matches_analyzed += 1
        if reading["supported_map"]:
            supported_reads.append(reading)
        else:
            unsupported_maps.add(reading["map_name"])

    zone_counts = {}
    description_by_zone = {}
    distances_by_zone = {}
    for reading in supported_reads:
        key = reading["zone_key"]
        zone_counts[key] = zone_counts.get(key, 0) + 1
        description_by_zone[key] = reading["description"]
        # Only single-POI zones ("near X" / "edge of X") have one
        # unambiguous anchor point to report a distance against - a
        # "between X and Y" zone_key has no single center, so it's never
        # populated here (see format_drop_zone_line's None handling).
        if not key.startswith("between:"):
            distances_by_zone.setdefault(key, []).append(reading["nearest_distance_m"])

    if zone_counts and len(supported_reads) >= MIN_MATCHES_FOR_SIGNAL:
        top_zone_key = max(zone_counts, key=zone_counts.get)
        drop_zone_description = description_by_zone[top_zone_key]
        top_zone_median_distance_m = (
            round(statistics.median(distances_by_zone[top_zone_key]), 1)
            if top_zone_key in distances_by_zone else None
        )
    else:
        top_zone_key = None
        drop_zone_description = None
        top_zone_median_distance_m = None

    return {
        "drop_zone_description": drop_zone_description,
        "top_zone_key": top_zone_key,
        "top_zone_median_distance_m": top_zone_median_distance_m,
        "matches_analyzed": matches_analyzed,
        "matches_on_supported_map": len(supported_reads),
        "unsupported_maps_seen": sorted(unsupported_maps),
        "zone_counts": zone_counts,
    }
