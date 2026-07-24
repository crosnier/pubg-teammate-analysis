##########
# Unit Test for Telemetry URL parsing
# from root of project: `python -m unittest discover tests`
##########

import unittest
from api.telemetry_fetcher import get_telemetry_url


class TestGetTelemetryUrl(unittest.TestCase):

    def test_finds_telemetry_asset_url(self):
        metadata = {
            "included": [
                {"type": "asset", "attributes": {"URL": "https://example.com/telemetry-data.json"}},
                {"type": "roster", "attributes": {}},
            ]
        }

        self.assertEqual(get_telemetry_url(metadata), "https://example.com/telemetry-data.json")

    def test_ignores_non_asset_and_non_telemetry_entries(self):
        metadata = {
            "included": [
                {"type": "asset", "attributes": {"URL": "https://example.com/other-asset.json"}},
            ]
        }

        self.assertIsNone(get_telemetry_url(metadata))

    def test_missing_included_key_returns_none(self):
        self.assertIsNone(get_telemetry_url({}))


if __name__ == '__main__':
    unittest.main()
