# ==============================
# utils/display_squad_roster.py
# ==============================
from utils.display_archetype_tag import render_archetype_tag
from utils.display_headline_number import render_headline_number

NAME_WIDTH = 14
TAG_WIDTH = 24


def render_squad_roster(roster):
    print("=============================================")
    print("🎮 SQUAD ROSTER - At a Glance")
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


def render_full_squad_cards(members, archetypes, headlines):
    """Full per-player 5-slot cards after the roster summary - members[0]
    is "you", already shown in the roster table above so only teammates
    get a full card here (matches the design doc's mockup)."""
    for member in members[1:]:
        name = member["name"]
        print()
        print(f"--- {name} ---")
        render_archetype_tag(archetypes[name])
        render_headline_number(headlines[name])
