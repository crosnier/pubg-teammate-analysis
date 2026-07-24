##########
# Unit Test for Match History parsing
# from root of project: `python -m unittest discover tests`
##########

import unittest
from utils.display_match_history import extract_match_ids_by_mode


class TestExtractMatchIdsByMode(unittest.TestCase):

    def test_groups_matches_by_normalized_mode(self):
        stats = {
            "data": {
                "relationships": {
                    "matchesSoloFPP": {"data": [{"id": "m1"}, {"id": "m2"}]},
                    "matchesDuo": {"data": [{"id": "m3"}]},
                    "roster": {"data": []},
                }
            }
        }

        result = extract_match_ids_by_mode(stats)

        self.assertEqual(result["solo-fpp"], ["m1", "m2"])
        self.assertEqual(result["duo"], ["m3"])
        self.assertNotIn("roster", result)

    def test_empty_matches_key_maps_to_unknown(self):
        stats = {"data": {"relationships": {"matches": {"data": [{"id": "m1"}]}}}}

        result = extract_match_ids_by_mode(stats)

        self.assertEqual(result["unknown"], ["m1"])

    def test_missing_data_key_yields_empty_list(self):
        stats = {"data": {"relationships": {"matchesSquad": {}}}}

        result = extract_match_ids_by_mode(stats)

        self.assertEqual(result["squad"], [])


if __name__ == '__main__':
    unittest.main()
