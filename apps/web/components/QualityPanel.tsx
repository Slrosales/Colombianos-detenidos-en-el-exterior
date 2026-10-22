"use client";

import type { FiltersResponse, Meta } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

type QualityPanelProps = {
  meta: Meta | null;
  options: FiltersResponse | null;
};

function share(part: number, total: number): number | null {
  if (!total) return null;
  return (100 * part) / total;
}

export function QualityPanel({ meta, options }: QualityPanelProps) {
  const total = meta?.total_corte_actual ?? 0;
  const edad = options?.values.edad ?? [];
  const delito = options?.values.delito ?? [];

  const edadDesconocida =
    edad.find((row) => row.valor === "DESCONOCIDO")?.cantidad ?? 0;
  const delitoNoReportado = delito
    .filter((row) => row.valor === "OTRO" || row.valor === "NO REPORTA")
    .reduce((sum, row) => sum + row.cantidad, 0);

  const items = [
    {
      label: "País sin identificar",
      value: formatPercent(meta?.pct_pais_desconocido_corte_actual),
      note: "Recuperado desde el consulado",
    },
    {
      label: "Edad desconocida",
      value: formatPercent(share(edadDesconocida, total)),
      note: "Se conserva como categoría",
    },
    {
      label: "Delito OTRO / NO REPORTA",
      value: formatPercent(share(delitoNoReportado, total)),
      note: "Agregado, no es un delito específico",
    },
    {
      label: "Duplicados eliminados",
      value: formatNumber(meta?.duplicados_eliminados),
      note: `${formatNumber(meta?.filas_totales)} filas analizadas`,
    },
  ];

  return (
    <section className="card quality-panel">
      <header className="card-header">
        <div>
          <h3>Calidad de los datos</h3>
          <p>Corte {meta?.corte_actual ?? "—"}. El subregistro se muestra, no se oculta.</p>
        </div>
      </header>
      <div className="card-body">
        <ul className="quality-list">
          {items.map((item) => (
            <li className="quality-row" key={item.label}>
              <div className="quality-meta">
                <span className="quality-label">{item.label}</span>
                <span className="quality-value">{item.value}</span>
              </div>
              <p className="quality-note">{item.note}</p>
            </li>
          ))}
        </ul>
        <p className="chart-note" style={{ margin: "12px 0 0" }}>
          Desde finales de 2022 la fuente deja de reportar el país en la mayoría de
          registros; se imputa desde <code>CONSULADO</code>. El porcentaje de país sin
          identificar corresponde al corte completo.
        </p>
      </div>
    </section>
  );
}
