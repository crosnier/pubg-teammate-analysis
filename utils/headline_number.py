# ==============================
# utils/headline_number.py
# ==============================
"""
Headline Number: one differentiating, confidence-gated "so-what" stat,
programmatically chosen from a fixed pool of PEPS+-grounded candidate
templates (Firepower, Finishing, Combat Distance, and a team-support
read via revives). No LLM involved - see docs/design/storyboard-profile.
md's "Headline Number: how it's chosen" section for the full spec this
implements.
"""
import glob
import json
import math
import os
import statistics
from datetime import datetime

from utils.last_match_brief import player_present_in_match
from utils.range_signal import CLOSE_RANGE_MAX_METERS

TELEMETRY_DIR = "match-telemetry"

# Matches the MIN_*_FOR_SIGNAL threshold used across tempo/range/weapon
# signals (Epstein aggregation principle / Spearman-Brown, ~8+ occasions
# for a meaningfully reliable behavioral read) - a candidate needs at
# least this many matches of underlying data to be eligible at all.
MIN_MATCHES_FOR_CANDIDATE = 8

# Stability gate: split a candidate's readings into chronological halves
# and require both halves' deviation from the neutral reference to point
# the same direction, with neither half's deviation dwarfing the other's
# (guards against a pattern being carried entirely by one hot streak).
MIN_HALF_STABILITY_RATIO = 0.25


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def _parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _is_real_kill(event, account_id):
    if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
        return False
    killer = event.get("killer") or {}
    victim = event.get("victim") or {}
    return (
        killer.get("accountId") == account_id and killer.get("type") == "user"
        and victim.get("type") == "user" and victim.get("accountId") != account_id
    )


def _is_real_death(event, account_id):
    if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
        return False
    killer = event.get("killer") or {}
    victim = event.get("victim") or {}
    return (
        victim.get("accountId") == account_id and killer.get("type") == "user"
        and killer.get("accountId") != account_id
    )


def _extract_match_readings(account_id, events):
    """Pull every candidate's readings out of one match in a single pass.

    Returns per-match magnitude readings (kills-before-death, revives,
    damage) plus per-fight/per-knockdown binary readings (close-range
    win, knockdown conversion), all tagged with the match start time so
    they can be pooled across matches and split chronologically later.
    """
    if not player_present_in_match(account_id, events):
        return None

    start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
    if not start_event or not start_event.get("_D"):
        return None
    match_start = _parse_timestamp(start_event["_D"])

    kills_before_death = 0
    died = False
    revives = 0
    damage = 0
    close_range_fights = []
    groggy_ids = {}
    resolved_conversions = []

    for event in events:
        event_type = event.get("_T")

        if _is_real_kill(event, account_id):
            if not died:
                kills_before_death += 1
            distance_m = (event.get("killerDamageInfo") or {}).get("distance", 0) / 100
            if distance_m <= CLOSE_RANGE_MAX_METERS:
                close_range_fights.append(1)

        elif _is_real_death(event, account_id):
            died = True
            distance_m = (event.get("killerDamageInfo") or {}).get("distance", 0) / 100
            if distance_m <= CLOSE_RANGE_MAX_METERS:
                close_range_fights.append(0)

        elif event_type == "LogPlayerRevive":
            if (event.get("reviver") or {}).get("accountId") == account_id:
                revives += 1

        elif event_type == "LogPlayerTakeDamage":
            attacker = event.get("attacker") or {}
            victim = event.get("victim") or {}
            if attacker.get("accountId") == account_id and attacker.get("type") == "user" \
                    and victim.get("type") == "user" and victim.get("accountId") != account_id:
                damage += event.get("damage", 0)

        elif event_type == "LogPlayerMakeGroggy":
            attacker = event.get("attacker") or {}
            victim = event.get("victim") or {}
            dbno_id = event.get("dBNOId")
            if attacker.get("accountId") == account_id and attacker.get("type") == "user" \
                    and victim.get("type") == "user" and dbno_id is not None:
                groggy_ids[dbno_id] = None

    # Resolve each knockdown this player caused: did it end in a kill
    # (converted) or a revive (saved)? Unresolved knockdowns (neither
    # happened before the match ended, e.g. disconnect) aren't counted.
    if groggy_ids:
        for event in events:
            dbno_id = event.get("dBNOId")
            if dbno_id not in groggy_ids or groggy_ids[dbno_id] is not None:
                continue
            if event.get("_T") == "LogPlayerKillV2" and not event.get("isSuicide"):
                groggy_ids[dbno_id] = 1
            elif event.get("_T") == "LogPlayerRevive":
                groggy_ids[dbno_id] = 0
        resolved_conversions = [v for v in groggy_ids.values() if v is not None]

    return {
        "match_start": match_start,
        "kills_before_death": kills_before_death,
        "revives": revives,
        "damage": damage,
        "close_range_fights": close_range_fights,
        "knockdown_conversions": resolved_conversions,
    }


def _is_stable(ordered_values, neutral_reference):
    if len(ordered_values) < 2:
        return False
    midpoint = len(ordered_values) // 2
    first_half, second_half = ordered_values[:midpoint], ordered_values[midpoint:]
    if not first_half or not second_half:
        return False

    deviation_1 = statistics.mean(first_half) - neutral_reference
    deviation_2 = statistics.mean(second_half) - neutral_reference
    if deviation_1 == 0 or deviation_2 == 0:
        return False
    if (deviation_1 > 0) != (deviation_2 > 0):
        return False

    ratio = min(abs(deviation_1), abs(deviation_2)) / max(abs(deviation_1), abs(deviation_2))
    return ratio >= MIN_HALF_STABILITY_RATIO


