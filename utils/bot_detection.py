# ==============================
# utils/bot_detection.py
# ==============================
import glob
import json
import os

TELEMETRY_DIR = "match-telemetry"


def _load_telemetry_files(telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        with open(path, "r") as f:
            yield match_id, json.load(f)


def find_latest_match(telemetry_dir=TELEMETRY_DIR):
    """Return (match_id, events) for the most recently played cached match.

    Recency is read from each match's LogMatchStart timestamp rather than
    match ID ordering, since PUBG match IDs aren't sortable by time.
    """
    latest_timestamp = None
    latest_match_id = None
    latest_events = None

    for match_id, events in _load_telemetry_files(telemetry_dir):
        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event:
            continue
        timestamp = start_event.get("_D")
        if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
            latest_timestamp = timestamp
            latest_match_id = match_id
            latest_events = events

    return latest_match_id, latest_events


def detect_bots(telemetry_events):
    """Return {accountId: name} for AI-controlled players in a match.

    Bots are identified by "type": "user_ai" on LogPlayerCreate's character.
    """
    bots = {}
    for event in telemetry_events:
        if event.get("_T") != "LogPlayerCreate":
            continue
        character = event.get("character") or {}
        if character.get("type") == "user_ai":
            account_id = character.get("accountId")
            if account_id:
                bots[account_id] = character.get("name", "Unknown")
    return bots
