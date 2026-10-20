const numberFormatter = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return numberFormatter.format(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${decimalFormatter.format(value)} %`;
}

export function formatSignedPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${decimalFormatter.format(value)} %`;
}

export function formatCutoff(value: string | null | undefined): string {
  if (!value) return "—";
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function shortLabel(value: string, max = 26): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

export function titleCase(value: string): string {
  return value
    .toLocaleLowerCase("es-CO")
    .replace(/(^|\s|\/)(\p{L})/gu, (_, space: string, letter: string) => {
      return `${space}${letter.toLocaleUpperCase("es-CO")}`;
    });
}
