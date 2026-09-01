"use client";

import { useEffect, useState } from "react";
import { useLotStore } from "@/src/stores/useLotStore";
import { ProgressBar } from "@/components/chat/ProgressBar";
import { loadConversations } from "@/lib/store";
import type { Conversation } from "@/lib/types";

export default function LotsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const lotsState = useLotStore((s) => s.lots);

  useEffect(() => {
    // Load conversations from local storage
    const loaded = loadConversations();
    setConversations(loaded);
  }, []);

  return (
    <div className="p-8 min-h-screen">
      <h1 className="text-3xl font-bold text-text-primary mb-8">Tableau de Bord des Lots</h1>

      {conversations.length === 0 ? (
        <div className="text-text-secondary text-center py-12">
          Aucun lot trouvé. Lancez une orchestration depuis l'onglet Chat.
        </div>
      ) : (
        <div className="grid gap-6">
          {conversations.map((c) => {
            const steps = lotsState[c.id] || {};
            const stepEntries = Object.entries(steps);

            return (
              <div
                key={c.id}
                className="border border-border rounded-xl p-6 bg-bg-primary shadow-sm"
              >
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-text-primary mb-1">{c.title || "Lot Sans Nom"}</h2>
                    <span className="text-sm font-medium text-text-secondary bg-bg-secondary px-3 py-1 rounded-full">
                      {c.crewName}
                    </span>
                  </div>
                  <div className="text-sm text-text-secondary">
                    {new Date(c.createdAt).toLocaleString("fr-FR")}
                  </div>
                </div>

                <div className="space-y-3">
                  {stepEntries.length === 0 ? (
                    <div className="text-sm text-text-secondary italic">Aucune étape enregistrée pour ce lot.</div>
                  ) : (
                    stepEntries.map(([key, step]) => (
                      <ProgressBar
                        key={key}
                        label={step.label}
                        status={step.status}
                        tokens={step.tokens}
                        cost={step.cost}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
