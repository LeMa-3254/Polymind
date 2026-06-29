from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config
from pipeline.dedup import deduplicate_items
from pipeline.enrich import enrich_items
from pipeline.ingest import ingest_enabled_sources
from pipeline.score import score_item
from store.db import connect, init_db, log_run, recent_embedding_memory, upsert_items


def run_pipeline(config_path: str = "targeting.yaml", db_path: str = "data/tracker.db") -> int:
    config = load_config(config_path)
    items, errors = ingest_enabled_sources(config)
    scored = [score_item(item, config) for item in items]

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as db:
        init_db(db)
        memory = recent_embedding_memory(
            db,
            window_days=int(config.get("dedup", {}).get("window_days", 30)),
        )
        deduped = deduplicate_items(scored, memory, config)
        included = [item for item in deduped if item.status == "included"]
        enriched = enrich_items(included, config)
        upsert_items(db, deduped)
        log_run(
            db,
            counts={
                "fetched": len(items),
                "scored": len(scored),
                "included": len(enriched),
                "duplicates": sum(1 for item in deduped if item.status == "dropped_dup"),
                "errors": len(errors),
            },
            errors=errors,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Polymind tracker pipeline")
    parser.add_argument("--config", default="targeting.yaml")
    parser.add_argument("--db", default="data/tracker.db")
    args = parser.parse_args()
    return run_pipeline(config_path=args.config, db_path=args.db)


if __name__ == "__main__":
    raise SystemExit(main())
