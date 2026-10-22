// Shared ECharts theme and constants.
//
// Every panel builds its own series but shares the same palette, tooltip and axis
// styles here. The `Chart` component registers this as an ECharts theme so panels do
// not repeat background, text and axis colors.

export const CHART_THEME_NAME = "detenidos";

export const PALETTE = {
  cyan: "#5ec8d8",
  cyanBright: "#8be3ee",
  orange: "#d98b5f",
  purple: "#8a7fe0",
  green: "#5fb88a",
  gold: "#c9a35e",
  positive: "#6bcf9b",
  negative: "#e17268",
} as const;

export const TOOLTIP = {
  backgroundColor: "#0b1422",
  borderColor: "#2b4364",
  borderWidth: 1,
  padding: 10,
  textStyle: { color: "#eef4fc", fontSize: 11 },
} as const;

export const chartTheme = {
  color: [
    PALETTE.cyan,
    PALETTE.orange,
    PALETTE.purple,
    PALETTE.green,
    PALETTE.gold,
    PALETTE.negative,
    PALETTE.positive,
  ],
  backgroundColor: "transparent",
  textStyle: {
    color: "#9eb0c7",
    fontFamily:
      '"Inter", "Segoe UI", system-ui, -apple-system, sans-serif',
  },
  tooltip: TOOLTIP,
  categoryAxis: {
    axisLine: { lineStyle: { color: "#263850" } },
    axisTick: { show: false },
    axisLabel: { color: "#6e819b", fontSize: 10 },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: "#6e819b", fontSize: 9 },
    splitLine: { lineStyle: { color: "rgba(120,150,190,.10)" } },
  },
};
