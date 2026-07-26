# ==============================
# utils/display_squad_roster.py
# ==============================
from utils.display_archetype_tag import render_archetype_tag
from utils.display_combat_stats import render_kd_summary
from utils.display_headline_number import render_headline_number

NAME_WIDTH = 14
TAG_WIDTH = 24


def render_squad_roster(roster):
    print("=============================================")
    print("🎮 SQUAD ROSTER")
    print("=============================================")

    for row in roster["roster_rows"]:
        tempo = row["tempo_tag"] or "Not enough data"
        tag = row["short_tag"] or "-"
        print(f"  {row['name'].ljust(NAME_WIDTH)}{tempo.ljust(TAG_WIDTH)}{tag}")

    print()
    print("🤝 Squad Read:", roster["coverage_summary"] or "Not enough data yet for a squad read.")

    if roster["bolstered_line"]:
        print()
        print(roster["bolstered_line"])

    if roster["drop_zone_best_fit_line"]:
        print()
        print("🪂", roster["drop_zone_best_fit_line"])
        if roster["drop_zone_change_it_up_line"]:
            print("🪂", roster["drop_zone_change_it_up_line"])

    print("=============================================")


def render_full_squad_cards(members, archetypes, headlines, combat_stats, drop_zone_lines=None, flow_lines=None):
    """Full per-player cards after the roster summary. Teammates render
    first, then "you" last regardless of argument order - the running
    user's own card is the one they already know, so it reads better as
    the closer than the opener."""
    drop_zone_lines = drop_zone_lines or {}
    flow_lines = flow_lines or {}
    ordered = members[1:] + [members[0]]
    for i, member in enumerate(ordered):
        is_self = (i == len(ordered) - 1)
        key = member["name"]
        display_name = "You" if is_self else key
        print()
        print("=============================================")
        print(f"👤 {display_name}")
        print("=============================================")
        render_archetype_tag(archetypes[key])
        render_headline_number(headlines[key])
        render_kd_summary(combat_stats[key])

        drop_zone_line = drop_zone_lines.get(key)
        flow_line = flow_lines.get(key)
        if drop_zone_line or flow_line:
            print()
            print("=============================")
            print("🪂 Drop Zone + Flow")
            print("=============================")
            if drop_zone_line:
                print(drop_zone_line)
            if flow_line:
                print(flow_line)
