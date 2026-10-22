"""Export precomputed JSON for the free static demo.

The live site queries FastAPI/DuckDB. The demo mode uses these JSON files instead, so it
can be deployed to Vercel (or any static host) with no backend.

Demo scope:
  - last cutoff of each year, plus 2021-05-01 for the comparison;
  - country map, overall breakdowns, country profiles and 2021 -> cutoff comparison;
  - cross-filters are intentionally not precomputed.

Usage:
    python pipeline/export_web_data.py
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = ROOT / "data" / "processed" / "detentions.parquet"
DEFAULT_MANIFEST = ROOT / "data" / "processed" / "manifest.json"
DEFAULT_OUTPUT = ROOT / "apps" / "web" / "public" / "data" / "demo"
METRICS_PATH = ROOT / "outputs" / "tables" / "metricas_modelos.csv"
BASE_CUTOFF = "2021-05-01"
TARGET_ORDER = ["EN INVESTIGACIÓN", "EN JUICIO", "CONDENADO"]

DIMENSIONS = {
    "delito": "delito",
    "edad": "edad",
    "genero": "genero",
    "situacion": "situacion",
    "consulado": "consulado",
}
PROFILE_LIMITS = {
    "delito": 6,
    "edad": 8,
    "genero": 6,
    "situacion": 8,
    "consulado": 6,
}


def _quote(path: Path) -> str:
    return str(path).replace("'", "''")


def _dimension_rows(con: duckdb.DuckDBPyConnection, relation: str, column: str, cutoff: str):
    return con.execute(
        f"""
        SELECT COALESCE({column}, 'DESCONOCIDO') AS valor,
               CAST(SUM(cantidad) AS BIGINT) AS cantidad
        FROM {relation}
        WHERE fecha_publicacion = CAST(? AS DATE)
        GROUP BY valor
        ORDER BY cantidad DESC, valor
        """,
        [cutoff],
    ).fetchall()


def _countries(
    con: duckdb.DuckDBPyConnection, relation: str, cutoff: str, total: int
):
    rows = con.execute(
        f"""
        SELECT pais, pais_iso3, CAST(SUM(cantidad) AS BIGINT) AS cantidad,
               AVG(latitud) AS latitud, AVG(longitud) AS longitud
        FROM {relation}
        WHERE fecha_publicacion = CAST(? AS DATE)
          AND pais <> 'DESCONOCIDO'
          AND pais_iso3 IS NOT NULL
        GROUP BY pais, pais_iso3
        ORDER BY cantidad DESC, pais
        """,
        [cutoff],
    ).fetchall()
    return [
        {
            "pais": pais,
            "pais_iso3": iso,
            "cantidad": int(cantidad),
            "participacion": round(100 * cantidad / total, 4) if total else 0.0,
            "latitud": lat,
            "longitud": lon,
        }
        for pais, iso, cantidad, lat, lon in rows
    ]


def _profiles(
    con: duckdb.DuckDBPyConnection,
    relation: str,
    cutoff: str,
    country_names: list[str],
):
    profiles: dict[str, dict[str, list[dict[str, Any]]]] = {
        name: {dimension: [] for dimension in DIMENSIONS} for name in country_names
    }
    for dimension, column in DIMENSIONS.items():
        limit = PROFILE_LIMITS[dimension]
        rows = con.execute(
            f"""
            WITH grouped AS (
                SELECT pais, COALESCE({column}, 'DESCONOCIDO') AS valor,
                       CAST(SUM(cantidad) AS BIGINT) AS cantidad
                FROM {relation}
                WHERE fecha_publicacion = CAST(? AS DATE)
                  AND pais <> 'DESCONOCIDO'
                GROUP BY pais, valor
            ), ranked AS (
                SELECT pais, valor, cantidad,
                       ROW_NUMBER() OVER (
                           PARTITION BY pais ORDER BY cantidad DESC, valor
                       ) AS rn
                FROM grouped
            )
            SELECT pais, valor, cantidad
            FROM ranked
            WHERE rn <= ?
            """,
            [cutoff, limit],
        ).fetchall()
        for pais, valor, cantidad in rows:
            profiles.setdefault(
                pais, {name: [] for name in DIMENSIONS}
            )[dimension].append({"valor": valor, "cantidad": int(cantidad)})
    return profiles


def _compare(
    countries_by_cutoff: dict[str, list[dict[str, Any]]], target: str
) -> list[dict[str, Any]]:
    base_rows = countries_by_cutoff.get(BASE_CUTOFF)
    target_rows = countries_by_cutoff.get(target)
    if not base_rows or not target_rows:
        return []
    base = {row["pais"]: row for row in base_rows}
    result = []
    for row in target_rows:
        previous = base.get(row["pais"])
        base_count = int(previous["cantidad"]) if previous else 0
        target_count = int(row["cantidad"])
        change = target_count - base_count
        result.append(
            {
                "pais": row["pais"],
                "pais_iso3": row["pais_iso3"],
                "base": base_count,
                "target": target_count,
                "cambio": change,
                "cambio_pct": round(100 * change / base_count, 2)
                if base_count
                else None,
            }
        )
    return result


def _model_metrics() -> dict[str, Any] | None:
    if not METRICS_PATH.exists():
        return None
    with open(METRICS_PATH, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    models = []
    for row in rows:
        clean: dict[str, Any] = {}
        for key, value in row.items():
            try:
                clean[key] = round(float(value), 4)
            except (TypeError, ValueError):
                clean[key] = value
        models.append(clean)
    first = models[0] if models else {}
    return {
        "train_date": first.get("fecha_train"),
        "test_date": first.get("fecha_test"),
        "target_order": TARGET_ORDER,
        "models": models,
        "advertencia": (
            "Resultados de validaci\u00f3n temporal con QWK \u2248 0,39. El modelo describe "
            "asociaciones y no permite evaluar el riesgo de una persona."
        ),
    }


def export_demo(
    parquet_path: Path = DEFAULT_PARQUET,
    manifest_path: Path = DEFAULT_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    if not parquet_path.exists():
        raise FileNotFoundError(f"Warehouse not found: {parquet_path}. Run `make warehouse`.")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}. Run `make warehouse`.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    relation = f"read_parquet('{_quote(parquet_path)}')"
    all_cutoffs = [
        item[0]
        for item in con.execute(
            f"""
            SELECT DISTINCT CAST(fecha_publicacion AS VARCHAR) AS fecha
            FROM {relation}
            ORDER BY fecha
            """
        ).fetchall()
    ]

    annual: dict[str, str] = {}
    for cutoff in all_cutoffs:
        annual[cutoff[:4]] = cutoff
    annual_cutoffs = sorted(annual.values())
    demo_cutoffs = annual_cutoffs + (
        [BASE_CUTOFF] if BASE_CUTOFF not in annual_cutoffs else []
    )
    demo_cutoffs = sorted(set(demo_cutoffs))

    cutoffs_data: dict[str, dict[str, Any]] = {}
    countries_by_cutoff: dict[str, list[dict[str, Any]]] = {}
    totals_by_cutoff: dict[str, int] = {}

    for cutoff in demo_cutoffs:
        total = con.execute(
            f"""
            SELECT COALESCE(SUM(cantidad), 0)
            FROM {relation}
            WHERE fecha_publicacion = CAST(? AS DATE)
            """,
            [cutoff],
        ).fetchone()[0]
        total = int(total)
        countries = _countries(con, relation, cutoff, total)
        countries_by_cutoff[cutoff] = countries
        totals_by_cutoff[cutoff] = total

        filters = {
            dimension: [
                {"valor": valor, "cantidad": int(cantidad)}
                for valor, cantidad in _dimension_rows(con, relation, column, cutoff)
            ]
            for dimension, column in DIMENSIONS.items()
        }
        filters["pais"] = [
            {"valor": row["pais"], "cantidad": row["cantidad"]}
            for row in countries
        ]

        breakdowns = {
            dimension: filters[dimension]
            for dimension in DIMENSIONS
        }
        profiles = _profiles(
            con, relation, cutoff, [row["pais"] for row in countries]
        )
        cutoffs_data[cutoff] = {
            "cutoff": cutoff,
            "total": total,
            "countries": countries,
            "filters": filters,
            "breakdowns": breakdowns,
            "profiles": profiles,
        }

    for cutoff in demo_cutoffs:
        cutoffs_data[cutoff]["compare"] = _compare(countries_by_cutoff, cutoff)
        (output_dir / f"{cutoff}.json").write_text(
            json.dumps(cutoffs_data[cutoff], ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    trend_total = [
        {
            "anio": int(cutoff[:4]),
            "fecha": cutoff,
            "cantidad": totals_by_cutoff[cutoff],
        }
        for cutoff in annual_cutoffs
    ]
    trend_by_country: dict[str, list[dict[str, Any]]] = {}
    for cutoff in annual_cutoffs:
        for row in countries_by_cutoff[cutoff]:
            trend_by_country.setdefault(row["pais"], []).append(
                {
                    "anio": int(cutoff[:4]),
                    "fecha": cutoff,
                    "cantidad": row["cantidad"],
                }
            )

    meta = {
        **manifest,
        "demo": True,
        "modo": "static-demo",
        "cutoffs": demo_cutoffs,
        "corte_actual": demo_cutoffs[-1],
        "total_corte_actual": totals_by_cutoff[demo_cutoffs[-1]],
        "demo_nota": (
            "Demo est\u00e1tica: cortes anuales y perfiles por pa\u00eds. Los filtros "
            "combinados requieren la API en vivo."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "trend.json").write_text(
        json.dumps(
            {"total": trend_total, "by_country": trend_by_country},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    metrics = _model_metrics()
    if metrics:
        (output_dir / "model-metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    total_bytes = sum(path.stat().st_size for path in output_dir.glob("*.json"))
    return {
        "output": str(output_dir.relative_to(ROOT))
        if output_dir.is_relative_to(ROOT)
        else str(output_dir),
        "cutoffs": len(demo_cutoffs),
        "annual_cutoffs": annual_cutoffs,
        "files": len(list(output_dir.glob("*.json"))),
        "size_mb": round(total_bytes / 1024 / 1024, 2),
        "latest": meta["corte_actual"],
        "total_corte_actual": meta["total_corte_actual"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", default=str(DEFAULT_PARQUET))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    summary = export_demo(
        Path(args.parquet), Path(args.manifest), Path(args.output)
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
