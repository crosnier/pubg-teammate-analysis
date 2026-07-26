# ==============================
# utils/telemetry_cache.py
# ==============================
"""
Shared telemetry loading for callers that need the same match set fed
into multiple signal functions - see archetype_tag.py, which computes
Tempo, Range, and Weapon Signature from one player's scoped matches.
Each of those previously called its own private file loader, so every
cached match got re-opened and re-parsed once per signal (issue #30) -
load_telemetry_events() parses each file exactly once; select_telemetry_
events() lets each signal function accept that pre-parsed result instead
of hitting disk again, while still falling back to its own disk read
when no pre-loaded cache is given (existing single-signal callers, and
every current test, are unaffected).
"""
import glob
import json
import os

TELEMETRY_DIR = "match-telemetry"


def load_telemetry_events(match_ids, telemetry_dir=TELEMETRY_DIR):
    """Parse each of these match IDs' cached telemetry file exactly once,
    keyed by match_id. Matches not yet cached are skipped, same as every
    other telemetry reader in this codebase."""
    events_by_match = {}
    for match_id in match_ids:
        path = os.path.join(telemetry_dir, f"{match_id}-telemetry.json")
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            events_by_match[match_id] = json.load(f)
    return events_by_match


def select_telemetry_events(match_ids=None, telemetry_dir=TELEMETRY_DIR, events_by_match=None):
    """Return the list of parsed match events a signal function should
    iterate over.

    When events_by_match is given (see load_telemetry_events), reuse it
    instead of re-reading/re-parsing from disk - it may be a superset
    built for a wider caller (archetype_tag.py loads the union of
    tempo's and range/weapon's match sets once), so match_ids still
    applies as a filter either way. When events_by_match is None, this
    falls back to the original glob-and-parse-from-disk behavior.
    """
    if events_by_match is not None:
        if match_ids is None:
            return list(events_by_match.values())
        return [events_by_match[mid] for mid in match_ids if mid in events_by_match]

    events = []
    for path in glob.glob(os.path.join(telemetry_dir, "*-telemetry.json")):
        match_id = os.path.basename(path).replace("-telemetry.json", "")
        if match_ids is not None and match_id not in match_ids:
            continue
        with open(path, "r") as f:
            events.append(json.load(f))
    return events
