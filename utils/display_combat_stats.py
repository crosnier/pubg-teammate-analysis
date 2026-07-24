# ==============================
# utils/display_combat_stats.py
# ==============================


def render_combat_stats(stats):
    total_elims = stats["total_eliminations"]
    total_deaths = stats["total_deaths"]
    kd = total_elims / total_deaths if total_deaths else float(total_elims)
    matches_analyzed = stats["matches_analyzed"]

    print("=============================")
    print("🎯 Summary - Combat Stats")
    print("=============================")
    print(f"Eliminations : {total_elims}")
    print(f"Deaths       : {total_deaths}")
    print(f"K/D Ratio    : {kd:.2f}")
    plural = "es" if matches_analyzed != 1 else ""
    print(f"(from {matches_analyzed} cached match{plural} with telemetry)")
    print()

    _render_breakdown("🔫 Eliminations Breakdown", stats["eliminations_breakdown"])
    print()
    _render_breakdown("💀 Deaths Breakdown", stats["deaths_breakdown"])


def _render_breakdown(title, breakdown):
    print("=============================")
    print(title)
    print("=============================")
    if not breakdown:
        print("No data in cached telemetry.")
        return
    width = max(len(name) for name in breakdown)
    for name, count in breakdown.items():
        print(f"{name:<{width}} : {count}")
