# ==============================
# main CLI entry point
# ==============================
from api.player_stats import fetch_player_stats
from api.rate_limiter import player_api_queue
from utils.io_helpers import save_json
from utils.display_stats_by_mode import render_ascii_table, load_player_stats
from utils.display_match_history import display_match_history
from api.telemetry_fetcher import fetch_telemetry_for_matches
from utils.combat_stats import compute_combat_stats
from utils.display_combat_stats import render_combat_stats
from utils.bot_detection import find_latest_match, detect_bots
from utils.display_bot_stats import render_bot_summary
from api.bot_index import update_bot_index
import asyncio


import argparse

async def run(playername):
    try:
        await _run(playername)
    finally:
        await player_api_queue.close()

async def _run(playername):
    data, player_id = await fetch_player_stats(playername)
    save_json(data, f"playerstats/{playername}.json")
    print(f"[SUCCESS] Stats saved for '{playername}' (account ID: {player_id})")
    print()
    print()

    # Display stats as ASCII table
    stats = load_player_stats(f"playerstats/{playername}.json")
    render_ascii_table(stats, playername)

    # Display match history grouped by mode
    print("\n\n")
    display_match_history(playername)

    # Fetch telemetry for all matches
    match_ids = []
    relationships = data["data"]["relationships"]
    for key in relationships:
        if key.startswith("matches"):
            match_ids.extend([entry["id"] for entry in relationships[key].get("data", [])])

    print()
    print()
    print(f"[INFO] Fetching telemetry for {len(match_ids)} matches...")
    await fetch_telemetry_for_matches(match_ids)

    # Display combat stats mined from cached telemetry
    print("\n\n")
    combat_stats = compute_combat_stats(player_id)
    render_combat_stats(combat_stats)

    # Detect bots in the most recently played match and record them
    print("\n\n")
    latest_match_id, latest_events = find_latest_match()
    if latest_match_id:
        bots = detect_bots(latest_events)
        update_bot_index(bots, latest_match_id)
        render_bot_summary(latest_match_id, bots)

def main():
    parser = argparse.ArgumentParser(description="Query and save PUBG lifetime player stats.")
    parser.add_argument("playername", help="The PUBG player name to query")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.playername))
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
