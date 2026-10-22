"use client";

import { useEffect, useMemo, useRef } from "react";
import type { FeatureCollection } from "geojson";
import type {
  ExpressionSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
  Popup as MapLibrePopup,
  StyleSpecification,
} from "maplibre-gl";
import type { CountryRow } from "@/lib/api";
import { formatNumber } from "@/lib/format";

type WorldMapProps = {
  data: CountryRow[];
  selected: string | null;
  onSelect: (country: string | null) => void;
};

const WORLD_GEOJSON = "/data/countries.geojson";
const ISO_ALIASES: Record<string, string> = {
  CWU: "CW",
  BES: "BQ",
  UMI: "UM",
};

const COLORS_6 = ["#17324a", "#1e566f", "#2d8391", "#d9a15b", "#d36c4e", "#b33a4a"];
const BASE_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#080d16" },
    },
  ],
};

function normalizeIso(iso: string | null | undefined): string | null {
  if (!iso) return null;
  return ISO_ALIASES[iso] ?? iso;
}

function quantile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const position = (sorted.length - 1) * p;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

export function buildScale(data: CountryRow[]) {
  const counts = data
    .map((row) => row.cantidad)
    .filter((value) => value > 0)
    .sort((a, b) => a - b);

  if (counts.length === 0) {
    return { breaks: [], colors: COLORS_6.slice(0, 1), labels: ["Sin datos"] };
  }

  const rawBreaks = [0.12, 0.3, 0.5, 0.7, 0.88]
    .map((p) => Math.max(1, Math.round(quantile(counts, p))))
    .filter((value, index, array) => array.indexOf(value) === index)
    .sort((a, b) => a - b);

  const colors = COLORS_6.slice(0, rawBreaks.length + 1);
  const labels = rawBreaks.map((value, index) => {
    if (index === 0) return `≤ ${formatNumber(value)}`;
    return `${formatNumber(rawBreaks[index - 1])}–${formatNumber(value)}`;
  });
  labels.push(`> ${formatNumber(rawBreaks[rawBreaks.length - 1])}`);

  return { breaks: rawBreaks, colors, labels };
}

function fillExpression(breaks: number[]): ExpressionSpecification {
  const empty = "#121b2b";
  if (breaks.length === 0) {
    return ["case", ["==", ["get", "count"], null], empty, COLORS_6[0]] as unknown as ExpressionSpecification;
  }
  const colors = COLORS_6.slice(0, breaks.length + 1);
  const step: unknown[] = ["step", ["get", "count"], colors[0]];
  breaks.forEach((value, index) => {
    step.push(value, colors[index + 1]);
  });
  return ["case", ["==", ["get", "count"], null], empty, step] as unknown as ExpressionSpecification;
}

function joinCountries(base: FeatureCollection, rows: CountryRow[]): FeatureCollection {
  const byIso = new Map<string, CountryRow>();
  const byName = new Map<string, CountryRow>();
  for (const row of rows) {
    const iso = normalizeIso(row.pais_iso3);
    if (iso) byIso.set(iso, row);
    byName.set(row.pais, row);
  }

  return {
    ...base,
    features: base.features.map((feature) => {
      const properties = (feature.properties ?? {}) as Record<string, unknown>;
      const rawIso =
        (properties.ISO_A3 as string) ||
        (properties.ISO_A3_EH as string) ||
        (properties.ADM0_A3 as string) ||
        "";
      const iso = normalizeIso(rawIso === "-99" ? null : rawIso);
      const row =
        (iso ? byIso.get(iso) : undefined) ??
        byName.get((properties.NAME_ES as string) ?? "") ??
        null;

      return {
        ...feature,
        properties: {
          ...properties,
          iso3: iso,
          count: row?.cantidad ?? null,
          pais: row?.pais ?? null,
        },
      };
    }),
  };
}

