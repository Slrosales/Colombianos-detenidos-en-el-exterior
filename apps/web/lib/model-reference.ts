export const MODEL_REFERENCE = {
  trainDate: "2025-11-01",
  testDate: "2026-10-09",
  targetOrder: ["EN INVESTIGACIÓN", "EN JUICIO", "CONDENADO"],
  models: [
    {
      modelo: "Regresión logística ordinal",
      accuracy: 0.647,
      balanced_accuracy: 0.539,
      macro_f1: 0.553,
      qwk: 0.393,
      kappa: 0.375,
      mae_ordinal: 0.617,
    },
    {
      modelo: "Random Forest",
      accuracy: 0.617,
      balanced_accuracy: 0.634,
      macro_f1: 0.576,
      qwk: 0.394,
      kappa: 0.381,
      mae_ordinal: 0.604,
    },
  ],
};
