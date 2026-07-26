##########
# Unit Test for Drop Zone + Flow display formatting (issue #44)
# from root of project: `python -m unittest discover tests`
##########

import unittest

from utils.display_drop_zone import format_drop_zone_line, format_flow_line


def drop_zone_signal(description=None, distance_m=None, matches_analyzed=0, matches_on_supported_map=0):
    return {
        "drop_zone_description": description,
        "top_zone_median_distance_m": distance_m,
        "matches_analyzed": matches_analyzed,
        "matches_on_supported_map": matches_on_supported_map,
    }


class TestFormatDropZoneLine(unittest.TestCase):

    def test_includes_distance_when_available(self):
        signal = drop_zone_signal("near Pochinki, southeast", distance_m=304.8, matches_analyzed=8,
                                   matches_on_supported_map=8)
        line = format_drop_zone_line(signal)
        self.assertEqual(line, "You typically drop near Pochinki, southeast (~305m from center).")

    def test_omits_distance_for_between_reads(self):
        # "between X and Y" zones never get a top_zone_median_distance_m
        # (see compute_drop_zone_signal) - no unambiguous single anchor.
        signal = drop_zone_signal("between Sosnovka Island and Sosnovka Military Base", distance_m=None,
                                   matches_analyzed=8, matches_on_supported_map=8)
        line = format_drop_zone_line(signal)
        self.assertEqual(line, "You typically drop between Sosnovka Island and Sosnovka Military Base.")

    def test_unsupported_map_fallback(self):
        signal = drop_zone_signal(matches_analyzed=8, matches_on_supported_map=0)
        line = format_drop_zone_line(signal)
        self.assertEqual(line, "Drop zone: map not yet supported for tracking.")

    def test_none_when_no_data(self):
        signal = drop_zone_signal()
        self.assertIsNone(format_drop_zone_line(signal))


class TestFormatFlowLine(unittest.TestCase):

    def test_known_tag(self):
        self.assertIn("center", format_flow_line({"flow_tag": "Zone Center"}))

    def test_none_when_no_tag(self):
        self.assertIsNone(format_flow_line({"flow_tag": None}))


if __name__ == '__main__':
    unittest.main()
