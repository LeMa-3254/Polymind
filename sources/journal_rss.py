from __future__ import annotations

import xml.etree.ElementTree as ET

from models import Item
from .base import SourceAdapter, SourceResult, clean_text, fetch_url, normalize_date, vocabulary_match


class JournalRssAdapter(SourceAdapter):
    source_type = "journal_rss"

    def fetch(self) -> SourceResult:
        items: list[Item] = []
        errors: list[str] = []
        for feed in self.source_config.get("feeds", []):
            name = feed.get("name", "journal RSS")
            try:
                parsed = parse_rss_or_atom(fetch_url(feed["url"]), source_name=name, tier=self.tier)
            except Exception as exc:
                errors.append(f"journal_rss:{name}: {exc}")
                continue
            items.extend(item for item in parsed if vocabulary_match(item, self.config))
        return SourceResult(items=items, errors=errors)


def parse_rss_or_atom(payload: bytes, *, source_name: str, tier: str) -> list[Item]:
    root = ET.fromstring(payload)
    if root.tag.endswith("rss") or root.find("./channel") is not None:
        return parse_rss(root, source_name=source_name, tier=tier)
    return parse_atom(root, source_name=source_name, tier=tier)


def parse_rss(root: ET.Element, *, source_name: str, tier: str) -> list[Item]:
    items: list[Item] = []
    for element in root.findall("./channel/item"):
        title = clean_text(element.findtext("title"))
        url = clean_text(element.findtext("link"))
        abstract = clean_text(element.findtext("description"))
        published = normalize_date(element.findtext("pubDate"))
        if title and url:
            items.append(
                Item.from_source(
                    title=title,
                    url=url,
                    source_type="journal_rss",
                    source_name=source_name,
                    tier=tier,
                    published_date=published,
                    abstract=abstract,
                )
            )
    return items


def parse_atom(root: ET.Element, *, source_name: str, tier: str) -> list[Item]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns) or root.findall("entry")
    items: list[Item] = []
    for entry in entries:
        title = clean_text(entry.findtext("atom:title", namespaces=ns) or entry.findtext("title"))
        url = entry.findtext("atom:id", namespaces=ns) or entry.findtext("id") or ""
        for link in entry.findall("atom:link", ns) + entry.findall("link"):
            if link.attrib.get("href"):
                url = link.attrib["href"]
                break
        abstract = clean_text(entry.findtext("atom:summary", namespaces=ns) or entry.findtext("summary"))
        published = normalize_date(entry.findtext("atom:published", namespaces=ns) or entry.findtext("published"))
        if title and url:
            items.append(
                Item.from_source(
                    title=title,
                    url=url,
                    source_type="journal_rss",
                    source_name=source_name,
                    tier=tier,
                    published_date=published,
                    abstract=abstract,
                )
            )
    return items

