# ==============================
# utils/squad_roster.py
# ==============================
"""
Squad Roster: the at-a-glance summary for 2+ profiled teammates. Describes
the squad's range/temperament coverage (which ranges are represented,
which are missing, how aggression distributes) rather than combining
pairwise Squad Read lines - see docs/design/storyboard-profile.md's
"Squad Roster summary view" section.

Per-member role callouts ("entry fragger", "support anchor") are derived
directly from that member's own (range, temperament) pair, not a
hand-authored combo table - each member is classified independently, then
the squad-level text is composed from those classifications.
"""
from utils.squad_read import compute_engagement_lead_stats, format_engagement_lead

TELEMETRY_DIR = "match-telemetry"

RANGE_ORDER = ["Close-Range", "Mid-Range", "Long-Range"]


def _member_role(range_bucket, temperament):
    if temperament == "Aggressive" and range_bucket == "Close-Range":
        return "entry fragger"
    if temperament == "Passive":
        return "support anchor"
    if temperament == "Aggressive":
        return "aggressive skirmisher"
    return None


def _join_names(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def _display_name(member, is_self):
    return "you" if is_self else member["name"]


def _sentence_case(text):
    """Capitalize a composed sentence's leading "you" (the generic
    self-pronoun) without mangling a real player name that happens to
    lead a different sentence - names keep whatever case they already
    have."""
    if text.startswith("you "):
        return "You" + text[3:]
    return text


def compute_squad_coverage_summary(members):
    """The squad-level range/temperament coverage paragraph.

    members[0] is always "you" (the profile-owner perspective). Members
    without a resolved range bucket or temperament yet (not enough data)
    are excluded from the coverage analysis entirely, same confidence-
    gating philosophy as the rest of the Archetype Tag signals.
    """
    profiled = [
        (i, m) for i, m in enumerate(members)
        if m["archetype"]["range"]["range_bucket"] and m["archetype"]["temperament"]
    ]
    if len(profiled) < 2:
        return None

    temperaments = [m["archetype"]["temperament"] for _, m in profiled]
    distinct_temperaments = set(temperaments)

    if "Aggressive" in distinct_temperaments and "Passive" in distinct_temperaments:
        opener = "Balanced squad"
    elif len(distinct_temperaments) == 1:
        opener = f"All-{next(iter(distinct_temperaments))} squad"
    else:
        opener = "Mixed squad"

    role_clauses = []
    leftover = []
    for i, m in profiled:
        range_bucket = m["archetype"]["range"]["range_bucket"]
        temperament = m["archetype"]["temperament"]
        role = _member_role(range_bucket, temperament)
        name = _display_name(m, is_self=(i == 0))
        if role:
            role_clauses.append(f"{name} ({role})")
        else:
            leftover.append((name, range_bucket))

    sentences = []
    if role_clauses:
        text = f"{_join_names(role_clauses)}."
        sentences.append(_sentence_case(text))

    if leftover:
        leftover_names = _join_names([name for name, _ in leftover])
        leftover_bucket_indices = sorted({RANGE_ORDER.index(bucket) for _, bucket in leftover})
        if len(leftover_bucket_indices) == 1:
            span = RANGE_ORDER[leftover_bucket_indices[0]].replace("-Range", "").lower() + "-range"
        else:
            low = RANGE_ORDER[leftover_bucket_indices[0]].replace("-Range", "")
            high = RANGE_ORDER[leftover_bucket_indices[-1]].replace("-Range", "")
            span = f"{low.lower()}-to-{high.lower()}"
        text = f"{leftover_names} cover {span}."
        sentences.append(_sentence_case(text))

    range_buckets_present = {m["archetype"]["range"]["range_bucket"] for _, m in profiled}
    missing_buckets = [b for b in RANGE_ORDER if b not in range_buckets_present]

    if missing_buckets:
        gap_names = ", ".join(b.lower() for b in missing_buckets)
        concluding = f"No one covers {gap_names} - you may be exposed there."
    else:
        concluding = "No overlapping blind spots."

    return f"{opener}: {' '.join(sentences)} {concluding}"


def compute_best_engagement_lead(members, telemetry_dir=TELEMETRY_DIR):
    """The single strongest "opens first" bolstered line, comparing "you"
    (members[0]) against each teammate and surfacing whichever comparison
    clears the confidence bar with the highest count - matches the design
    doc's mockup, which highlights exactly one standout teammate rather
    than a line per pairing.
    """
    if len(members) < 2:
        return None

    self_member = members[0]
    best_teammate_name = None
    best_stats = None

    for teammate in members[1:]:
        stats = compute_engagement_lead_stats(
            self_member["account_id"],
            teammate["account_id"],
            set(self_member["match_ids"]) & set(teammate["match_ids"]),
            telemetry_dir=telemetry_dir,
        )
        if stats is None:
            continue
        if best_stats is None or stats["count"] > best_stats["count"]:
            best_stats = stats
            best_teammate_name = teammate["name"]

    return format_engagement_lead(best_stats, best_teammate_name)


def compute_squad_roster(members, telemetry_dir=TELEMETRY_DIR):
    """Full Squad Roster: per-member summary rows plus the squad-level
    coverage/distribution read and the single strongest bolstered line.

    members: list of {"name", "account_id", "archetype", "match_ids"},
    members[0] is "you".
    """
    roster_rows = [
        {
            "name": "You" if i == 0 else m["name"],
            "tempo_tag": m["archetype"]["tempo"]["tempo_tag"],
            "short_tag": m["archetype"]["short_tag"],
        }
        for i, m in enumerate(members)
    ]

    return {
        "roster_rows": roster_rows,
        "coverage_summary": compute_squad_coverage_summary(members),
        "bolstered_line": compute_best_engagement_lead(members, telemetry_dir=telemetry_dir),
    }
