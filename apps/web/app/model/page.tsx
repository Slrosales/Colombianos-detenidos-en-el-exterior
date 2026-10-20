import type { Metadata } from "next";
import { ModelPanel } from "@/components/ModelPanel";

export const metadata: Metadata = {
  title: "Modelo ordinal",
  description:
    "Resultados, validación temporal y límites del modelo ordinal de situación jurídica.",
};

export default function ModelPage() {
  return (
    <main className="page">
      <ModelPanel />
    </main>
  );
}
