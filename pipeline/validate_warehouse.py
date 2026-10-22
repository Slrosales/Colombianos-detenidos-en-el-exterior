"""Validate the generated warehouse and manifest before deployment.

Usage:
    python pipeline/validate_warehouse.py
    python pipeline/validate_warehouse.py --allow-stale-config
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = ROOT / "data" / "processed" / "detentions.parquet"
DEFAULT_MANIFEST = ROOT / "data" / "processed" / "manifest.json"

REQUIRED_COLUMNS = {
    "fecha_publicacion",
    "anio",
    "pais",
    "pais_iso3",
    "consulado",
    "delito",
    "edad",
    "genero",
    "situacion",
    "cantidad",
    "latitud",
    "longitud",
}


def _quote(path: Path) -> str:
    return str(path).replace("'", "''")


def validate_warehouse(
    parquet_path: Path = DEFAULT_PARQUET,
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    allow_stale_config: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {}

    if not parquet_path.exists():
        return [f"Warehouse not found: {parquet_path}"], summary
    if not manifest_path.exists():
        return [f"Manifest not found: {manifest_path}"], summary

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Manifest is not valid JSON: {exc}"], summary

    con = duckdb.connect()
    relation = f"read_parquet('{_quote(parquet_path)}')"

    columns = [
        row[0]
        for row in con.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    ]
    missing = sorted(REQUIRED_COLUMNS - set(columns))
    if missing:
        return [f"Missing warehouse columns: {', '.join(missing)}"], summary

    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS filas,
            CAST(MIN(fecha_publicacion) AS VARCHAR) AS fecha_min,
            CAST(MAX(fecha_publicacion) AS VARCHAR) AS fecha_max,
            COALESCE(SUM(cantidad), 0) AS total,
            COUNT(*) FILTER (WHERE cantidad < 0) AS negativos,
            COUNT(*) FILTER (WHERE fecha_publicacion IS NULL) AS nulos_fecha,
            COUNT(*) FILTER (WHERE pais IS NULL OR pais = '') AS nulos_pais,
            COUNT(*) FILTER (
                WHERE pais <> 'DESCONOCIDO'
                  AND (pais_iso3 IS NULL OR pais_iso3 = '')
            ) AS faltan_iso3
        FROM {relation}
        """
    ).fetchone()
    if row is None:
        return ["DuckDB returned no summary row"], summary

    (
        filas,
        fecha_min,
        fecha_max,
        total,
        negativos,
        nulos_fecha,
        nulos_pais,
        faltan_iso3,
    ) = row

    cutoffs = [
        item[0]
        for item in con.execute(
            f"""
            SELECT DISTINCT CAST(fecha_publicacion AS VARCHAR) AS fecha
            FROM {relation}
            ORDER BY fecha
            """
        ).fetchall()
    ]

    latest_total = con.execute(
        f"""
        SELECT COALESCE(SUM(cantidad), 0)
        FROM {relation}
        WHERE fecha_publicacion = CAST(? AS DATE)
        """,
        [fecha_max],
    ).fetchone()[0]

    summary = {
        "cutoff": fecha_max,
        "fecha_min": fecha_min,
        "filas_totales": int(filas),
        "total_corte_actual": int(latest_total),
        "cutoffs": len(cutoffs),
        "faltan_iso3": int(faltan_iso3),
        "manifest": str(manifest_path.relative_to(ROOT))
        if manifest_path.is_relative_to(ROOT)
        else str(manifest_path),
    }

    if int(filas) == 0:
        errors.append("Warehouse has no rows")
    if int(negativos) > 0:
        errors.append(f"Negative CANTIDAD rows: {negativos}")
    if int(nulos_fecha) > 0:
        errors.append(f"Rows with null publication date: {nulos_fecha}")
    if int(nulos_pais) > 0:
        errors.append(f"Rows with null/empty country: {nulos_pais}")
    if int(faltan_iso3) > 0:
        errors.append(
            f"Rows without ISO3 code (excluding DESCONOCIDO): {faltan_iso3}"
        )

    if manifest.get("filas_totales") != int(filas):
        errors.append(
            "Manifest filas_totales does not match warehouse "
            f"({manifest.get('filas_totales')} != {int(filas)})"
        )
    if manifest.get("fecha_max") != fecha_max:
        errors.append(
            "Manifest fecha_max does not match warehouse "
            f"({manifest.get('fecha_max')} != {fecha_max})"
        )
    if manifest.get("corte_actual") != fecha_max:
        errors.append(
            "Manifest corte_actual does not match warehouse "
            f"({manifest.get('corte_actual')} != {fecha_max})"
        )
    if manifest.get("total_corte_actual") != int(latest_total):
        errors.append(
            "Manifest total_corte_actual does not match warehouse "
            f"({manifest.get('total_corte_actual')} != {int(latest_total)})"
        )
    if manifest.get("cutoffs") != cutoffs:
        errors.append(
            "Manifest cutoffs do not match warehouse "
            f"({len(manifest.get('cutoffs') or [])} != {len(cutoffs)})"
        )

    configured = manifest.get("report_cutoff_config")
    if configured and configured != fecha_max and not allow_stale_config:
        errors.append(
            "config/params.json report_cutoff is stale "
            f"({configured} != {fecha_max}). Update it before deploying."
        )

    return errors, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", default=str(DEFAULT_PARQUET))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument(
        "--allow-stale-config",
        action="store_true",
        help="Do not fail when config/params.json report_cutoff is older than the data.",
    )
    args = parser.parse_args()

    errors, summary = validate_warehouse(
        Path(args.parquet),
        Path(args.manifest),
        allow_stale_config=args.allow_stale_config,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if errors:
        print("\nValidation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print("\nWarehouse is valid.")


if __name__ == "__main__":
    main()
