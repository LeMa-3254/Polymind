from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time
from typing import Any


class ApiUnavailable(RuntimeError):
    pass


def read_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def add_token_usage(bucket: dict[str, Any] | None, name: str, usage: dict[str, Any]) -> None:
    if bucket is None:
        return
    target = bucket.setdefault(name, {})
    for key, value in usage.items():
        if isinstance(value, (int, float)):
            target[key] = target.get(key, 0) + value


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(text.strip())
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            value, _ = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("No JSON object found in model response")


def strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_message_text(message: Any) -> str:
    parts: list[str] = []
    for block in getattr(message, "content", []):
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def anthropic_usage(message: Any) -> dict[str, int]:
    usage = getattr(message, "usage", None)
    if usage is None:
        return {}
    keys = [
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    ]
    return {
        key: value
        for key in keys
        if isinstance((value := getattr(usage, key, None)), int)
    }


def retry_call(fn, *, attempts: int = 3, initial_delay: float = 1.0):
    delay = initial_delay
    for attempt in range(attempts):
        try:
            return fn()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)
            delay *= 2


class AnthropicModelClient:
    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ApiUnavailable("ANTHROPIC_API_KEY is not set")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ApiUnavailable("anthropic package is not installed") from exc
        self.client = Anthropic(api_key=api_key)

    def complete_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        message = retry_call(
            lambda: self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        )
        return parse_json_object(extract_message_text(message)), anthropic_usage(message)


class VoyageEmbeddingClient:
    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ApiUnavailable("VOYAGE_API_KEY is not set")
        try:
            import voyageai
        except ImportError as exc:
            raise ApiUnavailable("voyageai package is not installed") from exc
        self.client = voyageai.Client(api_key=api_key)

    def embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: str = "document",
    ) -> tuple[list[list[float]], dict[str, int]]:
        result = retry_call(lambda: self.client.embed(texts, model=model, input_type=input_type))
        usage = getattr(result, "usage", {}) or {}
        if not isinstance(usage, dict):
            usage = {}
        return result.embeddings, {
            key: value
            for key, value in usage.items()
            if isinstance(value, int)
        }


def build_anthropic_client() -> AnthropicModelClient | None:
    try:
        return AnthropicModelClient()
    except ApiUnavailable:
        return None


def build_voyage_client() -> VoyageEmbeddingClient | None:
    try:
        return VoyageEmbeddingClient()
    except ApiUnavailable:
        return None
