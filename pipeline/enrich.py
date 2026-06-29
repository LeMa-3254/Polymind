from __future__ import annotations

import json
from typing import Any

from models import Item
from pipeline.model_clients import add_token_usage, build_anthropic_client, read_prompt


def enrich_items(
    items: list[Item],
    config: dict[str, Any],
    *,
    model_client: Any | None = None,
    token_usage: dict[str, Any] | None = None,
) -> list[Item]:
    limit = config.get("enrich", {}).get("max_items_per_run", 40)
    client = model_client if model_client is not None else build_anthropic_client()
    enriched: list[Item] = []
    for item in sorted(items, key=lambda current: current.relevance_score or 0, reverse=True)[:limit]:
        if client is None:
            bootstrap_enrich_item(item)
        else:
            try:
                enrich_item_with_model(item, config, client=client, token_usage=token_usage)
            except Exception:
                bootstrap_enrich_item(item)
        enriched.append(item)
    return enriched


def enrich_item_with_model(
    item: Item,
    config: dict[str, Any],
    *,
    client: Any,
    token_usage: dict[str, Any] | None = None,
) -> Item:
    enrich = config.get("enrich", {})
    prompt = read_prompt(enrich.get("prompt", "prompts/enrich.md"))
    result, usage = client.complete_json(
        model=enrich["model"],
        system_prompt=prompt,
        user_prompt=json.dumps(enrich_payload(item), indent=2, sort_keys=True),
        max_tokens=512,
    )
    add_token_usage(token_usage, "anthropic_enrichment", usage)
    item.summary = str(result.get("summary") or item.abstract or item.title)
    item.why_it_matters = str(
        result.get("why_it_matters")
        or "Potentially relevant to AI-enabled polymer and materials development."
    )
    return item


def bootstrap_enrich_item(item: Item) -> Item:
    item.summary = item.abstract or item.title
    item.why_it_matters = "Potentially relevant to AI-enabled polymer and materials development."
    return item


def enrich_payload(item: Item) -> dict[str, Any]:
    return {
        "title": item.title,
        "url": item.url,
        "source_name": item.source_name,
        "published_date": item.published_date,
        "abstract": item.abstract,
        "relevance_score": item.relevance_score,
        "quality_score": item.quality_score,
        "score_reason": item.score_reason,
        "theme": item.theme,
    }
