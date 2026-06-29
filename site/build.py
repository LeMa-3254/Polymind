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
    (output / "archive.html").write_text(render_archive(config, items), encoding="utf-8")
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
    <nav><a href="index.html">Daily feed</a><a href="archive.html">Archive</a><a href="weekly.html">Weekly synthesis</a><a href="feed.xml">RSS</a></nav>
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


def render_archive(config: dict, items: list) -> str:
    site = config["site"]
    cards = "\n".join(render_card(item) for item in items) or "<p>No included items yet.</p>"
    sources = option_list(sorted({item["source_name"] for item in items if item["source_name"]}))
    themes = option_list(sorted({item["theme"] for item in items if item["theme"]}))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site["name"])} - archive</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; color: #202124; background: #f7f8fa; }}
    header, main {{ max-width: 1080px; margin: 0 auto; padding: 24px; }}
    header {{ border-bottom: 1px solid #d9dde3; }}
    h1 {{ margin: 0 0 8px; font-size: 2rem; }}
    nav a {{ margin-right: 12px; }}
    .toolbar {{ align-items: end; display: grid; gap: 12px; grid-template-columns: 2fr 1fr 1fr; margin: 24px 0; }}
    label {{ color: #5f6368; display: grid; font-size: 0.85rem; gap: 6px; }}
    input, select {{ border: 1px solid #c8ced8; border-radius: 6px; color: #202124; font: inherit; min-height: 40px; padding: 8px 10px; }}
    article {{ background: white; border: 1px solid #d9dde3; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    article h2 {{ margin: 0 0 8px; font-size: 1.1rem; }}
    .meta, #result-count {{ color: #5f6368; font-size: 0.9rem; }}
    @media (max-width: 760px) {{ .toolbar {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(site["name"])} Archive</h1>
    <p>{escape(site["description"])}</p>
    <nav><a href="index.html">Daily feed</a><a href="archive.html">Archive</a><a href="weekly.html">Weekly synthesis</a><a href="feed.xml">RSS</a></nav>
  </header>
  <main>
    <section class="toolbar">
      <label>Search<input id="search" type="search" autocomplete="off"></label>
      <label>Source<select id="source"><option value="">All sources</option>{sources}</select></label>
      <label>Theme<select id="theme"><option value="">All themes</option>{themes}</select></label>
    </section>
    <p id="result-count">{len(items)} items</p>
    <section id="items">{cards}</section>
  </main>
  <script>
    const items = {json_for_script([archive_item(item) for item in items])};
    const search = document.querySelector("#search");
    const source = document.querySelector("#source");
    const theme = document.querySelector("#theme");
    const count = document.querySelector("#result-count");
    const container = document.querySelector("#items");

    function text(value) {{
      return value == null ? "" : String(value);
    }}

    function html(value) {{
      return text(value).replace(/[&<>"']/g, char => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }}[char]));
    }}

    function renderItem(item) {{
      const date = item.published_date || item.fetched_date || "";
      const theme = item.theme || "materials AI";
      const summary = item.summary || item.abstract || "";
      return `<article>
  <h2><a href="${{html(item.url)}}">${{html(item.title)}}</a></h2>
  <p class="meta">${{html(item.source_name)}} · ${{html(date)}} · ${{html(theme)}}</p>
  <p>${{html(summary)}}</p>
  <p><strong>Why it matters:</strong> ${{html(item.why_it_matters || "")}}</p>
</article>`;
    }}

    function render() {{
      const query = search.value.trim().toLowerCase();
      const filtered = items.filter(item => {{
        const haystack = [item.title, item.summary, item.abstract, item.why_it_matters, item.theme, item.source_name]
          .map(text)
          .join(" ")
          .toLowerCase();
        return (!query || haystack.includes(query))
          && (!source.value || item.source_name === source.value)
          && (!theme.value || item.theme === theme.value);
      }});
      count.textContent = `${{filtered.length}} item${{filtered.length === 1 ? "" : "s"}}`;
      container.innerHTML = filtered.length ? filtered.map(renderItem).join("") : "<p>No matching items.</p>";
    }}

    search.addEventListener("input", render);
    source.addEventListener("change", render);
    theme.addEventListener("change", render);
  </script>
</body>
</html>
"""


def archive_item(item) -> dict:
    return {
        "title": item["title"],
        "url": item["url"],
        "source_name": item["source_name"],
        "published_date": item["published_date"],
        "fetched_date": item["fetched_date"],
        "theme": item["theme"],
        "summary": item["summary"],
        "abstract": item["abstract"],
        "why_it_matters": item["why_it_matters"],
    }


def option_list(values: list[str]) -> str:
    return "".join(f'<option value="{escape(value)}">{escape(value)}</option>' for value in values)


def json_for_script(value) -> str:
    return json.dumps(value, sort_keys=True).replace("</", "<\\/")


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
    <nav><a href="index.html">Daily feed</a><a href="archive.html">Archive</a><a href="weekly.html">Weekly synthesis</a><a href="feed.xml">RSS</a></nav>
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
