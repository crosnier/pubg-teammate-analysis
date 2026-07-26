# ==============================
# squad CLI entry point - profile an entire squad at once
# ==============================
"""
Profile a whole squad (2+ players) in one run: fetches/refreshes each
player's stats concurrently, shares one deduplicated telemetry fetch
across the whole squad (a match two teammates played together only needs
pulling once), then renders the Squad Roster - a coverage/distribution
summary plus a full Archetype Tag + Headline Number card per teammate.

Kept as a genuinely separate entry point from main.py rather than a mode
switch inside it, so the single-player flow (main.py <playername>) stays
completely untouched.
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
from utils.match_scope import select_scoped_match_ids
from utils.movement_flow import compute_flow_signal
from utils.squad_roster import compute_squad_roster
from utils.display_squad_roster import render_squad_roster, render_full_squad_cards


async def run(playernames):
    try:
        await _run(playernames)
    finally:
        await player_api_queue.close()


async def _run(playernames):
    # Concurrent player-stats fetch across the squad - safe today since
    # api/rate_limiter.py's queue already serializes the actual HTTP calls
    # via an asyncio.Lock regardless of how many callers use it at once.
    fetched = await asyncio.gather(*(fetch_player_and_match_ids(name) for name in playernames))

    members = []
    for name, (account_id, match_ids, team_mode_match_ids) in zip(playernames, fetched):
        print(f"[SUCCESS] Stats saved for '{name}' (account ID: {account_id})")
        members.append({
            "name": name,
            "account_id": account_id,
            "match_ids": match_ids,
            "team_mode_match_ids": team_mode_match_ids,
        })

    # One combined, deduplicated telemetry fetch for the whole squad - a
    # match two teammates played together only needs pulling once
    # (fetch_telemetry_for_matches already skips already-cached matches),
    # and this keeps the per-run new-match cap meaningful for the squad as
    # a whole rather than effectively multiplying it by squad size.
    all_match_ids = set()
    for m in members:
        all_match_ids.update(m["match_ids"])
    print()
    print(f"[INFO] Fetching telemetry for {len(all_match_ids)} unique matches across {len(playernames)} players...")
    await fetch_telemetry_for_matches(list(all_match_ids))

    archetypes = {}
    headlines = {}
    combat_stats = {}
    drop_zone_lines = {}
    flow_lines = {}
    for i, m in enumerate(members):
        scoped = set(select_scoped_match_ids(m["match_ids"]))
        team_mode_scoped = set(select_scoped_match_ids(m["team_mode_match_ids"]))
        possessive = "your" if i == 0 else "their"
        archetype = compute_archetype_tag(m["account_id"], match_ids=scoped, team_mode_match_ids=team_mode_scoped)
        m["archetype"] = archetype
        archetypes[m["name"]] = archetype
        headlines[m["name"]] = compute_headline_number(m["account_id"], match_ids=scoped, possessive=possessive)
        combat_stats[m["name"]] = compute_combat_stats(m["account_id"], match_ids=scoped)

        drop_zone_signal = compute_drop_zone_signal(m["account_id"], match_ids=scoped)
        m["drop_zone_signal"] = drop_zone_signal
        drop_zone_lines[m["name"]] = format_drop_zone_line(drop_zone_signal)
        flow_signal = compute_flow_signal(m["account_id"], match_ids=scoped)
        flow_lines[m["name"]] = format_flow_line(flow_signal)

    roster = compute_squad_roster(members)

    print("\n\n")
    render_squad_roster(roster)
    render_full_squad_cards(members, archetypes, headlines, combat_stats, drop_zone_lines, flow_lines)


def main():
    parser = argparse.ArgumentParser(description="Profile a full squad (2+ players) at once.")
    parser.add_argument("playernames", nargs="+", help="PUBG player names in the squad, you first")
    args = parser.parse_args()

    if len(args.playernames) < 2:
        print("[ERROR] Provide at least 2 player names for a squad lookup (you first, then teammates).")
        return

    try:
        asyncio.run(run(args.playernames))
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
