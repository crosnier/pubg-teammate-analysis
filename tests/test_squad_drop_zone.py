##########
# Unit Test for Squad Drop Zone consolidation (issue #44)
# from root of project: `python -m unittest discover tests`
##########

import unittest

from utils.squad_drop_zone import compute_squad_drop_zone_consolidation


def member(name, top_zone_key):
    signal = {"top_zone_key": top_zone_key} if top_zone_key else None
    return {"name": name, "drop_zone_signal": signal}


class TestComputeSquadDropZoneConsolidation(unittest.TestCase):

    def test_no_consensus_when_all_members_differ(self):
        members = [
            member("A", "Baltic_Main||Pochinki"),
            member("B", "Baltic_Main||School"),
            member("C", "Baltic_Main||Mylta"),
        ]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIsNone(result["best_fit_line"])
        self.assertIsNone(result["change_it_up_line"])

    def test_no_consensus_when_no_members_have_a_signal(self):
        members = [member("A", None), member("B", None)]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIsNone(result["best_fit_line"])

    def test_best_fit_when_two_members_share_a_poi(self):
        members = [
            member("A", "Baltic_Main||Pochinki"),
            member("B", "Baltic_Main||Pochinki"),
            member("C", "Baltic_Main||School"),
        ]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIn("Pochinki", result["best_fit_line"])
        self.assertIn("2 of 3", result["best_fit_line"])

    def test_edge_and_between_zone_keys_still_count_toward_their_poi(self):
        # "edge:Pochinki" and "between:Pochinki|School" both gravitate
        # toward Pochinki even though neither is a plain "Pochinki" read.
        members = [
            member("A", "Baltic_Main||edge:Pochinki"),
            member("B", "Baltic_Main||between:Pochinki|School"),
        ]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIn("Pochinki", result["best_fit_line"])

    def test_same_poi_name_on_different_maps_does_not_count_as_consensus(self):
        # "School" exists on both Erangel and Taego - a member converging
        # on Erangel's School and another converging on Taego's School are
        # NOT the same real spot and must not be treated as agreement.
        members = [
            member("A", "Baltic_Main||School"),
            member("B", "Tiger_Main||School"),
        ]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIsNone(result["best_fit_line"])

    def test_change_it_up_suggests_a_real_and_distant_poi(self):
        members = [member("A", "Baltic_Main||Zharki"), member("B", "Baltic_Main||Zharki")]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIsNotNone(result["change_it_up_line"])
        # Should not suggest Zharki itself, and should be a real POI name.
        self.assertNotIn("try Zharki", result["change_it_up_line"])

    def test_change_it_up_avoids_unpopular_dead_corners(self):
        # Zharki (23 landings) is the map's most extreme dead corner - it
        # should never be suggested as the "change it up" alternative,
        # even when it's geographically the farthest option from School.
        members = [member("A", "Baltic_Main||School"), member("B", "Baltic_Main||School")]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertNotIn("Zharki", result["change_it_up_line"])

    def test_change_it_up_works_on_a_non_erangel_map(self):
        # Rondo (Neon_Main) consensus should get its own map's "change it
        # up" suggestion, not silently fall back to nothing just because
        # the consolidation logic used to be Erangel-only.
        members = [member("A", "Neon_Main||Yu Lin"), member("B", "Neon_Main||Yu Lin")]
        result = compute_squad_drop_zone_consolidation(members)
        self.assertIsNotNone(result["change_it_up_line"])
        self.assertNotIn("try Yu Lin", result["change_it_up_line"])


if __name__ == '__main__':
    unittest.main()
