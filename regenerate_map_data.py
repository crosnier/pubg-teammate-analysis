# ==============================
# regenerate_map_data.py - Drop Zone reference-data regeneration tool
# ==============================
"""
CLI wrapper around utils/map_calibration.py, for repeating Erangel's
research process (issue #44) on a new/changed map without re-deriving the
method from scratch each time.

This does NOT read POI positions off a map image for you - that step is
still a human (or vision-capable assistant) visually locating each named
town/POI's building cluster and recording its pixel position. What this
automates is everything after that: the pixel-to-world conversion and the
real-telemetry validation pass, plus a printed report flagging any POI
whose landing density looks anomalous relative to its peers.

Usage:
    python regenerate_map_data.py --map Tiger_Main --image-size 819 \
        --pixels '{"Ranger Station": [100, 200], "Yeon Myeong": [300, 400]}'

The printed POI_WORLD_COORDINATES / VALIDATION report is meant to be
hand-copied into utils/map_regions_data.py (or a new per-map sibling
module) in the same shape as ERANGEL_POI_PIXELS /
ERANGEL_LANDING_VALIDATION_400M, after a human reviews any NEEDS_REVIEW
flags - this tool deliberately doesn't write to that file automatically,
since a bad pixel reading silently overwriting validated data would be
worse than a manual copy-paste step.
"""
import argparse
import json

from utils.map_calibration import convert_pixels_to_world, validate_landing_density
from utils.map_regions_data import MAP_SIZE_CM


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate + validate Drop Zone POI reference data for one map."
    )
    parser.add_argument("--map", required=True, help="Telemetry mapName, e.g. Tiger_Main")
    parser.add_argument("--image-size", type=int, required=True,
                         help="Reference map image width/height in pixels (assumed square)")
    parser.add_argument("--pixels", required=True,
                         help='JSON object of {"POI Name": [px, py], ...} read off the map image')
    parser.add_argument("--radius-m", type=int, default=400,
                         help="Validation radius in meters (default: 400, matches Erangel's pass)")
    args = parser.parse_args()

    if args.map not in MAP_SIZE_CM:
        print(f"[ERROR] '{args.map}' has no verified MAP_SIZE_CM entry yet - "
              f"confirm the map's coordinate range against official docs before proceeding.")
        return

    pixel_coords = {name: tuple(xy) for name, xy in json.loads(args.pixels).items()}
    world_coords = convert_pixels_to_world(pixel_coords, MAP_SIZE_CM[args.map], args.image_size)

    print(f"[INFO] Validating {len(world_coords)} POIs against cached '{args.map}' telemetry "
          f"(radius: {args.radius_m}m)... this scans the whole telemetry cache and can take a "
          f"few minutes - progress prints every 100 files so it doesn't look hung.")
    validation = validate_landing_density(world_coords, args.map, radius_m=args.radius_m, progress_every=100)

    total_landings = sum(v["count"] for v in validation.values())
    if total_landings == 0:
        print(f"[WARN] Zero landings found on '{args.map}' in the cache - "
              f"nothing to validate against yet. Coordinates below are unverified.")

    print()
    print("# Paste into utils/map_regions_data.py (or a new per-map module), after review:")
    print(f"{args.map.upper()}_POI_PIXELS = {json.dumps(pixel_coords, indent=4)}")
    print()
    print(f"{args.map.upper()}_LANDING_VALIDATION_{args.radius_m}M = {{")
    for name, result in sorted(validation.items(), key=lambda kv: -kv[1]["count"]):
        flag = "  # NEEDS_REVIEW" if result["needs_review"] else ""
        print(f'    "{name}": {result["count"]},{flag}')
    print("}")


if __name__ == "__main__":
    main()
