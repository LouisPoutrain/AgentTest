import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Wrench, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentLogProps {
  content: string;
  timestamp: string;
}

export function AgentLog({ content, timestamp }: AgentLogProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Parse if it's an action or a thought
  const isAction = content.includes("[Action]") || content.includes("Action:");
  const isThought = content.includes("[Réflexion]") || content.includes("Thought:");

  const Icon = isAction ? Wrench : BrainCircuit;
  const title = isAction ? "Outil utilisé" : "Réflexion de l'agent";

  // Clean the prefix from the content for display
  const displayContent = content
    .replace("[Réflexion]", "")
    .replace("[Action]", "")
    .trim();

  return (
    <div className="flex w-full py-1 px-4 md:px-8 group">
      <div className="flex-1 max-w-3xl mx-auto flex gap-4">
        <div className="w-8 flex justify-center shrink-0 mt-1">
          {/* Empty spacer to align with avatar */}
        </div>
        
        <div className="flex-1 max-w-full">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors py-1.5 px-3 bg-bg-secondary/20 rounded-md border border-border/50 hover:bg-bg-secondary/40 w-fit"
          >
            <Icon size={14} className="text-accent" />
            {title}
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown size={14} />
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
                <div className="p-3 mt-2 text-xs font-mono text-text-secondary bg-bg-tertiary/50 border border-border/50 rounded-md whitespace-pre-wrap">
                  {displayContent}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
