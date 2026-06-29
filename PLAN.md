# Polymind — AI-for-Polymer-Materials Tracker

A low-maintenance, shareable feed of *fresh, high-quality, non-repeating* developments in AI applied to
polymer and materials development. A scheduled pipeline ingests new work, filters for relevance and
quality, removes repeats, summarizes each item with a source link, and publishes a browsable static
website (rolling daily feed + weekly synthesis headline + searchable archive + RSS).

Everything runs in CI; **nothing runs in production except static files.** The whole "app" is
regenerated each run.

Configuration lives in [`targeting.yaml`](targeting.yaml) — the single source of truth for *what* to
look for and *where* to look. Tune precision vs. recall there, not in code.

---

## Locked decisions

| Decision | Choice | Why |
|---|---|---|
| **Cadence** | Daily pipeline run; weekly synthesis is the shareable headline | Daily run keeps the 30-day dedup memory fresh and catches fast movers; weekly synthesis reads as *trends, not lists* |
| **Host** | GitHub Pages first; custom domain later | Simplest share URL, free, native to the Actions workflow; custom domain is a config-only follow-up once registered |
| **Embeddings** | Voyage `voyage-3` (hosted) | One API call/item, no ~100 MB model download per CI run; cents/month |
| **Access** | Public | Public news + source links; enables RSS subscribe and link-sharing |
| **LLM models** | **Config-driven, not pinned** | A fast/cheap tier for high-volume scoring, a stronger tier for enrichment + synthesis; swap models in config without touching code |

> **MVP alignment:** [`targeting.yaml`](targeting.yaml) enables only arXiv, OpenAlex, Crossref, and
> journal RSS for Phase 1. Org blogs and Google News remain configured but disabled until Phase 3.

---

## Architecture

```
GitHub Actions cron (daily)
  → Ingest    (MVP: arXiv, OpenAlex, Crossref, journal RSS — per targeting.yaml)
  → Gate      (scoring model: relevance + quality, structured JSON out)
  → Dedup     (Voyage embeddings vs. rolling 30-day store; cosine ≥ 0.85)
  → Enrich    (enrichment model: "what it is" + "why it matters", capped per run)
  → Store     (SQLite, committed back to repo = dedup memory + archive)
  → Build     (Jinja2 → static HTML + JSON index + RSS)
  → Deploy    (GitHub Pages)

Weekly trigger → Synthesis (synthesis model over the week's included items, theme-clustered)
```

---

## Tech stack

- **Language:** Python.
- **LLM:** model choice is **flexible and config-driven**, not pinned in code. `scoring.model`,
  `enrich.model`, and `synth.model` live in [`targeting.yaml`](targeting.yaml), so models can be
  swapped without code changes. Convention: a **fast/cheap tier** for high-volume scoring, a
  **stronger tier** for enrichment + weekly synthesis. Verify ZDR at the Anthropic account/API
  configuration layer when wiring model calls.
- **Embeddings:** Voyage `voyage-3` (configured under `dedup` in [`targeting.yaml`](targeting.yaml)).
- **Store:** SQLite committed to the repo each run (dedup memory + full archive).
- **Site generator:** a small Python build script rendering Jinja2 templates → static HTML, plus a
  JSON index and RSS.
- **Search:** client-side (Pagefind or Fuse.js) — no server.
- **Host:** GitHub Pages. Use the Pages URL for first launch; switch `site.url` to a custom domain
  later after registration and DNS setup.
- **Orchestration:** GitHub Actions cron.

---

## Repo structure

```
polymer-ai-tracker/
├─ sources/          # one adapter per source → normalized Item; reads targeting.yaml
├─ pipeline/         # score.py, dedup.py, enrich.py, synth.py
├─ store/            # db.py (SQLite), schema.sql
├─ site/             # build.py, templates/, static/
├─ data/tracker.db   # committed SQLite (dedup memory + archive)
├─ public/           # generated static site (deployed)
├─ prompts/          # relevance.md, enrich.md, synth.md
├─ targeting.yaml    # single source of truth for what/where  (EXISTS)
├─ PLAN.md           # this document
└─ .github/workflows/daily.yml
```

---

## Data model (SQLite)

- **items** — `id` (hash of DOI/url), `title`, `url`, `source_type`, `source_name`, `tier`, `authors`,
  `published_date`, `fetched_date`, `abstract`, `embedding` (blob), `relevance_score`, `quality_score`,
  `score_reason`, `theme`, `summary` ("what's the development"), `why_it_matters`, `digest_date`,
  `status` (`included` / `dropped_dup` / `dropped_lowscore`), `dup_of` (nullable → threads the
  "update to an existing item" case).
- **weekly_summaries** — `week_start`, `week_end`, `synthesis_md`, `item_ids` (json), `generated_at`.
- **runs** — per-run log: counts (in / candidates / scored / deduped / included), per-source fetch
  status & errors, model token usage, `started_at` / `finished_at`. Drives debugging + cost visibility.

---

## Pipeline stages — requirement → mechanism

