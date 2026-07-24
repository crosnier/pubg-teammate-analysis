# ==============================
# utils/combat_stats.py
# ==============================
import glob
import json
import os

TELEMETRY_DIR = "match-telemetry"


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def compute_combat_stats_from_events(account_id, telemetry_documents):
    """Tally eliminations/deaths against real opponents from parsed telemetry.

    Environmental deaths (bluezone, falls, drowning) and suicides have no
    opposing player and are excluded, since the breakdown is keyed by
    opponent name.
    """
    eliminations = {}
    deaths = {}

    for telemetry in telemetry_documents:
        for event in telemetry:
            if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
                continue

            killer = event.get("killer") or {}
            victim = event.get("victim") or {}

            if killer.get("type") != "user" or victim.get("type") != "user":
                continue

            if killer.get("accountId") == account_id and victim.get("accountId") != account_id:
                name = victim.get("name", "Unknown")
                eliminations[name] = eliminations.get(name, 0) + 1

            if victim.get("accountId") == account_id and killer.get("accountId") != account_id:
                name = killer.get("name", "Unknown")
                deaths[name] = deaths.get(name, 0) + 1

    return {
        "total_eliminations": sum(eliminations.values()),
        "total_deaths": sum(deaths.values()),
        "eliminations_breakdown": dict(sorted(eliminations.items(), key=lambda kv: kv[1], reverse=True)),
        "deaths_breakdown": dict(sorted(deaths.items(), key=lambda kv: kv[1], reverse=True)),
    }


def compute_combat_stats(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR):
    documents = list(_load_telemetry_files(match_ids, telemetry_dir))
    stats = compute_combat_stats_from_events(account_id, documents)
    stats["matches_analyzed"] = len(documents)
    return stats
