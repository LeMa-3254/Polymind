from pathlib import Path
import tempfile
import unittest

from models import Item
import pipeline.run as pipeline_run
from store.db import connect


class PipelineRunTests(unittest.TestCase):
    def test_pipeline_dry_run_writes_items_run_log_and_weekly_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "targeting.yaml"
            db_path = root / "tracker.db"
            week_start, _week_end = pipeline_run.last_complete_week_bounds()
            config_path.write_text(
                "\n".join(
                    [
                        "site:",
                        "  name: Polymind",
                        "  description: Daily feed plus weekly synthesis.",
                        "  url: https://polymind.github.io/",
                        "targeting:",
                        "  ai_terms: [machine learning]",
                        "  materials_terms: [polymer]",
                        "  exclude_terms: []",
                        "  polymer_boost_terms: [polymer]",
                        "sources: {}",
                        "scoring:",
                        "  min_score: 3",
                        "  polymer_boost: 0.5",
                        "  source_tier_prior:",
                        "    A: 0.5",
                        "dedup:",
                        "  window_days: 30",
                        "  similarity_threshold: 0.92",
                        "  on_duplicate: drop",
                        "enrich:",
                        "  max_items_per_run: 5",
                        "synth: {}",
                    ]
                ),
                encoding="utf-8",
            )

            def fake_ingest(_config):
                item = Item.from_source(
                    title="Machine learning for polymer design",
                    url="https://example.test/paper",
                    source_type="test",
                    source_name="Example",
                    tier="A",
                    published_date=week_start,
                    abstract="A polymer property prediction paper.",
                )
                return [item], []

            original_ingest = pipeline_run.ingest_enabled_sources
            pipeline_run.ingest_enabled_sources = fake_ingest
            try:
                exit_code = pipeline_run.run_pipeline(
                    config_path=str(config_path),
                    db_path=str(db_path),
                    weekly_synthesis=True,
                )
            finally:
                pipeline_run.ingest_enabled_sources = original_ingest

            self.assertEqual(exit_code, 0)
            with connect(db_path) as db:
                item_count = db.execute("SELECT COUNT(*) FROM items WHERE status = 'included'").fetchone()[0]
                run_count = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
                weekly_count = db.execute("SELECT COUNT(*) FROM weekly_summaries").fetchone()[0]

        self.assertEqual(item_count, 1)
        self.assertEqual(run_count, 1)
        self.assertEqual(weekly_count, 1)


if __name__ == "__main__":
    unittest.main()
