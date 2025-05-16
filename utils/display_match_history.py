# utils/display_match_history.py

import os
import json
from collections import defaultdict

def print_static_banner(playername=None):
    box_width = 45
    title = f"{playername} Match History" if playername else "Player Match History"
    padding = (box_width - len(title)) // 2
    padded_title = f"{' ' * padding}{title}{' ' * (box_width - len(title) - padding)}"

    print("╔" + "═" * box_width + "╗")
    print(f"║{padded_title}║")
    print("╚" + "═" * box_width + "╝\n")


GAME_MODE_KEYS = [
    "solo-fpp", "duo-fpp", "squad-fpp",
    "solo", "duo", "squad"
]

OTHER_MODE_LABEL = "⛔ Other Modes"


def load_player_stats(playername):
    filepath = f"playerstats/{playername}.json"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing stats file: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)


def extract_match_ids_by_mode(stats):
    relationships = stats["data"]["relationships"]
    mode_matches = defaultdict(list)

    for key in relationships:
        if key.startswith("matches"):
            # Derive the mode name (e.g., "SoloFPP" → "solo-fpp")
            raw_mode = key.replace("matches", "")
            mode = raw_mode.lower().replace("fpp", "-fpp").strip("-")
            if mode == "":
                mode = "unknown"

            match_ids = [entry["id"] for entry in relationships[key].get("data", [])]
            mode_matches[mode].extend(match_ids)

    return mode_matches


def display_match_history(playername):
    print_static_banner(playername)
    raw = load_player_stats(playername)
    matches_by_mode = extract_match_ids_by_mode(raw)

    empty_modes = []

    for mode in GAME_MODE_KEYS:
        match_ids = matches_by_mode.get(mode, [])
        if not match_ids:
            empty_modes.append(mode)
            continue

        header = f"🕹️ {mode.upper()} Matches (Most Recent First)"
        print("=" * len(header))
        print(header)
        print("=" * len(header))
        print(f"Total Matches: {len(match_ids)}")
        print()

        for match_id in match_ids:
            print(f"  • Match ID: {match_id}")
        print()

    # Other Modes section
    if empty_modes:
        print("=" * 40)
        print(OTHER_MODE_LABEL)
        print("=" * 40)
        for mode in empty_modes:
            print(f"{mode.ljust(14)} → No matches")
