"use client";

import React, { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled }: ChatInputProps) {
  const [input, setInput] = React.useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !isStreaming && !disabled) {
      onSend(input.trim());
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasContent = input.trim().length > 0;

  return (
    <div className={cn(
      "relative w-full max-w-4xl mx-auto flex items-end gap-2 bg-bg-elevated p-1.5 rounded-2xl border transition-all duration-200 shadow-sm",
      "focus-within:border-accent/40 focus-within:shadow-md",
      isStreaming && "border-border/60"
    )}>
      <Textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Sélectionnez un Crew pour commencer..." : "Écrivez votre message..."}
        disabled={disabled}
        aria-label="Message"
        className={cn(
          "min-h-[44px] max-h-[200px] w-full resize-none bg-transparent border-0 focus-visible:ring-0 px-3 py-2.5 overflow-y-auto text-sm",
          "leading-relaxed"
        )}
        rows={1}
      />

      <div className="flex items-center gap-1.5 shrink-0">

        {isStreaming ? (
          <Button
            variant="destructive"
            size="icon"
            onClick={onStop}
            className={cn(
              "h-[44px] w-[44px] shrink-0 rounded-xl text-xs",
              "animate-border-glow"
            )}
            title="Arrêter la génération"
          >
            <Square className="h-5 w-5 fill-current" />
          </Button>
        ) : (
          <Button
            variant="default"
            size="icon"
            onClick={handleSend}
            disabled={!hasContent || disabled}
            className={cn(
              "h-[44px] w-[44px] shrink-0 rounded-xl transition-all duration-200",
              hasContent
                ? "gradient-accent text-white shadow-sm hover:shadow-md hover:opacity-90"
                : "bg-bg-tertiary text-text-tertiary cursor-not-allowed opacity-50"
            )}
          >
            <Send className="h-5 w-5" />
          </Button>
        )}
      </div>
    </div>
  );
}
