"use client";

import React, { useRef, useEffect, useState } from "react";
import { ChatMessageComponent } from "./ChatMessage";
import { AgentLog } from "./AgentLog";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { AutomationWizard } from "@/components/lab/AutomationWizard";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { Button } from "@/components/ui/button";
import { RotateCcw, Sliders, Bot, Folder } from "lucide-react";
import { FolderPickerModal } from "./FolderPickerModal";
import type { ChatMessage, CrewDetail } from "@/lib/types";
import { MissionPanel } from "./MissionPanel";
import { CrewSelector } from "./CrewSelector";
import { Header } from "@/components/ui/Header";
import { transitionClasses } from "@/src/theme";
import { cn } from "@/lib/utils";
import { useLotStore } from "@/src/stores/useLotStore";
import { ProgressBar } from "./ProgressBar";
import { motion, AnimatePresence } from "framer-motion";

/**
 * Props for the ChatWindow component.
 */
interface ChatWindowProps {
  /** Array of chat messages to display in the conversation */
  messages: ChatMessage[];
  /** ID of the currently active execution/crew run */
  activeId?: string;
  /** Whether a streaming response is currently in progress */
  isStreaming: boolean;
  /** Name of the currently selected crew */
  crewName?: string;
  /** Detailed information about the active crew (agents, tasks, etc.) */
  crewDetail?: CrewDetail | null;
  /** List of crew names available for multi-crew mission panel */
  crewNames?: string[];
  /** Execution mode for multi-crew conversations */
  executionMode?: "sequential" | "parallel";
  /** List of available crew names for the selector dropdown */
  availableCrews?: string[];
  /** List of available model identifiers for the launch pad */
  availableModels?: string[];
  /** Callback when the user selects a different crew */
  onCrewChange?: (name: string) => void;
  /** Custom React node rendered in the header actions area */
  headerAction?: React.ReactNode;
  /** Callback to send a plain text message to the chat */
  onSendMessage: (message: string) => void;
  /** Callback to launch a crew with structured inputs and options */
  onLaunchCrew?: (params: {
    message: string;
    inputs: Record<string, unknown>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => void;
  /** Callback to stop the current streaming response */
  onStop: () => void;
  /** Callback to reset the launch pad / start a new session */
  onResetLaunchPad?: () => void;
  /** Current folder context for the session (path on disk) */
  folderContext?: string;
  /** Callback when the folder context is changed */
  onFolderChange?: (folder: string) => void;
}

/**
 * Main chat window component that renders the conversation interface,
 * message stream, input area, and optional crew launch pad sidebar.
 *
 * @param props - The ChatWindowProps containing messages, callbacks, and state.
 * @returns A fully featured chat interface with header, message list,
 *          execution timeline, and toggleable crew configuration panel.
 *
 * @example
 * ```tsx
 * <ChatWindow
 *   messages={messages}
 *   isStreaming={isStreaming}
 *   onSendMessage={sendMessage}
 *   onStop={stopStreaming}
 *   crewName="default"
 *   availableCrews={["code-review", "debug-helper"]}
 * />
 * ```
 */
export function ChatWindow({
  messages,
  activeId,
  isStreaming,
  crewName,
  crewDetail,
  crewNames,
  executionMode,
  availableCrews = [],
  availableModels = [],
  onCrewChange,
  headerAction,
  onSendMessage,
  onLaunchCrew,
  onStop,
  onResetLaunchPad,
  folderContext,
  onFolderChange,
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLaunchPadOverride, setShowLaunchPadOverride] = useState(false);
  const [folderPickerOpen, setFolderPickerOpen] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current;
      scrollElement.scrollTo({ top: scrollElement.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  const activeAgentName = React.useMemo(() => {
    if (!isStreaming || messages.length === 0) return undefined;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.type === "log" && crewDetail?.agents) {
      const found = crewDetail.agents.find((ag) =>
        lastMsg.content.toLowerCase().includes(ag.name.toLowerCase())
      );
      if (found) return found.name;
    }
    return undefined;
  }, [messages, isStreaming, crewDetail]);

  const handleLaunchFromPad = (params: {
    message: string;
    inputs: Record<string, unknown>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => {
    setShowLaunchPadOverride(false);
    if (onLaunchCrew) {
      onLaunchCrew(params);
    } else {
      onSendMessage(params.message);
    }
  };

  return (
    <div className={cn("flex flex-col h-full w-full bg-bg-primary overflow-hidden", transitionClasses.base)}>
      {/* Header */}
      <Header
        logo={
          crewName === "default" && !showLaunchPadOverride ? (
            <div className="flex items-center gap-2 font-semibold text-text-primary px-2">
              <Bot className="h-5 w-5 text-accent" />
              <span>Orchestrateur</span>
            </div>
          ) : (
            <CrewSelector
              selectedCrew={crewName || ""}
              availableCrews={availableCrews}
              onSelectCrew={onCrewChange}
              disabled={isStreaming}
            />
          )
        }
        actions={
          <div className="flex items-center gap-2">
            {!isStreaming && (
              <Button
                variant="agent-secondary"
                size="sm"
                onClick={() => setShowLaunchPadOverride(!showLaunchPadOverride)}
                className="text-xs h-8 gap-1.5 rounded-lg"
                title={crewName === "default" ? "Passer en Sélection Manuelle" : "Paramètres du Crew"}
              >
                <Sliders className="h-3.5 w-3.5 text-accent" />
                {showLaunchPadOverride
                  ? "Masquer"
                  : crewName === "default"
                    ? "Sélection Manuelle"
                    : "Paramètres du Crew"}
              </Button>
            )}
            {headerAction && crewName !== "default" && <div>{headerAction}</div>}
          </div>
        }
      />

      {/* Execution Stepper / Timeline */}
      {crewDetail?.agents && crewDetail.agents.length > 0 && (
        <div className={cn("border-b border-border bg-bg-secondary/30", transitionClasses.base)}>
          <ExecutionTimeline
            agents={crewDetail.agents}
            isStreaming={isStreaming}
            activeAgentName={activeAgentName}
          />
        </div>
      )}

      {/* Mission Panel for multi-crew conversations */}
      {crewNames && crewNames.length > 0 && (
        <div className={cn("border-b border-border bg-bg-secondary/20", transitionClasses.base)}>
          <MissionPanel
            crewNames={crewNames}
            executionMode={executionMode || "sequential"}
            isStreaming={isStreaming}
            activeId={activeId || ""}
          />
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-row overflow-hidden relative">

        {/* Left Column: Chat Area */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Messages Stream */}
          <div
            className="flex-1 w-full overflow-y-auto"
            ref={scrollRef}
            role="log"
            aria-live="polite"
            aria-label="Messages de conversation"
          >
            <div className="flex flex-col w-full max-w-5xl mx-auto py-6 px-4 md:px-8">
              <AnimatePresence mode="wait">
                {messages.length === 0 && !isStreaming && (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.97 }}
                    transition={{ duration: 0.3 }}
                    className="flex flex-col items-center justify-center h-full text-text-secondary py-24"
                  >
                    <div className="h-16 w-16 rounded-2xl bg-accent-subtle border border-accent/20 flex items-center justify-center mb-4 shadow-sm">
                      <Bot className="h-8 w-8 text-accent" />
                    </div>
                    <p className="text-sm font-medium text-text-primary mb-1">
                      Bienvenue sur Agent Zouglou
                    </p>
                    <p className="text-xs text-text-tertiary text-center max-w-sm">
                      Posez-moi une question ou ouvrez le panneau latéral pour lancer un Crew manuellement.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex flex-col gap-2 pb-4">
                {messages.filter(m => m.content.trim() !== "").map((msg, index) => {
                  const isLast = index === messages.length - 1;
                  if (msg.type === "log") {
                    return (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, delay: index * 0.02 }}
                      >
                        <AgentLog content={msg.content} timestamp={msg.timestamp} />
                      </motion.div>
                    );
                  }

                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.02 }}
                    >
                      <ChatMessageComponent message={msg} isStreaming={isStreaming && isLast && msg.role !== "user"} />
                    </motion.div>
                  );
                })}

                {/* Inline Progress Bars */}
                {activeId && (
                  <ChatProgress activeId={activeId} />
                )}

                {/* Typing indicator */}
                {isStreaming &&
                  (messages.length === 0 ||
                    messages[messages.length - 1].role === "user" ||
                    messages[messages.length - 1].type === "log") && (
                    <div className="mt-2">
                      <TypingIndicator />
                    </div>
                  )}
              </div>
            </div>
          </div>

          {/* Bottom Input Area */}
          <div className="shrink-0 p-4 bg-gradient-to-t from-bg-primary via-bg-primary to-transparent relative" aria-label="Zone de saisie">
            <div className="max-w-4xl mx-auto flex items-center justify-between mb-3 px-1">
              <div className="flex items-center gap-4">
                <span className="text-xs text-text-secondary flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Session active : <strong className="text-text-primary font-medium">{crewName === "default" ? "Orchestrateur" : crewName}</strong>
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    setFolderPickerOpen(true);
                  }}
                  disabled={isStreaming}
                  className="text-xs text-accent bg-accent/10 border border-accent/20 px-2.5 py-1 rounded-full hover:bg-accent/20 flex items-center gap-1.5 transition-colors relative z-50 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Folder className="h-3 w-3" />
                  <span className="truncate max-w-[120px]">{folderContext || "."}</span>
                </button>
              </div>

              {messages.length > 0 && !isStreaming && onResetLaunchPad && (
                <button
                  type="button"
                  onClick={onResetLaunchPad}
                  className="text-xs text-accent hover:underline flex items-center gap-1 opacity-80 hover:opacity-100 transition-opacity duration-200"
                >
                  <RotateCcw className="h-3 w-3" /> Nouvelle session
                </button>
              )}
            </div>

            <ChatInput
              onSend={onSendMessage}
              onStop={onStop}
              isStreaming={isStreaming}
              disabled={false}
            />
            <p className="text-[10px] text-center text-text-tertiary mt-2.5">
              Le Meta-Routeur orchestre vos requêtes.
            </p>
          </div>
        </div>

        {/* Right Sidebar: Crew Launch Pad (Toggleable) */}
        <AnimatePresence>
          {showLaunchPadOverride && crewName && (
            <motion.div
              key="launchpad"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 420, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="h-full shrink-0 border-l border-border bg-bg-secondary/20 overflow-hidden shadow-xl z-10 hidden lg:block"
            >
              <div className="w-[420px] h-full overflow-y-auto">
                <AutomationWizard
                  onLaunch={handleLaunchFromPad}
                  availableModels={availableModels}
                  crewName={crewName}
                  maxRpm={15}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <FolderPickerModal
        isOpen={folderPickerOpen}
        onClose={() => setFolderPickerOpen(false)}
        onSelect={(path) => {
          if (onFolderChange) onFolderChange(path);
          setFolderPickerOpen(false);
        }}
        currentValue={folderContext || "."}
        title="Sélectionner le dossier contextuel pour la session"
      />
    </div>
  );
}

/**
 * Renders a progress bar panel showing the current orchestration steps
 * for an active crew execution. Reads state from the zustand lot store.
 *
 * @param props - Component props.
 * @param props.activeId - The active execution ID used to look up progress data.
 * @returns A progress panel with per-step progress bars, or `null` if no steps.
 */
function ChatProgress({ activeId }: { activeId: string }) {
  const lotData = useLotStore((state) => state.lots[activeId]);
  const steps = lotData ? Object.values(lotData) : [];

  if (!steps || steps.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-2 p-4 mt-2 mb-4 bg-bg-secondary/40 rounded-xl border border-border shadow-sm"
    >
      <div className="flex items-center gap-2 mb-2">
        <Bot size={14} className="text-accent" />
        <h4 className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
          Progression de l{'’'}Orchestration
        </h4>
      </div>
      {steps.map((step) => (
        <ProgressBar
          key={step.label}
          label={step.label}
          status={step.status}
          tokens={step.tokens}
          cost={step.cost}
        />
      ))}
    </motion.div>
  );
}
