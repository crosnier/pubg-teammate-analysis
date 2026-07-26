# ==============================
# utils/map_calibration.py
# ==============================
"""
Reusable pieces of the Drop Zone research process (issue #44), factored
out of the ad hoc scripts used to build Erangel's reference data so the
next map doesn't repeat that process by hand from scratch.

What this DOES automate: pixel -> world coordinate conversion, and
telemetry-density validation of a set of candidate POI coordinates
(counting real LogParachuteLanding events near each one, flagging outliers
relative to the rest of that map's POIs).

What this deliberately does NOT automate: reading POI label positions off
the official map image in the first place. That step stays a human (or
vision-capable assistant) visually locating each named town/POI's building
cluster on the image - OCR/CV auto-detection of loot-map label positions
was not attempted and would be its own real research effort, not a
few-line addition. See regenerate_map_data.py for the CLI that ties this
together with that manual pixel-reading step.
"""
import glob
import json
import math
import os

TELEMETRY_DIR = "match-telemetry"

DEFAULT_VALIDATION_RADIUS_M = 400

# A POI's validated landing count below this fraction of the map's median
# POI count gets flagged NEEDS_REVIEW - same "notably lower than peers"
# standard used to originally flag Kameshki (520 vs a median in the
# thousands), not an arbitrary cutoff.
NEEDS_REVIEW_FRACTION_OF_MEDIAN = 0.5


def convert_pixels_to_world(pixel_coords, map_size_cm, image_size_px):
    """pixel_coords: {name: (px, py)} read off a map image of
    image_size_px, top-left origin. Returns {name: (x_cm, y_cm)} in the
    same coordinate system as telemetry's `location` fields."""
    scale = map_size_cm / image_size_px
    return {name: (px * scale, py * scale) for name, (px, py) in pixel_coords.items()}


def validate_landing_density(poi_world_coords, map_name, radius_m=DEFAULT_VALIDATION_RADIUS_M,
                              telemetry_dir=TELEMETRY_DIR, progress_every=None):
    """Count real LogParachuteLanding events within radius_m of each POI,
    across every cached match on map_name. Returns
    {poi_name: {"count": int, "needs_review": bool}} - flags whatever
    lands notably below the rest of this map's POIs, the same signal
    that originally caught Kameshki's low count (not proof of a wrong
    coordinate on its own, see map_regions_data.py's writeup of that
    case - just a prompt to re-examine placement).

    progress_every: if set, prints a "[INFO] Scanned X/Y cached files..."
    line every N files - the telemetry cache can be tens of GB, so a
    silent multi-minute scan is easy to mistake for a hang. None (default)
    stays silent, so this doesn't clutter unit test output.
    """
    radius_cm = radius_m * 100
    counts = {name: 0 for name in poi_world_coords}

    paths = glob.glob(os.path.join(telemetry_dir, "*-telemetry.json"))
    total = len(paths)
    for i, path in enumerate(paths, start=1):
        try:
            with open(path, "r") as f:
                events = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        start_event = next((e for e in events if e.get("_T") == "LogMatchStart"), None)
        if start_event and start_event.get("mapName") == map_name:
            for event in events:
                if event.get("_T") != "LogParachuteLanding":
                    continue
                location = (event.get("character") or {}).get("location")
                if not location:
                    continue
                for name, (px, py) in poi_world_coords.items():
                    if math.hypot(location["x"] - px, location["y"] - py) <= radius_cm:
                        counts[name] += 1

        if progress_every and i % progress_every == 0:
            print(f"[INFO] Scanned {i}/{total} cached files...", flush=True)

    sorted_counts = sorted(counts.values())
    median_count = sorted_counts[len(sorted_counts) // 2] if sorted_counts else 0
    threshold = median_count * NEEDS_REVIEW_FRACTION_OF_MEDIAN

    return {
        name: {"count": count, "needs_review": count < threshold}
        for name, count in counts.items()
    }
