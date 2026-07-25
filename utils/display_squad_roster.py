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

    print("=============================================")


def render_full_squad_cards(members, archetypes, headlines, combat_stats):
    """Full per-player cards after the roster summary. Teammates render
    first, then "you" last regardless of argument order - the running
    user's own card is the one they already know, so it reads better as
    the closer than the opener."""
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
