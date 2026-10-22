// Static demo adapter. It implements the same surface as the live HTTP client using
// precomputed JSON in `public/data/demo/`, so the site can deploy without a backend.
//
// Demo scope: annual cutoffs + country profiles. Cross-filters are intentionally not
// precomputed; the UI disables them when NEXT_PUBLIC_STATIC_DEMO=true.

import type {
  BreakdownRow,
  CompareRow,
  CountryRow,
  Dimension,
  FilterOption,
  Filters,
  FiltersResponse,
  Meta,
  ModelMetrics,
  TrendPoint,
} from "./api";

const BASE = "/data/demo";

type DemoCutoff = {
  cutoff: string;
  total: number;
  countries: CountryRow[];
  filters: Record<string, FilterOption[]>;
  breakdowns: Record<string, BreakdownRow[]>;
  profiles: Record<string, Record<string, BreakdownRow[]>>;
  compare: CompareRow[];
};

type TrendData = {
  total: TrendPoint[];
  by_country: Record<string, TrendPoint[]>;
};

const cutoffCache = new Map<string, Promise<DemoCutoff>>();
let metaPromise: Promise<Meta> | null = null;
let trendPromise: Promise<TrendData> | null = null;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`No se pudo cargar ${path} (HTTP ${response.status})`);
  }
  return (await response.json()) as T;
}

function loadMeta(): Promise<Meta> {
  metaPromise ??= getJson<Meta>(`${BASE}/meta.json`);
  return metaPromise;
}

function loadTrend(): Promise<TrendData> {
  trendPromise ??= getJson<TrendData>(`${BASE}/trend.json`);
  return trendPromise;
}

function loadCutoff(cutoff: string): Promise<DemoCutoff> {
  let promise = cutoffCache.get(cutoff);
  if (!promise) {
    promise = getJson<DemoCutoff>(`${BASE}/${cutoff}.json`);
    cutoffCache.set(cutoff, promise);
  }
  return promise;
}

export const staticApi = {
  meta: () => loadMeta(),

  filters: async (cutoff: string): Promise<FiltersResponse> => {
    const data = await loadCutoff(cutoff);
    return { cutoff, values: data.filters as FiltersResponse["values"] };
  },

  countries: async (
    cutoff: string,
    _filters: Filters = {},
  ): Promise<CountryRow[]> => {
    const data = await loadCutoff(cutoff);
    return data.countries;
  },

  breakdown: async (
    dimension: Dimension,
    cutoff: string,
    filters: Filters & { pais?: string } = {},
  ): Promise<BreakdownRow[]> => {
    const data = await loadCutoff(cutoff);
    if (filters.pais) {
      return data.profiles[filters.pais]?.[dimension] ?? [];
    }
    return data.breakdowns[dimension] ?? [];
  },

  trend: async (filters: Filters & { pais?: string } = {}): Promise<TrendPoint[]> => {
    const data = await loadTrend();
    return filters.pais ? data.by_country[filters.pais] ?? [] : data.total;
  },

  compare: async (base = "2021-05-01", target?: string): Promise<CompareRow[]> => {
    const resolved = target ?? (await loadMeta()).corte_actual;
    const data = await loadCutoff(resolved);
    return data.compare;
  },

  modelMetrics: (): Promise<ModelMetrics> =>
    getJson<ModelMetrics>(`${BASE}/model-metrics.json`),
};
