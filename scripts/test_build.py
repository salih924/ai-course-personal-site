import unittest
from unittest.mock import patch
from urllib.error import URLError

from build import refresh_topics


class RefreshTests(unittest.TestCase):
    def test_failed_feed_keeps_its_date_while_other_feed_refreshes(self):
        saved = {"cars": {"updated": "2025-05-01", "stories": [{"title": "Previous story"}]}}
        fresh = [{"title": "New race story"}]
        topics = [
            {"slug": "cars", "name": "Cars", "feed": "https://example.org/cars"},
            {"slug": "racing", "name": "Racing", "feed": "https://example.org/racing"},
        ]
        with patch("build.fetch_stories", side_effect=[URLError("feed unavailable"), fresh]):
            result = refresh_topics(topics, saved)

        self.assertEqual(result["cars"], saved["cars"])
        self.assertEqual(result["racing"]["stories"], fresh)
        self.assertIn("updated", result["racing"])


if __name__ == "__main__":
    unittest.main()
