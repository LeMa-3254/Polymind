from __future__ import annotations

from typing import Any

from models import Item
from sources.base import vocabulary_match


def score_item(item: Item, config: dict[str, Any]) -> Item:
    scoring = config.get("scoring", {})
    tier_prior = scoring.get("source_tier_prior", {}).get(item.tier, 0)
    base_relevance = 3 if vocabulary_match(item, config) else 1
    text = f"{item.title} {item.abstract or ''}".lower()
    boost_terms = [term.lower() for term in config.get("targeting", {}).get("polymer_boost_terms", [])]
    boost = scoring.get("polymer_boost", 0) if any(term in text for term in boost_terms) else 0

    item.relevance_score = min(5, base_relevance + boost + tier_prior)
    item.quality_score = min(5, 3 + tier_prior)
    item.score_reason = "Keyword/tier bootstrap score; replace with configured model scoring."
    item.theme = infer_theme(item)
    item.status = "included" if item.relevance_score >= scoring.get("min_score", 3) else "dropped_lowscore"
    return item


def infer_theme(item: Item) -> str:
    text = f"{item.title} {item.abstract or ''}".lower()
    if "self-driving" in text or "autonomous" in text:
        return "autonomous labs"
    if "generative" in text or "inverse design" in text:
        return "generative design"
    if "property" in text or "qspr" in text:
        return "property prediction"
    return "materials AI"

