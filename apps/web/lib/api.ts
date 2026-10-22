export const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export type Dimension =
  | "pais"
  | "delito"
  | "edad"
  | "genero"
  | "situacion"
  | "consulado";

export type Filters = {
  pais?: string;
  delito?: string;
  edad?: string;
  genero?: string;
  situacion?: string;
};

export type Meta = {
  corte_actual: string;
  fecha_min: string;
  fecha_max: string;
  filas_totales: number;
  filas_corte_actual: number;
  total_corte_actual: number;
  duplicados_eliminados: number;
  pct_pais_desconocido_corte_actual: number | null;
  paises_distintos_corte_actual: number;
  cutoffs: string[];
  source_sha256?: string;
  generated_at?: string;
};

export type CountryRow = {
  pais: string;
  pais_iso3: string | null;
  cantidad: number;
  participacion: number;
  latitud: number | null;
  longitud: number | null;
};

export type BreakdownRow = {
  valor: string;
  cantidad: number;
};

export type TrendPoint = {
  anio: number;
  fecha: string;
  cantidad: number;
};

export type CompareRow = {
  pais: string;
  pais_iso3: string | null;
  base: number;
  target: number;
  cambio: number;
  cambio_pct: number | null;
};

export type FilterOption = BreakdownRow;

export type FiltersResponse = {
  cutoff: string;
  values: Record<Dimension | "consulado", FilterOption[]>;
};

export type ModelMetrics = {
  train_date: string | null;
  test_date: string | null;
  target_order: string[];
  models: Array<Record<string, string | number | null>>;
  advertencia: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const url = new URL(`${API_BASE}${path}`);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function getJson<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<T> {
  const response = await fetch(buildUrl(path, params), { cache: "no-store" });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the status text when the server does not return JSON.
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export const api = {
  meta: () => getJson<Meta>("/api/meta"),
  filters: (cutoff: string) =>
    getJson<FiltersResponse>("/api/filters", { cutoff }),
  countries: (cutoff: string, filters: Filters = {}) =>
    getJson<CountryRow[]>("/api/countries", {
      cutoff,
      limit: 250,
      ...filters,
    }),
  breakdown: (
    dimension: Dimension,
    cutoff: string,
    filters: Filters & { pais?: string } = {},
  ) =>
    getJson<BreakdownRow[]>(`/api/breakdown/${dimension}`, {
      cutoff,
      limit: 100,
      ...filters,
    }),
  trend: (filters: Filters & { pais?: string } = {}) =>
    getJson<TrendPoint[]>("/api/trend", filters),
  compare: (base = "2021-05-01", target?: string) =>
    getJson<CompareRow[]>("/api/compare", { base, target, limit: 250 }),
  modelMetrics: () => getJson<ModelMetrics>("/api/model/metrics"),
};
