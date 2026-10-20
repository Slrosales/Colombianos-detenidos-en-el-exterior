import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Metodología",
  description:
    "Stock vs flujo, recuperación del país desde el consulado y límites de los datos de colombianos detenidos en el exterior.",
};

export default function MethodologyPage() {
  return (
    <main className="page">
      <article className="prose">
        <p className="eyebrow">Cómo leer las cifras</p>
        <h1>Metodología</h1>
        <p>
          Esta página resume las decisiones de la actualización 2026 del análisis. Son la
          base de todas las consultas del explorador y corrigen la forma de agregar los
          datos usada en los entregables de 2021 y 2025.
        </p>

        <div className="callout">
          <p>
            <strong>Regla principal:</strong> <code>CANTIDAD</code> es el número de
            personas detenidas activas en un registro. El archivo es una sucesión de
            cortes de publicación. No sumes <code>CANTIDAD</code> entre cortes: la misma
            persona puede aparecer varias veces.
          </p>
        </div>

        <h2>1. Stock, flujo y unidad de análisis</h2>
        <p>
          El explorador usa tres reglas explícitas:
        </p>
        <ul>
          <li>
            <strong>Stock actual:</strong> solo el último corte disponible.
          </li>
          <li>
            <strong>Comparación temporal:</strong> el último corte de cada año.
          </li>
          <li>
            <strong>Flujo:</strong> no se estima. No hay un identificador individual que
            permita seguir una misma persona entre cortes.
          </li>
        </ul>
        <p>
          Por eso los totales grandes de 2021 y 2025 (por ejemplo, 76.715 en España) son
          observaciones acumuladas, no personas activas en un momento dado. En el corte
          del 9 de octubre de 2026 hay <strong>28.732 detenidos activos</strong> y 6.595
          filas.
        </p>

        <h2>2. Recuperación del país desde el consulado</h2>
        <p>
          Desde finales de 2022, la columna <code>PAIS PRISIÓN</code> contiene en su
          mayoría valores como <code>DESCONOCIDO</code>, <code>EXTRADICION</code> o{" "}
          <code>REPATRIACION</code>. Para recuperar el país se usa <code>CONSULADO</code>{" "}
          y el diccionario <code>config/consulado_a_pais.json</code>.
        </p>
        <p>
          En el corte de 2026 solo 72 registros (0,25 %) quedan sin país identificado. El
          mapa excluye esos registros y el indicador &quot;País sin identificar&quot;
          reporta su peso. Sin esta recuperación, el análisis geográfico sería inviable.
        </p>

        <h2>3. Cifras de referencia (corte 2026-10-09)</h2>
        <ul>
          <li>394.744 filas descargadas; 32.599 duplicados exactos eliminados.</li>
          <li>362.145 filas para el análisis.</li>
          <li>28.732 detenidos activos, frente a 26.392 en mayo de 2021 (+8,9 %).</li>
          <li>
            España (5.586), Venezuela (3.896), Estados Unidos (3.807), Panamá (2.652) y
            Chile (2.640) concentran el mayor stock.
          </li>
          <li>Narcotráfico: 11.849 registros (41,2 %).</li>
          <li>31,7 % de los registros tienen edad desconocida.</li>
        </ul>

        <h2>4. Cambios 2021 → 2026</h2>
        <p>
          La comparación usa mayo de 2021 y octubre de 2026. Ecuador cae 74,5 %, mientras
          que México (+93,1 %), Panamá (+73,6 %) y Chile (+65,7 %) aumentan. Estas
          variaciones pueden reflejar cambios reales, pero también cambios de reporte,
          cobertura consular o clasificación. El diseño no permite separar esas
          explicaciones ni atribuir causalidad.
        </p>

        <h2>5. Normalización de etiquetas</h2>
        <p>
          El archivo mezcla codificaciones UTF-8 y Latin-1, y contiene errores de
          escritura. <code>src/cleaning.py</code> repara mojibake, normaliza delitos,
          géneros, edades y situaciones, y elimina duplicados exactos. Las categorías{" "}
          <code>OTRO</code>, <code>NO REPORTA</code> y <code>DESCONOCIDO</code> se
          conservan: son parte del subregistro y no deben desaparecer silenciosamente.
        </p>

        <h2>6. Límites</h2>
        <ol>
          <li>No hay identificador individual ni seguimiento de cohortes.</li>
          <li>Subregistro: edad desconocida 31,7 %; delito agrupado 22,8 %.</li>
          <li>Los cortes no son estrictamente mensuales.</li>
          <li>El país es imputado desde el consulado después de 2022.</li>
          <li>Las asociaciones no son causales.</li>
          <li>
            El modelo ordinal tiene un acuerdo moderado (QWK ≈ 0,39): no sirve para
            evaluar a una persona.
          </li>
        </ol>

        <h2>7. Fuente y reproducción</h2>
        <p>
          Fuente:{" "}
          <a
            href="https://www.datos.gov.co/Estad-sticas-Nacionales/Colombianos-detenidos-en-el-exterior/e97j-vuf7"
            target="_blank"
            rel="noreferrer"
          >
            Datos Abiertos Colombia, Cancillería de Colombia
          </a>
          . El corte, los conteos y el manifiesto de datos se muestran en el explorador.
          La lógica reproducible vive en <code>src/</code> y <code>pipeline/</code>; el
          informe completo está en <code>reports/informe_actualizado_2026.md</code>.
        </p>
        <p>
          <Link href="/">Volver al explorador</Link> ·{" "}
          <Link href="/model">Ver el modelo y sus límites</Link>
        </p>
      </article>
    </main>
  );
}
