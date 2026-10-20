"use client";

import { useEffect, useRef } from "react";
import type { ECharts, EChartsOption } from "echarts";

type ChartProps = {
  option: EChartsOption;
  className?: string;
};

export function Chart({ option, className = "chart" }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ECharts | null>(null);

  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | null = null;

    async function mount() {
      const echarts = await import("echarts");
      if (disposed || !containerRef.current) return;

      const chart = echarts.init(containerRef.current, undefined, {
        renderer: "canvas",
      });
      chartRef.current = chart;
      chart.setOption(option, true);

      observer = new ResizeObserver(() => chart.resize());
      observer.observe(containerRef.current);
    }

    void mount();

    return () => {
      disposed = true;
      observer?.disconnect();
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, [option]);

  return <div ref={containerRef} className={className} role="img" />;
}
