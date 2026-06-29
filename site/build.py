from __future__ import annotations

import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from store.db import connect, included_items, latest_weekly_summary, weekly_summaries


# ---------------------------------------------------------------------------
# Shared design system — one stylesheet for every page (light, calm, scannable)
# ---------------------------------------------------------------------------
SITE_CSS = """
:root{
  --bg:#fafafa;--surface:#fff;--ink:#16181d;--muted:#6b7280;--faint:#9aa1ac;
  --line:#ececf0;--accent:#ea580c;--accent-soft:#fff4ed;--accent-ink:#c2410c;
  --radius:14px;--maxw:880px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink);background:var(--bg);line-height:1.55;font-size:16px;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 20px}
.site-header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.85);
  backdrop-filter:saturate(180%) blur(10px);-webkit-backdrop-filter:saturate(180%) blur(10px);
  border-bottom:1px solid var(--line)}
.header-inner{display:flex;align-items:center;justify-content:space-between;height:60px;gap:16px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.15rem;letter-spacing:-.01em}
.brand-mark{display:grid;place-items:center;width:30px;height:30px;border-radius:9px;
  background:var(--accent);color:#fff;font-weight:800;font-size:.95rem}
.nav{display:flex;gap:4px;align-items:center}
.nav a{padding:7px 12px;border-radius:999px;font-size:.9rem;color:var(--muted);font-weight:500}
.nav a:hover{color:var(--ink);background:#f1f1f4}
.nav a.active{color:var(--accent-ink);background:var(--accent-soft)}
.nav a.rss{color:var(--faint)}
.hero{padding:36px 0 6px}
.hero h1{margin:0 0 8px;font-size:1.9rem;line-height:1.15;letter-spacing:-.025em}
.lede{margin:0;color:var(--muted);font-size:1.02rem;max-width:62ch}
.hero-stat{margin:14px 0 0;color:var(--faint);font-size:.84rem;font-weight:500}
.page-head{padding:30px 0 2px}
.page-head h1{margin:0;font-size:1.55rem;letter-spacing:-.02em}
.page-head p{margin:7px 0 0;color:var(--muted)}
.feed{padding:6px 0 40px}
.date-group{margin-top:26px}
.date-label{display:flex;align-items:center;gap:12px;font-size:.8rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.07em;color:var(--faint);margin:0 0 12px}
.date-label::after{content:"";flex:1;height:1px;background:var(--line)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px 20px;margin:12px 0;transition:border-color .15s ease,box-shadow .15s ease}
.card:hover{border-color:#dcdce2;box-shadow:0 8px 26px -14px rgba(20,24,40,.22)}
.card-head{display:flex;gap:12px;justify-content:space-between;align-items:flex-start}
.card-title{margin:0;font-size:1.08rem;font-weight:650;line-height:1.36;letter-spacing:-.01em}
.card-title a:hover{color:var(--accent-ink)}
.heat{flex:none;display:inline-flex;align-items:center;gap:5px;font-size:.78rem;font-weight:700;
  padding:3px 9px;border-radius:999px;white-space:nowrap}
.heat::before{content:"";width:6px;height:6px;border-radius:50%}
.heat-high{background:var(--accent-soft);color:var(--accent-ink)}
.heat-high::before{background:var(--accent)}
.heat-med{background:#fff7e6;color:#b45309}
.heat-med::before{background:#f59e0b}
.heat-low{background:#f1f3f5;color:#6b7280}
.heat-low::before{background:#9aa1ac}
.card-meta{margin:7px 0 0;display:flex;flex-wrap:wrap;align-items:center;gap:7px;
  color:var(--muted);font-size:.86rem}
.card-meta .src{font-weight:600;color:#374151}
.dot{color:var(--faint)}
.summary{margin:10px 0 0;color:#3f4651;font-size:.95rem;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.why{margin:12px 0 0;padding:9px 13px;background:#fafbfc;border-left:3px solid var(--accent);
  border-radius:0 8px 8px 0;font-size:.88rem;color:#3f4651}
.why b{color:var(--accent-ink);font-weight:650}
.card-foot{margin-top:12px}
.tag{display:inline-block;max-width:100%;font-size:.78rem;color:var(--muted);background:#f4f4f6;
  border-radius:7px;padding:3px 9px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}
.toolbar{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px;margin:20px 0 6px}
.toolbar label{display:grid;gap:6px;font-size:.74rem;font-weight:600;color:var(--muted);
  text-transform:uppercase;letter-spacing:.05em}
.toolbar input,.toolbar select{appearance:none;-webkit-appearance:none;border:1px solid var(--line);
  background:var(--surface);border-radius:10px;padding:10px 12px;font:inherit;font-size:.92rem;
  color:var(--ink);min-height:42px;min-width:0;width:100%}
.toolbar input:focus,.toolbar select:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-soft)}
.result-count{margin:16px 0 0;color:var(--faint);font-size:.85rem}
.prose h2{font-size:1.15rem;margin:20px 0 8px;letter-spacing:-.01em}
.prose h2:first-child{margin-top:0}
.prose h3{font-size:.95rem;margin:16px 0 4px;color:#374151}
.prose p{margin:7px 0;color:#3f4651;font-size:.96rem}
.prose ul{margin:7px 0;padding-left:20px;color:#3f4651;font-size:.96rem}
.prose li{margin:5px 0;line-height:1.5}
.prose a{color:var(--accent-ink);font-weight:550;border-bottom:1px solid #f1c9af}
.prose a:hover{border-bottom-color:var(--accent)}
.prose-clip{max-height:200px;overflow:hidden;position:relative;
  -webkit-mask-image:linear-gradient(#000 62%,transparent);mask-image:linear-gradient(#000 62%,transparent)}
.weekly-meta{color:var(--faint);font-size:.85rem;margin:0 0 6px}
.weekly-link{display:inline-block;margin-top:10px;color:var(--accent-ink);font-weight:600;font-size:.9rem}
.empty{padding:48px 0;text-align:center;color:var(--faint)}
.site-footer{border-top:1px solid var(--line);margin-top:30px}
.footer-inner{display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between;align-items:center;
  padding:22px 0;color:var(--faint);font-size:.85rem}
.footer-inner a{color:var(--muted)}
.footer-inner a:hover{color:var(--accent-ink)}
@media (max-width:680px){
  .toolbar{grid-template-columns:1fr}
  .hero h1{font-size:1.55rem}
  .nav a{padding:6px 9px}
}
"""

