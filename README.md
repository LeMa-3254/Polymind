# Polymind

Polymind tracks fresh AI methods and tools for polymer and materials development. It is designed as a
scheduled pipeline that ingests public sources, filters and enriches items, stores the archive in
SQLite, and publishes a static GitHub Pages site.

## Current State

The repository scaffold is in place, with source adapters, a runnable pipeline shape, SQLite storage,
prompt files, static rendering, dedup behavior for stored embeddings, and offline tests. The Anthropic
model integrations and Voyage embedding generation are still bootstrap stubs; see
`IMPLEMENTATION_STATUS.md` for the live tracker.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For future live model calls, copy `.env.example` to `.env` and fill the API keys locally. GitHub
Actions should use repository secrets instead of committing `.env`.

## Common Commands

```bash
make test
make run
make build-site
```

Equivalent direct commands:

```bash
python3 -m unittest discover -s tests
python3 pipeline/run.py --config targeting.yaml --db data/tracker.db
python3 pipeline/run.py --config targeting.yaml --db data/tracker.db --weekly-synthesis
python3 site/build.py --config targeting.yaml --db data/tracker.db --output public
```

## GitHub Pages Launch Notes

The initial launch target is GitHub Pages. After the repository exists on GitHub:

1. Add repository secrets: `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY`.
2. Enable Pages from GitHub Actions in repository settings.
3. Confirm Pages serves the project URL: `https://lema-3254.github.io/Polymind/`.
4. Update `targeting.yaml` if a custom domain replaces the Pages URL.

The current workflow is an initial scaffold. It runs tests, runs the pipeline, builds static output,
deploys `public/` to Pages, and commits `data/tracker.db` back when it changes.
