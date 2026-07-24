##########
# Unit Test for Player Index normalization
# from root of project: `python -m unittest discover tests`
##########

import unittest
from api.player_index import normalize_filename


class TestNormalizeFilename(unittest.TestCase):

    def test_lowercases_and_strips_spaces(self):
        self.assertEqual(normalize_filename("Some Player"), "someplayer")

    def test_strips_leading_and_trailing_whitespace(self):
        self.assertEqual(normalize_filename("  Player  "), "player")

    def test_handles_already_normalized_input(self):
        self.assertEqual(normalize_filename("player"), "player")


if __name__ == '__main__':
    unittest.main()
