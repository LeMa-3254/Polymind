from __future__ import annotations

from typing import Any

from models import Item


def enrich_items(items: list[Item], config: dict[str, Any]) -> list[Item]:
    limit = config.get("enrich", {}).get("max_items_per_run", 40)
    enriched: list[Item] = []
    for item in sorted(items, key=lambda current: current.relevance_score or 0, reverse=True)[:limit]:
        item.summary = item.abstract or item.title
        item.why_it_matters = "Potentially relevant to AI-enabled polymer and materials development."
        enriched.append(item)
    return enriched

