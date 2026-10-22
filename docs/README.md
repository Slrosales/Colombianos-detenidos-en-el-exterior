# Documentation index

This folder explains how the data pipeline, the API and the web app fit together. The
public interface is in Spanish; the developer documentation is in English.

Start here:

| Document | What it answers |
|---|---|
| [`architecture.md`](architecture.md) | How the pieces connect and why the stack was chosen |
| [`data-contract.md`](data-contract.md) | Warehouse schema and HTTP API contract |
| [`backend.md`](backend.md) | FastAPI + DuckDB module, routes, local run and deployment |
| [`frontend.md`](frontend.md) | Next.js components, map, filters and Vercel deployment |
| [`model-lab.md`](model-lab.md) | Why ML is not a public predictor and how the server-side lab should work |
| [`testing.md`](testing.md) | Test layers, commands and CI recommendation |
| [`deployment.md`](deployment.md) | Production topology, Fly.io/Vercel steps, data updates and rollback |
| [`roadmap.md`](roadmap.md) | Phased TODO for every module |
| [`decisions/0001-stack.md`](decisions/0001-stack.md) | Architecture decision record for the initial stack |

## Repository map

```text
src/              reusable cleaning and analysis library
pipeline/         builds and validates the queryable warehouse
apps/api/         live-query HTTP API (FastAPI + DuckDB)
apps/web/         public Next.js site (MapLibre + ECharts)
data/             raw downloads, processed warehouse, static geo assets
notebooks/        research notebooks (public)
docs/             public developer documentation
```

The complete research package (lessons, paper, reports, generated outputs and the 2026
research memo) is kept locally by the author and is not part of this public repository.
Notebooks remain public because they were part of the original repository.

## Rules of the project

1. **The 2026 interpretation wins.** `CANTIDAD` is a stock, not a flow. The site must never
   sum it across monthly publication dates.
2. **The UI is descriptive first.** The ML model is a methodological exhibit, not a
   decision tool.
3. **Every number must be traceable.** The API exposes the cutoff date and the pipeline
   writes a manifest with row counts and checksums.
4. **The map is interactive, not decorative.** Clicking a country filters the rest of the
   dashboard.
5. **Spanish is the default language.** Domain labels are kept exactly as normalized in
   `src/cleaning.py`.
