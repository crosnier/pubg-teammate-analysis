##########
# Unit Test for Match Pathing display formatting (issue #8)
# from root of project: `python -m unittest discover tests`
##########

import unittest

from utils.display_match_pathing import format_match_pathing_line


def pathing(map_name="Baltic_Main", mode_label="Squad TPP", supported_map=True, path_description=None):
    return {
        "map_name": map_name,
        "mode_label": mode_label,
        "supported_map": supported_map,
        "path_description": path_description,
    }


class TestFormatMatchPathingLine(unittest.TestCase):

    def test_none_when_pathing_is_none(self):
        self.assertIsNone(format_match_pathing_line(None))

    def test_unsupported_map_line(self):
        line = format_match_pathing_line(pathing(map_name="Summerland_Main", supported_map=False))
        self.assertIn("Karakin", line)
        self.assertIn("not yet supported", line)

    def test_not_enough_data_line(self):
        line = format_match_pathing_line(pathing(path_description=None))
        self.assertIn("not enough position data", line)

    def test_full_line_includes_map_mode_and_path(self):
        line = format_match_pathing_line(pathing(path_description="Pochinki → School → Mylta"))
        self.assertIn("Erangel", line)
        self.assertIn("Squad TPP", line)
        self.assertIn("Pochinki → School → Mylta", line)

    def test_falls_back_to_raw_map_name_when_unmapped(self):
        line = format_match_pathing_line(pathing(map_name="Unknown_Map", path_description="A → B"))
        self.assertIn("Unknown_Map", line)


if __name__ == '__main__':
    unittest.main()
