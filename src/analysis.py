"""Generate updated tables, figures and ordinal-model metrics.

Usage:
    python src/analysis.py --input data/raw/colombianos_detenidos.csv
"""

# Author: Laura Sofía Gómez Rosales (2025-2026).

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    cohen_kappa_score,
    f1_score,
    mean_absolute_error,
)
from sklearn.preprocessing import OneHotEncoder

try:
    from .cleaning import read_raw, snapshot, weighted_counts
except ImportError:  # when executed as a script
    from cleaning import read_raw, snapshot, weighted_counts

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARAMS = ROOT / "config" / "params.json"
TARGET_ORDER = ["EN INVESTIGACIÓN", "EN JUICIO", "CONDENADO"]
FEATURES = ["PAIS", "DELITO_LIMPIO", "EDAD_LIMPIA", "GENERO_LIMPIO"]


class OrdinalLogisticRegression:
    """Cumulative-logit ordinal classifier using two binary logistic models."""

    def __init__(self) -> None:
        self.models: list[LogisticRegression] = []

    def fit(self, features: np.ndarray, target: np.ndarray, weights: np.ndarray):
        self.models = []
        for threshold in (1, 2):
            model = LogisticRegression(
                max_iter=3000, class_weight="balanced", random_state=42
            )
            model.fit(features, (target >= threshold).astype(int), sample_weight=weights)
            self.models.append(model)
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        probability_ge_1 = self.models[0].predict_proba(features)[:, 1]
        probability_ge_2 = np.minimum(
            self.models[1].predict_proba(features)[:, 1], probability_ge_1
        )
        scores = np.column_stack(
            [1 - probability_ge_1, probability_ge_1 - probability_ge_2, probability_ge_2]
        )
        return scores.argmax(axis=1)


def build_features(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, OneHotEncoder]:
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    train_encoded = encoder.fit_transform(train[FEATURES])
    test_encoded = encoder.transform(test[FEATURES])
    return train_encoded, test_encoded, encoder


def evaluate_model(name, model, x_train, y_train, w_train, x_test, y_test, w_test):
    if isinstance(model, OrdinalLogisticRegression):
        model.fit(x_train, y_train, w_train)
    else:
        model.fit(x_train, y_train, sample_weight=w_train)
    predictions = model.predict(x_test)
    report = classification_report(
        y_test,
        predictions,
        target_names=TARGET_ORDER,
        sample_weight=w_test,
        output_dict=True,
        zero_division=0,
    )
    return {
        "modelo": name,
        "accuracy": accuracy_score(y_test, predictions, sample_weight=w_test),
        "balanced_accuracy": balanced_accuracy_score(
            y_test, predictions, sample_weight=w_test
        ),
        "macro_f1": f1_score(
            y_test, predictions, average="macro", sample_weight=w_test
        ),
        "qwk": cohen_kappa_score(
            y_test, predictions, weights="quadratic", sample_weight=w_test
        ),
        "kappa": cohen_kappa_score(y_test, predictions, sample_weight=w_test),
        "mae_ordinal": mean_absolute_error(y_test, predictions, sample_weight=w_test),
        "n_train_filas": len(y_train),
        "n_test_filas": len(y_test),
        "peso_train": int(w_train.sum()),
        "peso_test": int(w_test.sum()),
    }, report


