import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, AlertTriangle } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { transitionClasses } from "@/src/theme";
import { motion } from "framer-motion";

interface ChatMessageProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function ChatMessageComponent({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex w-full py-4 px-4 md:px-8 justify-end">
        <div className="max-w-3xl flex gap-4 items-start flex-row-reverse">
          <Avatar className={cn("h-8 w-8 mt-1 border border-border shadow-sm", transitionClasses.base)}>
            <AvatarFallback className="bg-bg-tertiary text-text-primary">
              <User size={16} />
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 max-w-2xl bg-bg-secondary/50 rounded-2xl rounded-tr-none px-5 py-3 shadow-sm border border-border/50">
            <div className="prose prose-invert max-w-none text-text-primary">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex w-full py-6 px-4 md:px-8 group transition-colors duration-200",
        message.type === "error" && "bg-destructive/10"
      )}
    >
      <div className="max-w-3xl w-full mx-auto flex gap-4">
        <Avatar className={cn("h-8 w-8 mt-1 border border-border shadow-sm", transitionClasses.base)}>
          <AvatarFallback className={cn(
            "bg-accent text-accent-foreground",
            message.type === "error" && "bg-destructive text-destructive-foreground"
          )}>
            {message.type === "error" ? <AlertTriangle size={16} /> : <Bot size={16} />}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0 space-y-2 overflow-hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-text-primary">
              Agent Zouglou
            </span>
          </div>

          <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-bg-tertiary prose-pre:border prose-pre:border-border rounded-lg transition-colors duration-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {isStreaming && (
              <motion.span
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 0.8, repeat: Infinity }}
                className="inline-block w-2 h-4 ml-1 bg-accent align-middle"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
