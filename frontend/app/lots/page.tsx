"use client";

import { useState } from "react";
import { useLotStore } from "@/src/stores/useLotStore";
import { ProgressBar } from "@/components/chat/ProgressBar";
import { loadConversations } from "@/lib/store";
import type { Conversation } from "@/lib/types";
import { Bot, FolderKanban, CheckCircle2, Clock, AlertCircle, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { transitionClasses } from "@/src/theme";
import { motion } from "framer-motion";

export default function LotsPage() {
  const [conversations] = useState<Conversation[]>(() => loadConversations());
  const lotsState = useLotStore((s) => s.lots);

  // Compute stats
  const stats = (() => {
    let total = 0;
    let completed = 0;
    let running = 0;
    let errors = 0;
    conversations.forEach((c) => {
      const steps = lotsState[c.id] || {};
      Object.values(steps).forEach((step) => {
        total++;
        if (step.status === "completed") completed++;
        else if (step.status === "running") running++;
        else if (step.status === "error") errors++;
      });
    });
    return { total, completed, running, errors };
  })();

  return (
    <div className={cn("min-h-screen bg-bg-primary", transitionClasses.base)}>
      {/* Header */}
      <div className="border-b border-border bg-bg-secondary/50 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-accent-subtle border border-accent/20 flex items-center justify-center">
            <FolderKanban size={20} className="text-accent" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-text-primary tracking-tight">Tableau de Bord des Lots</h1>
            <p className="text-[11px] text-text-tertiary mt-0.5">Suivi des orchestrations en cours et passées</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {conversations.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center py-20"
          >
            <div className="h-16 w-16 rounded-2xl bg-accent-subtle border border-accent/20 flex items-center justify-center mx-auto mb-4">
              <Bot size={32} className="text-text-tertiary" />
            </div>
            <p className="text-text-tertiary text-sm">Aucun lot trouvé. Lancez une orchestration depuis l{'’'}onglet Chat.</p>
          </motion.div>
        ) : (
          <div className="space-y-6 max-w-4xl">
            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard
                icon={<Clock className="h-4 w-4" />}
                label="Total"
                value={stats.total}
                color="text-text-primary"
              />
              <StatCard
                icon={<CheckCircle2 className="h-4 w-4" />}
                label="Terminés"
                value={stats.completed}
                color="text-emerald-500"
              />
              <StatCard
                icon={<TrendingUp className="h-4 w-4" />}
                label="En cours"
                value={stats.running}
                color="text-accent"
              />
              <StatCard
                icon={<AlertCircle className="h-4 w-4" />}
                label="Erreurs"
                value={stats.errors}
                color="text-red-500"
              />
            </div>

            {/* Conversation Cards */}
            <div className="space-y-4">
              {conversations.map((c, index) => {
                const steps = lotsState[c.id] || {};
                const stepEntries = Object.entries(steps);

                return (
                  <motion.div
                    key={c.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, delay: index * 0.05 }}
                    className="border border-border/60 rounded-xl bg-bg-elevated/80 shadow-sm overflow-hidden"
                  >
                    <div className="flex justify-between items-center px-5 py-4 border-b border-border/40">
                      <div>
                        <h2 className="text-sm font-semibold text-text-primary mb-1">{c.title || "Lot Sans Nom"}</h2>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-medium text-text-tertiary bg-bg-secondary px-2 py-0.5 rounded-full">
                            {c.crewName}
                          </span>
                          {stepEntries.length > 0 && (
                            <span className="text-[10px] text-text-tertiary">
                              {stepEntries.filter(([, s]) => s.status === "completed").length}/{stepEntries.length} étapes
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-[10px] text-text-tertiary font-mono">
                        {new Date(c.createdAt).toLocaleString("fr-FR")}
                      </div>
                    </div>

                    <div className="p-5">
                      {stepEntries.length === 0 ? (
                        <div className="text-xs text-text-tertiary italic">Aucune étape enregistrée pour ce lot.</div>
                      ) : (
                        <div className="space-y-2">
                          {stepEntries.map(([key, step]) => (
                            <ProgressBar
                              key={key}
                              label={step.label}
                              status={step.status}
                              tokens={step.tokens}
                              cost={step.cost}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="p-3.5 rounded-xl border border-border/60 bg-bg-elevated/80 shadow-sm flex items-center gap-3">
      <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", "bg-bg-secondary/50", color)}>
        {icon}
      </div>
      <div>
        <div className={cn("text-lg font-bold tabular-nums", color)}>{value}</div>
        <div className="text-[10px] text-text-tertiary font-medium">{label}</div>
      </div>
    </div>
  );
}