export function WorldMap({ data, selected, onSelect }: WorldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const baseRef = useRef<FeatureCollection | null>(null);
  const popupRef = useRef<MapLibrePopup | null>(null);
  const dataRef = useRef(data);
  const selectedRef = useRef(selected);
  const onSelectRef = useRef(onSelect);
  const scale = useMemo(() => buildScale(data), [data]);

  dataRef.current = data;
  selectedRef.current = selected;
  onSelectRef.current = onSelect;

  useEffect(() => {
    let disposed = false;
    let map: MapLibreMap | null = null;

    async function mount() {
      const maplibregl = await import("maplibre-gl");
      if (disposed || !containerRef.current) return;

      // Next.js/Turbopack does not resolve the worker URL automatically; point it at
      // the self-contained worker module so the map renders in dev and production.
      maplibregl.setWorkerUrl(
        new URL(
          "maplibre-gl/dist/maplibre-gl-worker.mjs",
          import.meta.url,
        ).href,
      );

      map = new maplibregl.Map({
        container: containerRef.current,
        style: BASE_STYLE,
        center: [12, 18],
        zoom: 1.25,
        minZoom: 1,
        maxZoom: 6,
        attributionControl: false,
        dragRotate: false,
      });
      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

      const popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 12,
        className: "country-popup",
      });
      popupRef.current = popup;

      map.on("load", async () => {
        if (!map) return;
        try {
          const response = await fetch(WORLD_GEOJSON);
          if (!response.ok) throw new Error(`GeoJSON HTTP ${response.status}`);
          const base = (await response.json()) as FeatureCollection;
          baseRef.current = base;

          const joined = joinCountries(base, dataRef.current);
          map.addSource("countries", {
            type: "geojson",
            data: joined,
            generateId: true,
          });
          map.addLayer({
            id: "country-fill",
            type: "fill",
            source: "countries",
            paint: {
              "fill-color": fillExpression(buildScale(dataRef.current).breaks),
              "fill-opacity": 0.92,
            },
          });
          map.addLayer({
            id: "country-border",
            type: "line",
            source: "countries",
            paint: {
              "line-color": "rgba(190, 220, 245, 0.18)",
              "line-width": 0.55,
            },
          });
          map.addLayer({
            id: "country-selected",
            type: "line",
            source: "countries",
            filter: ["==", ["get", "pais"], "__none__"],
            paint: {
              "line-color": "#8be3ee",
              "line-width": 2.2,
              "line-blur": 0.5,
            },
          });

          map.on("mousemove", "country-fill", (event) => {
            const feature = event.features?.[0];
            const properties = (feature?.properties ?? {}) as {
              count?: number | null;
              pais?: string | null;
            };
            if (!feature || properties.count === null || properties.count === undefined) {
              map!.getCanvas().style.cursor = "";
              popup.remove();
              return;
            }
            map!.getCanvas().style.cursor = "pointer";
            popup
              .setLngLat(event.lngLat)
              .setText(
                `${properties.pais ?? "País"}\n${formatNumber(properties.count)} detenidos activos`,
              )
              .addTo(map!);
          });

          map.on("mouseleave", "country-fill", () => {
            if (!map) return;
            map.getCanvas().style.cursor = "";
            popup.remove();
          });

          map.on("click", "country-fill", (event) => {
            const feature = event.features?.[0];
            const properties = (feature?.properties ?? {}) as {
              pais?: string | null;
            };
            if (!properties.pais) return;
            onSelectRef.current(
              selectedRef.current === properties.pais ? null : properties.pais,
            );
          });

          map.on("click", (event) => {
            const features = map!.queryRenderedFeatures(event.point, {
              layers: ["country-fill"],
            });
            if (features.length === 0) onSelectRef.current(null);
          });

          applySelection(map, selectedRef.current);
        } catch (error) {
          console.error("Could not load the world map", error);
        }
      });
    }

    void mount();

    return () => {
      disposed = true;
      popupRef.current?.remove();
      map?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const base = baseRef.current;
    if (!map || !base || !map.getSource("countries")) return;

    const joined = joinCountries(base, data);
    const source = map.getSource("countries") as GeoJSONSource | undefined;
    if (!source) return;
    source.setData(joined);
    map.setPaintProperty(
      "country-fill",
      "fill-color",
      fillExpression(buildScale(data).breaks),
    );
    applySelection(map, selected);
  }, [data, selected]);

  return (
    <div className="map-shell">
      <div
        ref={containerRef}
        className="map-canvas"
        role="application"
        aria-label="Mapa mundial interactivo de colombianos detenidos activos por país"
      />
      {data.length === 0 ? (
        <div className="map-empty">Sin países que cumplan este filtro.</div>
      ) : null}
      <div className="map-legend">
        <div className="legend-title">Detenidos activos</div>
        <div className="legend-items">
          {scale.labels.map((label, index) => (
            <div className="legend-item" key={label}>
              <div
                className="legend-swatch"
                style={{ background: scale.colors[index] }}
              />
              {label}
            </div>
          ))}
        </div>
      </div>
      <div className="map-hint">Haz clic en un país para filtrar</div>
    </div>
  );
}

function applySelection(map: MapLibreMap, selected: string | null) {
  if (!map.getLayer("country-selected")) return;
  map.setFilter("country-selected", [
    "==",
    ["get", "pais"],
    selected ?? "__none__",
  ]);
}
