"use client";

import { useEffect, useMemo, useState } from "react";
import {
  api,
  API_BASE,
  type BreakdownRow,
  type CompareRow,
  type CountryRow,
  type Filters,
  type FiltersResponse,
  type Meta,
  type TrendPoint,
} from "@/lib/api";
import { formatCutoff, formatNumber, formatPercent } from "@/lib/format";
import { BarPanel } from "./BarPanel";
import { ComparePanel } from "./ComparePanel";
import { CountryPanel } from "./CountryPanel";
import { FilterBar } from "./FilterBar";
import { StatCard } from "./StatCard";
import { TrendPanel } from "./TrendPanel";
import { WorldMap } from "./WorldMap";

type Groups = Record<"delito" | "edad" | "genero" | "situacion", BreakdownRow[]>;

const EMPTY_GROUPS: Groups = { delito: [], edad: [], genero: [], situacion: [] };

export function ExploreDashboard() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [cutoff, setCutoff] = useState("");
  const [filters, setFilters] = useState<Filters>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [options, setOptions] = useState<FiltersResponse | null>(null);
  const [countries, setCountries] = useState<CountryRow[]>([]);
  const [groups, setGroups] = useState<Groups>(EMPTY_GROUPS);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [compare, setCompare] = useState<CompareRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .meta()
      .then((value) => {
        if (!active) return;
        setMeta(value);
        setCutoff(value.corte_actual);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(
          `No se pudo conectar con la API (${API_BASE}). ${
            reason instanceof Error ? reason.message : ""
          }`,
        );
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!cutoff) return;
    let active = true;
    setError(null);
    Promise.all([
      api.filters(cutoff),
      api.countries(cutoff, filters),
      api.compare("2021-05-01", meta?.corte_actual),
    ])
      .then(([filterOptions, countryRows, compareRows]) => {
        if (!active) return;
        setOptions(filterOptions);
        setCountries(countryRows);
        setCompare(compareRows);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "Error al cargar los datos");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [cutoff, filters, meta?.corte_actual]);

  useEffect(() => {
    if (!cutoff) return;
    let active = true;
    const scoped = { ...filters, pais: selected ?? undefined };
    Promise.all([
      api.breakdown("delito", cutoff, scoped),
      api.breakdown("edad", cutoff, scoped),
      api.breakdown("genero", cutoff, scoped),
      api.breakdown("situacion", cutoff, scoped),
      api.trend(scoped),
    ])
      .then(([delito, edad, genero, situacion, trendRows]) => {
        if (!active) return;
        setGroups({ delito, edad, genero, situacion });
        setTrend(trendRows);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "Error al cargar el perfil");
      });
    return () => {
      active = false;
    };
  }, [cutoff, filters, selected]);

  const selectedCountry = useMemo(
    () => countries.find((row) => row.pais === selected),
    [countries, selected],
  );

  const filteredTotal = useMemo(
    () => groups.situacion.reduce((sum, row) => sum + row.cantidad, 0),
    [groups.situacion],
  );

  const topCountry = countries[0];
  const topCrime = groups.delito[0];
  const unknownShare = meta?.pct_pais_desconocido_corte_actual ?? null;
  const hasFilters = Object.values(filters).some(Boolean);
  const displayTotal =
    selected || hasFilters ? filteredTotal : meta?.total_corte_actual ?? filteredTotal;

  function handleCutoffChange(value: string) {
    setCutoff(value);
    setSelected(null);
  }

  function handleReset() {
    setFilters({});
    setSelected(null);
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Explorador de datos abiertos · 2018–2026</p>
          <h1>Colombianos detenidos en el exterior</h1>
          <p>
            Consulta el stock de personas detenidas activas por país, delito, edad,
            género y situación jurídica. Cada cifra corresponde a un corte de
            publicación; las comparaciones usan el último corte de cada año.
          </p>
        </div>
        <div className="cutoff-chip">
          <span className="dot" />
          Corte {formatCutoff(meta?.corte_actual)}
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="stats-grid" aria-label="Indicadores del corte">
        <StatCard
          label="Detenidos activos"
          value={formatNumber(displayTotal)}
          detail={selected ? `Filtrado por ${selected}` : `Corte ${cutoff || "—"}`}
        />
        <StatCard
          label="País principal"
          value={topCountry?.pais ?? "—"}
          detail={
            topCountry
              ? `${formatNumber(topCountry.cantidad)} personas · ${formatPercent(
                  topCountry.participacion,
                )}`
              : "Sin datos"
          }
        />
        <StatCard
          label="Delito principal"
          value={topCrime?.valor ?? "—"}
          detail={topCrime ? `${formatNumber(topCrime.cantidad)} registros` : "Sin datos"}
        />
        <StatCard
          label="País sin identificar"
          value={formatPercent(unknownShare)}
          detail="Del total del corte actual"
        />
      </section>

      <FilterBar
        cutoff={cutoff}
        cutoffs={meta?.cutoffs ?? []}
        filters={filters}
        options={options}
        onChange={setFilters}
        onCutoffChange={handleCutoffChange}
        onReset={handleReset}
      />

      {loading ? (
        <div className="loading-box">Cargando el tablero y el mapa…</div>
      ) : (
        <>
          <div className="dashboard-grid">
            <section className="card">
              <header className="card-header">
                <div>
                  <h2>Detenidos activos por país</h2>
                  <p>
                    {cutoff}. Escala por cuantiles. El país se recupera desde el
                    consulado cuando la fuente no lo reporta.
                  </p>
                </div>
              </header>
              <WorldMap
                data={countries}
                selected={selected}
                onSelect={setSelected}
              />
            </section>

            <CountryPanel
              selected={selected}
              country={selectedCountry}
              groups={groups}
              onClear={() => setSelected(null)}
            />
          </div>

          <div className="charts-grid">
            <TrendPanel points={trend} country={selected} />
            <BarPanel
              title={selected ? `Delitos en ${selected}` : "Delitos en el corte"}
              subtitle="Categorías normalizadas; OTRO incluye DESCONOCIDO."
              rows={groups.delito}
              color="#d98b5f"
            />
            <BarPanel
              title={selected ? `Edad en ${selected}` : "Grupo de edad"}
              subtitle="DESCONOCIDO se conserva como categoría."
              rows={groups.edad}
              color="#8a7fe0"
            />
            <BarPanel
              title={selected ? `Género en ${selected}` : "Género"}
              subtitle="Distribución ponderada por CANTIDAD."
              rows={groups.genero}
              color="#5fb88a"
            />
            <BarPanel
              title={selected ? `Situación jurídica en ${selected}` : "Situación jurídica"}
              subtitle="EN INVESTIGACIÓN → EN JUICIO → CONDENADO es un orden, no una escala de riesgo."
              rows={groups.situacion}
              color="#5ec8d8"
            />
            <BarPanel
              title="Consulados"
              subtitle="Los consulados permiten recuperar el país después de 2022."
              rows={options?.values?.consulado ?? []}
              color="#c9a35e"
              limit={6}
            />
          </div>

          <ComparePanel
            rows={compare}
            base="2021-05-01"
            target={meta?.corte_actual ?? cutoff}
          />

        </>
      )}
    </main>
  );
}
