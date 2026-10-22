import type { Page } from "@playwright/test";

const META = {
  corte_actual: "2026-10-09",
  fecha_min: "2018-09-17",
  fecha_max: "2026-10-09",
  filas_totales: 362145,
  filas_corte_actual: 6595,
  total_corte_actual: 28732,
  duplicados_eliminados: 32599,
  pct_pais_desconocido_corte_actual: 0.25,
  paises_distintos_corte_actual: 62,
  cutoffs: ["2021-05-01", "2026-10-09"],
};

const BREAKDOWNS: Record<string, Array<{ valor: string; cantidad: number }>> = {
  delito: [
    { valor: "NARCOTRÁFICO", cantidad: 11849 },
    { valor: "OTRO", cantidad: 5480 },
  ],
  edad: [
    { valor: "ADULTO", cantidad: 14811 },
    { valor: "DESCONOCIDO", cantidad: 9096 },
  ],
  genero: [
    { valor: "MASCULINO", cantidad: 25236 },
    { valor: "FEMENINO", cantidad: 3480 },
  ],
  situacion: [
    { valor: "CONDENADO", cantidad: 13357 },
    { valor: "EN INVESTIGACIÓN", cantidad: 11286 },
  ],
  consulado: [
    { valor: "C. MADRID", cantidad: 3518 },
    { valor: "C. BARCELONA", cantidad: 792 },
  ],
};

export async function mockApi(page: Page) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    let body: unknown;

    if (path.endsWith("/api/meta")) {
      body = META;
    } else if (path.endsWith("/api/cutoffs")) {
      body = { cutoffs: META.cutoffs, latest: META.corte_actual };
    } else if (path.endsWith("/api/filters")) {
      body = {
        cutoff: META.corte_actual,
        values: {
          delito: BREAKDOWNS.delito,
          edad: BREAKDOWNS.edad,
          genero: BREAKDOWNS.genero,
          situacion: BREAKDOWNS.situacion,
          consulado: BREAKDOWNS.consulado,
          pais: [
            { valor: "ESPAÑA", cantidad: 5586 },
            { valor: "VENEZUELA", cantidad: 3896 },
          ],
        },
      };
    } else if (path.endsWith("/api/countries")) {
      body = [
        {
          pais: "ESPAÑA",
          pais_iso3: "ESP",
          cantidad: 5586,
          participacion: 19.44,
          latitud: 40.4,
          longitud: -3.7,
        },
        {
          pais: "VENEZUELA",
          pais_iso3: "VEN",
          cantidad: 3896,
          participacion: 13.56,
          latitud: 8.0,
          longitud: -66.0,
        },
      ];
    } else if (path.endsWith("/api/trend")) {
      body = [
        { anio: 2021, fecha: "2021-09-01", cantidad: 26767 },
        { anio: 2026, fecha: "2026-10-09", cantidad: 28732 },
      ];
    } else if (path.endsWith("/api/compare")) {
      body = [
        {
          pais: "ESPAÑA",
          pais_iso3: "ESP",
          base: 4654,
          target: 5586,
          cambio: 932,
          cambio_pct: 20.03,
        },
        {
          pais: "VENEZUELA",
          pais_iso3: "VEN",
          base: 3423,
          target: 3896,
          cambio: 473,
          cambio_pct: 13.82,
        },
      ];
    } else {
      const match = path.match(/\/api\/breakdown\/([a-z]+)$/);
      const dimension = match?.[1] ?? "delito";
      body = BREAKDOWNS[dimension] ?? BREAKDOWNS.delito;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}
