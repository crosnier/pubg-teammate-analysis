# ==============================
# utils/killer_intel.py
# ==============================
"""
Killer Intel: solo.py's replacement for Last Match Brief's "Squad Status at
the time" section, which has no meaning without a squad - if you died, the
more useful read is how the player who killed you actually played that
match, not who else was on your own team.

Scoped to the single match you died in - reuses tempo_signal.py's existing
per-match first-contact reading (already exactly the "aggressive from the
start vs. held back" signal) against the killer's own account within that
match's events, rather than parsing anything new.
"""
from utils.tempo_signal import compute_time_to_first_contact_from_events, \
    VERY_FAST_CONTACT_SECONDS, MODERATE_DELAY_SECONDS

PACE_PHRASES = {
    "early": "came out swinging early, engaging well before you crossed paths",
    "mid": "played a measured mid-game, engaging once gear was sorted",
    "late": "held back and stayed quiet for most of the round",
    "unknown": "had no other engagements logged this match",
}


def _engagement_pace(contact_seconds):
    if contact_seconds is None:
        return "unknown"
    if contact_seconds <= VERY_FAST_CONTACT_SECONDS:
        return "early"
    if contact_seconds <= MODERATE_DELAY_SECONDS:
        return "mid"
    return "late"


def compute_killer_intel(events, death_info):
    """Kill count, engagement pace, and final placement for whoever killed
    you in this match - or None if you survived to match end (no killer)
    or the killing event's account ID wasn't captured."""
    if not death_info or not death_info.get("killer_account_id"):
        return None
    killer_id = death_info["killer_account_id"]

    kill_count = 0
    for event in events:
        if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
            continue
        killer = event.get("killer") or {}
        victim = event.get("victim") or {}
        if killer.get("accountId") == killer_id and killer.get("type") == "user" \
                and victim.get("type") == "user" and victim.get("accountId") != killer_id:
            kill_count += 1

    contact = compute_time_to_first_contact_from_events(killer_id, events)
    contact_seconds = contact["contact_seconds"] if contact else None

    match_end = next((e for e in events if e.get("_T") == "LogMatchEnd"), None)
    final_rank = None
    if match_end:
        entry = next(
            (c for c in match_end.get("characters", []) if (c.get("character") or {}).get("accountId") == killer_id),
            None,
        )
        if entry:
            final_rank = entry["character"].get("ranking")

    return {
        "killer_name": death_info["killed_by"],
        "kill_count": kill_count,
        "engagement_pace": _engagement_pace(contact_seconds),
        "final_rank": final_rank,
    }


def format_killer_intel(intel):
    if intel is None:
        return None

    pace_phrase = PACE_PHRASES[intel["engagement_pace"]]
    kill_count = intel["kill_count"]
    if kill_count == 0:
        kill_phrase = "with no other confirmed kills this match"
    elif kill_count == 1:
        kill_phrase = "picking up 1 kill this match"
    else:
        kill_phrase = f"racking up {kill_count} kills this match"

    rank_phrase = f", and went on to finish #{intel['final_rank']}" if intel["final_rank"] else ""

    return f"{intel['killer_name']} {pace_phrase}, {kill_phrase}{rank_phrase}."
