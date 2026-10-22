from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from pipeline.export_web_data import export_demo


def _row(cutoff: date, country: str, iso3: str, amount: int) -> dict:
    return {
        "fecha_publicacion": cutoff,
        "anio": cutoff.year,
        "pais": country,
        "pais_iso3": iso3,
        "consulado": f"C. {country}",
        "delito": "NARCOTRÁFICO",
        "edad": "ADULTO",
        "genero": "MASCULINO",
        "situacion": "CONDENADO",
        "cantidad": amount,
        "latitud": 4.0,
        "longitud": -72.0,
    }


def test_export_demo_creates_cutoffs_trend_and_profiles(tmp_path: Path):
    rows = [
        _row(date(2021, 5, 1), "ESPAÑA", "ESP", 10),
        _row(date(2021, 9, 1), "ESPAÑA", "ESP", 12),
        _row(date(2026, 10, 9), "ESPAÑA", "ESP", 20),
        _row(date(2026, 10, 9), "MÉXICO", "MEX", 5),
    ]
    parquet = tmp_path / "detentions.parquet"
    pd.DataFrame(rows).to_parquet(parquet, index=False)

    manifest = {
        "source_sha256": "abc",
        "corte_actual": "2026-10-09",
        "fecha_min": "2021-05-01",
        "fecha_max": "2026-10-09",
        "filas_totales": 4,
        "filas_corte_actual": 2,
        "total_corte_actual": 25,
        "duplicados_eliminados": 0,
        "pct_pais_desconocido_corte_actual": 0.0,
        "paises_distintos_corte_actual": 2,
        "cutoffs": ["2021-05-01", "2021-09-01", "2026-10-09"],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    output = tmp_path / "demo"
    summary = export_demo(parquet, manifest_path, output)

    assert summary["cutoffs"] == 3
    meta = json.loads((output / "meta.json").read_text(encoding="utf-8"))
    assert meta["demo"] is True
    assert meta["cutoffs"] == ["2021-05-01", "2021-09-01", "2026-10-09"]

    latest = json.loads((output / "2026-10-09.json").read_text(encoding="utf-8"))
    assert [row["pais"] for row in latest["countries"]] == ["ESPAÑA", "MÉXICO"]
    assert latest["profiles"]["ESPAÑA"]["delito"][0]["valor"] == "NARCOTRÁFICO"
    assert latest["compare"][0]["base"] == 10

    trend = json.loads((output / "trend.json").read_text(encoding="utf-8"))
    assert [point["anio"] for point in trend["total"]] == [2021, 2026]
