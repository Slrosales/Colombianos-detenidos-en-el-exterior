"use client";

import { useEffect, useState } from "react";
import { api, type ModelMetrics } from "@/lib/api";
import { MODEL_REFERENCE } from "@/lib/model-reference";

type Row = {
  modelo: string;
  accuracy: number;
  balanced_accuracy: number;
  macro_f1: number;
  qwk: number;
  kappa: number;
  mae_ordinal: number;
};

function normalize(metrics: ModelMetrics | null): Row[] {
  if (!metrics) return MODEL_REFERENCE.models;
  return metrics.models.map((model) => ({
    modelo: String(model.modelo ?? "Modelo"),
    accuracy: Number(model.accuracy ?? 0),
    balanced_accuracy: Number(model.balanced_accuracy ?? 0),
    macro_f1: Number(model.macro_f1 ?? 0),
    qwk: Number(model.qwk ?? 0),
    kappa: Number(model.kappa ?? 0),
    mae_ordinal: Number(model.mae_ordinal ?? 0),
  }));
}

function pct(value: number) {
  return `${(100 * value).toFixed(1)} %`;
}

function num(value: number) {
  return value.toFixed(3).replace(".", ",");
}

export function ModelPanel() {
  const [live, setLive] = useState<ModelMetrics | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .modelMetrics()
      .then((value) => {
        if (active) setLive(value);
      })
      .catch(() => {
        if (active) setOffline(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const rows = normalize(live);
  const trainDate = live?.train_date ?? MODEL_REFERENCE.trainDate;
  const testDate = live?.test_date ?? MODEL_REFERENCE.testDate;

  return (
    <div className="prose">
      <p className="eyebrow">Investigación 2026</p>
      <h1>Modelo ordinal y sus límites</h1>
      <p>
        La situación jurídica tiene un orden natural:{" "}
        <strong>EN INVESTIGACIÓN → EN JUICIO → CONDENADO</strong>. El equipo ajustó una
        regresión logística ordinal con validación temporal y la comparó con un Random
        Forest. El resultado no es un predictor confiable: es una herramienta para
        entender qué pueden y qué no pueden explicar las variables disponibles.
      </p>

      <div className="callout warning">
        <p>
          <strong>Esto no es una evaluación de riesgo.</strong> El acuerdo es moderado
          (QWK ≈ 0,39). El modelo no debe usarse para tomar decisiones sobre una persona
          ni para inferir su situación jurídica real.
        </p>
      </div>

      <h2>Diseño de validación</h2>
      <ul>
        <li>Entrenamiento: corte {trainDate}.</li>
        <li>Prueba: corte {testDate}, posterior al entrenamiento.</li>
        <li>
          Variables: país, delito, grupo de edad y género. <code>CANTIDAD</code> se usa
          como peso muestral.
        </li>
        <li>No se aplica SMOTE sobre variables categóricas codificadas one-hot.</li>
      </ul>

      <h2>Resultados</h2>
      <table className="metric-table">
        <thead>
          <tr>
            <th>Modelo</th>
            <th>Accuracy</th>
            <th>Bal. acc.</th>
            <th>Macro F1</th>
            <th>QWK</th>
            <th>Kappa</th>
            <th>MAE</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.modelo}>
              <td>{row.modelo}</td>
              <td>{pct(row.accuracy)}</td>
              <td>{pct(row.balanced_accuracy)}</td>
              <td>{num(row.macro_f1)}</td>
              <td>{num(row.qwk)}</td>
              <td>{num(row.kappa)}</td>
              <td>{num(row.mae_ordinal)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="chart-note">
        {offline
          ? "Vista de referencia: la API no está disponible en este momento."
          : "Métricas leídas de la API cuando está disponible."}
      </p>

      <h2>Por qué no es un predictor público</h2>
      <p>
        El modelo aprende patrones, pero las cuatro variables categóricas no capturan los
        factores procesales que determinan la situación jurídica: tiempo desde la
        detención, antecedentes, defensa legal, gravedad del delito y etapa procesal. Un
        QWK de 0,39 indica acuerdo moderado, no capacidad de decisión.
      </p>

      <h2>Laboratorio server-side (siguiente fase)</h2>
      <p>
        Para aprender cómo se sirve un modelo desde un backend, la fase 4 añadirá un
        endpoint aislado y claramente marcado como demostración. El flujo será:
      </p>
      <ol>
        <li>Entrenar y serializar el modelo ordinal con metadatos versionados.</li>
        <li>Cargar modelo y encoder en FastAPI al iniciar.</li>
        <li>Validar país, delito, edad y género contra categorías permitidas.</li>
        <li>Devolver probabilidades ordenadas y una advertencia explícita.</li>
      </ol>
      <p>
        El detalle técnico está en <code>docs/model-lab.md</code>. Mientras tanto, la
        prioridad del sitio es el análisis exploratorio y la interpretación correcta del
        stock.
      </p>

      <div className="callout">
        <p>
          Decisión de producto: <strong>omitir ML como función pública</strong> y
          conservarlo como página metodológica y laboratorio de aprendizaje. La utilidad
          informativa está en los mapas, las series y la calidad de los datos.
        </p>
      </div>
    </div>
  );
}
