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


def compute_archetype_tag(account_id, match_ids, telemetry_dir=TELEMETRY_DIR):
    """Combine tempo, range, and weapon-signature into the Archetype Tag.

    match_ids is the player's scoped match set (see match_scope.py),
    resolved once by the caller and reused across all three signals here
    rather than each one independently rescanning the telemetry cache.
    """
    match_ids = set(match_ids)

    tempo = compute_tempo_signal(account_id, match_ids=match_ids, telemetry_dir=telemetry_dir)
    range_signal = compute_range_signal(account_id, match_ids=match_ids, telemetry_dir=telemetry_dir)
    weapon = compute_weapon_signature(account_id, match_ids=match_ids, telemetry_dir=telemetry_dir)

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
