from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from models import Item
from pipeline.dedup import deduplicate_items
from pipeline.embeddings import embed_items
from pipeline.enrich import enrich_items
from pipeline.ingest import ingest_enabled_sources
from pipeline.score import score_item
from pipeline.synth import last_complete_week_bounds, synthesize_week
from sources.base import vocabulary_match
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
    candidates = prefilter_candidates(items, config)
    scored = [score_item(item, config, token_usage=token_usage) for item in candidates]
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
            week_start, week_end = last_complete_week_bounds()
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
                "candidates": len(candidates),
                "scored": len(scored),
                "included": len(enriched),
                "duplicates": sum(1 for item in deduped if item.status == "dropped_dup"),
                "errors": len(errors),
            },
            errors=errors,
            token_usage=token_usage,
        )
    return 0


def prefilter_candidates(items: list[Item], config: dict) -> list[Item]:
    """Drop items that miss the keyword gate, then keep the most promising N (polymer-first,
    most recent) before any LLM scoring — fewer model calls, faster runs, tighter scope."""
    gated = [item for item in items if vocabulary_match(item, config)]
    boost_terms = [term.lower() for term in config.get("targeting", {}).get("polymer_boost_terms", [])]

    def is_polymer(item: Item) -> bool:
        text = f"{item.title} {item.abstract or ''}".lower()
        return any(term in text for term in boost_terms)

    gated.sort(key=lambda it: (it.published_date or it.fetched_date or ""), reverse=True)
    gated.sort(key=lambda it: 0 if is_polymer(it) else 1)  # stable: polymer first, recency preserved
    cap = int(config.get("scoring", {}).get("max_candidates", 0) or 0)
    return gated[:cap] if cap else gated


def item_from_row(row) -> Item:
    return Item(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        source_type=row["source_type"],
        source_name=row["source_name"],
        tier=row["tier"],
        authors=json.loads(row["authors"]) if row["authors"] else [],
        published_date=row["published_date"],
        fetched_date=row["fetched_date"],
        abstract=row["abstract"],
        doi=row["doi"],
        embedding=json.loads(row["embedding"]) if row["embedding"] else None,
        relevance_score=row["relevance_score"],
        quality_score=row["quality_score"],
        score_reason=row["score_reason"],
        theme=row["theme"],
        summary=row["summary"],
        why_it_matters=row["why_it_matters"],
        digest_date=row["digest_date"],
        status=row["status"],
        dup_of=row["dup_of"],
    )


def rescore_archive(
    config_path: str = "targeting.yaml",
    db_path: str = "data/tracker.db",
    *,
    weekly_synthesis: bool = True,
) -> int:
    """One-time maintenance: re-score every stored item against the current rubric.

    Drops items that no longer pass and reassigns the theme, so a targeting change applies
    to the whole archive (not just newly fetched items). Preserves existing summaries,
    why-it-matters text, and embeddings."""
    config = load_config(config_path)
    token_usage: dict = {}
    with connect(db_path) as db:
        init_db(db)
        rows = list(db.execute("SELECT * FROM items"))
        before = sum(1 for row in rows if row["status"] == "included")
        rescored = [score_item(item_from_row(row), config, token_usage=token_usage) for row in rows]
        upsert_items(db, rescored)
        after = sum(1 for item in rescored if item.status == "included")
        if weekly_synthesis:
            week_start, week_end = last_complete_week_bounds()
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
            counts={"rescored": len(rows), "included_before": before, "included_after": after},
            token_usage=token_usage,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Polymind tracker pipeline")
    parser.add_argument("--config", default="targeting.yaml")
    parser.add_argument("--db", default="data/tracker.db")
    parser.add_argument("--weekly-synthesis", action="store_true")
    parser.add_argument("--rescore-all", action="store_true", help="Re-score the whole archive against the current rubric")
    args = parser.parse_args()
    if args.rescore_all:
        return rescore_archive(config_path=args.config, db_path=args.db)
    return run_pipeline(config_path=args.config, db_path=args.db, weekly_synthesis=args.weekly_synthesis)


if __name__ == "__main__":
    raise SystemExit(main())