NAV = [("index.html", "Feed"), ("archive.html", "Archive"), ("weekly.html", "Weekly")]

# Home feed is curated and ranked: polymer/soft-matter first, then broader materials AI.
POLYMER_FEED_LIMIT = 12
OTHER_FEED_LIMIT = 18


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


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
def document(site: dict, *, page_title: str, active: str, main_html: str, body_script: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(site.get("description", ""))}">
  <link rel="alternate" type="application/rss+xml" title="{escape(site.get("name", ""))} RSS" href="feed.xml">
  <style>{SITE_CSS}</style>
</head>
<body>
{header_html(site, active)}
{main_html}
{footer_html(site)}
{body_script}
</body>
</html>
"""


def header_html(site: dict, active: str) -> str:
    name = site.get("name", "Polymind")
    mark = escape(name[:1].upper() or "P")
    links = "".join(
        f'<a href="{href}" class="{nav_class(href, active)}">{escape(label)}</a>' if nav_class(href, active)
        else f'<a href="{href}">{escape(label)}</a>'
        for href, label in NAV
    )
    return f"""<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html"><span class="brand-mark">{mark}</span>{escape(name)}</a>
    <nav class="nav">{links}</nav>
  </div>
</header>"""


def nav_class(href: str, active: str) -> str:
    if href == "feed.xml":
        return "rss"
    return "active" if href == active else ""


def footer_html(site: dict) -> str:
    name = escape(site.get("name", "Polymind"))
    return f"""<footer class="site-footer">
  <div class="wrap footer-inner">
    <span>{name} — AI for polymer &amp; materials development</span>
    <span><a href="archive.html">Archive</a> &nbsp;·&nbsp; <a href="weekly.html">Weekly</a> &nbsp;·&nbsp; <a href="feed.xml">RSS</a></span>
  </div>
