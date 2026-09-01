import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, AlertTriangle } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { transitionClasses } from "@/src/theme";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-4 py-6 px-4 md:px-8 group",
        transitionClasses.base,
        isUser ? "bg-transparent" : "bg-bg-secondary/30 hover:bg-bg-secondary/50",
        message.type === "error" && "bg-destructive/10"
      )}
    >
      <Avatar className={cn("h-8 w-8 mt-1 border border-border transition-transform duration-200", transitionClasses.base)}>
        {isUser ? (
          <AvatarFallback className="bg-accent text-accent-foreground">
            <User size={16} />
          </AvatarFallback>
        ) : (
          <AvatarFallback className={cn(
            "bg-bg-tertiary transition-colors duration-200",
            message.type === "error" && "bg-destructive text-destructive-foreground"
          )}>
            {message.type === "error" ? <AlertTriangle size={16} /> : <Bot size={16} />}
          </AvatarFallback>
        )}
      </Avatar>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm text-text-primary">
            {isUser ? "Vous" : "AgentTest"}
          </span>
          <span className="text-xs text-text-secondary">
            {new Date(message.timestamp).toLocaleTimeString("fr-FR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        <div className={cn(
          "prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-bg-tertiary prose-pre:border prose-pre:border-border rounded-lg p-3 transition-colors duration-200",
          !isUser && "bg-bg-primary/50"
        )}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