def _score_rate(ordered_values):
    """One-sample z-test for a proportion against a neutral 50/50 split.

    Standard test for "is this rate different from chance" - uses the
    fixed null-hypothesis variance p(1-p) at p=0.5 rather than the sample's
    own variance, so a rate that happens to be perfectly consistent (every
    reading the same) never divides by zero; the score just keeps growing
    with sample size the way a real proportion test would.
    """
    n = len(ordered_values)
    p_hat = statistics.mean(ordered_values)
    standard_error = math.sqrt(0.25 / n)
    return abs(p_hat - 0.5) / standard_error


def _score_magnitude(ordered_values):
    """One-sample t-statistic for a count/sum stat against a neutral zero.

    Self-relative by construction (no external population dataset) -
    rewards a candidate for being both large and consistent match to
    match, since a wide spread inflates the standard error and drags the
    score down even when the mean looks impressive. A sample with zero
    observed variance (every match identical) gives no basis to estimate
    spread at all - rather than guess at a distributional assumption
    (which would let large-magnitude stats like damage score arbitrarily
    high just for being suspiciously constant), score it 0 and defer to
    a candidate with genuine measurable spread.
    """
    n = len(ordered_values)
    mean = statistics.mean(ordered_values)
    variance = statistics.variance(ordered_values) if n > 1 else 0
    if variance == 0:
        return 0.0
    standard_error = math.sqrt(variance / n)
    return mean / standard_error


def compute_headline_number(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR, possessive="your"):
    """Pick the single most differentiating, confidence-gated stat.

    Evaluates a fixed pool of candidates, keeps only those with enough
    underlying matches and a directionally stable pattern, and surfaces
    whichever eligible candidate scores highest. Falls back to a plain
    kill count if nothing clears the bar, rather than force a shaky
    "notable" stat onto a small or noisy sample.

    possessive: pronoun used in the rendered sentence ("your" for the
    CLI's own user in main.py, "their" when squad.py renders a
    teammate's card).
    """
    magnitude_readings = {"kills_before_death": [], "revives": [], "damage": []}
    rate_readings = {"close_range_win": [], "knockdown_conversion": []}
    matches_analyzed = 0
    total_kills = 0

    matches = []
    for events in _load_telemetry_files(match_ids, telemetry_dir):
        match = _extract_match_readings(account_id, events)
        if match is not None:
            matches.append(match)

    matches.sort(key=lambda m: m["match_start"])

    for match in matches:
        matches_analyzed += 1
        total_kills += match["kills_before_death"]
        magnitude_readings["kills_before_death"].append(match["kills_before_death"])
        magnitude_readings["revives"].append(match["revives"])
        magnitude_readings["damage"].append(match["damage"])
        rate_readings["close_range_win"].extend(match["close_range_fights"])
        rate_readings["knockdown_conversion"].extend(match["knockdown_conversions"])

    matches_with_close_range = sum(1 for m in matches if m["close_range_fights"])
    matches_with_knockdowns = sum(1 for m in matches if m["knockdown_conversions"])

    candidates = []

    if matches_analyzed >= MIN_MATCHES_FOR_CANDIDATE:
        values = magnitude_readings["kills_before_death"]
        if _is_stable(values, 0):
            candidates.append({
                "key": "kills_before_death",
                "score": _score_magnitude(values),
                "sentence": (
                    f"Averages {statistics.mean(values):.1f} kills before first death "
                    f"over {possessive} last {matches_analyzed} matches"
                ),
            })

        values = magnitude_readings["revives"]
        if _is_stable(values, 0):
            candidates.append({
                "key": "revives",
                "score": _score_magnitude(values),
                "sentence": (
                    f"Averages {statistics.mean(values):.1f} revives per match over {possessive} "
                    f"last {matches_analyzed} matches"
                ),
            })

        values = magnitude_readings["damage"]
        if _is_stable(values, 0):
            candidates.append({
                "key": "damage",
                "score": _score_magnitude(values),
                "sentence": (
                    f"Averages {statistics.mean(values):.0f} damage per match over {possessive} "
                    f"last {matches_analyzed} matches"
                ),
            })

    if matches_with_close_range >= MIN_MATCHES_FOR_CANDIDATE:
        values = rate_readings["close_range_win"]
        if _is_stable(values, 0.5):
            wins = sum(values)
            candidates.append({
                "key": "close_range_win_rate",
                "score": _score_rate(values),
                "sentence": (
                    f"Wins {statistics.mean(values):.0%} of close-range fights "
                    f"(inside {CLOSE_RANGE_MAX_METERS}m) - {wins}/{len(values)} across "
                    f"{possessive} last {matches_with_close_range} matches"
                ),
            })

    if matches_with_knockdowns >= MIN_MATCHES_FOR_CANDIDATE:
        values = rate_readings["knockdown_conversion"]
        if _is_stable(values, 0.5):
            converted = sum(values)
            candidates.append({
                "key": "knockdown_conversion_rate",
                "score": _score_rate(values),
                "sentence": (
                    f"Converts {statistics.mean(values):.0%} of knockdowns into kills - "
                    f"{converted}/{len(values)} over {possessive} last {matches_with_knockdowns} matches"
                ),
            })

    if candidates:
        best = max(candidates, key=lambda c: c["score"])
        return {
            "headline": best["sentence"],
            "stat_key": best["key"],
            "score": best["score"],
            "matches_analyzed": matches_analyzed,
        }

    return {
        "headline": f"{total_kills} kills over {possessive} last {matches_analyzed} matches"
        if matches_analyzed else "Not enough data yet",
        "stat_key": "fallback_kill_count",
        "score": None,
        "matches_analyzed": matches_analyzed,
    }
