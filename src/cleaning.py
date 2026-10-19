"""Cleaning and normalization helpers for the datos.gov.co dataset."""

# Author: Laura Sofía Gómez Rosales (2025-2026).

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONSULATE_MAP_PATH = ROOT / "config" / "consulado_a_pais.json"

SITUATION_MAP = {
    "EN INVESTIGACIN": "EN INVESTIGACIÓN",
    "EN JUICIO": "EN JUICIO",
    "CONDENADO": "CONDENADO",
    "EN ESPERA DE DEPORTACIN": "EN ESPERA DE DEPORTACIÓN",
    "NO REPORTA CONFIDENCIALIDAD ESTATAL": "NO REPORTA",
    "EXTRADITADO": "EXTRADITADO",
}

CRIME_MAP = {
    "NARCOTRFICO": "NARCOTRÁFICO",
    "ROBO HURTO": "ROBO",
    "HOMICIDIO TENTATIVA DE": "HOMICIDIO",
    "FRAUDE ESTAFA": "FRAUDE",
    "OTROS": "OTRO",
    "DESCONOCIDO": "OTRO",
    "NO REPORTA CONFIDENCIALIDAD ESTATAL": "NO REPORTA",
    "LAVADO DE ACTIVOS": "DELITOS FINANCIEROS",
    "FALSIFICACIN": "DELITOS FINANCIEROS",
    "FALSEDAD EN DOCUMENTO": "DELITOS FINANCIEROS",
    "DESACATO A LA AUTORIDAD": "DELITOS CONTRA LA ADMINISTRACIÓN PÚBLICA",
    "CELEBRACIN INDEBIDA DE CONTRATOS": "DELITOS CONTRA LA ADMINISTRACIÓN PÚBLICA",
    "TERRORISMO": "DELITOS CONTRA EL ESTADO",
    "DELITOS POLTICOS": "DELITOS CONTRA EL ESTADO",
    "VIOLENCIA DE GENERO": "VIOLENCIA DE GÉNERO",
    "VIOLENCIA INTRAFAMILIAR": "VIOLENCIA DE GÉNERO",
    "EXTORSIN": "EXTORSIÓN",
    "DAOS": "DAÑOS",
    "COACCIN": "COACCIÓN",
    "CONDUCCIN TEMERARIA": "CONDUCCIÓN TEMERARIA",
}

AGE_MAP = {
    "PRIMERA INFANCIA": "MENORES",
    "ADOLESCENTE": "MENORES",
    "INFANTE": "MENORES",
}

GENDER_MAP = {"NO BINARIO": "OTRO"}

COUNTRY_ALIASES = {
    "ESPAA": "ESPAÑA",
    "CURAAO": "CURAÇAO",
    "MEXICO": "MÉXICO",
    "PANAMA": "PANAMÁ",
    "PERU": "PERÚ",
    "JAPON": "JAPÓN",
    "BELGICA": "BÉLGICA",
    "CANADA": "CANADÁ",
    "RUMANIA": "RUMANÍA",
    "SUDAFRICA": "SUDÁFRICA",
    "TURQUIA": "TURQUÍA",
    "VIET NAM": "VIETNAM",
}

UNKNOWN_COUNTRY_VALUES = {"", "DESCONOCIDO", "EXTRADICION", "REPATRIACION"}


MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "\x80", "\x81", "\x89", "\x8d", "\x91", "\x9d")


def _decode_once(value: str) -> str:
    if "ï¿½" in value:
        return value.replace("ï¿½", "\ufffd")
    if "\ufffd" in value:
        return value
    if not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value.encode("latin-1", errors="replace").decode("utf-8", errors="replace")


def decode_mojibake(value: object) -> object:
    """Repair values that were read as Latin-1 but actually contain UTF-8 bytes.

    The source file mixes valid UTF-8, invalid single-byte characters and even
    doubly-encoded replacement characters. This function only re-decodes strings
    that look like mojibake, so already-clean accented labels are left untouched.
    """
    if not isinstance(value, str):
        return value
    previous = value
    for _ in range(3):
        current = _decode_once(previous)
        if current == previous:
            break
        previous = current
    return previous


