# ==============================
# solo CLI entry point - narrative single-player profile
# ==============================
"""
Profile a single player with the same narrative Mode 1 slots as squad.py's
per-teammate cards (Archetype Tag, Headline Number, Last Match Brief, K/D) -
no raw stats table, no full match history, no full combat breakdown. Those
stay available via main.py, which is untouched.

Squad Read's capstone comparison line has no solo equivalent (nothing to
compare against), so this profile has no capstone line - see issue #40.
"""
import argparse
import asyncio

from api.player_stats import fetch_player_and_match_ids
from api.rate_limiter import player_api_queue
from api.telemetry_fetcher import fetch_telemetry_for_matches
from utils.archetype_tag import compute_archetype_tag
from utils.combat_stats import compute_combat_stats
from utils.display_drop_zone import format_drop_zone_line, format_flow_line
from utils.drop_zone import compute_drop_zone_signal
from utils.headline_number import compute_headline_number
from utils.killer_intel import compute_killer_intel, format_killer_intel
from utils.last_match_brief import find_latest_match_for_player, compute_last_match_brief
from utils.match_scope import select_scoped_match_ids
from utils.movement_flow import compute_flow_signal
from utils.solo_coaching import compute_solo_coaching
from utils.display_solo_profile import render_solo_profile


async def run(playername):
    try:
        await _run(playername)
    finally:
        await player_api_queue.close()


async def _run(playername):
    player_id, match_ids, team_mode_match_ids = await fetch_player_and_match_ids(playername)
    print(f"[SUCCESS] Stats saved for '{playername}' (account ID: {player_id})")

    print()
    print(f"[INFO] Fetching telemetry for {len(match_ids)} matches...")
    await fetch_telemetry_for_matches(match_ids)

    scoped_match_ids = set(select_scoped_match_ids(match_ids))
    team_mode_scoped_ids = set(select_scoped_match_ids(team_mode_match_ids))

    archetype = compute_archetype_tag(player_id, match_ids=scoped_match_ids, team_mode_match_ids=team_mode_scoped_ids)
    headline = compute_headline_number(player_id, match_ids=scoped_match_ids)
    combat_stats = compute_combat_stats(player_id, match_ids=scoped_match_ids)
    coaching = compute_solo_coaching(player_id, headline, scoped_match_ids)
    drop_zone_signal = compute_drop_zone_signal(player_id, match_ids=scoped_match_ids)
    drop_zone_line = format_drop_zone_line(drop_zone_signal)
    flow_signal = compute_flow_signal(player_id, match_ids=scoped_match_ids)
    flow_line = format_flow_line(flow_signal)

    latest_match_id, latest_events = find_latest_match_for_player(player_id, match_ids)
    brief = compute_last_match_brief(player_id, latest_match_id, latest_events) if latest_match_id else None
    killer_intel_line = None
    if brief:
        killer_intel = compute_killer_intel(latest_events, brief["death_info"])
        killer_intel_line = format_killer_intel(killer_intel)

    print("\n\n")
    render_solo_profile(playername, archetype, headline, combat_stats, coaching, brief,
                         killer_intel_line, drop_zone_line, flow_line)


def main():
    parser = argparse.ArgumentParser(description="Profile a single player with narrative Mode 1 slots.")
    parser.add_argument("playername", help="The PUBG player name to profile")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.playername))
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
