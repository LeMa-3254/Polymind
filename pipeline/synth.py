from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import json
from typing import Any

from pipeline.model_clients import add_token_usage, build_anthropic_client, read_prompt


def current_week_bounds(today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def synthesize_week(
    items: list[Any],
    config: dict[str, Any],
    *,
    model_client: Any | None = None,
    token_usage: dict[str, Any] | None = None,
) -> str:
    if not items:
        return "No included items for this week yet."

    client = model_client if model_client is not None else build_anthropic_client()
    if client is None:
        return fallback_synthesis(items)

    synth = config.get("synth", {})
    prompt = read_prompt(synth.get("prompt", "prompts/synth.md"))
    try:
        result, usage = client.complete_json(
            model=synth["model"],
            system_prompt=prompt,
            user_prompt=json.dumps([item_payload(item) for item in items], indent=2, sort_keys=True),
            max_tokens=1600,
        )
    except Exception:
        return fallback_synthesis(items)
    add_token_usage(token_usage, "anthropic_synthesis", usage)
    return str(result.get("synthesis_md") or result.get("synthesis") or fallback_synthesis(items))


def fallback_synthesis(items: list[Any]) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in items:
        grouped[str(item_value(item, "theme") or "materials AI")].append(str(item_value(item, "title")))

    lines = ["## Weekly Synthesis", ""]
    for theme, titles in sorted(grouped.items()):
        lines.append(f"### {theme}")
        for title in titles[:5]:
            lines.append(f"- {title}")
        lines.append("")
    return "\n".join(lines).strip()


def item_payload(item: Any) -> dict[str, Any]:
    return {
        "id": item_value(item, "id"),
        "title": item_value(item, "title"),
        "url": item_value(item, "url"),
        "source_name": item_value(item, "source_name"),
        "published_date": item_value(item, "published_date"),
        "theme": item_value(item, "theme"),
        "summary": item_value(item, "summary"),
        "why_it_matters": item_value(item, "why_it_matters"),
    }


def item_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    try:
        return item[key]
    except (KeyError, TypeError, IndexError):
        return getattr(item, key, None)
