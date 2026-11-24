import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Wrench, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Props for the AgentLog component.
 */
interface AgentLogProps {
  /** The raw log content from the agent, which may contain "[Action]" or "[Réflexion]" prefixes. */
  content: string;
  /** Optional ISO 8601 timestamp string for the log entry. Currently unused in rendering. */
  timestamp?: string;
}

/**
 * Renders a collapsible agent log entry that auto-detects whether the content
 * is an action (tool usage) or a thought (reasoning), and displays it with
 * an appropriate icon, title, and animated expand/collapse panel.
 *
 * @example
 * // Basic usage — action log
 * <AgentLog content="[Action]\nTool: read_file\nInput: src/main.py" />
 *
 * @example
 * // Basic usage — thought log
 * <AgentLog content="[Réflexion]\nI should check the file first before editing it." />
 *
 * @example
 * // With optional timestamp
 * <AgentLog content="[Action]\nTool: run_test" timestamp="2026-09-06T12:00:00Z" />
 *
 * @param props - The component props.
 * @returns A collapsible log entry with icon, title, and animated content panel.
 */
export function AgentLog({ content }: AgentLogProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Parse if it's an action or a thought
  const isAction = content.includes("[Action]") || content.includes("Action:");

  const Icon = isAction ? Wrench : BrainCircuit;
  const title = isAction ? "Outil utilisé" : "Réflexion de l'agent";

  // Clean the prefix from the content for display
  const displayContent = content
    .replace("[Réflexion]", "")
    .replace("[Action]", "")
    .trim();

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className="flex w-full py-1 px-4 md:px-8 group"
      role="listitem"
    >
      <div className="flex-1 max-w-3xl mx-auto flex gap-3">
        <div className="w-7 flex justify-center shrink-0 mt-0.5" />

        <div className="flex-1 max-w-full">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              "flex items-center gap-2 text-[11px] font-medium text-text-secondary hover:text-text-primary transition-colors py-1.5 px-3.5 bg-bg-secondary/40 rounded-xl border border-border/60 hover:bg-bg-secondary/60 w-fit",
              isOpen && "bg-bg-secondary/60 text-text-primary border-accent/30"
            )}
            aria-expanded={isOpen}
            aria-label={title}
          >
            <Icon size={13} className="text-accent" />
            {title}
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown size={13} />
            </motion.div>
          </button>

          <AnimatePresence initial={false}>
            {isOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="p-3.5 mt-2 text-[11px] font-mono text-text-secondary bg-bg-secondary/60 border border-border/60 rounded-xl whitespace-pre-wrap leading-relaxed shadow-sm">
                  {displayContent}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
