import unittest

import numpy as np

from src.analysis import OrdinalLogisticRegression


class OrdinalModelTests(unittest.TestCase):
    def test_ordinal_model_fits_and_predicts_ordered_classes(self):
        features = np.array(
            [[0, 0], [0, 1], [1, 0], [1, 1], [2, 0], [2, 1]] * 10, dtype=float
        )
        target = np.array([0, 0, 1, 1, 2, 2] * 10, dtype=int)
        weights = np.ones(len(target), dtype=float)
        model = OrdinalLogisticRegression().fit(features, target, weights)
        predictions = model.predict(features)
        self.assertEqual(predictions.shape, (len(features),))
        self.assertTrue(set(np.unique(predictions)).issubset({0, 1, 2}))
        self.assertGreater(len(set(predictions)), 1)


if __name__ == "__main__":
    unittest.main()
