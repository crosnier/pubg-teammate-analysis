# ==============================
# utils/display_match_pathing.py
# ==============================

MAP_DISPLAY_NAMES = {
    "Baltic_Main": "Erangel",
    "Desert_Main": "Miramar",
    "DihorOtok_Main": "Vikendi",
    "Tiger_Main": "Taego",
    "Kiki_Main": "Deston",
    "Savage_Main": "Sanhok",
    "Chimera_Main": "Paramo",
    "Summerland_Main": "Karakin",
    "Range_Main": "Camp Jackal",
    "Heaven_Main": "Haven",
    "Neon_Main": "Rondo",
}


def format_match_pathing_line(pathing):
    """One-line "last match pathing" read, or None if there's nothing to
    show (player absent from that match entirely - see
    compute_match_pathing's own None return for that case)."""
    if pathing is None:
        return None

    map_label = MAP_DISPLAY_NAMES.get(pathing["map_name"], pathing["map_name"] or "Unknown map")

    if not pathing["supported_map"]:
        return f"Last match ({map_label}, {pathing['mode_label']}): pathing not yet supported for this map."

    if not pathing["path_description"]:
        return f"Last match ({map_label}, {pathing['mode_label']}): not enough position data to trace a path."

    return f"Last match ({map_label}, {pathing['mode_label']}): {pathing['path_description']}"
