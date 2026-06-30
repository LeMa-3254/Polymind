# Polymind Implementation Status

## Current Status

The MVP implementation is running end to end. The project now has configuration, source adapters,
model-client plumbing, Voyage embedding plumbing, SQLite storage, prompt files, static site pages,
setup docs, GitHub Actions automation, and offline tests. The repository has had a first manual
workflow run, produced a committed tracker database, and exposed live-site data-quality issues that
have been fixed in code and in the committed SQLite archive.

The local directory is initialized as a git repository and pushed to `LeMa-3254/Polymind`. The repo
was made public so GitHub Pages can run on the current GitHub plan. Repository API secrets were added
by the user.

The UI redesign and polymer-specific targeting refocus are now live: the pipeline has been run
through GitHub Actions with the new targeting plus the open-web sources, the whole archive has been
re-scored onto the 0–100 scale, and the site is deployed and serving at
`https://lema-3254.github.io/Polymind/`. A normal weekly run (367 fetched → 80 candidates → 35
included) confirmed the new sources work end to end (Google News alone contributed 20 included items),
and a follow-up `--rescore-all` maintenance run normalized the legacy 0–5 archive (re-scored 511
items, 108 → 50 included, dropping the non-polymer back-catalog).

The most recent work this session expanded ingestion to open-web sources, tightened the "High signal"
featured section to require both high relevance and high quality, and added freshness enforcement so
the feed shows only recent items. All of this is committed and pushed to `LeMa-3254/Polymind`; the
freshness changes take effect on the next scheduled Monday run (redeploy intentionally deferred).

## Completed

- Created the project plan in `PLAN.md`.
- Created the targeting configuration in `targeting.yaml`.
- Selected the Phase 1 MVP source scope: arXiv, OpenAlex, Crossref, and journal RSS.
- Deferred org blogs and Google News to Phase 3 while keeping them configured for later enablement.
- Selected GitHub Pages as the first launch host.
- Deferred custom domain setup to a later config/DNS update.
- Selected `dedup.on_duplicate: "drop"` as the v1 duplicate policy.
- Added config-driven model keys for scoring, enrichment, and weekly synthesis.
- Set `meta.contact_email` for OpenAlex/Crossref polite-pool access.
- Set the initial GitHub Pages project URL to `https://lema-3254.github.io/Polymind/`.
- Added Python project metadata and dependency declarations in `pyproject.toml` and `requirements.txt`.
- Scaffolded the planned `sources/`, `pipeline/`, `store/`, `site/`, `prompts/`, and `tests/` structure.
- Added normalized `Item` modeling and stable item ID generation.
- Added MVP source adapter foundations for arXiv, OpenAlex, Crossref, and journal RSS.
- Added vocabulary filtering, date normalization, feed parsing, and `{lookback_date}` filter resolution.
- Added bootstrap scoring/enrichment stubs that keep the pipeline shape runnable before model wiring.
- Added cosine similarity helper for the future Voyage dedup stage.
- Added dedup stage behavior against stored embeddings and same-run embeddings, with duplicate counts in run logs.
- Added SQLite schema, item upsert, run logging, and included-item querying.
- Added SQLite read path for the rolling embedding memory.
- Added a minimal static renderer for `index.html`, `index.json`, and `feed.xml`.
- Added prompt files for relevance scoring, enrichment, and weekly synthesis.
- Added offline unit tests for source parsing/filtering, store behavior, and static rendering.
- Added Anthropic model-client plumbing for scoring and enrichment, with bootstrap fallback when no key/SDK is available.
- Added Voyage embedding-client plumbing and connected embedding generation before dedup, with bootstrap skip when no key/SDK is available.
- Added token usage aggregation for Anthropic scoring, Anthropic enrichment, and Voyage embeddings.
- Added bounded retry behavior around live Anthropic and Voyage calls.
- Added offline tests for model JSON parsing, injected model clients, injected embedding clients, and token accounting.
- Added weekly synthesis generation and SQLite storage, with model-backed and deterministic fallback paths.
- Added `weekly.html` and a latest weekly synthesis preview on the home page.
- Added `archive.html` with generated source/theme filters and client-side search over included items.
- Added static site tests for archive rendering and generated output files.
- Added an offline pipeline dry-run test covering ingest, scoring fallback, enrichment fallback, weekly synthesis, SQLite writes, and run logging.
- Updated the SQLite connection helper so `with connect(...)` blocks close cleanly after commit/rollback.
- Extended the GitHub Actions workflow with a Monday weekly-synthesis schedule and manual workflow input.
- Installed local runtime dependencies in `.venv` and verified the pipeline with a live source-fetch smoke run:
  312 fetched, 40 included, 0 source errors, and static site output generated in `/private/tmp`.