def save_bar(series: pd.Series, title: str, xlabel: str, path: Path, color="#3b6ea5"):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    series.plot(kind="bar", ax=ax, color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Detenidos activos")
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=35)
    for patch in ax.patches:
        ax.annotate(
            f"{int(patch.get_height()):,}".replace(",", "."),
            (patch.get_x() + patch.get_width() / 2, patch.get_height()),
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(ROOT / "data/raw/colombianos_detenidos.csv"))
    parser.add_argument("--params", default=str(DEFAULT_PARAMS))
    args = parser.parse_args()

    params = json.loads(Path(args.params).read_text(encoding="utf-8"))
    output_tables = ROOT / "outputs" / "tables"
    output_figures = ROOT / "outputs" / "figures"
    output_tables.mkdir(parents=True, exist_ok=True)
    output_figures.mkdir(parents=True, exist_ok=True)

    with open(args.input, encoding="latin-1") as handle:
        filas_descargadas = sum(1 for _ in handle) - 1
    frame = read_raw(args.input)
    cutoff = pd.Timestamp(params["report_cutoff"])
    current = snapshot(frame, params["report_cutoff"])
    historical_cutoff = snapshot(frame, "2021-05-01")

    summary = {
        "filas_descargadas": int(filas_descargadas),
        "duplicados_eliminados": int(filas_descargadas - len(frame)),
        "filas_totales": int(len(frame)),
        "fecha_min": str(frame["FECHA PUBLICACIÓN"].min().date()),
        "fecha_max": str(frame["FECHA PUBLICACIÓN"].max().date()),
        "corte_actual": params["report_cutoff"],
        "filas_corte_actual": int(len(current)),
        "total_corte_actual": int(current["CANTIDAD"].sum()),
        "filas_2021": int(len(historical_cutoff)),
        "total_2021": int(historical_cutoff["CANTIDAD"].sum()),
        "paises_distintos_corte_actual": int(
            current.loc[current["PAIS"] != "DESCONOCIDO", "PAIS"].nunique()
        ),
        "pct_pais_desconocido_corte_actual": float(
            100
            * current.loc[current["PAIS"] == "DESCONOCIDO", "CANTIDAD"].sum()
            / current["CANTIDAD"].sum()
        ),
    }
    (output_tables / "resumen_general.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    top_n = int(params.get("top_n", 10))
    countries = weighted_counts(current, "PAIS")
    countries_2021 = weighted_counts(historical_cutoff, "PAIS")
    crimes = weighted_counts(current, "DELITO_LIMPIO")
    ages = weighted_counts(current, "EDAD_LIMPIA")
    genders = weighted_counts(current, "GENERO_LIMPIO")
    situations = weighted_counts(current, "SITUACION_LIMPIA")

    for name, series in {
        "paises_corte_actual": countries,
        "paises_2021": countries_2021,
        "delitos_corte_actual": crimes,
        "edad_corte_actual": ages,
        "genero_corte_actual": genders,
        "situacion_corte_actual": situations,
    }.items():
        series.rename("CANTIDAD").to_csv(output_tables / f"{name}.csv", encoding="utf-8")

    save_bar(
        countries.head(top_n),
        f"Países con más colombianos detenidos activos ({params['report_cutoff']})",
        "País",
        output_figures / "paises_corte_actual.png",
    )
    save_bar(
        crimes.head(top_n),
        f"Delitos reportados en el corte {params['report_cutoff']}",
        "Delito",
        output_figures / "delitos_corte_actual.png",
        color="#a5523b",
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    genders.plot(kind="bar", ax=axes[0], color="#4c7a5a")
    axes[0].set_title("Distribución por género")
    axes[0].set_xlabel("Género")
    axes[0].set_ylabel("Detenidos activos")
    axes[0].tick_params(axis="x", rotation=20)
    ages.plot(kind="bar", ax=axes[1], color="#7b5aa6")
    axes[1].set_title("Distribución por grupo de edad")
    axes[1].set_xlabel("Grupo de edad")
    axes[1].set_ylabel("Detenidos activos")
    axes[1].tick_params(axis="x", rotation=25)
    for ax in axes:
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_figures / "genero_edad_corte_actual.png", dpi=160)
    plt.close(fig)

    # Stock at the last snapshot of each year (not a sum of monthly reports).
    annual = []
    dates = frame["FECHA PUBLICACIÓN"].dropna().dt.normalize().drop_duplicates().sort_values()
    for year, group in dates.groupby(dates.dt.year):
        last_date = group.max()
        annual.append(
            {
                "AÑO": int(year),
                "FECHA_CORTE": last_date.date().isoformat(),
                "DETENIDOS_ACTIVOS": int(
                    frame.loc[frame["FECHA PUBLICACIÓN"] == last_date, "CANTIDAD"].sum()
                ),
            }
        )
    annual_frame = pd.DataFrame(annual)
    annual_frame.to_csv(
        output_tables / "stock_por_ano.csv", index=False, encoding="utf-8"
    )
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(
        annual_frame["AÑO"],
        annual_frame["DETENIDOS_ACTIVOS"],
        marker="o",
        color="#2f5f8f",
    )
    ax.set_title("Detenidos activos al último corte de cada año")
    ax.set_xlabel("Año")
    ax.set_ylabel("Detenidos activos")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_figures / "stock_por_ano.png", dpi=160)
    plt.close(fig)

    comparison_countries = (
        pd.concat(
            [countries_2021.rename("2021-05-01"), countries.rename(params["report_cutoff"])],
            axis=1,
        )
        .fillna(0)
        .sort_values(params["report_cutoff"], ascending=False)
        .head(top_n)
    )
    comparison_countries.to_csv(
        output_tables / "comparacion_paises_2021_2026.csv", encoding="utf-8"
    )
    fig, ax = plt.subplots(figsize=(11, 5.2))
    comparison_countries.plot(kind="bar", ax=ax)
    ax.set_title("Comparación de detenidos activos por país: 2021 vs. 2026")
    ax.set_xlabel("País")
    ax.set_ylabel("Detenidos activos")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_figures / "comparacion_paises_2021_2026.png", dpi=160)
    plt.close(fig)

    # Temporal validation: train on one snapshot, test on a later one.
    train = snapshot(frame, params["train_date"])
    test = snapshot(frame, params["test_date"])
    train = train.loc[train["SITUACION_LIMPIA"].isin(TARGET_ORDER)].copy()
    test = test.loc[test["SITUACION_LIMPIA"].isin(TARGET_ORDER)].copy()
    x_train, x_test, _ = build_features(train, test)
    y_train = train["SITUACION_LIMPIA"].map({label: i for i, label in enumerate(TARGET_ORDER)}).to_numpy()
    y_test = test["SITUACION_LIMPIA"].map({label: i for i, label in enumerate(TARGET_ORDER)}).to_numpy()
    w_train = train["CANTIDAD"].to_numpy()
    w_test = test["CANTIDAD"].to_numpy()

    metrics = []
    for name, model in [
        ("Regresión logística ordinal", OrdinalLogisticRegression()),
        (
            "Random Forest",
            RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced_subsample",
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]:
        result, report = evaluate_model(
            name, model, x_train, y_train, w_train, x_test, y_test, w_test
        )
        result["fecha_train"] = params["train_date"]
        result["fecha_test"] = params["test_date"]
        metrics.append(result)
        pd.DataFrame(report).transpose().to_csv(
            output_tables
            / f"reporte_clasificacion_{name.lower().replace(' ', '_')}.csv",
            encoding="utf-8",
        )
    pd.DataFrame(metrics).to_csv(
        output_tables / "metricas_modelos.csv", index=False, encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\nMétricas de modelos:")
    print(pd.DataFrame(metrics).to_string(index=False))
    print("\nTablas y figuras generadas en outputs/.")


if __name__ == "__main__":
    main()
