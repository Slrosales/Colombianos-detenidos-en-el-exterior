from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from pipeline.validate_warehouse import validate_warehouse


def _write_fixture(tmp_path: Path, **manifest_overrides):
    rows = [
        {
            "fecha_publicacion": date(2021, 5, 1),
            "anio": 2021,
            "pais": "ESPAÑA",
            "pais_iso3": "ESP",
            "consulado": "C. MADRID",
            "delito": "NARCOTRÁFICO",
            "edad": "ADULTO",
            "genero": "MASCULINO",
            "situacion": "CONDENADO",
            "cantidad": 10,
            "latitud": 40.4,
            "longitud": -3.7,
        },
        {
            "fecha_publicacion": date(2026, 10, 9),
            "anio": 2026,
            "pais": "ESPAÑA",
            "pais_iso3": "ESP",
            "consulado": "C. MADRID",
            "delito": "NARCOTRÁFICO",
            "edad": "ADULTO",
            "genero": "MASCULINO",
            "situacion": "CONDENADO",
            "cantidad": 20,
            "latitud": 40.4,
            "longitud": -3.7,
        },
        {
            "fecha_publicacion": date(2026, 10, 9),
            "anio": 2026,
            "pais": "DESCONOCIDO",
            "pais_iso3": None,
            "consulado": "C. DESCONOCIDO",
            "delito": "OTRO",
            "edad": "DESCONOCIDO",
            "genero": "DESCONOCIDO",
            "situacion": "NO REPORTA",
            "cantidad": 2,
            "latitud": None,
            "longitud": None,
        },
    ]
    parquet = tmp_path / "detentions.parquet"
    pd.DataFrame(rows).to_parquet(parquet, index=False)

    manifest = {
        "filas_totales": 3,
        "fecha_min": "2021-05-01",
        "fecha_max": "2026-10-09",
        "corte_actual": "2026-10-09",
        "total_corte_actual": 22,
        "cutoffs": ["2021-05-01", "2026-10-09"],
        "report_cutoff_config": "2026-10-09",
    }
    manifest.update(manifest_overrides)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return parquet, manifest_path


def test_valid_warehouse(tmp_path: Path):
    parquet, manifest = _write_fixture(tmp_path)
    errors, summary = validate_warehouse(parquet, manifest)
    assert errors == []
    assert summary["cutoff"] == "2026-10-09"
    assert summary["total_corte_actual"] == 22


def test_manifest_total_mismatch(tmp_path: Path):
    parquet, manifest = _write_fixture(tmp_path, total_corte_actual=999)
    errors, _ = validate_warehouse(parquet, manifest)
    assert any("total_corte_actual" in error for error in errors)


def test_missing_iso3_is_reported(tmp_path: Path):
    parquet, manifest = _write_fixture(tmp_path)
    frame = pd.read_parquet(parquet)
    frame.loc[1, "pais_iso3"] = None
    frame.to_parquet(parquet, index=False)

    errors, _ = validate_warehouse(parquet, manifest)
    assert any("ISO3" in error for error in errors)


def test_stale_config_can_be_allowed(tmp_path: Path):
    parquet, manifest = _write_fixture(tmp_path, report_cutoff_config="2025-11-01")

    errors, _ = validate_warehouse(parquet, manifest)
    assert any("stale" in error for error in errors)

    errors, _ = validate_warehouse(parquet, manifest, allow_stale_config=True)
    assert errors == []
