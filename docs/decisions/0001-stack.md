# ADR 0001: Static-first frontend with a live-query API

Status: accepted (2026-10)

## Context

The repository already contains a reproducible Python analysis (`src/`), notebooks, reports
and a LaTeX paper. The new deliverable is a public, informative and interactive webpage based
on the interactive maps from the exploratory notebook. Live queries and a server-side model
lab were requested. The 2026 research corrects earlier aggregation mistakes, so the UI must
make `CANTIDAD` semantics explicit.

## Decision

- Build the public site with Next.js and MapLibre.
- Serve live aggregates from a read-only FastAPI service backed by DuckDB and a Parquet
  warehouse.
- Keep the model out of the public decision path; expose metrics and a future isolated lab.
- Organize by runtime responsibility (`apps/web`, `apps/api`, `pipeline`, `src`) rather than a
  premature generic `backend/frontend` split.

## Consequences

Positive:

- Fast local development and free/cheap deployment.
- No database server to operate.
- Filters and map interactions do not ship the full dataset.
- The SQL contract can migrate to PostgreSQL later.

Negative:

- Two deploy targets (Vercel + API host).
- The API needs the parquet artifact at runtime.
- A public API requires CORS, rate limiting and caching work before launch.

## Alternatives rejected

- **Static-only site:** cannot support arbitrary live filters without shipping data.
- **Streamlit/Dash:** fast for notebooks, weak for a polished public product and mobile UX.
- **Full Postgres from day one:** unnecessary operational cost for a read-only 362k-row table.
- **Client-side model:** avoids the server-side learning goal and exposes model internals.
