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

Two rounds of changes have since landed but have not yet been run through the pipeline or deployed:
(1) a full static-site UI redesign with a ranked, polymer-first feed and a restructured weekly
synthesis, and (2) a targeting refocus that narrows scope from general "AI + materials" to
polymer-specific AI across seven defined categories. These are config/prompt/render changes only; they
take effect on the next pipeline run. The current committed `data/tracker.db` and deployed site still
reflect the old broad targeting until a run is executed.

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

## Remaining

- Rerun the GitHub Actions workflow with the new targeting + UI and confirm the Pages deployment shows
  polymer-focused content tagged with the seven fixed themes (not yet triggered, by request).
- Review live scoring/enrichment outputs under the rewritten rubric; tune thresholds if the polymer
  gate is too strict or too loose (re-filtering the old pool kept ~22 of 160 items).
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
- Phase 1 uses only Tier A MVP sources; Tier B/C sources remain disabled until Phase 3.

## Open Questions

- Which custom domain, if any, should be configured after GitHub Pages is live?
- How will Anthropic ZDR be verified for the account/API configuration before production runs?