- Added certifi-backed HTTPS verification for source fetching.
- Moved RSC Digital Discovery and ACS journal RSS feeds to `disabled_feeds` after live smoke tests showed TLS/403 failures.
- Added `.gitignore` for local Python/cache artifacts.
- Added `README.md` with setup, run, test, and GitHub Pages launch notes.
- Added `.env.example` documenting local Anthropic and Voyage key names.
- Added `Makefile` targets for tests, pipeline runs, static site builds, and cleanup.
- Added initial `.github/workflows/daily.yml` for tests, daily pipeline runs, site build, Pages deploy,
  and SQLite commit-back.
- Made the GitHub repository public so GitHub Pages can be enabled without upgrading the GitHub plan.
- Added Anthropic and Voyage API keys as GitHub Actions repository secrets.
- Completed a first manual GitHub Actions run that produced and committed `data/tracker.db`.
- Updated GitHub Actions pins to current Node 24-compatible action major versions after the first manual
  run reported a Node 20 deprecation warning.
- Fixed first live-site data quality issues: future issue publication dates now fall back to real
  non-future source metadata dates, all included items receive summary/why fallback text beyond the
  model enrichment cap, and raw underscore theme identifiers render as readable labels.
- Initialized the local git repository and pushed it to `LeMa-3254/Polymind`.

### Site UI redesign
- Rebuilt `site/build.py` on a single shared design system (light, scannable, aihot.virxact.com-style)
  replacing the per-page duplicated styles and heavy boxed cards.
- Added a sticky minimal header with pill nav, compact cards with a relevance "heat" badge, relative
  dates, clamped summaries, an accented "why it matters" callout, and a theme tag.
- Made the home feed curated and ranked: sorted by relevance then quality, split into a
  polymer/soft-matter section first and a broader materials-AI section, capped (12 + 18); full history
  moved to the Archive.
- Restructured the weekly synthesis into "This week in brief" highlights plus "Trends by theme", with
  markdown link/bold rendering, an improved `prompts/synth.md`, and a structured deterministic fallback.
- Removed the RSS entry from the top nav (kept `feed.xml`, the footer link, and the alternate link).

### Targeting refocus (polymer-specific, 7 categories)
- Narrowed the `materials_terms` gate from generic materials vocabulary to polymer/soft-matter terms so
  alloys, concrete, ceramics, semiconductors, and off-topic ML no longer pass on keywords alone.
- Rewrote OpenAlex/Crossref searches and added one Google News query per target category.
- Rewrote `prompts/relevance.md` to define Polymind as AI-for-polymers, enumerate the seven categories,
  and score non-polymer materials work as low relevance.
- Added a fixed `targeting.themes` taxonomy (the seven categories) and made the scoring model and the
  bootstrap `infer_theme` map to it, replacing the prior free-text theme sentences.

### Scoring & scope tightening
- Switched scores to a **0–100** scale; `min_score` 70 (target ~20 quality items/week),
  `high_quality_score` 80 (featured in a separate "High signal" section on the feed).
- Fixed score inflation: tier/polymer priors are no longer added on top of the model's score, so a
  "not really polymer" verdict can't be pushed past the threshold (priors now only shape the bootstrap).
- Added a pre-score keyword gate + `max_candidates` cap (80) in `prefilter_candidates`, so far fewer
  items reach the model — faster, cheaper runs that score the most promising (polymer-first, recent).
- Narrowed arXiv to cond-mat.soft / cond-mat.mtrl-sci / physics.chem-ph (dropped the cs.LG/cs.CE
  firehoses); lowered the enrichment cap to 25.

### Open-web source expansion
- Added adapters and enabled four previously-deferred open-web source tiers, all routed through the
  same targeting vocabulary gate so off-topic stories never reach the LLM:
  - `google_news` (query mode): the seven per-category Google News RSS searches now fetch live
    (~65 gated items in a smoke run).
  - `university_news`: MIT News + MIT Materials topic, Stanford, UC Berkeley, Georgia Tech, NIST.
  - `web_news`: ScienceDaily (Materials Science, AI) and Phys.org (Polymers, Materials Science).
  - `org_blogs`: Google DeepMind, Microsoft Research, Google Research, Berkeley Lab.
