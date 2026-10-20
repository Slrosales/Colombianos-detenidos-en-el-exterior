"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { TrendPoint } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { Chart } from "./Chart";

type TrendPanelProps = {
  points: TrendPoint[];
  country?: string | null;
};

const TOOLTIP = {
  backgroundColor: "#0b1422",
  borderColor: "#2b4364",
  borderWidth: 1,
  padding: 10,
  textStyle: { color: "#eef4fc", fontSize: 11 },
};

export function TrendPanel({ points, country }: TrendPanelProps) {
  const option = useMemo<EChartsOption>(() => {
    const last = points.at(-1);
    return {
      backgroundColor: "transparent",
      animationDuration: 500,
      grid: { left: 10, right: 18, top: 20, bottom: 8, containLabel: true },
      tooltip: {
        ...TOOLTIP,
        trigger: "axis",
        valueFormatter: (value) => `${formatNumber(Number(value))} detenidos`,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: points.map((point) => point.anio),
        axisLabel: { color: "#6e819b", fontSize: 10 },
        axisLine: { lineStyle: { color: "#263850" } },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(120,150,190,.10)" } },
        axisLabel: {
          color: "#6e819b",
          fontSize: 9,
          formatter: (value: number) => `${Math.round(value / 1000)}k`,
        },
      },
      series: [
        {
          type: "line",
          data: points.map((point) => point.cantidad),
          smooth: 0.25,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#5ec8d8", width: 2.4 },
          itemStyle: { color: "#8be3ee", borderColor: "#080d16", borderWidth: 2 },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(94,200,216,.34)" },
                { offset: 1, color: "rgba(94,200,216,.01)" },
              ],
            },
          },
          markPoint: last
            ? {
                symbol: "circle",
                symbolSize: 9,
                itemStyle: { color: "#8be3ee" },
                label: {
                  show: true,
                  position: "top",
                  color: "#eef4fc",
                  fontSize: 10,
                  formatter: formatNumber(last.cantidad),
                },
                data: [{ name: String(last.anio), coord: [last.anio, last.cantidad] }],
              }
            : undefined,
        },
      ],
    };
  }, [points]);

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h3>Stock al último corte de cada año</h3>
          <p>
            {country
              ? `${country}: personas activas en el último corte disponible del año`
              : "Personas activas en el último corte disponible del año"}
          </p>
        </div>
      </header>
      <div className="card-body">
        {points.length === 0 ? (
          <div className="chart-error">Sin datos para este filtro.</div>
        ) : (
          <Chart option={option} />
        )}
      </div>
      <p className="chart-note">
        La serie mide stock, no flujo. No es el número de nuevas detenciones de cada año.
      </p>
    </section>
  );
}
