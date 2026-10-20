"""Research model metadata.

The model is intentionally not a public predictor in v1. This module exposes the 2026
temporal-validation results and leaves a documented extension point for the lab in phase 4.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..config import ROOT
from ..schemas import ModelMetricsResponse

router = APIRouter(prefix="/api/model", tags=["model"])

METRICS_PATH = ROOT / "outputs" / "tables" / "metricas_modelos.csv"
TARGET_ORDER = ["EN INVESTIGACIÓN", "EN JUICIO", "CONDENADO"]


@router.get("/metrics", response_model=ModelMetricsResponse)
def metrics() -> dict:
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Model metrics not found. Run `make analysis` first.",
        )

    frame = pd.read_csv(METRICS_PATH)
    models = []
    for row in frame.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            elif isinstance(value, float):
                clean[key] = round(value, 4)
            else:
                clean[key] = value
        models.append(clean)

    first = models[0] if models else {}
    return {
        "train_date": first.get("fecha_train"),
        "test_date": first.get("fecha_test"),
        "target_order": TARGET_ORDER,
        "models": models,
        "advertencia": (
            "Resultados de validación temporal con QWK ≈ 0,39. El modelo describe "
            "asociaciones y no permite evaluar el riesgo de una persona."
        ),
    }
