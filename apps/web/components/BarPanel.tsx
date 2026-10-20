"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { BreakdownRow } from "@/lib/api";
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

const TOOLTIP = {
  backgroundColor: "#0b1422",
  borderColor: "#2b4364",
  borderWidth: 1,
  padding: 10,
  textStyle: { color: "#eef4fc", fontSize: 11 },
};

export function BarPanel({
  title,
  subtitle,
  rows,
  color = "#5ec8d8",
  limit = 8,
  className = "chart",
}: BarPanelProps) {
  const option = useMemo<EChartsOption>(() => {
    const top = rows.slice(0, limit);
    const values = [...top].reverse();
    return {
      backgroundColor: "transparent",
      animationDuration: 450,
      grid: { left: 8, right: 54, top: 8, bottom: 4, containLabel: true },
      tooltip: {
        ...TOOLTIP,
        trigger: "axis",
        axisPointer: { type: "shadow", shadowStyle: { color: "rgba(94,200,216,.06)" } },
        valueFormatter: (value) => `${formatNumber(Number(value))} detenidos`,
      },
      xAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(120,150,190,.10)" } },
        axisLabel: { color: "#6e819b", fontSize: 9 },
      },
      yAxis: {
        type: "category",
        data: values.map((row) => shortLabel(row.valor, 24)),
        axisLabel: { color: "#9eb0c7", fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
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
            color: "#9eb0c7",
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