1. **Ingest.** Adapters emit normalized `Item`s; pull only `meta.lookback_hours` (48h) of items.
   Apply the keyword match rule (≥1 `ai_term` **AND** ≥1 `materials_term`, minus `exclude_terms`)
   where the source supports it.
   - **Politeness / limits:** set `meta.contact_email` for the OpenAlex/Crossref polite pool; throttle
     arXiv (~3s between calls).
   - **Source isolation:** a 404/timeout on one feed logs to `runs` and the pipeline continues — one
     dead feed never fails the run. Verify the `# verify`-marked feeds on first run.

2. **Relevance + quality gate** *(the "high quality" requirement)*. The scoring model (`scoring.model`)
   scores each candidate 1–5 against `prompts/relevance.md`, returning **structured JSON**
   (`{relevance, quality, reason, theme}`) so output is parseable. Add `source_tier_prior` +
   `polymer_boost` from [`targeting.yaml`](targeting.yaml); drop anything below `min_score` (3).

3. **Novelty / dedup** *(the "don't repeat" requirement)*. Embed survivors with Voyage; compare max
   cosine similarity against the rolling 30-day store. `≥ 0.85` → drop, or set `dup_of` and tag as an
   update to an existing thread (`on_duplicate`). Works across days, not just within a run; cosine over
   the 30-day window is trivial in-memory at this volume.

4. **Enrich.** The enrichment model (`enrich.model`) writes the 1–2 sentence "what it is" + one-line
   "why it matters," keeping the source link. **Cost cap:** enrich at most N included items/run
   (e.g. 40); overflow rolls to the next run ordered by score — bounds spend and protects against a
   flood day.

5. **Store.** Upsert to SQLite. **Commit-back discipline:** commit `data/tracker.db` only when it
   changed; use `concurrency: group` on the workflow to stop overlapping runs racing the commit;
   rebase/pull before push.

6. **Render + Deploy.** Build the static site + JSON index + RSS deterministically; publish to GitHub
   Pages.

---

## Website

- **Home:** latest daily feed + most recent weekly synthesis.
- **Archive:** all daily digests by date.
- **Weekly:** trend syntheses, theme-clustered (cluster the week's embeddings, then the synthesis model
  writes one narrative per cluster) so it reads as trends, not lists.
- **Item card:** title, what it is, why it matters, source link, date, source type, theme tag.
- **Search / filter:** client-side by keyword, source, theme, date.
- **RSS:** auto-generated — lets people subscribe instead of checking, and is itself a clean share
  mechanism.
- **Sharing:** public GitHub Pages URL for first launch (content is public AI/materials news with
  source links). A custom domain can be added later by updating `site.url` and Pages/DNS settings.
  Gating later, if ever wanted, can be added with Azure SWA + Entra or Cloudflare Access without
  touching the pipeline.

---

## Automation & secrets

- A single GitHub Actions workflow on a daily cron: run pipeline → build site → deploy → commit
  updated `tracker.db`. A separate weekly trigger (or a Monday branch in the same job) produces the
  synthesis. Optionally email/Slack the daily digest so the team gets push, while the site is the
  searchable pull archive.
- **Secrets (repo settings):** `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`. Verify ZDR for Anthropic at
  account/API configuration time before production runs.

---

## Cost

Effectively free infrastructure (GitHub Pages + Actions free tiers). The only real cost is the LLM
calls (scoring + enrichment/synthesis) — a few dollars/month at this volume, bounded by the per-run
enrichment cap and sensitive to which models are configured. Voyage embeddings are cents.
`runs.token_usage` makes spend observable.

---

## Build phases

- **Phase 1 (MVP):** arXiv + OpenAlex + Crossref + journal RSS enabled in `targeting.yaml` → gate →
  dedup → enrich → SQLite → static site on GitHub Pages, daily cron. End-to-end and shareable.
- **Phase 2:** weekly synthesis page, client-side search, RSS, optional email/Slack push.
- **Phase 3:** add org blogs + Google News (Tier B/C) behind the gate; tune theme clustering and
  thresholds against real precision/recall.
- **Phase 4 (optional):** social tier — curated X list via a third-party read API, LinkedIn manual
  paste.

---

## Verification (end-to-end)

1. **Per-adapter, offline:** run each source adapter standalone; assert it emits normalized `Item`s,
   and that a deliberately-bad feed URL logs an error to `runs` without aborting the run.
2. **Gate:** feed known on/off-topic abstracts; confirm the structured JSON parses, on-topic polymer
   items clear `min_score`, and `exclude_terms` items drop.
3. **Dedup:** run the same day twice; the second run must mark items `dropped_dup` (proves the 30-day
   store works across runs, not just within one).
4. **Full local run:** execute the whole pipeline locally → SQLite populated → `site/build.py` produces
   `public/` with valid HTML + JSON index + RSS (validate the RSS); open the site locally.
5. **CI dry-run:** trigger the workflow manually (`workflow_dispatch`); confirm it scores/dedups/
   enriches, commits `tracker.db` only on change, and Pages serves the updated site at the share URL.
6. **Cost check:** confirm `runs` records token usage and the enrichment cap holds on a high-volume day.
