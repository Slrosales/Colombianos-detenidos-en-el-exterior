"""Pydantic response models for the public API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MetaResponse(BaseModel):
    corte_actual: str
    fecha_min: str
    fecha_max: str
    filas_totales: int
    filas_corte_actual: int
    total_corte_actual: int
    duplicados_eliminados: int
    pct_pais_desconocido_corte_actual: float | None = None
    paises_distintos_corte_actual: int
    cutoffs: list[str]
    source_sha256: str | None = None
    generated_at: str | None = None


class CountryRow(BaseModel):
    pais: str
    pais_iso3: str | None = None
    cantidad: int
    participacion: float
    latitud: float | None = None
    longitud: float | None = None


class BreakdownRow(BaseModel):
    valor: str
    cantidad: int


class TrendPoint(BaseModel):
    anio: int
    fecha: str
    cantidad: int


class CompareRow(BaseModel):
    pais: str
    pais_iso3: str | None = None
    base: int
    target: int
    cambio: int
    cambio_pct: float | None = None


class FiltersResponse(BaseModel):
    cutoff: str
    values: dict[str, list[BreakdownRow]]


class ModelMetricsResponse(BaseModel):
    train_date: str | None = None
    test_date: str | None = None
    target_order: list[str] = Field(default_factory=list)
    models: list[dict]
    advertencia: str
