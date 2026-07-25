# ==============================
# utils/display_last_match_brief.py
# ==============================


def render_last_match_brief(playername, brief, played_with_you=None, show_squad_status=True, killer_intel_line=None):
    print("=============================")
    print(f"📋 Last Match Brief - {playername}")
    print("=============================")
    print(f"Match ID   : {brief['match_id']}")
    print(f"Round Rank : {brief['round_rank'] if brief['round_rank'] is not None else 'Unknown'}")

    time_alive = brief["time_alive_seconds"]
    if time_alive is not None:
        minutes, seconds = divmod(time_alive, 60)
        print(f"Time Alive : {minutes}m {seconds}s")
    else:
        print("Time Alive : Unknown")

    print(f"Kills      : {brief['kill_count']}")
    print(f"Top Weapon : {brief['most_used_weapon'] or '-'}")

    death_info = brief["death_info"]
    if death_info:
        print(f"Died To    : {death_info['killed_by']} ({death_info['weapon']}) from {death_info['distance_m']}m")
    else:
        print("Died To    : Survived to match end")

    if killer_intel_line:
        print(f"Who Killed You: {killer_intel_line}")

    squad_status = brief.get("squad_status")
    if show_squad_status and squad_status:
        print("Squad Status at the time:")
        for teammate in squad_status:
            if teammate["status"] == "alive":
                print(f"  {teammate['name']}: still alive")
            elif teammate["status"] == "same_engagement":
                print(f"  {teammate['name']}: went down {teammate['seconds_before']}s earlier, same fight")
            else:
                print(f"  {teammate['name']}: already eliminated earlier, unrelated to this fight")

    if played_with_you is not None:
        print(f"In your last shared match: {'Yes' if played_with_you else 'No'}")
    print()
