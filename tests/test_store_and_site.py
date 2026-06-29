import tempfile
from pathlib import Path
import importlib.util
import unittest

from models import Item
from store.db import connect, included_items, init_db, log_run, upsert_items


SITE_BUILD_PATH = Path(__file__).resolve().parents[1] / "site" / "build.py"
SPEC = importlib.util.spec_from_file_location("polymind_site_build", SITE_BUILD_PATH)
site_build = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(site_build)


class StoreTests(unittest.TestCase):
    def test_init_upsert_and_query_included_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "tracker.db"
            item = Item.from_source(
                title="Machine learning for polymer design",
                url="https://example.test/paper",
                source_type="test",
                source_name="Example",
                tier="A",
            )
            item.status = "included"
            item.summary = "A useful test item."
            item.why_it_matters = "It proves the store path works."

            with connect(db_path) as db:
                init_db(db)
                upsert_items(db, [item])
                log_run(db, counts={"fetched": 1, "included": 1})
                rows = included_items(db)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Machine learning for polymer design")

    def test_static_render_includes_item_and_rss_metadata(self):
        config = {
            "site": {
                "name": "Polymind",
                "description": "Daily feed plus weekly synthesis.",
                "url": "https://polymind.github.io/",
            }
        }
        item = {
            "id": "abc123",
            "title": "Machine learning for polymer design",
            "url": "https://example.test/paper",
            "source_name": "Example",
            "published_date": "2026-06-29",
            "fetched_date": "2026-06-29",
            "theme": "property prediction",
            "summary": "A useful test item.",
            "abstract": None,
            "why_it_matters": "It proves rendering works.",
        }

        html = site_build.render_index(config, [item])
        rss = site_build.render_rss(config, [item])

        self.assertIn("Machine learning for polymer design", html)
        self.assertIn("https://polymind.github.io/", rss)


if __name__ == "__main__":
    unittest.main()
