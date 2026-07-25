# ==============================
# utils/solo_coaching.py
# ==============================
"""
Solo Coaching Note: solo.py's stand-in for Squad Read's capstone line, which
has no meaning without a teammate to compare against (see issue #40). Same
two-line shape as Squad Read - a general read (here: the Headline Number's
already-chosen stat, reframed as second-person coaching) plus a data-backed
bolstered line (here: a per-map performance callout), only shown when it
clears the same MIN_MATCHES_FOR_SIGNAL=8 confidence bar used everywhere else
in this tool.

Map-based coaching was validated against real cached data before building:
mapName is reliably present in telemetry, and per-map performance does vary
meaningfully for a real player - but most players won't have 8+ cached
matches on any single map, so the map line is expected to often not appear.
That's the same confidence-gating philosophy as the rest of the project, not
a bug.
"""
import glob
import json
import os
import statistics

from utils.headline_number import MIN_MATCHES_FOR_CANDIDATE
from utils.last_match_brief import player_present_in_match

TELEMETRY_DIR = "match-telemetry"

# Same MIN_*_FOR_SIGNAL=8 convention used across tempo/range/weapon/headline.
MIN_MATCHES_FOR_MAP_SIGNAL = MIN_MATCHES_FOR_CANDIDATE

# How far a map's average damage has to deviate from the player's own
# overall average before it's worth calling out - guards against noise in
# a map bucket that's technically over the match-count bar but still close
# to the player's normal performance.
MAP_DEVIATION_THRESHOLD = 0.20

MAP_DISPLAY_NAMES = {
    "Baltic_Main": "Erangel",
    "Desert_Main": "Miramar",
    "Savage_Main": "Sanhok",
    "DihorOtok_Main": "Vikendi",
    "Summerland_Main": "Karakin",
    "Tiger_Main": "Taego",
    "Kiki_Main": "Deston",
    "Neon_Main": "Rondo",
    "Chimera_Main": "Paramo",
    "Heaven_Main": "Haven",
    "Range_Main": "Camp Jackal",
}

COACHING_BY_STAT_KEY = {
    "kills_before_death": (
        "You keep the pressure on once a fight starts - lean into staying "
        "aggressive after your first kill instead of playing it safe."
    ),
    "revives": (
        "You're a support anchor - keep prioritizing revives and squad "
        "positioning over solo pushes."
    ),
    "damage": (
        "You put out consistent damage match to match - work on converting "
        "more of that damage into confirmed kills."
    ),
}


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def _map_display_name(map_name):
    return MAP_DISPLAY_NAMES.get(map_name, map_name)


def compute_coaching_line(headline):
    """Reframe the Headline Number's already-chosen stat as a second-person
    coaching note - no new computation, just a different lens on data
    already trusted enough to headline."""
    stat_key = headline.get("stat_key")
    value = headline.get("value")

    if stat_key in COACHING_BY_STAT_KEY:
        return COACHING_BY_STAT_KEY[stat_key]

    if stat_key == "close_range_win_rate" and value is not None:
        if value >= 0.5:
            return (
                "You win close-range fights more often than not - trust "
                "your instinct to push in close."
            )
        return (
            "Close-range fights are costing you - consider disengaging "
            "earlier or repositioning before committing to one."
        )

    if stat_key == "knockdown_conversion_rate" and value is not None:
        if value >= 0.5:
            return (
                "You finish what you start - once someone's knocked down, "
                "trust yourself to close it out."
            )
        return (
            "You knock people down but don't always finish - follow up "
            "faster to secure the kill before they get revived."
        )

    return None


def compute_map_line(account_id, match_ids, telemetry_dir=TELEMETRY_DIR):
    """Bolstered per-map damage callout - the single most extreme map that
    clears both the match-count bar and the deviation threshold, or None if
    nothing qualifies."""
    damage_by_map = {}
    overall_damage = []

    for events in _load_telemetry_files(match_ids, telemetry_dir):
        if not player_present_in_match(account_id, events):
            continue
        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event:
            continue
        map_name = start_event.get("mapName")
        if not map_name:
            continue

        damage = 0
        for event in events:
            if event.get("_T") != "LogPlayerTakeDamage":
                continue
            attacker = event.get("attacker") or {}
            victim = event.get("victim") or {}
            if attacker.get("accountId") == account_id and attacker.get("type") == "user" \
                    and victim.get("type") == "user" and victim.get("accountId") != account_id:
                damage += event.get("damage", 0)

        damage_by_map.setdefault(map_name, []).append(damage)
        overall_damage.append(damage)

    if len(overall_damage) < MIN_MATCHES_FOR_CANDIDATE:
        return None

    overall_mean = statistics.mean(overall_damage)
    if overall_mean == 0:
        return None

    candidates = []
    for map_name, values in damage_by_map.items():
        if len(values) < MIN_MATCHES_FOR_MAP_SIGNAL:
            continue
        map_mean = statistics.mean(values)
        deviation = (map_mean - overall_mean) / overall_mean
        if abs(deviation) >= MAP_DEVIATION_THRESHOLD:
            candidates.append((abs(deviation), deviation, map_name, map_mean, len(values)))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0], reverse=True)
    _, deviation, map_name, map_mean, matches_on_map = candidates[0]
    label = _map_display_name(map_name)

    if deviation > 0:
        return (
            f"You average {map_mean:.0f} damage per match on {label}, well above your "
            f"{overall_mean:.0f} overall average ({matches_on_map} matches there) - lean into drops there."
        )
    return (
        f"You average {map_mean:.0f} damage per match on {label}, below your "
        f"{overall_mean:.0f} overall average ({matches_on_map} matches there) - worth extra caution there."
    )


def compute_solo_coaching(account_id, headline, match_ids, telemetry_dir=TELEMETRY_DIR):
    return {
        "coaching_line": compute_coaching_line(headline),
        "map_line": compute_map_line(account_id, match_ids, telemetry_dir=telemetry_dir),
    }
