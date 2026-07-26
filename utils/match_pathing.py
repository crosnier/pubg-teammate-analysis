# ==============================
# utils/match_pathing.py
# ==============================
"""
Issue #8, text-based variant: a simple text narrative of a player's
movement path through their last match - map, mode, and a named-POI
trail - built to work for a single player first, then reused per-member
in both solo.py and squad.py.

Mode (team size + view mode) is read straight off LogMatchStart rather
than cross-referenced against the player-stats API's per-mode match
lists, so this only needs the telemetry file already on hand:
- teamSize: 1/2/4 -> Solo/Duo/Squad (matches PUBG's own bucketing).
- cameraViewBehaviour: "FpsOnly" on FPP-only servers, "FpsAndTps" on TPP
  servers (which also allow first-person) - the only two values PUBG's
  API reports, so this is a direct read, not a guess.

The path trail reuses drop_zone.py's MAP_POI_LOOKUP + classify_landing
so named stops stay consistent with the Drop Zone signal's own POI
reference data - a map with no POI data yet falls back to "not
supported" the same way, rather than guessing.
"""
from utils.drop_zone import MAP_POI_LOOKUP, classify_landing
from utils.last_match_brief import player_present_in_match

MAX_PATH_STOPS = 6

TEAM_SIZE_LABELS = {1: "Solo", 2: "Duo", 4: "Squad"}
VIEW_LABELS = {"FpsOnly": "FPP", "FpsAndTps": "TPP"}


def _mode_label(start_event):
    team_label = TEAM_SIZE_LABELS.get(start_event.get("teamSize"), "Unknown")
    view_label = VIEW_LABELS.get(start_event.get("cameraViewBehaviour"), "Unknown")
    return f"{team_label} {view_label}"


def _downsample(stops, max_stops):
    """Evenly thin a longer stop list down to max_stops, always keeping
    the first and last stop so the trail still reads start-to-finish.

    Non-consecutive revisits of the same POI (player left and came back)
    survive the initial collapse-consecutive-duplicates pass as separate
    entries, so thinning can land two picks on the same name back-to-back -
    collapse those again afterward so "X → X" never reads as a stutter.
    """
    if len(stops) > max_stops:
        indices = {round(i * (len(stops) - 1) / (max_stops - 1)) for i in range(max_stops)}
        stops = [stop for i, stop in enumerate(stops) if i in indices]

    thinned = []
    for stop in stops:
        if not thinned or thinned[-1] != stop:
            thinned.append(stop)
    return thinned


def compute_match_pathing(account_id, match_id, events):
    """Return this player's last-match pathing read, or None if the
    player isn't present in this match at all.
    """
    if not player_present_in_match(account_id, events):
        return None

    start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
    map_name = start_event.get("mapName") if start_event else None
    mode_label = _mode_label(start_event) if start_event else "Unknown"

    poi_coords = MAP_POI_LOOKUP.get(map_name)
    if poi_coords is None:
        return {
            "match_id": match_id,
            "map_name": map_name,
            "mode_label": mode_label,
            "supported_map": False,
            "path_description": None,
        }

    positions = [
        e for e in events
        if e.get("_T") == "LogPlayerPosition"
        and (e.get("character") or {}).get("accountId") == account_id
        and (e.get("character") or {}).get("type") == "user"
    ]
    positions.sort(key=lambda e: e["elapsedTime"])

    stops = []
    for event in positions:
        location = event["character"]["location"]
        nearest_poi = classify_landing(location["x"], location["y"], poi_coords)["nearest_poi"]
        if not stops or stops[-1] != nearest_poi:
            stops.append(nearest_poi)

    stops = _downsample(stops, MAX_PATH_STOPS)

    path_description = " → ".join(stops) if len(stops) >= 2 else None

    return {
        "match_id": match_id,
        "map_name": map_name,
        "mode_label": mode_label,
        "supported_map": True,
        "path_description": path_description,
    }
