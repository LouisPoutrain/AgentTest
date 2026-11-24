import React from "react";
import { Bot, ChevronRight } from "lucide-react";
import type { AgentConfig } from "@/lib/types";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

/**
 * Props for the ExecutionTimeline component.
 */
interface ExecutionTimelineProps {
  /** Array of agent configurations to display in the timeline */
  agents: AgentConfig[];
  /** Whether a crew execution is currently streaming/active */
  isStreaming: boolean;
  /** Name of the currently active agent (case-insensitive match against agent names) */
  activeAgentName?: string;
  /** Optional CSS class name applied to the root container */
  className?: string;
}

/**
 * Displays a horizontal timeline bar showing available agents and their
 * active/inactive state during a crew execution.
 *
 * Renders a scrollable row of agent pills with a pulsing accent indicator
 * for the currently active agent. Non-active agents are dimmed.
 *
 * @example
 * // Basic usage with crew agents
 * <ExecutionTimeline
 *   agents={crewAgents}
 *   isStreaming={true}
 *   activeAgentName="Researcher"
 * />
 *
 * @example
 * // Conditional rendering when no agents are available
 * {agents.length > 0 && (
 *   <ExecutionTimeline agents={agents} isStreaming={false} />
 * )}
 *
 * @param props - The component props
 * @returns A horizontal agent timeline bar, or null if agents is empty
 */
export function ExecutionTimeline({
  agents,
  isStreaming,
  activeAgentName,
  className = "",
}: ExecutionTimelineProps) {
  if (!agents || agents.length === 0) return null;

  return (
    <div className={cn("w-full bg-bg-secondary/30 border-b border-border/40 py-2.5 px-4 backdrop-blur-sm", className)}>
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-3 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-semibold text-text-tertiary flex items-center gap-1.5 uppercase tracking-widest">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            Équipe
          </span>
        </div>

        <div className="flex items-center gap-1 sm:gap-2 shrink-0">
          {agents.map((agent, index) => {
            const isActive = isStreaming && activeAgentName?.toLowerCase().includes(agent.name.toLowerCase());
            const isLast = index === agents.length - 1;

            return (
              <React.Fragment key={agent.name}>
                <motion.div
                  initial={false}
                  animate={isActive ? { scale: [1, 1.05, 1] } : { scale: 1 }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className={cn(
                    "flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-[11px] transition-all cursor-default",
                    "hover:shadow-sm",
                    isActive
                      ? "bg-gradient-to-r from-accent-subtle to-accent-subtle/50 border-accent/40 text-accent font-semibold shadow-sm ring-1 ring-accent/20"
                      : "bg-bg-tertiary/50 border-border/60 text-text-tertiary hover:text-text-secondary"
                  )}
                  title={`${agent.name} - ${agent.role}`}
                >
                  <Bot className={cn(
                    "h-3 w-3 transition-colors duration-200",
                    isActive ? "text-accent" : "opacity-50"
                  )} />
                  <span className="truncate max-w-[100px]">{agent.name}</span>
                  {isActive && (
                    <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse shrink-0" />
                  )}
                </motion.div>

                {!isLast && (
                  <ChevronRight className={cn(
                    "h-3 w-3 shrink-0 transition-colors duration-200",
                    isActive && index === agents.findIndex(a =>
                      activeAgentName?.toLowerCase().includes(a.name.toLowerCase())
                    ) - 1
                      ? "text-accent/60"
                      : "text-text-tertiary/30"
                  )} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
