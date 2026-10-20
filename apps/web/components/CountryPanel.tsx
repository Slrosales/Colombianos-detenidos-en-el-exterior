"use client";

import type { BreakdownRow, CountryRow } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";

type CountryPanelProps = {
  selected: string | null;
  country: CountryRow | undefined;
  groups: Record<"delito" | "edad" | "genero" | "situacion", BreakdownRow[]>;
  onClear: () => void;
};

const LABELS = {
  delito: "Delito",
  edad: "Edad",
  genero: "Género",
  situacion: "Situación jurídica",
};

export function CountryPanel({
  selected,
  country,
  groups,
  onClear,
}: CountryPanelProps) {
  if (!selected) {
    return (
      <section className="card country-panel">
        <div className="panel-empty">
          <div className="big">Explora un país</div>
          <p>
            Haz clic en el mapa o elige un filtro para ver su perfil: delito, edad,
            género y situación jurídica.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="card country-panel">
      <header className="card-header">
        <div>
          <div className="selected-name">{selected}</div>
          <div className="selected-total">
            {formatNumber(country?.cantidad)} detenidos activos ·{" "}
            {formatPercent(country?.participacion)} del total filtrado
          </div>
        </div>
        <button className="ghost-button" type="button" onClick={onClear}>
          Quitar
        </button>
      </header>
      <div className="card-body">
        <div className="mini-breakdowns">
          {(Object.keys(LABELS) as Array<keyof typeof LABELS>).map((key) => {
            const rows = groups[key] ?? [];
            const top = rows.slice(0, 4);
            const max = top[0]?.cantidad || 1;
            return (
              <div className="mini-row" key={key}>
                <div className="mini-head">
                  <span>{LABELS[key]}</span>
                </div>
                {top.length === 0 ? (
                  <p className="chart-note" style={{ margin: 0 }}>
                    Sin datos.
                  </p>
                ) : (
                  top.map((row) => (
                    <div key={row.valor} style={{ marginBottom: 7 }}>
                      <div className="mini-head">
                        <span>{row.valor}</span>
                        <span>{formatNumber(row.cantidad)}</span>
                      </div>
                      <div className="mini-bar">
                        <span
                          style={{
                            width: `${Math.max(4, (100 * row.cantidad) / max)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
