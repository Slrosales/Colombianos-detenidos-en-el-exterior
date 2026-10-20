# Frontend module

```text
apps/web/
├── app/
│   ├── layout.tsx        shell, metadata, fonts and navigation
│   ├── page.tsx          explore dashboard
│   ├── methodology/      stock vs flow, consulate recovery, limitations
│   └── model/            research metrics and model lab placeholder
├── components/
│   ├── ExploreDashboard.tsx
│   ├── WorldMap.tsx
│   ├── BarPanel.tsx
│   ├── TrendPanel.tsx
│   ├── ComparePanel.tsx
│   ├── Filters.tsx
│   └── StatCard.tsx
├── lib/
│   ├── api.ts            typed API client
│   └── format.ts         numbers and percentages in es-CO
├── public/data/countries.geojson
└── package.json
```

## UX rules

- Spanish (`es-CO`) is the interface language.
- The cutoff is always visible. There is no ambiguous "latest" label without a date.
- The map is the primary control: clicking a country opens its profile and applies filters.
- Mobile first: filters collapse into a panel, charts stack vertically.
- The site must remain useful if the API is down: show a clear error, not empty cards.
- Never present the ordinal model as a prediction about a real person.

## Data flow

```text
ExploreDashboard
  ├── useFilters (cutoff + categorical filters + selected country)
  ├── /api/meta          -> cutoff badge and quality indicators
  ├── /api/countries     -> MapLibre choropleth + top countries
  ├── /api/breakdown/*   -> crime/age/gender/situation bars
  ├── /api/trend         -> stock at the last cutoff of each year
  └── /api/compare       -> 2021 vs 2026 diverging chart
```

The client is deliberately thin. It does not compute stock semantics; the API does.

## Map

- MapLibre GL JS with a blank background and a committed GeoJSON.
- Choropleth fill uses quantile bins over positive country counts.
- `DESCONOCIDO` is excluded from the country layer and reported separately.
- Clicking a feature selects the country; clicking the background clears it.
- No external basemap token is required. This keeps previews deterministic.

## Local run

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open <http://localhost:3000>.

## Production

- Vercel project root: `apps/web`.
- Environment: `NEXT_PUBLIC_API_URL=https://api.example.org`.
- The GeoJSON is static and cacheable; the API responses depend on the cutoff.

## TODO

- [ ] URL-synced filters (`?cutoff=...&pais=...`) for shareable views.
- [ ] Country profile page with a static, indexable route.
- [ ] Download filtered CSV.
- [ ] Accessibility audit and keyboard navigation on the map.
- [ ] English translation.
- [ ] Model lab interaction (phase 4).
