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

  return (
    <div className="relative w-full max-w-4xl mx-auto flex items-end gap-2 bg-bg-secondary p-2 rounded-xl border border-border focus-within:ring-1 focus-within:ring-accent transition-shadow shadow-sm">
      <Textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Sélectionnez un Crew pour commencer..." : "Écrivez votre message..."}
        disabled={disabled}
        className="min-h-[44px] max-h-[200px] w-full resize-none bg-transparent border-0 focus-visible:ring-0 px-3 py-3 overflow-y-auto"
        rows={1}
      />
      
      {isStreaming ? (
        <Button 
          variant="destructive" 
          size="icon" 
          onClick={onStop}
          className="h-[44px] w-[44px] shrink-0 rounded-lg"
          title="Arrêter la génération"
        >
          <Square className="h-5 w-5 fill-current" />
        </Button>
      ) : (
        <Button 
          variant="default" 
          size="icon" 
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          className={cn(
            "h-[44px] w-[44px] shrink-0 rounded-lg transition-all",
            input.trim() ? "bg-accent hover:bg-accent-hover text-white" : "bg-bg-tertiary text-text-secondary cursor-not-allowed opacity-50"
          )}
        >
          <Send className="h-5 w-5" />
        </Button>
      )}
    </div>
  );
}
