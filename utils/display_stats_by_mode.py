# utils/display_stats_by_mode.py
import json
import os

GAME_MODES = [
    "solo-fpp", "duo-fpp", "squad-fpp",
    "solo", "duo", "squad"
]

STAT_GROUPS = {
    "🎯 COMBAT PERFORMANCE": [
        ("Kills", "kills"),
        ("Assists", "assists"),
        ("Headshot Kills", "headshotKills"),
        ("Knockdowns (DBNOs)", "dBNOs"),
        ("Round Most Kills", "roundMostKills"),
        ("Kill Streak Max", "maxKillStreaks"),
        ("Team Kills", "teamKills"),
        ("Suicides", "suicides"),
    ],
    "🛡️ SURVIVAL OUTCOMES": [
        ("Wins", "wins"),
        ("Losses", "losses"),
        ("Top 10 Finishes", "top10s"),
        ("Rounds Played", "roundsPlayed"),
        ("Time Survived (min)", "timeSurvived"),
        ("Longest Survival (min)", "longestTimeSurvived"),
        ("Most Survival Time (min)", "mostSurvivalTime"),
        ("Daily Wins", "dailyWins"),
        ("Weekly Wins", "weeklyWins"),
    ],
    "💉 SUPPORT ACTIONS": [
        ("Heals", "heals"),
        ("Revives", "revives"),
        ("Boosts", "boosts"),
    ],
    "🏃 MOVEMENT STATS": [
        ("Walked Distance", "walkDistance"),
        ("Driven Distance", "rideDistance"),
        ("Swam Distance", "swimDistance"),
        ("Longest Kill Shot", "longestKill"),
        ("Road Kills", "roadKills"),
    ],
    "🔧 EQUIPMENT & VEHICLES": [
        ("Weapons Acquired", "weaponsAcquired"),
        ("Vehicles Destroyed", "vehicleDestroys"),
    ],
    "📆 ACTIVITY OVER TIME": [
        ("Days Played", "days"),
        ("Daily Kills", "dailyKills"),
        ("Weekly Kills", "weeklyKills"),
    ]
}


LABEL_WIDTH = 25  # updated for consistent alignment


def print_static_banner(playername=None):
    box_width = 45
    title = f"{playername} Stats" if playername else "Player Stats"
    padding = (box_width - len(title)) // 2
    padded_title = f"{' ' * padding}{title}{' ' * (box_width - len(title) - padding)}"

    print("╔" + "═" * box_width + "╗")
    print(f"║{padded_title}║")
    print("╚" + "═" * box_width + "╝\n")


def format_number(val, key=None):
    if key and "TimeSurvived" in key:
        minutes = int(val) // 60
        return f"{minutes:,}"
    if isinstance(val, (int, float)):
        return f"{val:,.0f}" if val < 100000 else f"{val/1000:,.0f}k"
    return "0"


def load_player_stats(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def render_ascii_table(stats, playername):
    mode_stats = stats["data"]["attributes"]["gameModeStats"]

    print_static_banner(playername)

    for group_name, fields in STAT_GROUPS.items():
        print("=" * 25)
        print(group_name)
        print("=" * 25)
        print("".ljust(LABEL_WIDTH) + "  ".join([m.ljust(10) for m in GAME_MODES[:3]]) + "  |  " + "  ".join([m.ljust(6) for m in GAME_MODES[3:]]))

        for label, key in fields:
            row = label.ljust(LABEL_WIDTH)
            for mode in GAME_MODES:
                val = mode_stats.get(mode, {}).get(key, 0)
                row += format_number(val, key).rjust(10) + "  " if mode in GAME_MODES[:3] else ""
            row += "|  "
            for mode in GAME_MODES[3:]:
                val = mode_stats.get(mode, {}).get(key, 0)
                row += format_number(val, key).rjust(6) + "  "
            print(row)
        print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("playername", help="Name of the player (matches JSON filename)")
    args = parser.parse_args()

    path = os.path.join("playerstats", f"{args.playername}.json")
    if os.path.exists(path):
        stats = load_player_stats(path)
        render_ascii_table(stats, args.playername)
    else:
        print(f"[ERROR] Stats not found for '{args.playername}'. Run data query first.")
