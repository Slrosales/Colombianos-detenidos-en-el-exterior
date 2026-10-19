import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.cleaning import (
    canonical_key,
    clean_dataframe,
    decode_mojibake,
    normalize_age,
    normalize_country,
    normalize_crime,
    normalize_gender,
    normalize_situation,
    read_raw,
    snapshot,
    weighted_counts,
)

HEADER = (
    "FECHA PUBLICACIÓN,PAIS PRISIÓN,CONSULADO,DELITO,EXTRADITADO Y O REPATRIADO,"
    "SITUACIÓN JURÍDICA,GÉNERO,GRUPO EDAD,UBICACIÓN PAÍS,CANTIDAD,LATITUD,LONGITUD\n"
)


class CleaningTests(unittest.TestCase):
    def test_decode_mojibake(self):
        self.assertEqual(decode_mojibake("NARCOTRÃ\x81FICO"), "NARCOTRÁFICO")

    def test_decode_utf8_replacement_character(self):
        self.assertEqual(decode_mojibake("NARCOTRï¿½FICO"), "NARCOTR\ufffdFICO")

    def test_canonical_key(self):
        self.assertEqual(canonical_key("NARCOTRÁFICO"), "NARCOTRAFICO")
        self.assertEqual(canonical_key("Robo / Hurto"), "ROBO HURTO")

    def test_situation_normalization(self):
        self.assertEqual(normalize_situation("EN INVESTIGACI�N"), "EN INVESTIGACIÓN")
        self.assertEqual(
            normalize_situation("NO REPORTA � CONFIDENCIALIDAD ESTATAL"), "NO REPORTA"
        )
        self.assertEqual(normalize_situation("CONDENADO"), "CONDENADO")

    def test_crime_normalization(self):
        self.assertEqual(normalize_crime("NARCOTR�FICO"), "NARCOTRÁFICO")
        self.assertEqual(normalize_crime("ROBO / HURTO"), "ROBO")
        self.assertEqual(normalize_crime("HOMICIDIO / TENTATIVA DE"), "HOMICIDIO")

    def test_age_and_gender_normalization(self):
        self.assertEqual(normalize_age("PRIMERA INFANCIA"), "MENORES")
        self.assertEqual(normalize_age("ADOLESCENTE"), "MENORES")
        self.assertEqual(normalize_age("ADULTO"), "ADULTO")
        self.assertEqual(normalize_gender("NO_BINARIO"), "OTRO")
        self.assertEqual(normalize_gender("MASCULINO"), "MASCULINO")

    def test_country_normalization(self):
        self.assertEqual(normalize_country("ESPA�A"), "ESPAÑA")
        self.assertEqual(normalize_country("MEXICO"), "MÉXICO")
        self.assertEqual(normalize_country("EXTRADICION"), "DESCONOCIDO")
        self.assertEqual(normalize_country(""), "DESCONOCIDO")

    def test_clean_dataframe_recovers_country_from_consulate(self):
        frame = pd.DataFrame(
            {
                "CONSULADO": ["C. MADRID", "C. DESCONOCIDO"],
                "PAIS PRISIÓN": ["DESCONOCIDO", "ESPA�A"],
                "DELITO": ["NARCOTR�FICO", "ROBO / HURTO"],
                "GRUPO EDAD": ["ADULTO", "ADOLESCENTE"],
                "GÉNERO": ["MASCULINO", "NO_BINARIO"],
                "SITUACIÓN JURÍDICA": ["CONDENADO", "EN INVESTIGACI�N"],
            }
        )
        cleaned = clean_dataframe(frame)
        self.assertEqual(cleaned.loc[0, "PAIS"], "ESPAÑA")
        self.assertEqual(cleaned.loc[0, "DELITO_LIMPIO"], "NARCOTRÁFICO")
        self.assertEqual(cleaned.loc[1, "PAIS"], "ESPAÑA")
        self.assertEqual(cleaned.loc[1, "EDAD_LIMPIA"], "MENORES")
        self.assertEqual(cleaned.loc[1, "GENERO_LIMPIO"], "OTRO")
        self.assertEqual(cleaned.loc[1, "SITUACION_LIMPIA"], "EN INVESTIGACIÓN")

    def test_read_raw_repairs_encoding_and_removes_duplicates(self):
        good = (
            "2026-10-09,DESCONOCIDO,C. MADRID,NARCOTRÁFICO,DESCONOCIDO,"
            "EN INVESTIGACIÓN,MASCULINO,ADULTO,,1,40.4,-3.7\n"
        )
        mixed = (
            "2026-10-09,DESCONOCIDO,C. MADRID,NARCOTRï¿½FICO,DESCONOCIDO,"
            "EN INVESTIGACIï¿½N,MASCULINO,ADULTO,,2,40.4,-3.7\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_bytes((HEADER + good + mixed + good).encode("utf-8"))
            frame = read_raw(path)
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame["DELITO_LIMPIO"].tolist(), ["NARCOTRÁFICO"] * 2)
        self.assertEqual(frame["SITUACION_LIMPIA"].tolist(), ["EN INVESTIGACIÓN"] * 2)
        self.assertEqual(frame["PAIS"].tolist(), ["ESPAÑA", "ESPAÑA"])
        self.assertEqual(frame["CANTIDAD"].tolist(), [1, 2])
        self.assertEqual(frame["FECHA PUBLICACIÓN"].iloc[0].year, 2026)

    def test_snapshot_and_weighted_counts(self):
        frame = pd.DataFrame(
            {
                "FECHA PUBLICACIÓN": pd.to_datetime(
                    ["2026-10-09", "2026-10-09", "2025-11-01"]
                ),
                "PAIS": ["ESPAÑA", "VENEZUELA", "ESPAÑA"],
                "CANTIDAD": [1, 2, 3],
            }
        )
        current = snapshot(frame, "2026-10-09")
        self.assertEqual(len(current), 2)
        counts = weighted_counts(current, "PAIS")
        self.assertEqual(counts["VENEZUELA"], 2)
        self.assertEqual(counts["ESPAÑA"], 1)


if __name__ == "__main__":
    unittest.main()
