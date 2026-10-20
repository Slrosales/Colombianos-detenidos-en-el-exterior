"use client";

import type { Dimension, Filters, FiltersResponse } from "@/lib/api";
import { formatNumber } from "@/lib/format";

type FilterBarProps = {
  cutoff: string;
  cutoffs: string[];
  filters: Filters;
  options: FiltersResponse | null;
  onChange: (filters: Filters) => void;
  onCutoffChange: (cutoff: string) => void;
  onReset: () => void;
};

const DIMENSIONS: Array<{ key: Dimension; label: string }> = [
  { key: "delito", label: "Delito" },
  { key: "edad", label: "Grupo de edad" },
  { key: "genero", label: "Género" },
  { key: "situacion", label: "Situación jurídica" },
];

export function FilterBar({
  cutoff,
  cutoffs,
  filters,
  options,
  onChange,
  onCutoffChange,
  onReset,
}: FilterBarProps) {
  return (
    <section className="toolbar" aria-label="Filtros del tablero">
      <div className="field">
        <label htmlFor="cutoff">Corte de publicación</label>
        <select
          id="cutoff"
          value={cutoff}
          onChange={(event) => onCutoffChange(event.target.value)}
        >
          {[...cutoffs].reverse().map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>

      {DIMENSIONS.map(({ key, label }) => {
        const values = options?.values?.[key] ?? [];
        return (
          <div className="field grow" key={key}>
            <label htmlFor={`filter-${key}`}>{label}</label>
            <select
              id={`filter-${key}`}
              value={filters[key] ?? ""}
              onChange={(event) =>
                onChange({ ...filters, [key]: event.target.value || undefined })
              }
            >
              <option value="">Todos</option>
              {values.map((option) => (
                <option key={option.valor} value={option.valor}>
                  {option.valor} ({formatNumber(option.cantidad)})
                </option>
              ))}
            </select>
          </div>
        );
      })}

      <button className="ghost-button" type="button" onClick={onReset}>
        Limpiar
      </button>
    </section>
  );
}
