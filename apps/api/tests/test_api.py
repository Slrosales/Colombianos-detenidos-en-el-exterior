from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from apps.api.app.config import Settings
from apps.api.app.main import create_app


def _row(
    cutoff: date,
    country: str,
    iso3: str | None,
    amount: int,
    crime: str = "NARCOTRÁFICO",
    situation: str = "CONDENADO",
) -> dict:
    return {
        "fecha_publicacion": cutoff,
        "anio": cutoff.year,
        "pais": country,
        "pais_iso3": iso3,
        "consulado": f"C. {country}",
        "delito": crime,
        "edad": "ADULTO",
        "genero": "MASCULINO",
        "situacion": situation,
        "cantidad": amount,
        "latitud": 4.0,
        "longitud": -72.0,
    }


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    rows = [
        _row(date(2021, 5, 1), "ESPAÑA", "ESP", 10),
        _row(date(2021, 5, 1), "ECUADOR", "ECU", 30),
        _row(date(2026, 10, 9), "ESPAÑA", "ESP", 20),
        _row(date(2026, 10, 9), "ECUADOR", "ECU", 5),
        _row(date(2026, 10, 9), "DESCONOCIDO", None, 2),
        _row(date(2025, 11, 1), "ESPAÑA", "ESP", 15),
    ]
    frame = pd.DataFrame(rows)
    parquet = tmp_path / "detentions.parquet"
    frame.to_parquet(parquet, index=False)

    manifest = {
        "generated_at": "2026-10-20T00:00:00+00:00",
        "source_sha256": "abc",
        "corte_actual": "2026-10-09",
        "fecha_min": "2021-05-01",
        "fecha_max": "2026-10-09",
        "filas_totales": len(frame),
        "filas_corte_actual": 3,
        "total_corte_actual": 27,
        "duplicados_eliminados": 0,
        "pct_pais_desconocido_corte_actual": 7.4074,
        "paises_distintos_corte_actual": 2,
        "cutoffs": ["2021-05-01", "2025-11-01", "2026-10-09"],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    settings = Settings(
        parquet_path=parquet,
        manifest_path=manifest_path,
        model_dir=tmp_path,
        allowed_origins=("http://testserver",),
        environment="test",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["cutoff"] == "2026-10-09"


def test_meta(client: TestClient) -> None:
    response = client.get("/api/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["total_corte_actual"] == 27
    assert body["cutoffs"][-1] == "2026-10-09"


def test_countries_excludes_unknown_and_computes_share(client: TestClient) -> None:
    response = client.get("/api/countries?cutoff=2026-10-09")
    assert response.status_code == 200
    body = response.json()
    assert [row["pais"] for row in body] == ["ESPAÑA", "ECUADOR"]
    assert body[0]["cantidad"] == 20
    assert body[0]["participacion"] == pytest.approx(74.0741, rel=1e-3)


def test_unknown_cutoff_is_rejected(client: TestClient) -> None:
    response = client.get("/api/countries?cutoff=1999-01-01")
    assert response.status_code == 422


def test_breakdown_validation(client: TestClient) -> None:
    assert client.get("/api/breakdown/delito").status_code == 200
    assert client.get("/api/breakdown/invalid").status_code == 422


def test_filters_apply_to_breakdown(client: TestClient) -> None:
    response = client.get("/api/breakdown/situacion?pais=ESPAÑA")
    assert response.status_code == 200
    assert response.json() == [{"valor": "CONDENADO", "cantidad": 20}]


def test_trend_uses_last_cutoff_of_each_year(client: TestClient) -> None:
    response = client.get("/api/trend")
    assert response.status_code == 200
    body = response.json()
    assert [row["anio"] for row in body] == [2021, 2025, 2026]
    assert body[-1]["fecha"] == "2026-10-09"
    assert body[-1]["cantidad"] == 27


def test_compare(client: TestClient) -> None:
    response = client.get("/api/compare?base=2021-05-01&target=2026-10-09")
    assert response.status_code == 200
    body = {row["pais"]: row for row in response.json()}
    assert body["ESPAÑA"]["cambio"] == 10
    assert body["ESPAÑA"]["cambio_pct"] == 100.0
    assert body["ECUADOR"]["cambio_pct"] == pytest.approx(-83.33, rel=1e-2)


def test_filters_endpoint(client: TestClient) -> None:
    response = client.get("/api/filters?cutoff=2026-10-09")
    assert response.status_code == 200
    body = response.json()
    assert body["values"]["pais"][0]["cantidad"] == 20


def test_cache_headers_and_conditional_request(client: TestClient) -> None:
    url = "/api/countries?cutoff=2026-10-09"
    first = client.get(url)
    assert first.status_code == 200
    etag = first.headers["etag"]
    assert etag.startswith('"')
    assert "max-age=300" in first.headers["cache-control"]

    second = client.get(
        url,
        headers={
            "If-None-Match": etag,
            "Origin": "http://testserver",
        },
    )
    assert second.status_code == 304
    assert second.headers["etag"] == etag
    assert second.headers["access-control-allow-origin"] == "http://testserver"
    assert second.content == b""


def test_etag_depends_on_resource(client: TestClient) -> None:
    countries = client.get("/api/countries?cutoff=2026-10-09")
    breakdown = client.get("/api/breakdown/delito?cutoff=2026-10-09")
    assert countries.headers["etag"] != breakdown.headers["etag"]


def test_health_is_not_cached(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "etag" not in response.headers
