# Documentation index

This folder explains how the research, the data pipeline, the API and the web app fit
together. The public interface is in Spanish; the developer documentation is in English.

Start here:

| Document | What it answers |
|---|---|
| [`architecture.md`](architecture.md) | How the pieces connect and why the stack was chosen |
| [`data-contract.md`](data-contract.md) | Warehouse schema and HTTP API contract |
| [`backend.md`](backend.md) | FastAPI + DuckDB module, routes, local run and deployment |
| [`frontend.md`](frontend.md) | Next.js components, map, filters and Vercel deployment |
| [`research-2026.md`](research-2026.md) | The 2026 methodological decisions that the site must preserve |
| [`model-lab.md`](model-lab.md) | Why ML is not a public predictor and how the server-side lab should work |
| [`roadmap.md`](roadmap.md) | Phased TODO for every module |
| [`../lessons/README.md`](../lessons/README.md) | Beginner-friendly lessons for the whole stack |
| [`decisions/0001-stack.md`](decisions/0001-stack.md) | Architecture decision record for the initial stack |

## Learning path

Start with [`../lessons/README.md`](../lessons/README.md) if you are new to Python,
React, APIs, maps or deployment. Each lesson points to the real files and includes small
exercises. Technical reference pages are below.

## Module ownership

```text
src/              reusable cleaning and analysis library (2026 logic)
pipeline/         builds the queryable warehouse from the raw CSV
apps/api/         live-query HTTP API (FastAPI + DuckDB)
apps/web/         public Next.js site (MapLibre + ECharts)
data/             raw downloads, processed warehouse, static geo assets
artifacts/        model binaries and exported research artifacts
lessons/          beginner tutorials for the stack
notebooks/        research provenance; not imported by production code
reports/          human-readable research reports
paper/            LaTeX paper
```

## Rules of the project

1. **The 2026 interpretation wins.** `CANTIDAD` is a stock, not a flow. The site must never
   sum it across monthly publication dates.
2. **The UI is descriptive first.** The ML model is a methodological exhibit, not a
   decision tool.
3. **Every number must be traceable.** The API exposes the cutoff date and the pipeline
   writes a manifest with row counts and checksums.
4. **The map is interactive, not decorative.** Clicking a country must filter the rest of
   the dashboard.
5. **Spanish is the default language.** Domain labels are kept exactly as normalized in
   `src/cleaning.py`.
