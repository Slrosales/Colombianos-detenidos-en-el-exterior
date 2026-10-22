import { Suspense } from "react";
import { ExploreDashboard } from "@/components/ExploreDashboard";

function DashboardSkeleton() {
  return (
    <main className="skeleton-page" aria-label="Cargando el tablero">
      <div className="skeleton-hero" />
      <div className="skeleton-block" />
    </main>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <ExploreDashboard />
    </Suspense>
  );
}
