# ==============================
# utils/archetype_tag.py
# ==============================
from utils.range_signal import compute_range_signal
from utils.tempo_signal import compute_tempo_signal
from utils.weapon_signature import compute_weapon_signature

TELEMETRY_DIR = "match-telemetry"

# Maps a tempo bucket to the short temperament word used alongside the
# range bucket (e.g. "Close-Range/Aggressive") in the design doc's Squad
# Read / roster mockups - reuses the tempo signal rather than computing a
# separate aggression metric.
TEMPO_TO_TEMPERAMENT = {
    "Hot-Drop Headhunter": "Aggressive",
    "Early Skirmisher": "Aggressive",
    "Quick-Gear Striker": "Balanced",
    "Calculated Pusher": "Balanced",
    "Slow-Roll Patient": "Passive",
}


def compute_archetype_tag(account_id, match_ids, telemetry_dir=TELEMETRY_DIR, team_mode_match_ids=None):
    """Combine tempo, range, and weapon-signature into the Archetype Tag.

    match_ids is the player's scoped match set (see match_scope.py),
    resolved once by the caller and reused across all three signals here
    rather than each one independently rescanning the telemetry cache.

    team_mode_match_ids, if given, scopes Range and Weapon specifically to
    team-mode (duo/squad) matches - validated against real data (issue
    #42): engagement range runs consistently shorter in team modes than
    solo, enough to flip the bucket for some players, while Tempo showed
    no mode sensitivity and stays on the full match_ids scope. Defaults to
    match_ids when not given, so existing callers are unaffected.
    """
    match_ids = set(match_ids)
    range_weapon_match_ids = set(team_mode_match_ids) if team_mode_match_ids is not None else match_ids

    tempo = compute_tempo_signal(account_id, match_ids=match_ids, telemetry_dir=telemetry_dir)
    range_signal = compute_range_signal(account_id, match_ids=range_weapon_match_ids, telemetry_dir=telemetry_dir)
    weapon = compute_weapon_signature(account_id, match_ids=range_weapon_match_ids, telemetry_dir=telemetry_dir)

    temperament = TEMPO_TO_TEMPERAMENT.get(tempo["tempo_tag"])
    range_bucket = range_signal["range_bucket"]
    short_tag = f"{range_bucket}/{temperament}" if range_bucket and temperament else None

    return {
        "tempo": tempo,
        "range": range_signal,
        "weapon": weapon,
        "temperament": temperament,
        "short_tag": short_tag,
        "matches_analyzed": len(match_ids),
    }
