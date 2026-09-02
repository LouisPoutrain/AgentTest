"use client";

import React, { useRef, useEffect, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { CrewLaunchPad } from "./CrewLaunchPad";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RotateCcw, Sliders, Sparkles, Zap, Bot, Folder } from "lucide-react";
import { FolderPickerModal } from "./FolderPickerModal";
import type { ChatMessage, CrewDetail } from "@/lib/types";
import { CrewSelector } from "./CrewSelector";
import { Header } from "@/components/ui/Header";
import { Footer } from "@/components/ui/Footer";
import { transitionClasses } from "@/src/theme";
import { cn } from "@/lib/utils";
import { useLotStore } from "@/src/stores/useLotStore";
import { ProgressBar } from "./ProgressBar";

interface ChatWindowProps {
  messages: ChatMessage[];
  activeId?: string;
  isStreaming: boolean;
  crewName?: string;
  crewDetail?: CrewDetail | null;
  availableCrews?: string[];
  availableModels?: string[];
  onCrewChange?: (name: string) => void;
  headerAction?: React.ReactNode;
  onSendMessage: (message: string) => void;
  onLaunchCrew?: (params: {
    message: string;
    inputs: Record<string, any>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => void;
  onStop: () => void;
  onResetLaunchPad?: () => void;
  folderContext?: string;
  onFolderChange?: (folder: string) => void;
}

export function ChatWindow({
  messages,
  activeId,
  isStreaming,
  crewName,
  crewDetail,
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
    inputs: Record<string, any>;
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
                className="text-xs h-8 gap-1.5"
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

      {/* Execution Stepper / Timeline when Crew has multiple agents */}
      {crewDetail?.agents && crewDetail.agents.length > 0 && (
        <div className={cn("border-b border-border bg-bg-secondary/50", transitionClasses.base)}>
          <ExecutionTimeline
            agents={crewDetail.agents}
            isStreaming={isStreaming}
            activeAgentName={activeAgentName}
          />
        </div>
      )}

      {/* Main Content Area with potential Right Sidebar */}
      <div className="flex-1 flex flex-row overflow-hidden relative">
        
        {/* Left Column: Chat Area */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Messages Stream */}
          <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
            <div className="flex flex-col w-full max-w-5xl mx-auto py-6 px-4">
              <div className="flex flex-col gap-1 pb-4">
                {messages.length === 0 && !isStreaming && (
                  <div className="text-center text-text-secondary mt-20 opacity-50">
                    <p>Posez-moi une question ou ouvrez le panneau latéral pour lancer un Crew manuellement.</p>
                  </div>
                )}
                {messages.filter(m => m.content.trim() !== "").map((msg) => (
                  <div key={msg.id} className={cn("animate-in fade-in-0 duration-300")}>
                    <MessageBubble message={msg} />
                  </div>
                ))}
                
                {/* Inline Progress Bars */}
                {activeId && (
                  <ChatProgress activeId={activeId} />
                )}

                {/* Typing indicator */}
                {isStreaming &&
                  (messages.length === 0 ||
                    messages[messages.length - 1].role === "user" ||
                    messages[messages.length - 1].type === "log") && (
                    <div className="mt-4">
                      <TypingIndicator />
                    </div>
                  )}
              </div>
            </div>
          </div>

          {/* Bottom Input Area */}
          <div className="shrink-0 p-4 bg-bg-primary border-t border-border/50 relative">
            <div className="max-w-4xl mx-auto flex items-center justify-between mb-2 px-1">
              <div className="flex items-center gap-4">
                <span className="text-xs text-text-secondary flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Session active : <strong className="text-text-primary">{crewName === "default" ? "Orchestrateur" : crewName}</strong>
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    setFolderPickerOpen(true);
                  }}
                  disabled={isStreaming}
                  className="text-xs text-accent bg-accent/10 border border-accent/20 px-2.5 py-1 rounded-full hover:bg-accent/20 flex items-center gap-1.5 transition-colors relative z-50 cursor-pointer disabled:opacity-50"
                >
                  <Folder className="h-3 w-3" />
                  Contexte : {folderContext || "."}
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
            <p className="text-xs text-center text-text-secondary mt-2 opacity-50">
              Le Meta-Routeur orchestre vos requêtes.
            </p>
          </div>
        </div>

        {/* Right Sidebar: Crew Launch Pad (Toggleable) */}
        {showLaunchPadOverride && crewName && (
          <div className="w-[420px] h-full shrink-0 border-l border-border bg-bg-secondary/20 overflow-y-auto animate-in slide-in-from-right-8 duration-300 shadow-xl z-10 hidden lg:block">
            <CrewLaunchPad
              crewDetail={crewDetail || null}
              crewName={crewName}
              onLaunch={handleLaunchFromPad}
              isStreaming={isStreaming}
              availableModels={availableModels}
            />
          </div>
        )}
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

function ChatProgress({ activeId }: { activeId: string }) {
  const lotData = useLotStore((state) => state.lots[activeId]);
  const steps = lotData ? Object.values(lotData) : [];

  if (!steps || steps.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 p-4 mt-2 mb-4 bg-bg-secondary/30 rounded-lg border border-border">
      <div className="flex items-center gap-2 mb-2">
        <Bot size={14} className="text-accent" />
        <h4 className="text-xs font-semibold text-text-secondary uppercase">
          Progression de l'Orchestration
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
    </div>
  );
}
