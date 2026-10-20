"""Build the queryable Parquet warehouse used by the API.

Usage:
    python pipeline/build_warehouse.py
    python pipeline/build_warehouse.py --input data/raw/colombianos_detenidos.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cleaning import canonical_key, read_raw  # noqa: E402

DEFAULT_INPUT = ROOT / "data" / "raw" / "colombianos_detenidos.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "detentions.parquet"
DEFAULT_MANIFEST = ROOT / "data" / "processed" / "manifest.json"
DEFAULT_PARAMS = ROOT / "config" / "params.json"
COUNTRIES_INFO = ROOT / "data" / "external" / "INFO Paises.csv"
COORDINATES = ROOT / "data" / "external" / "Coordenadas.csv"

COUNTRY_ALIASES_ISO3 = {
    "ESTADOS UNIDOS": "USA",
    "ESTADOS UNIDOS DE AMERICA": "USA",
    "REINO UNIDO": "GBR",
    "PAISES BAJOS": "NLD",
    "REPUBLICA CHECA": "CZE",
    "COREA REPUBLICA DE": "KOR",
    "COREA DEL SUR": "KOR",
    "FEDERACION DE RUSIA": "RUS",
    "GUYANA FRANCESA": "GUF",
    "RUSIA": "RUS",
}

OUTPUT_COLUMNS = [
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
]


def _read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    with open(path, encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def load_iso3_lookup() -> dict[str, str]:
    """Map accent-insensitive country labels to ISO-3166 alpha-3 codes."""
    lookup: dict[str, str] = {}
    for row in _read_csv(COUNTRIES_INFO):
        iso3 = (row.get(" iso3") or row.get("iso3") or "").strip()
        if not iso3:
            continue
        for label in (row.get("nombre"), row.get(" name")):
            if label:
                lookup[canonical_key(label)] = iso3

    coordinates = _read_csv(COORDINATES)
    for row in coordinates:
        iso3 = (row.get("Alpha-3 code") or "").strip()
        country = (row.get("Country") or "").strip()
        if iso3 and country:
            lookup.setdefault(canonical_key(country), iso3)

    lookup.update({canonical_key(key): value for key, value in COUNTRY_ALIASES_ISO3.items()})
    return lookup


def attach_iso3(frame: pd.DataFrame, lookup: dict[str, str]) -> pd.DataFrame:
    frame = frame.copy()
    frame["pais_iso3"] = frame["PAIS"].map(
        lambda value: lookup.get(canonical_key(value))
        if canonical_key(value) != "DESCONOCIDO"
        else None
    )
    return frame


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_lines(path: Path) -> int:
    with open(path, "rb") as handle:
        return sum(1 for _ in handle) - 1


def build_frame(input_path: Path = DEFAULT_INPUT) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Raw file not found at {input_path}. Run `make download` first."
        )

    frame = read_raw(input_path)
    frame = attach_iso3(frame, load_iso3_lookup())

    frame = frame.rename(
        columns={
            "FECHA PUBLICACIÓN": "fecha_publicacion",
            "PAIS": "pais",
            "CONSULADO": "consulado",
            "DELITO_LIMPIO": "delito",
            "EDAD_LIMPIA": "edad",
            "GENERO_LIMPIO": "genero",
            "SITUACION_LIMPIA": "situacion",
            "CANTIDAD": "cantidad",
            "LATITUD": "latitud",
            "LONGITUD": "longitud",
        }
    )
    frame["fecha_publicacion"] = pd.to_datetime(frame["fecha_publicacion"]).dt.date
    frame["anio"] = pd.to_numeric(
        pd.to_datetime(frame["fecha_publicacion"]).dt.year, errors="coerce"
    ).astype("Int64")
    frame["cantidad"] = pd.to_numeric(frame["cantidad"], errors="coerce").fillna(0).astype(int)
    frame["latitud"] = pd.to_numeric(frame["latitud"], errors="coerce")
    frame["longitud"] = pd.to_numeric(frame["longitud"], errors="coerce")

    for column in ("pais", "consulado", "delito", "edad", "genero", "situacion", "pais_iso3"):
        frame[column] = frame[column].astype("string")

    return frame[OUTPUT_COLUMNS]


def build_manifest(
    frame: pd.DataFrame,
    input_path: Path,
    output_path: Path,
    downloaded_rows: int,
    params: dict,
) -> dict:
    latest = frame["fecha_publicacion"].max()
    current = frame.loc[frame["fecha_publicacion"] == latest]
    unknown_country = current.loc[current["pais"] == "DESCONOCIDO", "cantidad"].sum()
    total = int(current["cantidad"].sum())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(input_path.relative_to(ROOT)),
        "source_sha256": _sha256(input_path),
        "warehouse_file": str(output_path.relative_to(ROOT)),
        "filas_descargadas": int(downloaded_rows),
        "duplicados_eliminados": int(downloaded_rows - len(frame)),
        "filas_totales": int(len(frame)),
        "fecha_min": str(frame["fecha_publicacion"].min()),
        "fecha_max": str(latest),
        "corte_actual": str(latest),
        "filas_corte_actual": int(len(current)),
        "total_corte_actual": total,
        "pct_pais_desconocido_corte_actual": round(
            100 * unknown_country / total, 4
        ) if total else None,
        "paises_distintos_corte_actual": int(
            current.loc[current["pais"] != "DESCONOCIDO", "pais"].nunique()
        ),
        "cutoffs": sorted(str(value) for value in frame["fecha_publicacion"].unique()),
        "report_cutoff_config": params.get("report_cutoff"),
        "columns": OUTPUT_COLUMNS,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--params", default=str(DEFAULT_PARAMS))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    params = json.loads(Path(args.params).read_text(encoding="utf-8"))

    frame = build_frame(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)

    manifest = build_manifest(
        frame, input_path, output_path, _count_lines(input_path), params
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"Wrote {len(frame):,} rows to {output_path} "
        f"({manifest['corte_actual']}, {manifest['total_corte_actual']:,} active detainees)"
    )
    if manifest["report_cutoff_config"] not in (None, manifest["corte_actual"]):
        print(
            "Warning: config/params.json report_cutoff differs from the newest cutoff "
            f"({manifest['report_cutoff_config']} != {manifest['corte_actual']})."
        )


if __name__ == "__main__":
    main()
