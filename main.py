# ==============================
# main CLI entry point
# ==============================
from api.player_stats import fetch_player_stats
from utils.io_helpers import save_json
from utils.display_stats_by_mode import render_ascii_table, load_player_stats
from utils.display_match_history import display_match_history

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
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
