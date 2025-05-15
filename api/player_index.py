# api/player_index.py

import os
import json
from datetime import datetime
from pathlib import Path

INDEX_PATH = Path("player-index.json")


def load_player_index():
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r") as f:
            return json.load(f)
    return {}


def save_player_index(index_data):
    with open(INDEX_PATH, "w") as f:
        json.dump(index_data, f, indent=2)


def normalize_filename(name):
    return name.strip().lower().replace(" ", "")


def update_player_index(account_id, playername):
    index = load_player_index()

    normalized_name = normalize_filename(playername)
    stats_file = f"playerstats/{normalized_name}.json"

    if account_id not in index:
        index[account_id] = {
            "playername": playername,
            "last_seen": datetime.now().strftime("%Y-%m-%d"),
            "stats_file": stats_file
        }
    else:
        index[account_id].update({
            "playername": playername,
            "last_seen": datetime.now().strftime("%Y-%m-%d"),
            "stats_file": stats_file
        })

    save_player_index(index)


def get_player_record(account_id):
    index = load_player_index()
    return index.get(account_id)