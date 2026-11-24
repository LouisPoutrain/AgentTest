"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Bot, ArrowRight, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { ProgressBar } from "./ProgressBar";
import { cn } from "@/lib/utils";
import { useLotStore } from "@/src/stores/useLotStore";
import type { CrewPipelineStep } from "@/lib/types";

interface MissionPanelProps {
  crewNames: string[];
  executionMode: "sequential" | "parallel";
  isStreaming: boolean;
  activeId: string;
}

export function MissionPanel({ crewNames, executionMode, isStreaming, activeId }: MissionPanelProps) {
  const lotData = useLotStore((state) => state.lots[activeId]);
  const steps = useMemo(() => {
    if (!lotData) return [] as CrewPipelineStep[];
    // Group steps by crewName prefix (format: "crewName/stepKey")
    const crewMap: Record<string, CrewPipelineStep> = {};
    for (const [key, step] of Object.entries(lotData)) {
      const slashIdx = key.indexOf("/");
      if (slashIdx === -1) continue;
      const crewName = key.slice(0, slashIdx);
      if (!crewMap[crewName]) {
        crewMap[crewName] = {
          crewName,
          status: "pending",
          tokens: 0,
          cost: 0,
        };
      }
      // Update with the latest step info for this crew
      if (step.status) {
        crewMap[crewName].status = step.status;
      }
      if (step.tokens) crewMap[crewName].tokens = step.tokens;
      if (step.cost) crewMap[crewName].cost = step.cost;
    }
    // Preserve order from crewNames array
    return crewNames.map((name) => crewMap[name] || { crewName: name, status: "pending" });
  }, [lotData, crewNames]);

  const allDone = steps.every((s) => s.status === "completed" || s.status === "error");
  const anyRunning = steps.some((s) => s.status === "running");

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn(
        "flex flex-col gap-3 p-4 mt-2 mb-4 bg-bg-secondary/40 rounded-xl border shadow-sm",
        anyRunning ? "border-accent/30" : "border-border"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <RocketIcon className="h-4 w-4 text-accent" />
          <h4 className="text-[11px] font-semibold text-text-primary uppercase tracking-wider">
            Mission
          </h4>
          <span className={cn(
            "text-[9px] font-medium px-1.5 py-0.5 rounded-full",
            executionMode === "sequential"
              ? "bg-blue-500/10 text-blue-400"
              : "bg-purple-500/10 text-purple-400"
          )}>
            {executionMode === "sequential" ? "Séquentiel" : "Parallèle"}
          </span>
        </div>
        {allDone && !isStreaming && (
          <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> Terminée
          </span>
        )}
      </div>

      {/* Pipeline */}
      <div className={cn(
        "flex flex-col gap-2",
        executionMode === "parallel" && "flex-row flex-wrap gap-2"
      )}>
        {steps.map((step, idx) => (
          <motion.div
            key={step.crewName}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className={cn(
              "flex items-center gap-2 p-2.5 rounded-lg border transition-all duration-300",
              step.status === "running" && "border-accent/40 bg-accent/5",
              step.status === "completed" && "border-emerald-500/30 bg-emerald-500/5",
              step.status === "error" && "border-red-500/30 bg-red-500/5",
              step.status === "pending" && "border-border/40 bg-bg-tertiary/30",
              executionMode === "parallel" && "flex-1 min-w-[140px]"
            )}
          >
            {/* Status Icon */}
            <div className={cn(
              "h-7 w-7 rounded-lg flex items-center justify-center shrink-0",
              step.status === "running" && "bg-accent/20",
              step.status === "completed" && "bg-emerald-500/20",
              step.status === "error" && "bg-red-500/20",
              step.status === "pending" && "bg-bg-tertiary"
            )}>
              {step.status === "running" && (
                <Loader2 className="h-3.5 w-3.5 text-accent animate-spin" />
              )}
              {step.status === "completed" && (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              )}
              {step.status === "error" && (
                <AlertCircle className="h-3.5 w-3.5 text-red-400" />
              )}
              {step.status === "pending" && (
                <Bot className="h-3.5 w-3.5 text-text-tertiary" />
              )}
            </div>

            {/* Crew Info */}
            <div className="min-w-0 flex-1">
              <div className="text-[11px] font-medium text-text-primary truncate">{step.crewName}</div>
              <div className="text-[9px] text-text-tertiary">
                {step.status === "pending" && "En attente"}
                {step.status === "running" && "En cours..."}
                {step.status === "completed" && "Terminé"}
                {step.status === "error" && "Erreur"}
              </div>
            </div>

            {/* Progress */}
            {step.status === "running" && (
              <div className="h-1 w-12 rounded-full bg-bg-tertiary overflow-hidden">
                <motion.div
                  className="h-full bg-accent rounded-full"
                  initial={{ width: "0%" }}
                  animate={{ width: ["0%", "70%", "90%"] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                />
              </div>
            )}
          </motion.div>
        ))}

        {/* Connectors for sequential mode */}
        {executionMode === "sequential" && steps.length > 1 && (
          <div className="flex flex-col gap-0">
            {steps.map((_, idx) => (
              idx < steps.length - 1 && (
                <div key={`connector-${idx}`} className="flex items-center justify-center py-0.5">
                  <ArrowRight className="h-3 w-3 text-text-tertiary/40 rotate-90" />
                </div>
              )
            ))}
          </div>
        )}
      </div>

      {/* Per-crew progress bars */}
      {steps.filter((s) => s.status === "running" || s.status === "completed").map((step) => (
        <ProgressBar
          key={step.crewName}
          label={step.crewName}
          status={step.status}
          tokens={step.tokens}
          cost={step.cost}
        />
      ))}
    </motion.div>
  );
}

function RocketIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
      <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
    </svg>
  );
}
