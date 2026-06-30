import unittest

from models import Item
import sources.google_news as google_news
from sources.base import normalize_date, resolve_filter_placeholders, vocabulary_match
from sources.crossref import crossref_source_date, date_parts
from sources.google_news import GoogleNewsAdapter
from sources.journal_rss import parse_rss_or_atom
from sources.openalex import openalex_source_date, reconstruct_abstract
from sources.rss_feeds import UniversityNewsAdapter


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

    def test_parse_rss_tags_caller_source_type(self):
        payload = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Machine learning polymer discovery</title>
          <link>https://example.test/uni-item</link>
          <description>University press release.</description>
        </item></channel></rss>"""

        items = parse_rss_or_atom(
            payload, source_name="MIT News", tier="C", source_type="university_news"
        )

        self.assertEqual(items[0].source_type, "university_news")

    def test_feed_list_adapter_gates_by_vocabulary(self):
        on_topic = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Machine learning for polymer design</title>
          <link>https://example.test/on</link>
          <description>Materials informatics study.</description>
        </item></channel></rss>"""
        off_topic = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Campus wins football championship</title>
          <link>https://example.test/off</link>
          <description>Sports news.</description>
        </item></channel></rss>"""
        fetched: list[str] = []

        def fake_fetch(url, **kwargs):
            fetched.append(url)
            return on_topic if url.endswith("/on.rss") else off_topic

        adapter = UniversityNewsAdapter(
            CONFIG,
            {
                "tier": "C",
                "feeds": [
                    {"name": "On", "url": "https://example.test/on.rss"},
                    {"name": "Off", "url": "https://example.test/off.rss"},
                ],
            },
        )
        import sources.rss_feeds as rss_feeds

        original = rss_feeds.fetch_url
        rss_feeds.fetch_url = fake_fetch
        try:
            result = adapter.fetch()
        finally:
            rss_feeds.fetch_url = original

        self.assertEqual(len(fetched), 2)
        self.assertEqual([item.title for item in result.items], ["Machine learning for polymer design"])
        self.assertEqual(result.items[0].source_type, "university_news")

    def test_google_news_encodes_queries_and_gates(self):
        payload = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>New machine learning model designs recyclable polymer</title>
          <link>https://news.google.test/article</link>
          <description>Coverage of an AI polymer result.</description>
        </item></channel></rss>"""
        urls: list[str] = []

        def fake_fetch(url, **kwargs):
            urls.append(url)
            return payload

        adapter = GoogleNewsAdapter(
            CONFIG,
            {"tier": "C", "queries": ["machine learning polymer property prediction"]},
        )
        original = google_news.fetch_url
        google_news.fetch_url = fake_fetch
        try:
            result = adapter.fetch()
        finally:
            google_news.fetch_url = original

        self.assertEqual(len(urls), 1)
        self.assertIn("q=machine+learning+polymer+property+prediction", urls[0])
        self.assertEqual(result.items[0].source_type, "google_news")
        self.assertEqual(result.items[0].source_name, "Google News")

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

    def test_openalex_source_date_uses_record_date_when_publication_is_future(self):
        self.assertEqual(
            openalex_source_date(
                {
                    "publication_date": "2035-09-05",
                    "created_date": "2026-06-20",
                    "updated_date": "2026-06-21",
                }
            ),
            "2026-06-20",
        )

    def test_crossref_source_date_uses_created_date_when_publication_is_future(self):
        self.assertEqual(
            crossref_source_date(
                {
                    "published-print": {"date-parts": [[2035, 9, 5]]},
                    "published-online": {"date-parts": [[2026, 12, 31]]},
                    "created": {"date-parts": [[2026, 6, 20]]},
                }
            ),
            "2026-06-20",
        )


if __name__ == "__main__":
    unittest.main()
