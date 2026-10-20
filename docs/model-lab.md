# Model lab (learning server-side ML)

## Decision

**Do not ship a public predictor in v1.** The research model reaches QWK ≈ 0.39 on a later
cutoff. It cannot support statements about a real person and the available features are
insufficient. The informative value is in explaining *why* the model is limited.

The public `/modelo` page should show:

- the temporal validation design;
- the metrics table and per-class report;
- the confusion matrices;
- the limitations;
- a clear "esto no es una evaluación de riesgo" warning.

The interactive lab is a separate, authenticated or clearly marked learning feature.

## What "server-side model" means here

The Python model lives in the API process. The browser sends a small JSON payload; the server
validates it, transforms it with the same `OneHotEncoder` used in training and returns class
probabilities. The browser never receives a binary artifact.

Planned flow:

```text
POST /api/model/predict
      |
      v
Pydantic validation (allowed categories)
      |
      v
OrdinalLogisticRegression.predict_proba()
      |
      v
{ probabilidades, version, advertencia }
```

## Training artifact

`pipeline/train_model.py` is the planned trainer (phase 4). It will write:

```text
artifacts/models/ordinal_logistic.joblib
artifacts/models/encoder.joblib
artifacts/models/model_metadata.json
```

Metadata must include:

- cutoff dates for train and test;
- feature list and allowed values;
- `CANTIDAD` weight policy;
- metrics and QWK;
- library versions;
- training timestamp and data checksum.

## Rules

1. Demand the user selects a country, crime, age and gender. No free text.
2. Show probabilities with a ± uncertainty and the QWK disclaimer.
3. Log only aggregate request counts; never log a combination that could identify a person.
4. Never call the output a "risk score". Call it a model-estimated probability conditional on
   four coarse categories.
5. Do not train on the current cutoff and then evaluate on itself.
6. Keep the Random Forest available as a comparison, not as the default.

## Learning path

1. Load the parquet with DuckDB; reproduce the 2026 counts.
2. Rebuild the one-hot encoder and the cumulative-logit model.
3. Add `predict_proba` to the ordinal classifier.
4. Serialize model + encoder + metadata.
5. Load them in FastAPI at startup.
6. Add the endpoint and tests with fixed expected probabilities.
7. Add the UI with a prominent warning.
8. Measure latency and add caching keyed by the four inputs.

## Anti-patterns

- Shipping a pickled model without versioned metadata.
- Using `SMOTE` on one-hot categorical data (the 2026 report rejects this).
- Evaluating on a random split when the data is a time series of cutoffs.
- Summing `CANTIDAD` across cutoffs in the training set.
- Exposing `predict` without `predict_proba`.
