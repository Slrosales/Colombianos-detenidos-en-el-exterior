"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { BreakdownRow } from "@/lib/api";
import { PALETTE, TOOLTIP } from "@/lib/chart-theme";
import { formatNumber, shortLabel } from "@/lib/format";
import { Chart } from "./Chart";

type BarPanelProps = {
  title: string;
  subtitle?: string;
  rows: BreakdownRow[];
  color?: string;
  limit?: number;
  className?: string;
};

export function BarPanel({
  title,
  subtitle,
  rows,
  color = PALETTE.cyan,
  limit = 8,
  className = "chart",
}: BarPanelProps) {
  const option = useMemo<EChartsOption>(() => {
    const top = rows.slice(0, limit);
    const values = [...top].reverse();
    return {
      animationDuration: 450,
      grid: { left: 8, right: 54, top: 8, bottom: 4, containLabel: true },
      tooltip: {
        ...TOOLTIP,
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: "rgba(94,200,216,.06)" } },
        valueFormatter: (value) => `${formatNumber(Number(value))} detenidos`,
      },
      xAxis: { type: "value" },
      yAxis: {
        type: "category",
        data: values.map((row) => shortLabel(row.valor, 24)),
      },
      series: [
        {
          type: "bar",
          data: values.map((row) => row.cantidad),
          barMaxWidth: 17,
          itemStyle: { color, borderRadius: [0, 5, 5, 0] },
          label: {
            show: true,
            position: "right",
            fontSize: 9,
            formatter: (params) => formatNumber(Number(params.value)),
          },
        },
      ],
    };
  }, [rows, color, limit]);

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </header>
      <div className="card-body">
        {rows.length === 0 ? (
          <div className="chart-error">Sin datos para este filtro.</div>
        ) : (
          <Chart option={option} className={className} />
        )}
      </div>
    </section>
  );
}
