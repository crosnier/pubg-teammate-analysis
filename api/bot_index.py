# ==============================
# api/bot_index.py
# ==============================
#
# Separate from player_index.py on purpose: bots are never real teammates,
# so this only tracks identity and encounter history for pattern analysis
# (see issues #8, #9), not the social/rapport fields player_index carries.

import json
from datetime import datetime
from pathlib import Path

BOT_INDEX_PATH = Path("bot-index.json")


def load_bot_index():
    if BOT_INDEX_PATH.exists():
        with open(BOT_INDEX_PATH, "r") as f:
            return json.load(f)
    return {}


def save_bot_index(index_data):
    with open(BOT_INDEX_PATH, "w") as f:
        json.dump(index_data, f, indent=2)


def update_bot_index(bots, match_id):
    """Record bots detected in a match into the persistent bot index.

    `bots` is an {accountId: name} mapping, as returned by
    utils.bot_detection.detect_bots.
    """
    index = load_bot_index()
    today = datetime.now().strftime("%Y-%m-%d")

    for account_id, name in bots.items():
        if account_id not in index:
            index[account_id] = {
                "playername": name,
                "first_seen": today,
                "last_seen": today,
                "matches_seen": [match_id],
                "times_seen": 1,
            }
        else:
            entry = index[account_id]
            entry["playername"] = name
            entry["last_seen"] = today
            if match_id not in entry["matches_seen"]:
                entry["matches_seen"].append(match_id)
            entry["times_seen"] = len(entry["matches_seen"])

    save_bot_index(index)
    return index
