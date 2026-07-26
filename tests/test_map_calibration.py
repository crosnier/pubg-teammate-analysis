##########
# Unit Test for Map Calibration (Drop Zone regeneration tooling, issue #44)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.map_calibration import convert_pixels_to_world, validate_landing_density


def match_start_event(map_name):
    return {"_T": "LogMatchStart", "mapName": map_name}


def landing_event(x, y):
    return {"_T": "LogParachuteLanding", "character": {"location": {"x": x, "y": y, "z": 0}}}


class TestConvertPixelsToWorld(unittest.TestCase):

    def test_scales_pixels_by_map_size_over_image_size(self):
        pixels = {"Alpha": (100, 200)}
        result = convert_pixels_to_world(pixels, map_size_cm=800000, image_size_px=800)
        self.assertEqual(result["Alpha"], (100000, 200000))

    def test_handles_multiple_pois(self):
        pixels = {"Alpha": (0, 0), "Bravo": (400, 400)}
        result = convert_pixels_to_world(pixels, map_size_cm=800000, image_size_px=800)
        self.assertEqual(result["Alpha"], (0, 0))
        self.assertEqual(result["Bravo"], (400000, 400000))


class TestValidateLandingDensity(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, map_name, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump([match_start_event(map_name)] + events, f)

    def test_counts_landings_within_radius(self):
        poi_coords = {"Alpha": (0, 0)}
        # 300m (30000cm) away - inside the default 400m radius.
        self._write_match("m1", "TestMap", [landing_event(30000, 0)])

        result = validate_landing_density(poi_coords, "TestMap", telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["Alpha"]["count"], 1)

    def test_excludes_landings_outside_radius(self):
        poi_coords = {"Alpha": (0, 0)}
        # 500m away - outside the default 400m radius.
        self._write_match("m1", "TestMap", [landing_event(50000, 0)])

        result = validate_landing_density(poi_coords, "TestMap", telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["Alpha"]["count"], 0)

    def test_excludes_other_maps(self):
        poi_coords = {"Alpha": (0, 0)}
        self._write_match("m1", "OtherMap", [landing_event(1000, 0)])

        result = validate_landing_density(poi_coords, "TestMap", telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["Alpha"]["count"], 0)

    def test_flags_outlier_low_count_as_needs_review(self):
        poi_coords = {"Popular": (0, 0), "Dead": (1000000, 1000000)}
        events = [landing_event(0, 0) for _ in range(20)]  # all at Popular
        self._write_match("m1", "TestMap", events)

        result = validate_landing_density(poi_coords, "TestMap", telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["Popular"]["count"], 20)
        self.assertFalse(result["Popular"]["needs_review"])
        self.assertEqual(result["Dead"]["count"], 0)
        self.assertTrue(result["Dead"]["needs_review"])


if __name__ == '__main__':
    unittest.main()
