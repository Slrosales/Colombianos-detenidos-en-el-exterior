import type { Metadata } from "next";
import Link from "next/link";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Colombianos detenidos en el exterior",
    template: "%s | Colombianos detenidos en el exterior",
  },
  description:
    "Explorador interactivo de los datos abiertos de la Cancillería de Colombia sobre colombianos detenidos en el exterior. Corte 2026.",
  openGraph: {
    title: "Colombianos detenidos en el exterior",
    description:
      "Mapa interactivo, series de stock y análisis de la situación jurídica. Datos abiertos, corte 2026.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <header className="site-header">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true" />
            <span>
              <strong>Detenidos en el exterior</strong>
              <small>Datos abiertos · Cancillería de Colombia</small>
            </span>
          </Link>
          <nav className="site-nav" aria-label="Navegación principal">
            <Link href="/">Explorar</Link>
            <Link href="/methodology">Metodología</Link>
            <Link href="/model">Modelo</Link>
          </nav>
        </header>
        {children}
        <footer className="site-footer">
          <p>
            Fuente: Datos Abiertos Colombia, Cancillería de Colombia. Actualización
            metodológica 2026: Laura Sofía Gómez Rosales.
          </p>
          <p className="footer-note">
            Los datos son registros administrativos agregados. No permiten seguir a una
            persona entre cortes ni establecer relaciones causales.
          </p>
        </footer>
      </body>
    </html>
  );
}
