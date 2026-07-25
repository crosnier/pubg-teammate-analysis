# ==============================
# main CLI entry point
# ==============================
from api.player_stats import fetch_player_and_match_ids
from api.rate_limiter import player_api_queue
from utils.display_stats_by_mode import render_ascii_table, load_player_stats
from utils.display_match_history import display_match_history
from api.telemetry_fetcher import fetch_telemetry_for_matches
from utils.combat_stats import compute_combat_stats
from utils.display_combat_stats import render_combat_stats
from utils.bot_detection import find_latest_match, detect_bots
from utils.display_bot_stats import render_bot_summary
from api.bot_index import update_bot_index
from utils.last_match_brief import find_latest_match_for_player, compute_last_match_brief
from utils.display_last_match_brief import render_last_match_brief
from utils.archetype_tag import compute_archetype_tag
from utils.display_archetype_tag import render_archetype_tag
from utils.headline_number import compute_headline_number
from utils.display_headline_number import render_headline_number
from utils.match_scope import select_scoped_match_ids
import asyncio


import argparse

async def run(playername):
    try:
        await _run(playername)
    finally:
        await player_api_queue.close()

async def _run(playername):
    player_id, match_ids, team_mode_match_ids = await fetch_player_and_match_ids(playername)
    print(f"[SUCCESS] Stats saved for '{playername}' (account ID: {player_id})")
    print()
    print()

    # Display stats as ASCII table
    stats = load_player_stats(f"playerstats/{playername}.json")
    render_ascii_table(stats, playername)

    # Display match history grouped by mode
    print("\n\n")
    display_match_history(playername)

    print()
    print()
    print(f"[INFO] Fetching telemetry for {len(match_ids)} matches...")
    await fetch_telemetry_for_matches(match_ids)

    # Display combat stats mined from cached telemetry
    print("\n\n")
    combat_stats = compute_combat_stats(player_id, match_ids=match_ids)
    render_combat_stats(combat_stats)

    # Resolve the player's scoped match set once and reuse it across both
    # signal computations below, rather than each one independently
    # rescanning the telemetry cache. match_ids (this player's own known
    # matches, from the player-stats API response above) is the candidate
    # list - never the whole shared cache, which holds other players' too.
    scoped_match_ids = set(select_scoped_match_ids(match_ids))
    team_mode_scoped_ids = set(select_scoped_match_ids(team_mode_match_ids))

    # Display Archetype Tag (tempo + range + weapon signature) mined from cached telemetry
    print("\n\n")
    archetype = compute_archetype_tag(player_id, match_ids=scoped_match_ids, team_mode_match_ids=team_mode_scoped_ids)
    render_archetype_tag(archetype)

    # Display the Headline Number: one differentiating, confidence-gated stat
    print("\n\n")
    headline = compute_headline_number(player_id, match_ids=scoped_match_ids)
    render_headline_number(headline)

    # Last Match section: brief for this player, then bot detection for
    # whichever cached match is most recent overall (a stand-in for "your"
    # last match until Phase 3 auto-detection establishes a real self-identity)
    print("\n\n")
    latest_match_id, latest_events = find_latest_match()

    player_match_id, player_events = find_latest_match_for_player(player_id, match_ids)
    if player_match_id:
        brief = compute_last_match_brief(player_id, player_match_id, player_events)
        played_with_you = (player_match_id == latest_match_id) if latest_match_id else None
        render_last_match_brief(playername, brief, played_with_you)

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
