import unittest

from models import Item
from sources.base import normalize_date, resolve_filter_placeholders, vocabulary_match
from sources.crossref import date_parts
from sources.journal_rss import parse_rss_or_atom
from sources.openalex import reconstruct_abstract


CONFIG = {
    "targeting": {
        "ai_terms": ["machine learning", "generative model"],
        "materials_terms": ["polymer", "materials"],
        "exclude_terms": ["clinical trial"],
    }
}


class SourceTests(unittest.TestCase):
    def test_vocabulary_match_requires_ai_and_materials_terms(self):
        item = Item.from_source(
            title="Machine learning for polymer property prediction",
            url="https://example.test/item",
            source_type="test",
            source_name="Test",
            tier="A",
        )

        self.assertTrue(vocabulary_match(item, CONFIG))

    def test_vocabulary_match_hard_drops_excludes(self):
        item = Item.from_source(
            title="Machine learning polymer clinical trial",
            url="https://example.test/item",
            source_type="test",
            source_name="Test",
            tier="A",
        )

        self.assertFalse(vocabulary_match(item, CONFIG))

    def test_parse_rss_feed(self):
        payload = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Machine learning polymer discovery</title>
          <link>https://example.test/rss-item</link>
          <description>New materials informatics result.</description>
          <pubDate>Mon, 29 Jun 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>"""

        items = parse_rss_or_atom(payload, source_name="Example Journal", tier="A")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source_name, "Example Journal")
        self.assertEqual(items[0].published_date, "2026-06-29")

    def test_reconstruct_openalex_abstract(self):
        self.assertEqual(
            reconstruct_abstract({"polymer": [1], "AI": [0], "design": [2]}),
            "AI polymer design",
        )

    def test_resolve_lookback_date_placeholder(self):
        resolved = resolve_filter_placeholders(
            {"from_publication_date": "{lookback_date}"},
            {"meta": {"lookback_hours": 48}},
        )

        self.assertRegex(resolved["from_publication_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_normalize_date_rejects_future_dates(self):
        self.assertIsNone(normalize_date("2035-09-05"))

    def test_crossref_date_parts_rejects_future_dates(self):
        self.assertIsNone(date_parts({"date-parts": [[2035, 9, 5]]}))


if __name__ == "__main__":
    unittest.main()
