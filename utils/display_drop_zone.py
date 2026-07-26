# ==============================
# utils/display_drop_zone.py
# ==============================

FLOW_TAG_LINES = {
    "Zone Center": "You tend to play close to the safe zone's center rather than hugging the edge.",
    "Balanced Rotator": "You rotate through the middle ground - not glued to the center, not living on the edge.",
    "Zone Edge": "You tend to hang near the safe zone's edge rather than pushing toward the center.",
}


def format_drop_zone_line(drop_zone_signal):
    """One-line drop-zone read for a player's card, or None if there's
    nothing worth showing (not enough matches, or every cached match is on
    a map without POI data yet)."""
    if drop_zone_signal["drop_zone_description"]:
        distance_m = drop_zone_signal.get("top_zone_median_distance_m")
        # Only "near X"/"edge of X" reads have a single unambiguous point
        # to report a distance from - "between X and Y" never gets one
        # (see compute_drop_zone_signal), so this only fires for those.
        suffix = f" (~{round(distance_m)}m from center)" if distance_m is not None else ""
        return f"You typically drop {drop_zone_signal['drop_zone_description']}{suffix}."

    if drop_zone_signal["matches_analyzed"] > 0 and drop_zone_signal["matches_on_supported_map"] == 0:
        return "Drop zone: map not yet supported for tracking."

    return None


def format_flow_line(flow_signal):
    """One-line zone-positioning read for a player's card, or None if
    there's not enough data yet. Map-agnostic (see movement_flow.py), so
    this doesn't have the same "map not yet supported" fallback as the
    drop-zone line."""
    return FLOW_TAG_LINES.get(flow_signal["flow_tag"])
