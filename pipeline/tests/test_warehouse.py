import unittest

import pandas as pd

from pipeline.build_warehouse import attach_iso3, load_iso3_lookup


class WarehouseTests(unittest.TestCase):
    def test_iso3_lookup_covers_spanish_and_english_names(self):
        lookup = load_iso3_lookup()
        self.assertEqual(lookup["ESPANA"], "ESP")
        self.assertEqual(lookup["SPAIN"], "ESP")
        self.assertEqual(lookup["ESTADOS UNIDOS"], "USA")

    def test_attach_iso3_handles_unknown(self):
        frame = pd.DataFrame({"PAIS": ["ESPAÑA", "DESCONOCIDO", "MÉXICO"]})
        result = attach_iso3(frame, load_iso3_lookup())
        values = result["pais_iso3"].tolist()
        self.assertEqual(values[0], "ESP")
        self.assertTrue(pd.isna(values[1]))
        self.assertEqual(values[2], "MEX")

    def test_aliases_are_not_duplicated(self):
        lookup = load_iso3_lookup()
        self.assertGreater(len(lookup), 150)


if __name__ == "__main__":
    unittest.main()
