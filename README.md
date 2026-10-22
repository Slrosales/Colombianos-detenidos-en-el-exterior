# Colombianos detenidos en el exterior

Análisis de los datos públicos de **Colombianos detenidos en el exterior** publicados por la
Cancillería colombiana en [datos.gov.co](https://www.datos.gov.co/Estad-sticas-Nacionales/Colombianos-detenidos-en-el-exterior/e97j-vuf7).

El proyecto combina un análisis exploratorio, mapas, aprendizaje no supervisado y un modelo
ordinal para explorar la situación jurídica de las personas detenidas. El corte de datos usado
en la actualización de 2026 es **2026-10-09** (última fecha de publicación disponible al momento
de la descarga).

La investigación completa (artículo, informes, material de aprendizaje y salidas generadas) se
conserva localmente y no forma parte de este repositorio público. Los notebooks originales sí se
mantienen públicos. Este repositorio publica el sitio web, la API y la documentación técnica.

## Sitio web interactivo (2026)

El repositorio incluye un explorador web en construcción:

- **Frontend:** Next.js + TypeScript, mapas con MapLibre GL y gráficos con ECharts.
- **Backend:** FastAPI + DuckDB, consultas en vivo sobre un Parquet limpio.
- **Datos:** `pipeline/build_warehouse.py` aplica la lógica de `src/cleaning.py` y añade
  ISO3, coordenadas y un manifiesto de procedencia.
- **Despliegue previsto:** Vercel para `apps/web` y Fly.io/Render para `apps/api`.
- **Demo gratis sin backend:** `make web-data` genera JSON precomputado y el frontend usa
  `NEXT_PUBLIC_STATIC_DEMO=true`. Se puede desplegar solo en Vercel; luego se conecta la API
  cambiando esa variable y `NEXT_PUBLIC_API_URL`.

El sitio prioriza el **análisis exploratorio**. El modelo ordinal se conserva como página
metodológica y laboratorio de aprendizaje, no como predictor público: su QWK ≈ 0,39 no permite
evaluar a una persona. La documentación técnica y el TODO por módulo están en
[`docs/`](docs/README.md) y el despliegue en
[`docs/deployment.md`](docs/deployment.md).

```bash
make install          # dependencias Python
make install-web      # dependencias del frontend
make download         # descarga el corte más reciente
make warehouse        # genera data/processed/detentions.parquet
make validate         # valida warehouse + manifiesto antes de publicar
make refresh          # download + warehouse + validate
make web-data         # JSON para la demo estática (sin backend)
make api              # FastAPI en http://localhost:8000/docs
make web              # Next.js en http://localhost:3000
```

## Autoría

- **Trabajo original (2021):** Ana Ardila Pacheco, Edgar Torres Pérez, Giuseppe Gómez Donado,
  Laura Gómez Rosales, Sebastián Abello Vásquez e Yitzhak Peña Jiménez.
- **Trabajo producido desde 2025 en adelante:** **Laura Sofía Gómez Rosales**. Incluye el notebook
  de ML de 2025, la actualización de 2026, el modelo ordinal, la reorganización del repositorio y
  el informe actualizado.

## Nota sobre las cifras de 2021, 2025 y 2026

Las cifras de los entregables originales no son contradictorias: corresponden a **fechas de
corte distintas** y, en algunos casos, a **formas distintas de agregar** la variable `CANTIDAD`.

- El informe de 2021 se elaboró con datos disponibles hasta mayo de 2021.
- El notebook de machine learning se ejecutó con un corte de 2025.
- La actualización de 2026 usa el corte de **2026-10-09**.
- `CANTIDAD` es el número de personas detenidas activas en cada registro. **No se debe sumar a
  través de todas las publicaciones mensuales**, porque la misma persona puede aparecer en varios
  cortes. Para comparar periodos se usa el último corte de cada año; para el estado actual se usa
  el corte más reciente.

Además, desde finales de 2022 la columna `PAIS PRISIÓN` contiene valores como `DESCONOCIDO`,
`EXTRADICION` o `REPATRIACION`. El país se recupera a partir de `CONSULADO`, usando el diccionario
`config/consulado_a_pais.json`. Con esa recuperación, en el corte de 2026 solo el **0,25 %** de los
detenidos queda sin país identificado.

## Estructura del repositorio

```text
.
├── README.md
├── Makefile
├── fly.toml                      # Configuración de Fly.io para la API
├── requirements.txt
├── requirements-dev.txt
├── .github/workflows/            # CI y actualización programada de datos
├── docs/                         # Arquitectura, datos, testing, despliegue y roadmap
├── config/
│   ├── consulado_a_pais.json
│   └── params.json
├── data/
│   ├── external/                 # Países, coordenadas y shapefile
│   ├── raw/                      # Descarga original (ignorada por git)
│   └── processed/                # Parquet + manifiesto (ignorados por git)
├── pipeline/                     # Construcción y validación del warehouse
│   ├── build_warehouse.py
│   ├── validate_warehouse.py
│   └── tests/
├── apps/
│   ├── api/                      # FastAPI + DuckDB
│   └── web/                      # Next.js + MapLibre + ECharts + Playwright
├── notebooks/                    # Notebooks originales, preservados
│   ├── Colombianos_detenidos_en_el_exterior.ipynb
│   ├── ML_Colombianos_detenidos.ipynb
│   └── 03_modelo_ordinal.ipynb
├── scripts/
│   └── download_data.py
├── src/                          # Limpieza y análisis reutilizable (2026)
│   ├── cleaning.py
│   └── analysis.py
├── tests/
│   ├── test_cleaning.py
│   └── test_model.py
└── artifacts/                    # Modelos serializados (ignorados por git)
```

Los artefactos de investigación (`lessons/`, `paper/`, `reports/` y `outputs/`) se mantienen
locales y están ignorados por Git. No forman parte del repositorio público.

Los notebooks originales se conservan en `notebooks/` y siguen siendo parte del proyecto.
`notebooks/03_modelo_ordinal.ipynb` es la interfaz de análisis actualizada y los dos notebooks
anteriores se conservan como registro. La lógica reutilizable y testeada vive en `src/`, para que
los notebooks no dupliquen código.

## Resultados principales (corte 2026-10-09)

La descarga contiene 394.744 filas; tras eliminar 32.599 duplicados exactos quedan 362.145
registros para el análisis. El corte de 2026 tiene 6.595 filas y 28.732 detenidos activos.

- **28.732** detenidos activos registrados, frente a **26.392** en el corte de mayo de 2021
  (+8,9 %).
- Países con más detenidos activos: **España (5.586)**, **Venezuela (3.896)**, **Estados Unidos
  (3.807)**, **Panamá (2.652)**, **Chile (2.640)**, **México (1.518)** y **Ecuador (1.386)**.
- **Narcotráfico** sigue siendo el delito más reportado: 11.849 registros (41,2 % del total).
- **87,8 %** de los detenidos son hombres; el grupo **adulto** concentra 14.811 registros.
- **46,5 %** están condenados, **39,3 %** en investigación y **8,8 %** en juicio.

Cambios relevantes frente a mayo de 2021: Ecuador pasó de 5.431 a 1.386 detenidos activos
(−74,5 %), mientras que México (+93,1 %), Panamá (+73,6 %) y Chile (+65,7 %) aumentaron.

## Modelo ordinal actualizado

El notebook de ML original se conserva como referencia. La actualización incorpora un modelo
ordinal con validación temporal:

- Entrenamiento: corte **2025-11-01** (5.638 filas, 26.243 detenidos ponderados).
- Prueba: corte **2026-10-09** (6.084 filas, 27.177 detenidos ponderados).
- Variables: país, delito, grupo de edad y género.
- Orden de la variable objetivo: `EN INVESTIGACIÓN` → `EN JUICIO` → `CONDENADO`.
- Se usa `CANTIDAD` como peso muestral.

Resultados en el conjunto de prueba:

| Modelo | Accuracy | Balanced accuracy | Macro F1 | QWK | Kappa |
|---|---:|---:|---:|---:|---:|
| Regresión logística ordinal | 0,647 | 0,539 | 0,553 | 0,393 | 0,375 |
| Random Forest | 0,617 | 0,634 | 0,576 | 0,394 | 0,381 |

El acuerdo es **moderado** (QWK ≈ 0,39). El modelo aprende patrones útiles, pero las cuatro
variables disponibles no alcanzan para predecir con precisión la situación jurídica. Se requieren
variables adicionales: tiempo desde la detención, antecedentes, tipo de representación legal y
gravedad del delito.

## Cómo ejecutar

Requisitos: Python 3.10+, Node 20+ y pnpm.

### Análisis y web

```bash
# 1. Instalar dependencias
make install          # Python (.venv, análisis + API + tests)
make install-web      # Node/Next.js

# 2. Descargar el corte más reciente
make download

# 3. Generar tablas, figuras y métricas de investigación
make analysis

# 4. Construir y validar el warehouse consultable
make warehouse
make validate

# 5. Levantar backend y frontend en dos terminales
make api              # http://localhost:8000/docs
make web              # http://localhost:3000
```

Pruebas:

```bash
make test             # tests de limpieza, modelo, pipeline y API
make test-web         # typecheck de TypeScript
make build-web        # build de producción

# E2E (la primera vez: cd apps/web && pnpm exec playwright install chromium)
make test-e2e         # Playwright: mapa, URL y filtros con API simulada
```

El detalle de cada capa y la recomendación para CI están en
[`docs/testing.md`](docs/testing.md).

También se puede usar un archivo ya descargado:

```bash
.venv/bin/python src/analysis.py --input data/raw/colombianos_detenidos.csv
```

La descarga se guarda en `data/raw/` y está ignorada por git. El Parquet y el manifiesto se
generan en `data/processed/`, también ignorados. Si se descarga un corte posterior, actualiza
`report_cutoff`, `train_date` y `test_date` en `config/params.json` antes de regenerar las tablas.

Los notebooks de `notebooks/` se ejecutan desde esa carpeta y usan rutas relativas a
`../data/external/` y `../data/processed/`. La lógica reutilizable vive en `src/`; el sitio no
importa notebooks.

### Variables de entorno

Copia `.env.example` para la API (CORS, ruta del Parquet) y `apps/web/.env.example` para el
frontend (`NEXT_PUBLIC_API_URL`). En desarrollo, los valores por defecto apuntan a
`http://localhost:3000` y `http://localhost:8000`.

## Limitaciones

- Los datos son registros administrativos agregados; no existe un identificador individual que
  permita seguir a una misma persona entre cortes.
- Hay subregistro y valores `DESCONOCIDO` en delito, edad y país.
- La comparación entre años mezcla cambios reales con cambios de reporte.
- Las asociaciones no son causales.
- El modelo no incluye variables jurídicas o temporales necesarias para una predicción robusta.

## Entregables

- `apps/web/` — explorador interactivo (Next.js + MapLibre + ECharts).
- `apps/web/public/data/demo/` — JSON precomputado para la demo estática.
- `apps/api/` — API de consultas en vivo (FastAPI + DuckDB).
- `docs/` — arquitectura, contrato de datos, testing, despliegue y roadmap.
- `notebooks/` — notebooks originales y de análisis.
- `pipeline/` — construcción y validación del warehouse.

## Fuente y cita

Datos Abiertos Colombia. *Colombianos detenidos en el exterior*. Cancillería de Colombia.
https://www.datos.gov.co/Estad-sticas-Nacionales/Colombianos-detenidos-en-el-exterior/e97j-vuf7

Trabajo original (2021): Ana Ardila Pacheco, Edgar Torres Pérez, Giuseppe Gómez Donado, Laura
Gómez Rosales, Sebastián Abello Vásquez e Yitzhak Peña Jiménez. Universidad del Norte.

Actualización, análisis desde 2025 y documento de trabajo (2026): Laura Sofía Gómez Rosales.
