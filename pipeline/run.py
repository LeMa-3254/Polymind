from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from pipeline.dedup import deduplicate_items
from pipeline.embeddings import embed_items
from pipeline.enrich import enrich_items
from pipeline.ingest import ingest_enabled_sources
from pipeline.score import score_item
from pipeline.synth import current_week_bounds, synthesize_week
from store.db import (
    connect,
    included_items_between,
    init_db,
    log_run,
    recent_embedding_memory,
    upsert_items,
    upsert_weekly_summary,
)


def run_pipeline(
    config_path: str = "targeting.yaml",
    db_path: str = "data/tracker.db",
    *,
    weekly_synthesis: bool = False,
) -> int:
    config = load_config(config_path)
    token_usage: dict = {}
    items, errors = ingest_enabled_sources(config)
    scored = [score_item(item, config, token_usage=token_usage) for item in items]
    embed_items(scored, config, token_usage=token_usage)

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as db:
        init_db(db)
        memory = recent_embedding_memory(
            db,
            window_days=int(config.get("dedup", {}).get("window_days", 30)),
        )
        deduped = deduplicate_items(scored, memory, config)
        included = [item for item in deduped if item.status == "included"]
        enriched = enrich_items(included, config, token_usage=token_usage)
        upsert_items(db, deduped)
        if weekly_synthesis:
            week_start, week_end = current_week_bounds()
            weekly_items = included_items_between(db, start_date=week_start, end_date=week_end)
            synthesis_md = synthesize_week(weekly_items, config, token_usage=token_usage)
            upsert_weekly_summary(
                db,
                week_start=week_start,
                week_end=week_end,
                synthesis_md=synthesis_md,
                item_ids=[item["id"] for item in weekly_items],
            )
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
            token_usage=token_usage,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Polymind tracker pipeline")
    parser.add_argument("--config", default="targeting.yaml")
    parser.add_argument("--db", default="data/tracker.db")
    parser.add_argument("--weekly-synthesis", action="store_true")
    args = parser.parse_args()
    return run_pipeline(config_path=args.config, db_path=args.db, weekly_synthesis=args.weekly_synthesis)


if __name__ == "__main__":
    raise SystemExit(main())
