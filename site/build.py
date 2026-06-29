from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from store.db import connect, included_items, latest_weekly_summary, weekly_summaries


def build_site(config_path: str = "targeting.yaml", db_path: str = "data/tracker.db", output_dir: str = "public") -> None:
    config = load_config(config_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as db:
        items = included_items(db)
        latest_weekly = latest_weekly_summary(db)
        all_weeklies = weekly_summaries(db)

    (output / "index.html").write_text(render_index(config, items, latest_weekly), encoding="utf-8")
    (output / "weekly.html").write_text(render_weekly(config, all_weeklies), encoding="utf-8")
    (output / "index.json").write_text(
        json.dumps([dict(item) for item in items], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output / "feed.xml").write_text(render_rss(config, items), encoding="utf-8")


def render_index(config: dict, items: list, latest_weekly=None) -> str:
    site = config["site"]
    cards = "\n".join(render_card(item) for item in items) or "<p>No included items yet.</p>"
    weekly = render_weekly_preview(latest_weekly)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site["name"])} - AI polymer materials tracker</title>
  <meta name="description" content="{escape(site["description"])}">
  <link rel="alternate" type="application/rss+xml" href="feed.xml">
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; color: #202124; background: #f7f8fa; }}
    header, main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    header {{ border-bottom: 1px solid #d9dde3; }}
    h1 {{ margin: 0 0 8px; font-size: 2rem; }}
    nav a {{ margin-right: 12px; }}
    section {{ margin: 24px 0; }}
    article {{ background: white; border: 1px solid #d9dde3; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    article h2 {{ margin: 0 0 8px; font-size: 1.1rem; }}
    .meta {{ color: #5f6368; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(site["name"])}</h1>
    <p>{escape(site["description"])}</p>
    <nav><a href="index.html">Daily feed</a><a href="weekly.html">Weekly synthesis</a><a href="feed.xml">RSS</a></nav>
  </header>
  <main>
    {weekly}
    <section>
      <h2>Latest Items</h2>
      {cards}
    </section>
  </main>
</body>
</html>
"""


def render_weekly_preview(summary) -> str:
    if summary is None:
        return ""
    return f"""<section>
  <h2>Latest Weekly Synthesis</h2>
  <p class="meta">{escape(summary["week_start"])} to {escape(summary["week_end"])}</p>
  <div>{markdown_to_html(summary["synthesis_md"])}</div>
  <p><a href="weekly.html">View all weekly syntheses</a></p>
</section>"""


def render_card(item) -> str:
    return f"""<article>
  <h2><a href="{escape(item["url"])}">{escape(item["title"])}</a></h2>
  <p class="meta">{escape(item["source_name"])} · {escape(item["published_date"] or item["fetched_date"])} · {escape(item["theme"] or "materials AI")}</p>
  <p>{escape(item["summary"] or item["abstract"] or "")}</p>
  <p><strong>Why it matters:</strong> {escape(item["why_it_matters"] or "")}</p>
</article>"""


def render_weekly(config: dict, summaries: list) -> str:
    site = config["site"]
    entries = "\n".join(render_weekly_entry(summary) for summary in summaries) or "<p>No weekly syntheses yet.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site["name"])} - weekly synthesis</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; color: #202124; background: #f7f8fa; }}
    header, main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    header {{ border-bottom: 1px solid #d9dde3; }}
    article {{ background: white; border: 1px solid #d9dde3; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    nav a {{ margin-right: 12px; }}
    .meta {{ color: #5f6368; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(site["name"])} Weekly Synthesis</h1>
    <nav><a href="index.html">Daily feed</a><a href="weekly.html">Weekly synthesis</a><a href="feed.xml">RSS</a></nav>
  </header>
  <main>{entries}</main>
</body>
</html>
"""


def render_weekly_entry(summary) -> str:
    return f"""<article>
  <h2>{escape(summary["week_start"])} to {escape(summary["week_end"])}</h2>
  <p class="meta">Generated {escape(summary["generated_at"])}</p>
  <div>{markdown_to_html(summary["synthesis_md"])}</div>
</article>"""


def markdown_to_html(markdown: str) -> str:
    lines = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### "):
            lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("## "):
            lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("- "):
            lines.append(f"<p>&bull; {escape(line[2:])}</p>")
        else:
            lines.append(f"<p>{escape(line)}</p>")
    return "\n".join(lines)


def render_rss(config: dict, items: list) -> str:
    site = config["site"]
    entries = "\n".join(
        f"""  <item>
    <title>{escape(item["title"])}</title>
    <link>{escape(item["url"])}</link>
    <guid>{escape(item["id"])}</guid>
    <description>{escape(item["summary"] or item["abstract"] or "")}</description>
  </item>"""
        for item in items[:50]
    )
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{escape(site["name"])}</title>
  <link>{escape(site["url"])}</link>
  <description>{escape(site["description"])}</description>
{entries}
</channel>
</rss>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Polymind static site")
    parser.add_argument("--config", default="targeting.yaml")
    parser.add_argument("--db", default="data/tracker.db")
    parser.add_argument("--output", default="public")
    args = parser.parse_args()
    build_site(config_path=args.config, db_path=args.db, output_dir=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