</footer>"""


# ---------------------------------------------------------------------------
# Index (curated feed, ranked by score, polymer/soft-matter first)
# ---------------------------------------------------------------------------
def render_index(config: dict, items: list, latest_weekly=None) -> str:
    site = config["site"]
    tagline = site.get("tagline") or site.get("description", "")
    stat = f"{len(items)} development{'s' if len(items) != 1 else ''} tracked" if items else ""
    hero = f"""<section class="hero">
    <h1>{escape(site.get("name", "Polymind"))}</h1>
    <p class="lede">{escape(tagline)}</p>
    {f'<p class="hero-stat">{escape(stat)}</p>' if stat else ''}
  </section>"""

    terms = polymer_terms(config)
    ranked = sorted(items, key=rank_key)  # stable sort keeps recency order within equal scores
    polymer = [item for item in ranked if is_polymer(item, terms)][:POLYMER_FEED_LIMIT]
    others = [item for item in ranked if not is_polymer(item, terms)][:OTHER_FEED_LIMIT]
    shown = len(polymer) + len(others)

    feed = []
    if polymer:
        feed.append(render_section("Polymer & soft matter", polymer))
    if others:
        label = "More in materials AI" if polymer else "Top developments"
        feed.append(render_section(label, others))
    feed_html = "\n".join(feed) or '<p class="empty">No included items yet.</p>'
    more = ""
    if len(items) > shown:
        more = f'<p style="text-align:center;margin:24px 0 0"><a class="weekly-link" href="archive.html">Browse all {len(items)} developments in the archive →</a></p>'

    main = f"""<main class="wrap">
  {hero}
  {render_weekly_preview(latest_weekly)}
  <section class="feed">{feed_html}{more}</section>
</main>"""
    return document(site, page_title=f'{site.get("name", "Polymind")} — AI polymer materials tracker', active="index.html", main_html=main)


def render_section(label: str, items: list) -> str:
    cards = "\n".join(render_card(item) for item in items)
    return f'<section class="date-group"><h2 class="date-label">{escape(label)}</h2>{cards}</section>'


def polymer_terms(config: dict) -> list[str]:
    targeting = config.get("targeting", {}) if isinstance(config, dict) else {}
    return [str(term).lower() for term in targeting.get("polymer_boost_terms", [])]


def is_polymer(item, terms: list[str]) -> bool:
    if not terms:
        return False
    haystack = " ".join(str(field(item, key) or "") for key in ("title", "summary", "abstract", "theme")).lower()
    return any(term in haystack for term in terms)


def rank_key(item) -> tuple[float, float]:
    return (-_num(field(item, "relevance_score")), -_num(field(item, "quality_score")))


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Archive (client-side search + filters)
# ---------------------------------------------------------------------------
def render_archive(config: dict, items: list) -> str:
    site = config["site"]
    sources = option_list(sorted({item["source_name"] for item in items if field(item, "source_name")}))
    themes = option_list(sorted({item["theme"] for item in items if field(item, "theme")}), labeler=format_theme)
    cards = "\n".join(render_card(item) for item in items) or '<p class="empty">No included items yet.</p>'
    main = f"""<main class="wrap">
  <section class="page-head">
    <h1>Archive</h1>
    <p>Search and filter every tracked development.</p>
  </section>
  <section class="toolbar">
    <label>Search<input id="search" type="search" autocomplete="off" placeholder="Keyword, author, method…"></label>
    <label>Source<select id="source"><option value="">All sources</option>{sources}</select></label>
    <label>Theme<select id="theme"><option value="">All themes</option>{themes}</select></label>
  </section>
  <p id="result-count" class="result-count">{len(items)} items</p>
  <section id="items" class="feed">{cards}</section>
