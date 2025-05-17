# ==============================
# main CLI entry point
# ==============================
from api.player_stats import fetch_player_stats
from utils.io_helpers import save_json
from utils.display_stats_by_mode import render_ascii_table, load_player_stats
from utils.display_match_history import display_match_history
from api.telemetry_fetcher import fetch_telemetry_for_matches
import asyncio


import argparse

def main():
    parser = argparse.ArgumentParser(description="Query and save PUBG lifetime player stats.")
    parser.add_argument("playername", help="The PUBG player name to query")
    args = parser.parse_args()

    try:
        data, player_id = fetch_player_stats(args.playername)
        save_json(data, f"playerstats/{args.playername}.json")
        print(f"[SUCCESS] Stats saved for '{args.playername}' (account ID: {player_id})")
        print()
        print()
        
        # Display stats as ASCII table
        stats = load_player_stats(f"playerstats/{args.playername}.json")
        render_ascii_table(stats, args.playername)

        # Display match history grouped by mode
        print("\n\n")
        display_match_history(args.playername)

        # Fetch telemetry for all matches
        match_ids = []
        relationships = data["data"]["relationships"]
        for key in relationships:
            if key.startswith("matches"):
                match_ids.extend([entry["id"] for entry in relationships[key].get("data", [])])

        print()
        print()
        print(f"[INFO] Fetching telemetry for {len(match_ids)} matches...")
        #asyncio.run(fetch_telemetry_for_matches(match_ids)) # Temporarily Disabled until Rate Limiting Deployed - IP Ban Risk!!! crap.
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
