# ==============================
# utils/display_archetype_tag.py
# ==============================


def render_archetype_tag(archetype):
    print("=============================")
    print("🏷️  Archetype Tag")
    print("=============================")

    tempo = archetype["tempo"]
    range_signal = archetype["range"]
    weapon = archetype["weapon"]

    tempo_line = tempo["tempo_tag"] or "Not enough data"
    if tempo["tempo_tag"]:
        tempo_line += f"  ({tempo['matches_with_contact']}/{tempo['matches_analyzed']} matches with contact)"
    print(f"Tempo  : {tempo_line}")

    range_bucket = range_signal["range_bucket"]
    if range_bucket:
        print(f"Range  : {range_bucket}  (median {range_signal['median_distance_m']}m over {range_signal['kills_analyzed']} kills)")
    else:
        print(f"Range  : Not enough data ({range_signal['kills_analyzed']} kills, need more)")

    if weapon["signature"]:
        print(f"Weapon : {weapon['signature']}  ({weapon['kills_analyzed']} classifiable kills)")
    else:
        print(f"Weapon : Not enough data ({weapon['kills_analyzed']} kills, need more)")

    print()
    if archetype["short_tag"]:
        print(f"Short tag: {archetype['short_tag']}")
    print(f"(from {archetype['matches_analyzed']} matches analyzed)")
