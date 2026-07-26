##########
# Unit Test for Map Drop Zone (issue #44)
# from root of project: `python -m unittest discover tests`
##########

import json
import os
import tempfile
import unittest

from utils.drop_zone import (
    classify_landing,
    compute_drop_zone_signal,
    compute_landing_read_from_events,
    MIN_MATCHES_FOR_SIGNAL,
)

ME = "account.me"

# Three POIs on a simple line, 1000cm apart, for easy hand-checked math.
POI_COORDS = {
    "Alpha": (0, 0),
    "Bravo": (1000, 0),
    "Charlie": (0, 1000),
}


def match_start_event(map_name="Baltic_Main"):
    return {"_T": "LogMatchStart", "mapName": map_name}


def player_create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id}}


def landing_event(account_id, x, y, char_type="user"):
    return {
        "_T": "LogParachuteLanding",
        "character": {
            "accountId": account_id,
            "type": char_type,
            "location": {"x": x, "y": y, "z": 0},
        },
    }


class TestClassifyLanding(unittest.TestCase):

    def test_confident_when_clearly_closest(self):
        # Landing near Alpha (offset southeast of it) - Bravo/Charlie are
        # both far away (ratio huge). Confident reads still carry a
        # compass direction, same as edge reads do.
        result = classify_landing(10, 10, POI_COORDS)
        self.assertEqual(result["description"], "near Alpha, southeast")
        self.assertEqual(result["nearest_poi"], "Alpha")

    def test_between_two_pois_when_ratio_near_one(self):
        # Equidistant from Alpha and Bravo (both 500cm away) - ratio == 1.0.
        result = classify_landing(500, 0, POI_COORDS)
        self.assertEqual(result["description"], "between Alpha and Bravo")
        self.assertEqual(result["zone_key"], "between:Alpha|Bravo")

    def test_edge_of_nearest_with_compass_direction_when_moderately_close(self):
        # 300cm from Alpha, 700cm from Bravo - ratio 2.33 is NOT in the edge
        # band (>= EDGE_RATIO 1.5), so pick a point that lands ratio ~1.3.
        # Distance to Alpha ~430, to Bravo ~570 -> ratio ~1.33.
        x, y = 430, 0
        result = classify_landing(x, y, POI_COORDS)
        self.assertIn("near the edge of Alpha", result["description"])
        self.assertEqual(result["nearest_poi"], "Alpha")

    def test_compass_direction_is_south_for_positive_y_offset(self):
        # Telemetry convention: y increases downward/south, not up.
        # (0, 430): nearest=Alpha(430), 2nd=Charlie(570), ratio 1.33 -> edge band,
        # so the compass qualifier actually appears in the description.
        result = classify_landing(0, 430, POI_COORDS)
        self.assertIn("near the edge of Alpha", result["description"])
        self.assertIn("south", result["description"])


class TestComputeLandingReadFromEvents(unittest.TestCase):

    def test_none_when_player_absent(self):
        events = [match_start_event()]
        self.assertIsNone(compute_landing_read_from_events(ME, events))

    def test_unsupported_map_flagged_not_crash(self):
        events = [match_start_event("Fictional_Main"), player_create_event(ME)]
        result = compute_landing_read_from_events(ME, events)
        self.assertFalse(result["supported_map"])
        self.assertEqual(result["map_name"], "Fictional_Main")

    def test_none_when_present_but_no_landing_event(self):
        events = [match_start_event(), player_create_event(ME)]
        self.assertIsNone(compute_landing_read_from_events(ME, events))

    def test_ignores_other_players_and_bots_landing_events(self):
        events = [
            match_start_event(),
            player_create_event(ME),
            landing_event("account.bot", 700000, 700000, char_type="user_ai"),
            landing_event("account.rival", 700000, 700000),
            landing_event(ME, 30000, 20000),
        ]
        result = compute_landing_read_from_events(ME, events)
        self.assertTrue(result["supported_map"])
        self.assertNotEqual(result["nearest_poi"], "Novorepnoye")


