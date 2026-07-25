# ==============================
# utils/last_match_brief.py
# ==============================
import glob
import json
import os
from datetime import datetime

TELEMETRY_DIR = "match-telemetry"

WEAPON_PREFIX = "Weap"
MELEE_CAUSERS = {"PlayerFemale_A", "PlayerMale_A"}
VEHICLE_HINTS = ("Uaz", "Dacia", "Mirado", "Coupe", "PickupTruck", "Buggy", "Motorbike", "Rony", "Van", "Scooter")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# How close in time two teammates' deaths need to be to read as "went down
# in the same fight" rather than "dead earlier, unrelated". Checked against
# real teammate-death-gap timing across 250 cached squad matches (10,744
# gaps): the distribution has no clean bimodal split, but its p60 (~29s)
# lines up closely with QUICK_KILL_WINDOW_SECONDS in tempo_signal.py (30s,
# separately calibrated at ~p60 of the contact-to-kill gap) - reusing the
# same window keeps "quick/connected" framed consistently project-wide
# rather than picking a second, unrelated constant for a similar question.
SAME_ENGAGEMENT_WINDOW_SECONDS = 30


def _load_telemetry_files(telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        with open(path, "r") as f:
            yield match_id, json.load(f)


def find_latest_match_for_player(account_id, telemetry_dir=TELEMETRY_DIR):
    """Return (match_id, events) for the player's most recently played cached match.

    Same LogMatchStart-timestamp approach as bot_detection.find_latest_match,
    but scoped to matches the given account actually appears in.
    """
    latest_timestamp = None
    latest_match_id = None
    latest_events = None

    for match_id, events in _load_telemetry_files(telemetry_dir):
        if not player_present_in_match(account_id, events):
            continue

        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event:
            continue

        timestamp = start_event.get("_D")
        if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
            latest_timestamp = timestamp
            latest_match_id = match_id
            latest_events = events

    return latest_match_id, latest_events


def player_present_in_match(account_id, events):
    return any(
        e.get("_T") == "LogPlayerCreate" and (e.get("character") or {}).get("accountId") == account_id
        for e in events
    )


def _clean_weapon_name(causer_name):
    """Best-effort readable name for a telemetry damageCauserName.

    Covers guns (the common case) precisely; vehicles, throwables, and
    melee get a general label; anything unrecognized falls back to a
    de-prefixed, space-separated version of the raw asset name rather than
    a hard failure.
    """
    if not causer_name:
        return "Unknown"

    name = causer_name[:-2] if causer_name.endswith("_C") else causer_name

    if name.startswith(WEAPON_PREFIX):
        return name[len(WEAPON_PREFIX):]
    if name in MELEE_CAUSERS:
        return "Melee"
    if "Grenade" in name:
        return "Grenade"
    if "Molotov" in name:
        return "Molotov Cocktail"
    if any(hint in name for hint in VEHICLE_HINTS):
        return "Vehicle"

    return name.replace("BP_", "").replace("_", " ").strip() or "Unknown"


def _parse_timestamp(value):
    return datetime.strptime(value, _TIMESTAMP_FORMAT) if value else None


def _compute_squad_status_at_death(account_id, events, player_death_ts):
    """Which squadmates were still alive when this player died, and which
    were already down before it - and if already down, whether that was
    part of the same fight or unrelated.

    Returns None when there's nothing meaningful to report: the player
    survived to match end (no death to anchor the comparison), or no other
    real-player teammates share their teamId (solo, or squad never loaded
    in for this cached match).
    """
    if player_death_ts is None:
        return None

    team_id = next(
        (
            (e.get("character") or {}).get("teamId")
            for e in events
            if e.get("_T") == "LogPlayerCreate" and (e.get("character") or {}).get("accountId") == account_id
        ),
        None,
    )
    if team_id is None:
        return None

    teammates = {}
    for event in events:
        if event.get("_T") != "LogPlayerCreate":
            continue
        character = event.get("character") or {}
        if character.get("type") != "user" or character.get("teamId") != team_id:
            continue
        teammate_id = character.get("accountId")
        if teammate_id != account_id:
            teammates[teammate_id] = character.get("name", "Unknown")

    if not teammates:
        return None

    death_ts_by_teammate = {}
    for event in events:
        if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
            continue
        killer = event.get("killer") or {}
        victim = event.get("victim") or {}
        victim_id = victim.get("accountId")
        if killer.get("type") != "user" or victim.get("type") != "user" or victim_id not in teammates:
            continue
        ts = _parse_timestamp(event.get("_D"))
        if victim_id not in death_ts_by_teammate or ts < death_ts_by_teammate[victim_id]:
            death_ts_by_teammate[victim_id] = ts

    squad_status = []
    for teammate_id, name in teammates.items():
        teammate_death_ts = death_ts_by_teammate.get(teammate_id)

        if teammate_death_ts is None or teammate_death_ts > player_death_ts:
            squad_status.append({"name": name, "status": "alive"})
            continue

        seconds_before = round((player_death_ts - teammate_death_ts).total_seconds(), 1)
        status = "same_engagement" if seconds_before <= SAME_ENGAGEMENT_WINDOW_SECONDS else "eliminated_earlier"
        squad_status.append({"name": name, "status": status, "seconds_before": seconds_before})

    return squad_status


def compute_last_match_brief(account_id, match_id, events):
    match_start = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
    match_end = next((e for e in events if e.get("_T") == "LogMatchEnd"), None)
    start_ts = _parse_timestamp(match_start.get("_D")) if match_start else None

    round_rank = None
    if match_end:
        entry = next(
            (c for c in match_end.get("characters", []) if (c.get("character") or {}).get("accountId") == account_id),
            None,
        )
        if entry:
            round_rank = entry["character"].get("ranking")

    kill_count = 0
    weapon_counts = {}
    death_info = None
    death_ts = None

    for event in events:
        if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
            continue

        killer = event.get("killer") or {}
        victim = event.get("victim") or {}
        if killer.get("type") != "user" or victim.get("type") != "user":
            continue

        if killer.get("accountId") == account_id and victim.get("accountId") != account_id:
            kill_count += 1
            weapon = _clean_weapon_name((event.get("killerDamageInfo") or {}).get("damageCauserName"))
            weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1

        if victim.get("accountId") == account_id and killer.get("accountId") != account_id:
            kdi = event.get("killerDamageInfo") or {}
            death_info = {
                "killed_by": killer.get("name", "Unknown"),
                "weapon": _clean_weapon_name(kdi.get("damageCauserName")),
                "distance_m": round(kdi.get("distance", 0) / 100, 1),
            }
            death_ts = _parse_timestamp(event.get("_D"))

    most_used_weapon = max(weapon_counts, key=weapon_counts.get) if weapon_counts else None

    end_ts = death_ts or (_parse_timestamp(match_end.get("_D")) if match_end else None)
    time_alive_seconds = int((end_ts - start_ts).total_seconds()) if start_ts and end_ts else None

    squad_status = _compute_squad_status_at_death(account_id, events, death_ts)

    return {
        "match_id": match_id,
        "round_rank": round_rank,
        "time_alive_seconds": time_alive_seconds,
        "kill_count": kill_count,
        "most_used_weapon": most_used_weapon,
        "death_info": death_info,
        "squad_status": squad_status,
    }
