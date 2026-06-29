# Polymind Implementation Status

## Current Status

The first implementation scaffold is in place. The project now has configuration, source adapter
foundations, pipeline stubs, SQLite storage, prompt files, a minimal static renderer, setup docs, a
GitHub Actions workflow scaffold, and offline tests. Anthropic/Voyage client plumbing is in place, but
live API credentials and GitHub Pages deployment still need to be verified in GitHub.

The local directory has been initialized as a git repository and pushed to the existing GitHub repo
`LeMa-3254/Polymind`. Workflow execution, commit-back behavior, repository secrets, and GitHub Pages
deployment settings still need to be verified in GitHub.

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
- Initialized the local git repository and pushed it to `LeMa-3254/Polymind`.

## Remaining

- Run Anthropic scoring/enrichment against live API credentials and tune prompts from real outputs.
- Verify the GitHub Actions workflow on `workflow_dispatch` after configuring repository secrets.
- Configure repository secrets and GitHub Pages settings.
- Revisit disabled RSC/ACS journal RSS feeds or replace them with accessible source URLs.
- Run Voyage embedding generation against live API credentials and verify duplicate behavior across repeated live runs.
- Expand the static site beyond the current renderer: archive page, search/filter UI, and polished templates.
- Add verification tests for adapters, gate behavior, dedup behavior, full local runs, CI dry-runs, and cost caps.

## Decisions Locked

- Daily pipeline run with weekly synthesis as the shareable trend headline.
- Static-only production deployment through GitHub Pages.
- Public access for v1.
- Config-driven model selection in `targeting.yaml`.
- Hosted Voyage `voyage-3` embeddings.
- SQLite committed to the repo as archive and dedup memory.
- Phase 1 uses only Tier A MVP sources; Tier B/C sources remain disabled until Phase 3.

## Open Questions

- Which custom domain, if any, should be configured after GitHub Pages is live?
- How will Anthropic ZDR be verified for the account/API configuration before production runs?
