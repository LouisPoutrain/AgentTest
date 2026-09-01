"use client";

import React, { useRef, useEffect, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { CrewLaunchPad } from "./CrewLaunchPad";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RotateCcw, Sliders, Sparkles, Zap, Bot } from "lucide-react";
import type { ChatMessage, CrewDetail } from "@/lib/types";

import { CrewSelector } from "./CrewSelector";

interface ChatWindowProps {
  messages: ChatMessage[];
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
}

export function ChatWindow({
  messages,
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
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLaunchPadOverride, setShowLaunchPadOverride] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current;
      scrollElement.scrollTo({ top: scrollElement.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  // Determine currently active agent from the latest log chunk for timeline highlight
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

  const shouldShowLaunchPad = (messages.length === 0 || showLaunchPadOverride) && !isStreaming;

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
    <div className="flex flex-col h-full w-full bg-bg-primary overflow-hidden">
      {/* Header */}
      <div className="shrink-0 h-14 border-b border-border flex items-center justify-between px-4 md:px-8 bg-bg-secondary/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <CrewSelector
            selectedCrew={crewName || ""}
            availableCrews={availableCrews}
            onSelectCrew={onCrewChange}
            disabled={isStreaming}
          />
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2">
          {messages.length > 0 && !isStreaming && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowLaunchPadOverride(!showLaunchPadOverride)}
              className="text-xs h-8 gap-1.5 border-border/80 bg-bg-secondary hover:bg-bg-tertiary"
              title="Ouvrir le formulaire de paramètres"
            >
              <Sliders className="h-3.5 w-3.5 text-accent" />
              {showLaunchPadOverride ? "Voir les logs" : "Paramètres du Crew"}
            </Button>
          )}

          {headerAction && <div>{headerAction}</div>}
        </div>
      </div>

      {/* Execution Stepper / Timeline when Crew has multiple agents */}
      {crewDetail?.agents && crewDetail.agents.length > 0 && (
        <ExecutionTimeline
          agents={crewDetail.agents}
          isStreaming={isStreaming}
          activeAgentName={activeAgentName}
        />
      )}

      {/* Main Content Area: LaunchPad vs Messages Log Stream */}
      <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
        {shouldShowLaunchPad && crewName ? (
          <CrewLaunchPad
            crewDetail={crewDetail || null}
            crewName={crewName}
            onLaunch={handleLaunchFromPad}
            isStreaming={isStreaming}
            availableModels={availableModels}
          />
        ) : (
          <div className="flex flex-col w-full max-w-5xl mx-auto py-6 px-4">
            <div className="flex flex-col gap-1 pb-4">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

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
        )}
      </div>

      {/* Bottom Input Area: Shown only when running or in discussion mode */}
      {!shouldShowLaunchPad && (
        <div className="shrink-0 p-4 bg-bg-primary border-t border-border/50">
          <div className="max-w-4xl mx-auto flex items-center justify-between mb-2 px-1">
            <span className="text-xs text-text-secondary flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Session active : <strong className="text-text-primary">{crewName}</strong>
            </span>

            {messages.length > 0 && !isStreaming && onResetLaunchPad && (
              <button
                type="button"
                onClick={onResetLaunchPad}
                className="text-xs text-accent hover:underline flex items-center gap-1 opacity-80 hover:opacity-100"
              >
                <RotateCcw className="h-3 w-3" /> Relancer avec de nouveaux paramètres
              </button>
            )}
          </div>

          <ChatInput
            onSend={onSendMessage}
            onStop={onStop}
            isStreaming={isStreaming}
            disabled={!crewName}
          />
          <p className="text-xs text-center text-text-secondary mt-2 opacity-50">
            AgentTest orchestre vos agents en temps réel.
          </p>
        </div>
      )}
    </div>
  );
}