- Generalized the RSS/Atom parsing into `sources/rss_feeds.py` with a shared `FeedListAdapter`
  (parameterized by `source_type`); `JournalRssAdapter` is now a thin subclass. Added a browser-like
  UA + Accept header to avoid spurious 403s on press feeds.
- Smoke-tested every new feed URL and pruned the dead ones (Meta AI, NREL, Caltech, ScienceDaily
  Plastic 404/DNS; fixed the Phys.org Materials slug). Added offline tests for source_type tagging,
  vocabulary gating on feed lists, and Google News query encoding.
- Ran the live workflow twice to exercise the new sources: a normal weekly run, then a `--rescore-all`
  pass to normalize the legacy 0–5 archive to 0–100. Three feeds 403'd/timed out on the CI runner IP
  (Stanford News, Science Advances, arXiv cond-mat.soft) — isolated, non-fatal, worth watching.

### Featured section: relevance AND quality
- The "High signal" featured section now requires BOTH bars: `relevance >= high_relevance_score` AND
  `quality >= high_quality_score` (both default 80), instead of the previous relevance-only test.
  Quality was previously only a sort tiebreaker; it now gates the feature. Added `high_relevance_score`
  to config; the per-card relevance "heat" badge still keys off relevance.
- Verified with synthetic 0–100 items (only rel≥80 AND qual≥80 is featured) and on the live archive,
  where exactly one item currently clears both bars.

### Freshness enforcement
- Added two complementary, config-driven recency gates so a weekly tracker actually shows fresh content:
  - Ingest ceiling `meta.max_age_days` (default 30): drops any candidate whose publication date is
    older than the ceiling before it is scored or stored. This is what bounds the RSS sources, which
    carry no date filter of their own. Undated items pass (just fetched).
  - Display window `site.feed_days` (default 30): the home feed and `feed.xml` show only items within
    the window; the Archive and `index.json` keep the full history.
- Verified against the live DB: home feed 48 → 14 cards (all current), archive unchanged at 51,
  `feed.xml` 14 items. Added offline tests for `is_fresh` and `within_days`.

## Remaining

- Redeploy with the freshness gates on the next scheduled Monday run (deferred by request); confirm the
  live front page then shows only items within `feed_days`.
- Harden weekly freshness against missed/late runs: the cron (weekly) and `lookback_hours` (168h) are
  aligned but have zero overlap, so a single skipped run leaves a permanent gap-week hole. Recommended
  fix is to widen `lookback_hours` to ~240–336 (10–14 days); the 30-day dedup memory already prevents
  the overlap from producing duplicates. Also decide whether the front page should be strictly weekly
  (`feed_days: 7`) or stay a rolling month (`feed_days: 30`).
- Review live scoring/enrichment outputs under the rewritten rubric; tune thresholds if the polymer
  gate is too strict or too loose.
- Watch the CI-runner feed failures (Stanford News, Science Advances 403; arXiv cond-mat.soft timeout);
  move to `disabled_feeds` or find accessible URLs if they persist.
- Revisit disabled RSC/ACS journal RSS feeds or replace them with accessible source URLs.
- Run Voyage embedding generation against live API credentials and verify duplicate behavior across repeated live runs.
- Confirm the weekly synthesis is well-populated now that the window targets the last complete week and
  ingest looks back 7 days (regenerated on the next run; the committed summary predates these changes).
- Add verification tests for adapters, gate behavior, CI dry-runs, and cost caps.

## Decisions Locked

- Weekly pipeline run (Mondays) with synthesis; `lookback_hours` widened to 168 (7 days) and the
  synthesis window set to the last complete Monday–Sunday week.
- Static-only production deployment through GitHub Pages.
- Public access for v1.
- Config-driven model selection in `targeting.yaml`.
- Hosted Voyage `voyage-3` embeddings.
- SQLite committed to the repo as archive and dedup memory.
- Tier A sources plus open-web Tier B/C (org blogs, university news, general web news, Google News)
  are now enabled; all open-web feeds pass through the same polymer+AI vocabulary gate. Tier D
  (social) remains deferred.
- "High signal" requires both high relevance and high quality (≥80 each); quality is no longer just a
  ranking tiebreaker.
- Freshness is enforced at ingest (`max_age_days`, default 30) and display (`feed_days`, default 30);
  the Archive retains full history regardless.

## Open Questions

- Which custom domain, if any, should be configured after GitHub Pages is live?
- How will Anthropic ZDR be verified for the account/API configuration before production runs?
- Should the front page be strictly weekly (`feed_days: 7`) or a rolling month (`feed_days: 30`), and
  should `lookback_hours` gain overlap margin to survive a missed run?
