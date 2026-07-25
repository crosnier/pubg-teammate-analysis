# ==============================
# utils/display_squad_read.py
# ==============================


def render_squad_read(squad_read):
    print("=============================")
    print("🤝 Squad Read")
    print("=============================")

    if squad_read["synergy_line"]:
        print(squad_read["synergy_line"])
    else:
        print("Not enough data yet for a synergy read.")

    if squad_read["bolstered_line"]:
        print()
        print(squad_read["bolstered_line"])
