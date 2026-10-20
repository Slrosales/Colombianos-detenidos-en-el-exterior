"""Exploratory query endpoints.

All endpoints read from the same cutoff. Country recovery, stock semantics and label
normalization happened in the pipeline; the API only aggregates.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..config import Settings
from ..db import Database
from ..schemas import (
    BreakdownRow,
    CompareRow,
    CountryRow,
    FiltersResponse,
    MetaResponse,
    TrendPoint,
)

router = APIRouter(prefix="/api", tags=["explore"])

FILTER_COLUMNS = {
    "pais": "pais",
    "delito": "delito",
    "edad": "edad",
    "genero": "genero",
    "situacion": "situacion",
}
DIMENSION_COLUMNS = {**FILTER_COLUMNS, "consulado": "consulado"}
MAX_LIMIT = 500


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


Db = Annotated[Database, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def _cutoffs(db: Database) -> list[str]:
    rows = db.query(
        "SELECT DISTINCT CAST(fecha_publicacion AS VARCHAR) AS fecha "
        "FROM detentions ORDER BY fecha"
    )
    return [row["fecha"] for row in rows]


def _resolve_cutoff(db: Database, cutoff: str | None) -> tuple[str, list[str]]:
    cutoffs = _cutoffs(db)
    if not cutoffs:
        raise HTTPException(status_code=503, detail="The warehouse is empty")
    resolved = cutoff or cutoffs[-1]
    if resolved not in cutoffs:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown cutoff '{resolved}'. Available: {', '.join(cutoffs[-6:])}",
        )
    return resolved, cutoffs


def _where(cutoff: str, filters: dict[str, str | None]) -> tuple[str, list[str]]:
    clauses = ["fecha_publicacion = CAST(? AS DATE)"]
    params: list[str] = [cutoff]
    for key, value in filters.items():
        if value:
            clauses.append(f"{FILTER_COLUMNS[key]} = ?")
            params.append(value)
    return " AND ".join(clauses), params


def _filter_kwargs(
    pais: str | None,
    delito: str | None,
    edad: str | None,
    genero: str | None,
    situacion: str | None,
) -> dict[str, str | None]:
    return {
        "pais": pais,
        "delito": delito,
        "edad": edad,
        "genero": genero,
        "situacion": situacion,
    }


@router.get("/health")
def health(db: Db) -> dict:
    latest = _cutoffs(db)[-1]
    return {"status": "ok", "cutoff": latest}


@router.get("/cutoffs")
def cutoffs(db: Db) -> dict:
    values = _cutoffs(db)
    return {"cutoffs": values, "latest": values[-1]}


@router.get("/meta", response_model=MetaResponse)
def meta(db: Db, config: Config) -> dict:
    cutoffs_list = _cutoffs(db)
    latest = cutoffs_list[-1]
    if config.manifest_path.exists():
        manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
        manifest["cutoffs"] = cutoffs_list
        manifest["corte_actual"] = latest
        return manifest

    row = db.query_one(
        "SELECT COUNT(*) AS filas_corte_actual, COALESCE(SUM(cantidad), 0) AS total "
        "FROM detentions WHERE fecha_publicacion = CAST(? AS DATE)",
        [latest],
    ) or {}
    total = int(row.get("total") or 0)
    return {
        "corte_actual": latest,
        "fecha_min": cutoffs_list[0],
        "fecha_max": latest,
        "filas_totales": int(
            db.query_one("SELECT COUNT(*) AS n FROM detentions")["n"]
        ),
        "filas_corte_actual": int(row.get("filas_corte_actual") or 0),
        "total_corte_actual": total,
        "duplicados_eliminados": 0,
        "pct_pais_desconocido_corte_actual": None,
        "paises_distintos_corte_actual": int(
            db.query_one(
                "SELECT COUNT(DISTINCT pais) AS n FROM detentions "
                "WHERE fecha_publicacion = CAST(? AS DATE) AND pais <> 'DESCONOCIDO'",
                [latest],
            )["n"]
        ),
        "cutoffs": cutoffs_list,
    }


@router.get("/countries", response_model=list[CountryRow])
def countries(
    db: Db,
    cutoff: str | None = None,
    pais: str | None = None,
    delito: str | None = None,
    edad: str | None = None,
    genero: str | None = None,
    situacion: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 250,
) -> list[dict]:
    resolved, _ = _resolve_cutoff(db, cutoff)
    filters = _filter_kwargs(pais, delito, edad, genero, situacion)
    where, params = _where(resolved, filters)

    total_row = db.query_one(
        f"SELECT COALESCE(SUM(cantidad), 0) AS total FROM detentions WHERE {where}",
        params,
    )
    total = float((total_row or {}).get("total") or 0)

    rows = db.query(
        f"""
        SELECT
            pais,
            pais_iso3,
            CAST(SUM(cantidad) AS BIGINT) AS cantidad,
            AVG(latitud) AS latitud,
            AVG(longitud) AS longitud
        FROM detentions
        WHERE {where}
          AND pais <> 'DESCONOCIDO'
          AND pais_iso3 IS NOT NULL
        GROUP BY pais, pais_iso3
        ORDER BY cantidad DESC, pais
        LIMIT ?
        """,
        [*params, limit],
    )
    for row in rows:
        row["participacion"] = (
            round(100 * row["cantidad"] / total, 4) if total else 0.0
        )
    return rows


@router.get("/breakdown/{dimension}", response_model=list[BreakdownRow])
def breakdown(
    db: Db,
    dimension: str,
    cutoff: str | None = None,
    pais: str | None = None,
    delito: str | None = None,
    edad: str | None = None,
    genero: str | None = None,
    situacion: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 100,
) -> list[dict]:
    column = DIMENSION_COLUMNS.get(dimension)
    if column is None:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid dimension. Use one of: {', '.join(DIMENSION_COLUMNS)}",
        )
    resolved, _ = _resolve_cutoff(db, cutoff)
    filters = _filter_kwargs(pais, delito, edad, genero, situacion)
    where, params = _where(resolved, filters)

    return db.query(
        f"""
        SELECT COALESCE({column}, 'DESCONOCIDO') AS valor,
               CAST(SUM(cantidad) AS BIGINT) AS cantidad
        FROM detentions
        WHERE {where}
        GROUP BY valor
        ORDER BY cantidad DESC, valor
        LIMIT ?
        """,
        [*params, limit],
    )


@router.get("/trend", response_model=list[TrendPoint])
def trend(
    db: Db,
    pais: str | None = None,
    delito: str | None = None,
    edad: str | None = None,
    genero: str | None = None,
    situacion: str | None = None,
) -> list[dict]:
    filters = _filter_kwargs(pais, delito, edad, genero, situacion)
    clauses = ["fecha_publicacion IS NOT NULL"]
    params: list[str] = []
    for key, value in filters.items():
        if value:
            clauses.append(f"{FILTER_COLUMNS[key]} = ?")
            params.append(value)
    where = " AND ".join(clauses)

    return db.query(
        f"""
        WITH ranked AS (
            SELECT
                anio,
                fecha_publicacion,
                CAST(SUM(cantidad) AS BIGINT) AS cantidad,
                ROW_NUMBER() OVER (
                    PARTITION BY anio ORDER BY fecha_publicacion DESC
                ) AS rn
            FROM detentions
            WHERE {where}
            GROUP BY anio, fecha_publicacion
        )
        SELECT
            CAST(anio AS INTEGER) AS anio,
            CAST(fecha_publicacion AS VARCHAR) AS fecha,
            cantidad
        FROM ranked
        WHERE rn = 1
        ORDER BY anio
        """,
        params,
    )


@router.get("/compare", response_model=list[CompareRow])
def compare(
    db: Db,
    base: str = "2021-05-01",
    target: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 15,
) -> list[dict]:
    resolved_target, cutoffs_list = _resolve_cutoff(db, target)
    if base not in cutoffs_list:
        raise HTTPException(status_code=422, detail=f"Unknown base cutoff '{base}'")

    rows = db.query(
        """
        SELECT
            pais,
            pais_iso3,
            CAST(SUM(CASE WHEN fecha_publicacion = CAST(? AS DATE)
                          THEN cantidad ELSE 0 END) AS BIGINT) AS base,
            CAST(SUM(CASE WHEN fecha_publicacion = CAST(? AS DATE)
                          THEN cantidad ELSE 0 END) AS BIGINT) AS target
        FROM detentions
        WHERE fecha_publicacion IN (CAST(? AS DATE), CAST(? AS DATE))
          AND pais <> 'DESCONOCIDO'
        GROUP BY pais, pais_iso3
        HAVING base > 0 OR target > 0
        ORDER BY target DESC, pais
        LIMIT ?
        """,
        [base, resolved_target, base, resolved_target, limit],
    )
    for row in rows:
        row["cambio"] = int(row["target"]) - int(row["base"])
        row["cambio_pct"] = (
            round(100 * row["cambio"] / row["base"], 2) if row["base"] else None
        )
    return rows


@router.get("/filters", response_model=FiltersResponse)
def filters(db: Db, cutoff: str | None = None) -> dict:
    resolved, _ = _resolve_cutoff(db, cutoff)
    values: dict[str, list[dict]] = {}
    for dimension, column in DIMENSION_COLUMNS.items():
        values[dimension] = db.query(
            f"""
            SELECT COALESCE({column}, 'DESCONOCIDO') AS valor,
                   CAST(SUM(cantidad) AS BIGINT) AS cantidad
            FROM detentions
            WHERE fecha_publicacion = CAST(? AS DATE)
            GROUP BY valor
            ORDER BY cantidad DESC, valor
            """,
            [resolved],
        )
    return {"cutoff": resolved, "values": values}
