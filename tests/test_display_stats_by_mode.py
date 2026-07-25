##########
# Unit Test for Player Stats display formatting
# from root of project: `python -m unittest discover tests`
##########

import unittest
from utils.display_stats_by_mode import format_number


class TestFormatNumber(unittest.TestCase):

    def test_formats_small_int_with_commas(self):
        self.assertEqual(format_number(1234), "1,234")

    def test_formats_large_value_in_thousands(self):
        self.assertEqual(format_number(150000), "150k")

    def test_converts_time_survived_seconds_to_minutes(self):
        self.assertEqual(format_number(120, key="longestTimeSurvived"), "2")

    def test_time_survived_lowercase_key_converts_to_minutes(self):
        self.assertEqual(format_number(120, key="timeSurvived"), "2")

    def test_non_numeric_value_defaults_to_zero(self):
        self.assertEqual(format_number(None), "0")


if __name__ == '__main__':
    unittest.main()
