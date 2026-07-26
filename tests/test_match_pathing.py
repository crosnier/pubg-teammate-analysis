##########
# Unit Test for Match Pathing text narrative (issue #8)
# from root of project: `python -m unittest discover tests`
##########

import unittest
from unittest.mock import patch

from utils.match_pathing import compute_match_pathing

ME = "account.me"

# Three POIs on a simple line, 1000cm apart, for easy hand-checked stops.
POI_COORDS = {
    "Alpha": (0, 0),
    "Bravo": (1000, 0),
    "Charlie": (2000, 0),
}
TEST_LOOKUP = {"Test_Main": POI_COORDS}


def match_start_event(map_name="Test_Main", team_size=4, view="FpsAndTps"):
    return {"_T": "LogMatchStart", "mapName": map_name, "teamSize": team_size, "cameraViewBehaviour": view}


def player_create_event(account_id):
    return {"_T": "LogPlayerCreate", "character": {"accountId": account_id}}


def position_event(account_id, elapsed_time, x, y):
    return {
        "_T": "LogPlayerPosition",
        "elapsedTime": elapsed_time,
        "character": {"accountId": account_id, "type": "user", "location": {"x": x, "y": y, "z": 0}},
    }


@patch("utils.match_pathing.MAP_POI_LOOKUP", TEST_LOOKUP)
class TestComputeMatchPathing(unittest.TestCase):

    def test_none_when_player_absent(self):
        events = [match_start_event()]
        self.assertIsNone(compute_match_pathing(ME, "m1", events))

    def test_unsupported_map_falls_back_gracefully(self):
        events = [
            match_start_event(map_name="Unmapped_Main"),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertFalse(result["supported_map"])
        self.assertIsNone(result["path_description"])
        self.assertEqual(result["map_name"], "Unmapped_Main")

    def test_mode_label_solo_fpp(self):
        events = [
            match_start_event(team_size=1, view="FpsOnly"),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertEqual(result["mode_label"], "Solo FPP")

    def test_mode_label_duo_tpp(self):
        events = [
            match_start_event(team_size=2, view="FpsAndTps"),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertEqual(result["mode_label"], "Duo TPP")

    def test_path_collapses_consecutive_same_poi_stops(self):
        events = [
            match_start_event(),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),      # Alpha
            position_event(ME, 10, 10, 0),    # Alpha again - collapsed
            position_event(ME, 20, 1000, 0),  # Bravo
            position_event(ME, 30, 2000, 0),  # Charlie
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertEqual(result["path_description"], "Alpha → Bravo → Charlie")

    def test_none_path_when_fewer_than_two_stops(self):
        events = [
            match_start_event(),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),
            position_event(ME, 10, 10, 0),
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertIsNone(result["path_description"])

    def test_downsamples_long_trails_to_max_stops(self):
        events = [match_start_event(), player_create_event(ME)]
        # 10 distinct POIs isn't possible with only 3 named ones, so
        # alternate between two POIs to force a long raw stop list, then
        # confirm the final trail never exceeds MAX_PATH_STOPS.
        for i in range(10):
            x = 0 if i % 2 == 0 else 1000
            events.append(position_event(ME, i * 10, x, 0))
        result = compute_match_pathing(ME, "m1", events)
        stops = result["path_description"].split(" → ")
        self.assertLessEqual(len(stops), 6)
        self.assertEqual(stops[0], "Alpha")
        self.assertEqual(stops[-1], "Bravo")

    def test_ignores_other_players_and_bots(self):
        events = [
            match_start_event(),
            player_create_event(ME),
            position_event(ME, 0, 0, 0),
            position_event(ME, 10, 2000, 0),
            {
                "_T": "LogPlayerPosition",
                "elapsedTime": 5,
                "character": {"accountId": "account.rival", "type": "user", "location": {"x": 1000, "y": 0, "z": 0}},
            },
            {
                "_T": "LogPlayerPosition",
                "elapsedTime": 6,
                "character": {"accountId": ME, "type": "user_ai", "location": {"x": 1000, "y": 0, "z": 0}},
            },
        ]
        result = compute_match_pathing(ME, "m1", events)
        self.assertEqual(result["path_description"], "Alpha → Charlie")


if __name__ == '__main__':
    unittest.main()