class TestComputeDropZoneSignal(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_match(self, match_id, events):
        path = os.path.join(self.tmpdir.name, f"{match_id}-telemetry.json")
        with open(path, "w") as f:
            json.dump(events, f)

    def test_none_below_minimum_matches(self):
        for i in range(MIN_MATCHES_FOR_SIGNAL - 1):
            self._write_match(f"m{i}", [
                match_start_event(), player_create_event(ME),
                landing_event(ME, 345 * 816000 / 819, 400 * 816000 / 819),
            ])

        result = compute_drop_zone_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result["drop_zone_description"])
        self.assertEqual(result["matches_on_supported_map"], MIN_MATCHES_FOR_SIGNAL - 1)

    def test_most_frequent_zone_wins_at_minimum_matches(self):
        scale = 816000 / 819
        # Slightly offset from Pochinki's exact center (not landing dead on
        # the point) so the compass direction below is well-defined rather
        # than an arbitrary atan2(0, 0) tie-break.
        pochinki = (345 * scale + 1000, 400 * scale + 1000)
        school = (430 * scale, 330 * scale)
        # 6 Pochinki landings, 2 School landings -> Pochinki should win.
        for i in range(6):
            self._write_match(f"p{i}", [
                match_start_event(), player_create_event(ME),
                landing_event(ME, *pochinki),
            ])
        for i in range(2):
            self._write_match(f"s{i}", [
                match_start_event(), player_create_event(ME),
                landing_event(ME, *school),
            ])

        result = compute_drop_zone_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["drop_zone_description"], "near Pochinki, southeast")
        self.assertEqual(result["top_zone_key"], "Baltic_Main||Pochinki")
        self.assertIsNotNone(result["top_zone_median_distance_m"])
        self.assertEqual(result["matches_on_supported_map"], MIN_MATCHES_FOR_SIGNAL)

    def test_same_poi_name_on_different_maps_not_merged(self):
        # "School" exists on both Erangel (Baltic_Main) and Taego
        # (Tiger_Main) - landings near each map's own "School" must not be
        # tallied together just because the name matches, or a player who
        # plays both maps would get an inflated, physically-meaningless
        # "School" read that mixes two different real locations.
        scale = 816000 / 819
        erangel_school = (430 * scale, 330 * scale)
        for i in range(MIN_MATCHES_FOR_SIGNAL):
            self._write_match(f"e{i}", [
                match_start_event("Baltic_Main"), player_create_event(ME),
                landing_event(ME, *erangel_school),
            ])
        taego_school_pixel_dict = __import__(
            "utils.map_regions_data", fromlist=["TAEGO_POI_PIXELS"]
        ).TAEGO_POI_PIXELS
        tpx, tpy = taego_school_pixel_dict["School"]
        taego_scale = 816000 / 819
        for i in range(MIN_MATCHES_FOR_SIGNAL):
            self._write_match(f"t{i}", [
                match_start_event("Tiger_Main"), player_create_event(ME),
                landing_event(ME, tpx * taego_scale, tpy * taego_scale),
            ])

        result = compute_drop_zone_signal(ME, telemetry_dir=self.tmpdir.name)

        # Each map's "School" should be its own zone_key, tied at
        # MIN_MATCHES_FOR_SIGNAL each - not merged into one 2x-count "School".
        self.assertEqual(result["zone_counts"].get("Baltic_Main||School"), MIN_MATCHES_FOR_SIGNAL)
        self.assertEqual(result["zone_counts"].get("Tiger_Main||School"), MIN_MATCHES_FOR_SIGNAL)

    def test_unsupported_map_matches_tracked_but_dont_count_toward_signal(self):
        for i in range(MIN_MATCHES_FOR_SIGNAL):
            self._write_match(f"u{i}", [
                match_start_event("Fictional_Main"), player_create_event(ME),
            ])

        result = compute_drop_zone_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertIsNone(result["drop_zone_description"])
        self.assertEqual(result["matches_on_supported_map"], 0)
        self.assertEqual(result["matches_analyzed"], MIN_MATCHES_FOR_SIGNAL)
        self.assertEqual(result["unsupported_maps_seen"], ["Fictional_Main"])

    def test_matches_player_absent_from_are_not_counted(self):
        self._write_match("other", [match_start_event()])

        result = compute_drop_zone_signal(ME, telemetry_dir=self.tmpdir.name)

        self.assertEqual(result["matches_analyzed"], 0)


if __name__ == '__main__':
    unittest.main()
