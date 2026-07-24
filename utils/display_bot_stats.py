# ==============================
# utils/display_bot_stats.py
# ==============================


def render_bot_summary(match_id, bots):
    print("=============================")
    print("🤖 Bot Detection - Last Match")
    print("=============================")
    print(f"Match ID: {match_id}")
    print(f"Bots Detected: {len(bots)}")
    print()

    if not bots:
        print("No AI players found in this match's telemetry.")
        return

    for account_id, name in bots.items():
        print(f"  • {name}  ({account_id})")
