"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { CompareRow } from "@/lib/api";
import { PALETTE, TOOLTIP } from "@/lib/chart-theme";
import { formatNumber, formatSignedPercent, shortLabel } from "@/lib/format";
import { Chart } from "./Chart";

type ComparePanelProps = {
  rows: CompareRow[];
  base: string;
  target: string;
};

export function ComparePanel({ rows, base, target }: ComparePanelProps) {
  const summary = useMemo(() => {
    const totalBase = rows.reduce((sum, row) => sum + row.base, 0);
    const totalTarget = rows.reduce((sum, row) => sum + row.target, 0);
    const pct = totalBase ? (100 * (totalTarget - totalBase)) / totalBase : null;
    const ranked = rows
      .filter((row) => row.cambio_pct !== null && row.base > 0)
      .sort((a, b) => (b.cambio_pct ?? 0) - (a.cambio_pct ?? 0));
    return {
      totalBase,
      totalTarget,
      pct,
      increases: ranked.slice(0, 6),
      decreases: ranked.slice(-6).reverse(),
    };
  }, [rows]);

  const option = useMemo<EChartsOption>(() => {
    const selected = [...summary.decreases, ...summary.increases].sort(
      (a, b) => (b.cambio_pct ?? 0) - (a.cambio_pct ?? 0),
    );
    const values = [...selected].reverse();
    return {
      animationDuration: 500,
      grid: { left: 8, right: 48, top: 8, bottom: 6, containLabel: true },
      tooltip: {
        ...TOOLTIP,
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: "rgba(94,200,216,.06)" } },
        formatter: (params) => {
          const index = Array.isArray(params) ? Number(params[0]?.dataIndex ?? 0) : 0;
          const row = values[index];
          if (!row) return "";
          return [
            `<strong>${row.pais}</strong>`,
            `${base}: ${formatNumber(row.base)}`,
            `${target}: ${formatNumber(row.target)}`,
            `Cambio: ${formatSignedPercent(row.cambio_pct)}`,
          ].join("<br/>");
        },
      },
      xAxis: {
        type: "value",
        axisLabel: {
          formatter: (value: number) => `${value}%`,
        },
      },
      yAxis: {
        type: "category",
        data: values.map((row) => shortLabel(row.pais, 22)),
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 16,
          data: values.map((row) => ({
            value: row.cambio_pct,
            itemStyle: {
              color:
                (row.cambio_pct ?? 0) >= 0
                  ? PALETTE.positive
                  : PALETTE.negative,
              borderRadius:
                (row.cambio_pct ?? 0) >= 0 ? [0, 5, 5, 0] : [5, 0, 0, 5],
            },
            label: {
              show: true,
              position: (row.cambio_pct ?? 0) >= 0 ? "right" : "left",
              fontSize: 9,
              formatter: formatSignedPercent(row.cambio_pct),
            },
          })),
        },
      ],
    };
  }, [summary, base, target]);

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h3>Cambio 2021 → 2026</h3>
          <p>
            Variación porcentual del stock entre {base} y {target}. Países con base
            positiva.
          </p>
        </div>
      </header>
      <div className="compare-summary">
        <div>
          <div className="k">Stock {base}</div>
          <div className="v">{formatNumber(summary.totalBase)}</div>
        </div>
        <div>
          <div className="k">Stock {target}</div>
          <div className="v">{formatNumber(summary.totalTarget)}</div>
        </div>
        <div>
          <div className="k">Cambio agregado</div>
          <div className="v">{formatSignedPercent(summary.pct)}</div>
        </div>
      </div>
      <div className="card-body">
        {rows.length === 0 ? (
          <div className="chart-error">Sin datos comparables.</div>
        ) : (
          <Chart option={option} className="chart tall" />
        )}
      </div>
      <p className="chart-note">
        Los cambios pueden reflejar dinámicas reales, pero también cambios de reporte,
        cobertura consular o clasificación. No implican causalidad.
      </p>
    </section>
  );
}
