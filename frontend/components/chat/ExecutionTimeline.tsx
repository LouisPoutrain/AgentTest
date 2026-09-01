"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Bot, CheckCircle2, CircleDashed, Loader2, ChevronRight } from "lucide-react";
import type { AgentConfig } from "@/lib/types";

interface ExecutionTimelineProps {
  agents: AgentConfig[];
  isStreaming: boolean;
  activeAgentName?: string;
  className?: string;
}

export function ExecutionTimeline({
  agents,
  isStreaming,
  activeAgentName,
  className = "",
}: ExecutionTimelineProps) {
  if (!agents || agents.length === 0) return null;

  return (
    <div className={`w-full bg-bg-secondary/40 border-b border-border/40 py-2.5 px-4 backdrop-blur-sm ${className}`}>
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-semibold text-text-secondary flex items-center gap-1.5 uppercase tracking-wider">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            Équipe
          </span>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {agents.map((agent, index) => {
            const isActive = isStreaming && activeAgentName?.toLowerCase().includes(agent.name.toLowerCase());
            const isLast = index === agents.length - 1;

            return (
              <React.Fragment key={agent.name}>
                <div
                  className={`flex items-center gap-2 px-2.5 py-1 rounded-lg border text-xs transition-all ${
                    isActive
                      ? "bg-accent/15 border-accent text-accent font-semibold shadow-sm ring-1 ring-accent/30 scale-105"
                      : "bg-bg-tertiary/40 border-border/60 text-text-secondary"
                  }`}
                  title={`${agent.name} - ${agent.role}`}
                >
                  {isActive ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
                  ) : (
                    <Bot className="h-3.5 w-3.5 opacity-70" />
                  )}
                  <span className="truncate max-w-[120px]">{agent.name}</span>
                </div>

                {!isLast && (
                  <ChevronRight className="h-3.5 w-3.5 text-text-secondary/40 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
