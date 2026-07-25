# ==============================
# utils/weapon_signature.py
# ==============================
import glob
import json
import os

from utils.weapon_classes import classify_weapon

TELEMETRY_DIR = "match-telemetry"

# Wildcard framing thresholds, per docs/design/storyboard-profile.md:
# a class only gets named as "the" preference if it has a real lead -
# otherwise the honest read is that there's no dominant pattern.
WILDCARD_SHARE_THRESHOLD = 0.45
WILDCARD_GAP_THRESHOLD = 0.10

MIN_KILLS_FOR_SIGNAL = 8


def _load_telemetry_files(match_ids=None, telemetry_dir=TELEMETRY_DIR):
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            yield json.load(f)


def compute_weapon_signature(account_id, match_ids=None, telemetry_dir=TELEMETRY_DIR):
    """Weapon Signature half of the Archetype Tag: preferred gun class.

    Only kills with a real player victim and a classifiable gun causer
    count - melee/throwables/vehicles aren't a "weapon preference" in the
    sense this slot means. Requires MIN_KILLS_FOR_SIGNAL classifiable
    kills before naming anything, matching the design doc's confidence-
    gating philosophy.

    Wildcard framing (no single dominant class) applies when the top
    class holds under WILDCARD_SHARE_THRESHOLD of kills, or the top two
    classes are within WILDCARD_GAP_THRESHOLD of each other - forcing a
    narrative onto a genuinely mixed loadout would be dishonest.
    """
    class_counts = {}
    total_classified = 0

    for events in _load_telemetry_files(match_ids, telemetry_dir):
        for event in events:
            if event.get("_T") != "LogPlayerKillV2" or event.get("isSuicide"):
                continue
            killer = event.get("killer") or {}
            victim = event.get("victim") or {}
            if killer.get("accountId") != account_id or killer.get("type") != "user":
                continue
            if victim.get("type") != "user" or victim.get("accountId") == account_id:
                continue
            weapon_class = classify_weapon((event.get("killerDamageInfo") or {}).get("damageCauserName"))
            if weapon_class is None:
                continue
            class_counts[weapon_class] = class_counts.get(weapon_class, 0) + 1
            total_classified += 1

    if total_classified < MIN_KILLS_FOR_SIGNAL:
        return {
            "signature": None,
            "is_wildcard": None,
            "top_classes": [],
            "class_counts": class_counts,
            "kills_analyzed": total_classified,
        }

    ranked = sorted(class_counts.items(), key=lambda kv: kv[1], reverse=True)
    top_class, top_count = ranked[0]
    top_share = top_count / total_classified

    is_wildcard = top_share < WILDCARD_SHARE_THRESHOLD
    if not is_wildcard and len(ranked) > 1:
        second_class, second_count = ranked[1]
        second_share = second_count / total_classified
        if (top_share - second_share) < WILDCARD_GAP_THRESHOLD:
            is_wildcard = True

    if is_wildcard:
        top_classes = [cls for cls, _ in ranked[:2]]
        signature = f"Wildcard - no dominant class; splits between {' and '.join(top_classes)}"
    else:
        top_classes = [top_class]
        signature = top_class

    return {
        "signature": signature,
        "is_wildcard": is_wildcard,
        "top_classes": top_classes,
        "class_counts": class_counts,
        "kills_analyzed": total_classified,
    }
