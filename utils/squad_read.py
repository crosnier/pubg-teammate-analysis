# ==============================
# utils/squad_read.py
# ==============================
"""
Squad Read: a synergy/gap sentence combining two profiled teammates'
Archetype Tags, bolstered with a data-backed "who opens first" line when
the pattern is consistent enough to say so with confidence. No named role
taxonomy - the synergy line is composed directly from the range-bucket and
temperament deltas between the two players, so it scales to any pairing
without a hand-authored combo table. See docs/design/storyboard-profile.md's
"Squad Read" section for the full spec this implements.
"""
import json
import os
from datetime import datetime

from utils.tempo_signal import compute_time_to_first_contact_from_events

TELEMETRY_DIR = "match-telemetry"

RANGE_ORDER = {"Close-Range": 0, "Mid-Range": 1, "Long-Range": 2}
TEMPERAMENT_ORDER = {"Aggressive": 0, "Balanced": 1, "Passive": 2}

# "Last N shared matches, need at least K" for the bolstered line - matches
# the design doc's explicit worked example ("6 of your last 8"). Reuses the
# project's established MIN_*_FOR_SIGNAL=8 confidence-gating convention
# rather than a looser all-time percentage.
BOLSTER_WINDOW = 8
BOLSTER_THRESHOLD = 5


def compute_synergy_line(self_range, self_temperament, teammate_name, teammate_range, teammate_temperament):
    """The general synergy/gap sentence, composed from the range and
    temperament deltas between the two players rather than a lookup table
    of named role combinations.

    Returns None if either player doesn't have enough data for a range
    bucket or temperament yet (matches the confidence-gating already
    applied upstream by range_signal.py/tempo_signal.py).
    """
    if not all([self_range, self_temperament, teammate_range, teammate_temperament]):
        return None

    prefix = f"You ({self_range}/{self_temperament}) + {teammate_name} ({teammate_range}/{teammate_temperament})"

    range_delta = RANGE_ORDER[self_range] - RANGE_ORDER[teammate_range]
    temperament_delta = TEMPERAMENT_ORDER[self_temperament] - TEMPERAMENT_ORDER[teammate_temperament]

    if range_delta == 0 and temperament_delta == 0:
        if self_temperament == "Aggressive":
            detail = (
                "matching aggressive playstyles - you'll both want to be first into the fight. "
                "Talk before you drop so you're not both pushing the same angle."
            )
        elif self_temperament == "Passive":
            detail = (
                "matching passive playstyles - neither of you likes to open engagements. "
                "Expect slower starts, but you'll have each other's range covered when it happens."
            )
        else:
            detail = "closely matched playstyles - predictable to coordinate with, just watch for blind spots you might share."
        return f"{prefix} = {detail}"

    if range_delta != 0 and temperament_delta == 0:
        if range_delta < 0:
            detail = f"same tempo, different distances - you get into the fight up close while {teammate_name} covers from range."
        else:
            detail = f"same tempo, different distances - {teammate_name} gets into the fight up close while you cover from range."
        return f"{prefix} = {detail}"

    if range_delta == 0 and temperament_delta != 0:
        if temperament_delta < 0:
            detail = "similar range, but you tend to commit sooner - you'll typically be first into engagements."
        else:
            detail = f"similar range, but {teammate_name} tends to commit sooner - expect them to be first into engagements."
        return f"{prefix} = {detail}"

    closer_is_self = range_delta < 0
    faster_is_self = temperament_delta < 0
    if closer_is_self == faster_is_self:
        if closer_is_self:
            detail = f"classic push-and-cover: you push in, {teammate_name} holds the angle."
        else:
            detail = f"classic push-and-cover: {teammate_name} pushes in, you hold your angle."
        return f"{prefix} = {detail}"

    detail = (
        "an unusual mix - your instincts pull in different directions (one of you commits fast but "
        "from range, the other holds close and waits). Worth talking through positioning before you push."
    )
    return f"{prefix} = {detail}"


def _load_dated_events(match_ids, telemetry_dir):
    for match_id in match_ids:
        path = os.path.join(telemetry_dir, f"{match_id}-telemetry.json")
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            events = json.load(f)
        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if not start_event or not start_event.get("_D"):
            continue
        yield events, datetime.fromisoformat(start_event["_D"].replace("Z", "+00:00"))


def compute_engagement_lead(self_id, teammate_id, teammate_name, shared_match_ids, telemetry_dir=TELEMETRY_DIR):
    """Bolstered "who opens first" line, or None if the pattern isn't
    consistent (or common) enough across the most recent shared matches to
    say so with confidence.

    "Opens first" compares each player's own time-to-first-contact
    (tempo_signal.py) within the same match - whichever of the two made
    contact with a real player earlier is the one who opened that match's
    engagement for the squad. Only matches where both players have a valid
    contact reading count (a match one of them never engaged in isn't a
    fair comparison). Reuses tempo_signal's own presence/contact logic
    rather than re-deriving it.
    """
    dated_openers = []
    for events, match_start in _load_dated_events(shared_match_ids, telemetry_dir):
        self_reading = compute_time_to_first_contact_from_events(self_id, events)
        teammate_reading = compute_time_to_first_contact_from_events(teammate_id, events)
        if not self_reading or not teammate_reading:
            continue

        self_seconds = self_reading["contact_seconds"]
        teammate_seconds = teammate_reading["contact_seconds"]
        if self_seconds is None or teammate_seconds is None or self_seconds == teammate_seconds:
            continue

        opener = "you" if self_seconds < teammate_seconds else teammate_name
        dated_openers.append((match_start, opener))

    dated_openers.sort(key=lambda r: r[0], reverse=True)
    recent_window = dated_openers[:BOLSTER_WINDOW]

    if len(recent_window) < BOLSTER_WINDOW:
        return None

    counts = {}
    for _, opener in recent_window:
        counts[opener] = counts.get(opener, 0) + 1

    leader, count = max(counts.items(), key=lambda kv: kv[1])
    if count < BOLSTER_THRESHOLD:
        return None

    if leader == "you":
        return f"High confidence: you've opened the first engagement in {count} of your last {len(recent_window)} shared matches."
    return (
        f"High confidence: {leader} has opened the first engagement in {count} of your last "
        f"{len(recent_window)} shared matches - expect {leader} to push first."
    )


def compute_squad_read(
    self_id, self_archetype, self_match_ids,
    teammate_id, teammate_name, teammate_archetype, teammate_match_ids,
    telemetry_dir=TELEMETRY_DIR,
):
    """Combine the general synergy line with the bolstered "opens first"
    line (when confident enough) into the full Squad Read.
    """
    synergy_line = compute_synergy_line(
        self_archetype["range"]["range_bucket"],
        self_archetype["temperament"],
        teammate_name,
        teammate_archetype["range"]["range_bucket"],
        teammate_archetype["temperament"],
    )

    shared_match_ids = set(self_match_ids) & set(teammate_match_ids)
    bolstered_line = compute_engagement_lead(
        self_id, teammate_id, teammate_name, shared_match_ids, telemetry_dir=telemetry_dir
    )

    return {
        "synergy_line": synergy_line,
        "bolstered_line": bolstered_line,
        "shared_matches_analyzed": len(shared_match_ids),
    }
