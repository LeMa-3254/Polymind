from __future__ import annotations

import json
from typing import Any

from models import Item
from pipeline.model_clients import add_token_usage, build_anthropic_client, read_prompt
from sources.base import vocabulary_match


def score_item(
    item: Item,
    config: dict[str, Any],
    *,
    model_client: Any | None = None,
    token_usage: dict[str, Any] | None = None,
) -> Item:
    client = model_client if model_client is not None else build_anthropic_client()
    if client is not None:
        try:
            return score_item_with_model(item, config, client=client, token_usage=token_usage)
        except Exception as exc:
            bootstrap_score_item(item, config)
            item.score_reason = f"Model scoring failed; bootstrap fallback used: {exc}"
            return item
    return bootstrap_score_item(item, config)


def score_item_with_model(
    item: Item,
    config: dict[str, Any],
    *,
    client: Any,
    token_usage: dict[str, Any] | None = None,
) -> Item:
    scoring = config.get("scoring", {})
    prompt = read_prompt(scoring.get("rubric_prompt", "prompts/relevance.md"))
    result, usage = client.complete_json(
        model=scoring["model"],
        system_prompt=prompt,
        user_prompt=json.dumps(item_payload(item), indent=2, sort_keys=True),
        max_tokens=512,
    )
    add_token_usage(token_usage, "anthropic_scoring", usage)
    apply_score_result(item, config, result)
    return item


def bootstrap_score_item(item: Item, config: dict[str, Any]) -> Item:
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


def apply_score_result(item: Item, config: dict[str, Any], result: dict[str, Any]) -> None:
    scoring = config.get("scoring", {})
    raw_relevance = clamp_score(result.get("relevance"))
    raw_quality = clamp_score(result.get("quality"))
    tier_prior = float(scoring.get("source_tier_prior", {}).get(item.tier, 0))
    text = f"{item.title} {item.abstract or ''}".lower()
    boost_terms = [term.lower() for term in config.get("targeting", {}).get("polymer_boost_terms", [])]
    boost = float(scoring.get("polymer_boost", 0)) if any(term in text for term in boost_terms) else 0

    item.relevance_score = min(5, raw_relevance + boost + tier_prior)
    item.quality_score = raw_quality
    item.score_reason = str(result.get("reason") or "Model scored relevance and quality.")
    item.theme = str(result.get("theme") or infer_theme(item))
    item.status = "included" if item.relevance_score >= scoring.get("min_score", 3) else "dropped_lowscore"


def clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 1.0
    return max(1.0, min(5.0, score))


def item_payload(item: Item) -> dict[str, Any]:
    return {
        "title": item.title,
        "url": item.url,
        "source_type": item.source_type,
        "source_name": item.source_name,
        "tier": item.tier,
        "authors": item.authors,
        "published_date": item.published_date,
        "abstract": item.abstract,
        "doi": item.doi,
    }


def infer_theme(item: Item) -> str:
    """Map to the fixed theme taxonomy (mirrors targeting.themes / the relevance rubric)."""
    text = f"{item.title} {item.abstract or ''}".lower()
    if any(term in text for term in ("polyinfo", "pi1m", "khazana", "citrine", "polymerize", "informatics platform", "database")):
        return "Informatics Platforms & Databases"
    if any(term in text for term in ("large language model", "llm", "foundation model", "literature mining")):
        return "LLMs in Materials Science"
    if any(term in text for term in ("recycl", "depolymeriz", "sustainab", "life cycle", "bio-based", "pfas")):
        return "Recycling & Sustainability"
    if any(term in text for term in ("injection molding", "extrusion", "compounding", "process control", "digital twin", "defect")):
        return "Processing Optimization"
    if any(term in text for term in ("ftir", "raman", "spectra", "spectral", "sem", "tem", "dsc", "dma", "microstructure", "characteriz")):
        return "Characterization"
    if any(term in text for term in ("generative", "inverse design", "diffusion model", "variational autoencoder", "gan")):
        return "Generative & Inverse Design"
    if any(term in text for term in ("property prediction", "qspr", "qsar", "mechanical", "thermal", "glass transition")):
        return "Property Prediction"
    return "Other"
