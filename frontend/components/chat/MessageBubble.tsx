"use client";

import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, AlertTriangle } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { transitionClasses } from "@/src/theme";
import { motion } from "framer-motion";

/**
 * Props for the MessageBubble component.
 */
interface MessageBubbleProps {
  /** The chat message to render, including role, content, and optional type metadata. */
  message: ChatMessage;
}

/**
 * A message bubble that renders a single chat message with an avatar,
 * sender label, timestamp, and markdown-formatted content.
 *
 * Displays user messages with a blue accent avatar and assistant messages
 * with a styled card background. Error-type messages receive a red highlight.
 *
 * @example
 * // Render a user message
 * <MessageBubble message={{
 *   id: "1",
 *   role: "user",
 *   content: "Hello, how does this work?",
 *   timestamp: "2025-01-15T10:30:00Z"
 * }} />
 *
 * @example
 * // Render an assistant error message
 * <MessageBubble message={{
 *   id: "2",
 *   role: "assistant",
 *   content: "Failed to process request",
 *   timestamp: "2025-01-15T10:31:00Z",
 *   type: "error"
 * }} />
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "flex w-full gap-3 py-3 px-4 md:px-8 group",
        transitionClasses.base,
        isUser ? "bg-transparent" : "bg-bg-secondary/20 hover:bg-bg-secondary/40",
        message.type === "error" && "bg-red-50/50 dark:bg-red-950/20"
      )}
    >
      <Avatar className={cn(
        "h-7 w-7 mt-0.5 border border-border transition-transform duration-200",
        transitionClasses.base,
        !isUser && "hover:scale-110"
      )}>
        {isUser ? (
          <AvatarFallback className="bg-accent-subtle text-accent">
            <User size={14} />
          </AvatarFallback>
        ) : (
          <AvatarFallback className={cn(
            "bg-bg-tertiary transition-colors duration-200",
            message.type === "error" && "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
          )}>
            {message.type === "error" ? <AlertTriangle size={14} /> : <Bot size={14} />}
          </AvatarFallback>
        )}
      </Avatar>

      <div className="flex-1 space-y-1.5 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm text-text-primary">
            {isUser ? "Vous" : "Agent Test"}
          </span>
          <span className="text-[10px] text-text-tertiary font-medium">
            {new Date(message.timestamp).toLocaleTimeString("fr-FR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        <div className={cn(
          "prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-bg-secondary prose-pre:border prose-pre:border-border rounded-xl p-3 transition-colors duration-200",
          !isUser && "bg-bg-elevated/80 border border-border/40 shadow-sm"
        )}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </motion.div>
  );
}
