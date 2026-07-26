# ==============================
# utils/squad_drop_zone.py
# ==============================
"""
Squad-level Drop Zone consolidation (issue #44's "Additionally" ask):
"Best fit" (where the squad already tends to converge) and "Change it up"
(a deliberately different, still-viable alternative), derived from each
member's already-computed individual compute_drop_zone_signal read - no
new telemetry parsing here, just consolidation logic on top of the
per-player signal.

Design decisions, made after checking what the data actually supports
rather than assumed upfront:
- "Best fit" requires at least MIN_MEMBERS_FOR_CONSENSUS squad members to
  independently favor the same named POI **on the same map**. Votes are
  grouped at the POI level, not the exact ambiguity phrasing - a member
  reading "near the edge of Pochinki" and another reading "between
  Pochinki and School" both count toward Pochinki, since they're both
  genuinely gravitating toward that area even if their most-common
  landing wasn't identically classified. Below that threshold there's no
  real consensus, so this stays silent rather than crowning an arbitrary
  "winner" out of a 4-way tie of 1 vote each - same "don't overreach past
  what the data supports" standard as the per-player signal's
  MIN_MATCHES_FOR_SIGNAL gate.
- "Change it up" picks the named POI farthest from the "best fit" POI, on
  that same map, restricted to POIs at or above that map's median real
  landing count (map_regions_data.py's per-map validation data) - a
  genuinely different spot on the map, but not a token suggestion of a
  corner nobody actually plays (Zharki-tier).
- Works across every map drop_zone.py supports (see its MAP_POI_LOOKUP),
  not just Erangel - each member's top_zone_key already carries its own
  map (drop_zone.py qualifies it as "<map_name>||<zone_key>" specifically
  so several real POI names that collide across maps, e.g. "School" on
  both Erangel and Taego, "Ruins"/"Quarry" on both Erangel and Sanhok,
  never get merged into one vote just because the names match - votes are
  tallied per (map, poi) pair, and "change it up" looks up whichever map
  the winning vote actually came from rather than assuming one map.
"""
import math

from utils.drop_zone import MAP_POI_LOOKUP
from utils.map_regions_data import MAP_LANDING_VALIDATION_400M

MIN_MEMBERS_FOR_CONSENSUS = 2


def _map_and_poi_names_in_zone_key(zone_key):
    """A zone_key is "<map_name>||<rest>" (see drop_zone.py's
    compute_landing_read_from_events). <rest> names one POI for a
    confident or edge read, or two for a "between" read."""
    map_name, _, rest = zone_key.partition("||")
    if rest.startswith("between:"):
        return map_name, set(rest[len("between:"):].split("|"))
    if rest.startswith("edge:"):
        return map_name, {rest[len("edge:"):]}
    return map_name, {rest}


def compute_squad_drop_zone_consolidation(members):
    """members: list of dicts with "name" and "drop_zone_signal" (the
    dict compute_drop_zone_signal returns) already computed per member.

    Returns {"best_fit_line": str or None, "change_it_up_line": str or None}.
    Both are None if there isn't enough real consensus to say anything
    non-arbitrary.
    """
    votes = {}
    for member in members:
        signal = member.get("drop_zone_signal")
        if not signal or not signal["top_zone_key"]:
            continue
        map_name, pois = _map_and_poi_names_in_zone_key(signal["top_zone_key"])
        for poi in pois:
            votes.setdefault((map_name, poi), []).append(member["name"])

    if not votes:
        return {"best_fit_line": None, "change_it_up_line": None}

    (best_map, best_poi), backers = max(votes.items(), key=lambda kv: len(kv[1]))
    if len(backers) < MIN_MEMBERS_FOR_CONSENSUS:
        return {"best_fit_line": None, "change_it_up_line": None}

    best_fit_line = (
        f"Best fit: {best_poi} - {len(backers)} of {len(members)} squad members already tend to land there."
    )

    poi_coords = MAP_POI_LOOKUP.get(best_map)
    landing_validation = MAP_LANDING_VALIDATION_400M.get(best_map)
    if not poi_coords or not landing_validation or best_poi not in poi_coords:
        return {"best_fit_line": best_fit_line, "change_it_up_line": None}

    sorted_counts = sorted(landing_validation.values())
    median_count = sorted_counts[len(sorted_counts) // 2]
    viable_alternatives = [
        name for name, count in landing_validation.items()
        if count >= median_count and name != best_poi and name in poi_coords
    ]
    if not viable_alternatives:
        return {"best_fit_line": best_fit_line, "change_it_up_line": None}

    best_x, best_y = poi_coords[best_poi]
    farthest = max(
        viable_alternatives,
        key=lambda name: math.hypot(poi_coords[name][0] - best_x, poi_coords[name][1] - best_y),
    )
    change_it_up_line = f"Change it up: try {farthest} for a genuinely different (but still active) drop."

    return {"best_fit_line": best_fit_line, "change_it_up_line": change_it_up_line}
