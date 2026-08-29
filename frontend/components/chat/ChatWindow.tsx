"use client";

import React, { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import type { ChatMessage } from "@/lib/types";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface ChatWindowProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  crewName?: string;
  availableCrews?: string[];
  onCrewChange?: (name: string) => void;
  headerAction?: React.ReactNode;
  onSendMessage: (message: string) => void;
  onStop: () => void;
}

export function ChatWindow({ messages, isStreaming, crewName, availableCrews = [], onCrewChange, headerAction, onSendMessage, onStop }: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current;
      scrollElement.scrollTo({ top: scrollElement.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  return (
    <div className="flex flex-col h-full w-full bg-bg-primary overflow-hidden">
      {/* Header */}
      <div className="shrink-0 h-14 border-b border-border flex items-center justify-between px-4 md:px-8 bg-bg-secondary/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-2">
          {crewName && availableCrews.length > 0 ? (
            <>
              <span className="text-accent">⚡</span>
              <Select value={crewName} onValueChange={onCrewChange} disabled={isStreaming}>
                <SelectTrigger className="w-auto min-w-[150px] border-none shadow-none bg-transparent font-semibold text-lg hover:bg-bg-tertiary focus:ring-0">
                  <SelectValue placeholder="Sélectionnez un Crew" />
                </SelectTrigger>
                <SelectContent>
                  {availableCrews.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </>
          ) : crewName ? (
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <span className="text-accent">⚡</span> {crewName}
            </h2>
          ) : (
            <span className="text-text-secondary">Sélectionnez un Crew pour commencer</span>
          )}
        </div>
        {headerAction && (
          <div>{headerAction}</div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
        <div className="flex flex-col w-full max-w-5xl mx-auto py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[50vh] text-text-secondary space-y-4">
              <div className="text-5xl opacity-50">🤖</div>
              <p className="text-lg">Aucun message pour le moment.</p>
              {crewName && <p className="text-sm">Envoyez un message pour déclencher l'agent {crewName}.</p>}
            </div>
          ) : (
            <div className="flex flex-col gap-1 pb-4">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              
              {/* Typing indicator shown only when streaming and last message is from user OR last msg is log */}
              {isStreaming && (messages.length === 0 || messages[messages.length - 1].role === "user" || messages[messages.length - 1].type === "log") && (
                <div className="mt-4">
                  <TypingIndicator />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="shrink-0 p-4 bg-bg-primary border-t border-border/50">
        <ChatInput 
          onSend={onSendMessage}
          onStop={onStop}
          isStreaming={isStreaming}
          disabled={!crewName}
        />
        <p className="text-xs text-center text-text-secondary mt-2 opacity-50">
          AgentTest peut faire des erreurs. Considérez vérifier les informations importantes.
        </p>
      </div>
    </div>
  );
}
