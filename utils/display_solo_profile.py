# ==============================
# utils/display_solo_profile.py
# ==============================
from utils.display_archetype_tag import render_archetype_tag
from utils.display_combat_stats import render_kd_summary
from utils.display_headline_number import render_headline_number
from utils.display_last_match_brief import render_last_match_brief


def render_solo_profile(playername, archetype, headline, combat_stats, coaching, brief,
                         killer_intel_line=None, drop_zone_line=None, flow_line=None):
    print("=============================================")
    print(f"🧍 SOLO PROFILE - {playername}")
    print("=============================================")

    render_archetype_tag(archetype)
    render_headline_number(headline)
    render_kd_summary(combat_stats)

    if coaching["coaching_line"] or coaching["map_line"]:
        print()
        print("=============================")
        print("🎯 Coaching Note")
        print("=============================")
        if coaching["coaching_line"]:
            print(coaching["coaching_line"])
        if coaching["map_line"]:
            print(coaching["map_line"])

    if drop_zone_line or flow_line:
        print()
        print("=============================")
        print("🪂 Drop Zone + Flow")
        print("=============================")
        if drop_zone_line:
            print(drop_zone_line)
        if flow_line:
            print(flow_line)

    if brief:
        print()
        render_last_match_brief(playername, brief, show_squad_status=False, killer_intel_line=killer_intel_line)