def canonical_key(value: object) -> str:
    """Return an accent-insensitive, punctuation-free key for matching labels."""
    value = decode_mojibake(value)
    if not isinstance(value, str):
        return ""
    value = value.replace("\ufffd", "")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def load_consulate_map(path: Path = CONSULATE_MAP_PATH) -> dict[str, str]:
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    return {canonical_key(name): country for name, country in raw.items()}


def normalize_country(value: object) -> str:
    decoded = decode_mojibake(value)
    if not isinstance(decoded, str):
        return "DESCONOCIDO"
    decoded = decoded.replace("\ufffd", "").strip().upper()
    if decoded in UNKNOWN_COUNTRY_VALUES:
        return "DESCONOCIDO"
    return COUNTRY_ALIASES.get(canonical_key(decoded), decoded)


def normalize_situation(value: object) -> str:
    return SITUATION_MAP.get(canonical_key(value), str(value).strip())


def normalize_crime(value: object) -> str:
    key = canonical_key(value)
    if key in CRIME_MAP:
        return CRIME_MAP[key]
    return str(decode_mojibake(value)).strip()


def normalize_age(value: object) -> str:
    key = canonical_key(value)
    if key in AGE_MAP:
        return AGE_MAP[key]
    return str(decode_mojibake(value)).strip().upper()


def normalize_gender(value: object) -> str:
    key = canonical_key(value)
    return GENDER_MAP.get(key, str(decode_mojibake(value)).strip().upper())


def read_raw(path: str | Path) -> pd.DataFrame:
    """Read the downloaded CSV, repairing mixed UTF-8/Latin-1 encodings."""
    frame = pd.read_csv(path, encoding="latin-1", dtype=str)
    frame.columns = [decode_mojibake(column) for column in frame.columns]
    for column in frame.columns:
        frame[column] = frame[column].map(decode_mojibake)
    frame["CANTIDAD"] = pd.to_numeric(frame["CANTIDAD"], errors="coerce").fillna(0).astype(int)
    frame["FECHA PUBLICACIÓN"] = pd.to_datetime(
        frame["FECHA PUBLICACIÓN"], errors="coerce"
    )
    # The original notebook removed exact duplicates before analysis.
    frame = frame.drop_duplicates().reset_index(drop=True)
    return clean_dataframe(frame)


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Add normalized analysis columns without mutating the input frame."""
    frame = frame.copy()
    consulate_map = load_consulate_map()
    from_consulate = frame["CONSULADO"].map(
        lambda value: consulate_map.get(canonical_key(value))
    )
    from_country = frame["PAIS PRISIÓN"].map(normalize_country)
    frame["PAIS"] = from_consulate.where(
        from_consulate.notna() & (from_consulate != "DESCONOCIDO"), from_country
    )
    frame["PAIS"] = frame["PAIS"].map(normalize_country)
    frame["DELITO_LIMPIO"] = frame["DELITO"].map(normalize_crime)
    frame["EDAD_LIMPIA"] = frame["GRUPO EDAD"].map(normalize_age)
    frame["GENERO_LIMPIO"] = frame["GÉNERO"].map(normalize_gender)
    frame["SITUACION_LIMPIA"] = frame["SITUACIÓN JURÍDICA"].map(normalize_situation)
    return frame


def snapshot(frame: pd.DataFrame, date: str) -> pd.DataFrame:
    return frame.loc[frame["FECHA PUBLICACIÓN"] == pd.Timestamp(date)].copy()


def weighted_counts(frame: pd.DataFrame, column: str) -> pd.Series:
    return (
        frame.groupby(column, dropna=False)["CANTIDAD"]
        .sum()
        .sort_values(ascending=False)
    )