</main>"""
    script = f"""<script>
    const items = {json_for_script([archive_item(item) for item in items])};
    const search = document.querySelector("#search");
    const source = document.querySelector("#source");
    const theme = document.querySelector("#theme");
    const count = document.querySelector("#result-count");
    const container = document.querySelector("#items");

    function text(value) {{ return value == null ? "" : String(value); }}
    function html(value) {{
      return text(value).replace(/[&<>"']/g, char => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }}[char]));
    }}
    function themeLabel(value) {{ return text(value).replaceAll("_", " "); }}

    function renderItem(item) {{
      const heat = item.heat_label
        ? `<span class="heat ${{item.heat_class}}" title="Relevance score (1-5)">${{html(item.heat_label)}}</span>` : "";
      const body = (item.summary || item.abstract)
        ? `<p class="summary">${{html(item.summary || item.abstract)}}</p>` : "";
      const why = item.why_it_matters
        ? `<div class="why"><b>Why it matters</b> ${{html(item.why_it_matters)}}</div>` : "";
      const tag = item.theme
        ? `<div class="card-foot"><span class="tag" title="${{html(themeLabel(item.theme))}}">${{html(themeLabel(item.theme))}}</span></div>` : "";
      return `<article class="card">
  <div class="card-head"><h3 class="card-title"><a href="${{html(item.url)}}" target="_blank" rel="noopener">${{html(item.title)}}</a></h3>${{heat}}</div>
  <p class="card-meta"><span class="src">${{html(item.source_name)}}</span><span class="dot">·</span><span>${{html(item.date_display)}}</span></p>
  ${{body}}
  ${{why}}
  ${{tag}}
</article>`;
    }}

    function render() {{
      const query = search.value.trim().toLowerCase();
      const filtered = items.filter(item => {{
        const haystack = [item.title, item.summary, item.abstract, item.why_it_matters, item.theme, item.source_name]
          .map(text).join(" ").toLowerCase();
        return (!query || haystack.includes(query))
          && (!source.value || item.source_name === source.value)
          && (!theme.value || item.theme === theme.value);
      }});
      count.textContent = `${{filtered.length}} item${{filtered.length === 1 ? "" : "s"}}`;
      container.innerHTML = filtered.length ? filtered.map(renderItem).join("") : '<p class="empty">No matching items.</p>';
    }}

    search.addEventListener("input", render);
    source.addEventListener("change", render);
    theme.addEventListener("change", render);
  </script>"""
    return document(site, page_title=f'{site.get("name", "Polymind")} — Archive', active="archive.html", main_html=main, body_script=script)


def archive_item(item) -> dict:
    cls, label = score_meta(field(item, "relevance_score"))
    return {
        "title": item["title"],
        "url": item["url"],
        "source_name": item["source_name"],
        "published_date": field(item, "published_date"),
        "fetched_date": field(item, "fetched_date"),
        "theme": field(item, "theme"),
        "summary": field(item, "summary"),
        "abstract": field(item, "abstract"),
        "why_it_matters": field(item, "why_it_matters"),
        "date_display": relative_date(field(item, "published_date") or field(item, "fetched_date")),
        "heat_class": cls,
        "heat_label": label,
    }


# ---------------------------------------------------------------------------
# Shared item card
# ---------------------------------------------------------------------------
def render_card(item) -> str:
    url = field(item, "url") or ""
    title = field(item, "title") or ""
    src = field(item, "source_name") or ""
    when = relative_date(field(item, "published_date") or field(item, "fetched_date"))
    summary = field(item, "summary") or field(item, "abstract") or ""
    why = field(item, "why_it_matters") or ""
    theme = format_theme(field(item, "theme") or "")
    cls, label = score_meta(field(item, "relevance_score"))

    heat = f'<span class="heat {cls}" title="Relevance score (1-5)">{escape(label)}</span>' if label else ""
    body = f'<p class="summary">{escape(summary)}</p>' if summary else ""
    why_html = f'<div class="why"><b>Why it matters</b> {escape(why)}</div>' if why else ""
    tag = f'<div class="card-foot"><span class="tag" title="{escape(theme)}">{escape(theme)}</span></div>' if theme else ""
    return f"""<article class="card">
  <div class="card-head"><h3 class="card-title"><a href="{escape(url)}" target="_blank" rel="noopener">{escape(title)}</a></h3>{heat}</div>
  <p class="card-meta"><span class="src">{escape(src)}</span><span class="dot">·</span><span>{escape(when)}</span></p>
  {body}
  {why_html}
  {tag}
</article>"""


# ---------------------------------------------------------------------------
# Weekly synthesis
# ---------------------------------------------------------------------------
def render_weekly(config: dict, summaries: list) -> str:
    site = config["site"]
    entries = "\n".join(render_weekly_entry(summary) for summary in summaries) or '<p class="empty">No weekly syntheses yet.</p>'
    main = f"""<main class="wrap">
  <section class="page-head">
    <h1>Weekly Synthesis</h1>
    <p>Trends across the week, clustered by theme.</p>
  </section>
  <section class="feed">{entries}</section>
</main>"""
    return document(site, page_title=f'{site.get("name", "Polymind")} — Weekly synthesis', active="weekly.html", main_html=main)


def render_weekly_preview(summary) -> str:
    if summary is None:
        return ""
    return f"""<section class="card">
  <h2 class="date-label" style="margin-bottom:8px">Latest weekly synthesis</h2>
  <p class="weekly-meta">{escape(summary["week_start"])} – {escape(summary["week_end"])}</p>
  <div class="prose prose-clip">{markdown_to_html(summary["synthesis_md"])}</div>
  <a class="weekly-link" href="weekly.html">Read the full synthesis →</a>
</section>"""


def render_weekly_entry(summary) -> str:
    return f"""<article class="card">
  <h2 style="margin:0 0 4px;font-size:1.15rem;letter-spacing:-.01em">{escape(summary["week_start"])} – {escape(summary["week_end"])}</h2>
  <p class="weekly-meta">Generated {escape(summary["generated_at"])}</p>
  <div class="prose">{markdown_to_html(summary["synthesis_md"])}</div>
</article>"""


def markdown_to_html(markdown: str) -> str:
    lines = []
    bullets: list[str] = []

    def flush():
        if bullets:
            lines.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if line.startswith("### "):
            flush()
            lines.append(f"<h3>{render_inline(format_theme(line[4:]))}</h3>")
        elif line.startswith("## "):
            flush()
            lines.append(f"<h2>{render_inline(format_theme(line[3:]))}</h2>")
        elif line.startswith("- "):
            bullets.append(render_inline(line[2:]))
        else:
            flush()
            lines.append(f"<p>{render_inline(line)}</p>")
    flush()
    return "\n".join(lines)


_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def render_inline(text: str) -> str:
    """Escape text, then render markdown links [label](url) and **bold** safely."""
    out = escape(text)
    out = _LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        out,
    )
    out = _BOLD_RE.sub(r"<b>\1</b>", out)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def field(item, key: str):
    """Safe accessor that works for dicts and sqlite3.Row (no .get)."""
    try:
        return item[key]
    except (KeyError, IndexError):
        return None


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def relative_date(value) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        return str(value or "")
    delta = (date.today() - parsed).days
    if delta <= 0:
        return "Today"
    if delta == 1:
        return "Yesterday"
    if delta < 7:
        return f"{delta} days ago"
    if delta < 30:
        weeks = delta // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def score_meta(value) -> tuple[str, str]:
    """Map a 1-5 relevance score to a (css class, label) heat badge."""
    if value is None:
        return ("", "")
    try:
        score = float(value)
    except (TypeError, ValueError):
        return ("", "")
    label = f"{score:g}"
    if score >= 4:
        return ("heat-high", label)
    if score >= 3:
        return ("heat-med", label)
    return ("heat-low", label)


def option_list(values: list[str], *, labeler=None) -> str:
    labeler = labeler or (lambda value: value)
    return "".join(f'<option value="{escape(value)}">{escape(labeler(value))}</option>' for value in values)


def format_theme(value: str) -> str:
    return (value or "").replace("_", " ")


def json_for_script(value) -> str:
    return json.dumps(value, sort_keys=True).replace("</", "<\\/")


def render_rss(config: dict, items: list) -> str:
    site = config["site"]
    entries = "\n".join(
        f"""  <item>
    <title>{escape(item["title"])}</title>
    <link>{escape(item["url"])}</link>
    <guid>{escape(item["id"])}</guid>
    <description>{escape(field(item, "summary") or field(item, "abstract") or "")}</description>
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
