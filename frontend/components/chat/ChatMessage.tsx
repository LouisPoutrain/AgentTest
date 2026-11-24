import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, AlertTriangle } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { transitionClasses } from "@/src/theme";
import { motion } from "framer-motion";

/**
 * Props for the ChatMessageComponent.
 */
interface ChatMessageProps {
  /** The chat message object containing id, role, content, timestamp, and optional type. */
  message: ChatMessage;
  /** Whether the assistant is currently streaming a response. */
  isStreaming?: boolean;
}

/**
 * Renders a single chat message in the conversation thread.
 *
 * Displays user messages as right-aligned bubbles with an avatar and timestamp,
 * and assistant messages as left-aligned blocks with an avatar, header, and
 * optional error badge. Supports streaming cursor animation and error styling.
 *
 * @example
 * ```tsx
 * <ChatMessageComponent
 *   message={{ id: "1", role: "user", content: "Hello", timestamp: "2026-09-06T12:00:00Z" }}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // Error message with streaming indicator
 * <ChatMessageComponent
 *   message={{ id: "2", role: "assistant", content: "Failed", timestamp: "...", type: "error" }}
 *   isStreaming={false}
 * />
 * ```
 */
export function ChatMessageComponent({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="flex w-full py-2 px-4 md:px-8 justify-end"
        role="listitem"
      >
        <div className="max-w-[80%] flex gap-3 items-start flex-row-reverse">
          <Avatar className={cn(
            "h-8 w-8 mt-0.5 border border-border shadow-sm",
            transitionClasses.base
          )}>
            <AvatarFallback className="bg-bg-tertiary text-text-primary">
              <User size={15} />
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 max-w-xl">
            {/* Timestamp */}
            <div className="text-[9px] text-text-tertiary text-right mb-1 font-medium">
              {new Date(message.timestamp).toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>

            {/* Bubble */}
            <div className={cn(
              "px-4 py-2.5 shadow-sm border",
              "bg-gradient-to-br from-bg-elevated to-bg-secondary/50",
              "rounded-2xl rounded-tr-none",
              "border-border/60"
            )}>
              <div className="prose prose-invert max-w-none text-text-primary text-sm leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "flex w-full py-3 px-4 md:px-8 group transition-colors duration-200",
        message.type === "error" && "bg-red-50/50 dark:bg-red-950/20"
      )}
      role="listitem"
      aria-label={message.type === "error" ? "Message d'erreur" : "Message assistant"}
    >
      <div className="max-w-[80%] w-full mx-auto flex gap-3">
        <div className="relative shrink-0">
          <Avatar className={cn(
            "h-8 w-8 mt-0.5 border border-border shadow-sm",
            isStreaming && "animate-pulse-glow",
            transitionClasses.base
          )}>
            <AvatarFallback className={cn(
              "bg-accent-subtle text-accent",
              message.type === "error" && "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
            )}>
              {message.type === "error" ? <AlertTriangle size={14} /> : <Bot size={14} />}
            </AvatarFallback>
          </Avatar>
          {/* Online indicator */}
          {isStreaming && (
            <span className={cn(
              "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-bg-primary",
              "bg-emerald-500"
            )} />
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-1.5 overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-text-primary">
              Agent Zouglou
            </span>
            <span className="text-[10px] text-text-tertiary font-medium">
              {new Date(message.timestamp).toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {message.type === "error" && (
              <span className="text-[9px] font-semibold text-red-500 bg-red-100/80 dark:bg-red-900/30 px-1.5 py-0.5 rounded-full">
                Erreur
              </span>
            )}
          </div>

          {/* Content */}
          <div className={cn(
            "prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-bg-secondary prose-pre:border prose-pre:border-border rounded-xl transition-colors duration-200",
            "bg-bg-elevated/80 p-4 border border-border/40 shadow-sm"
          )}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {isStreaming && (
              <motion.span
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 0.8, repeat: Infinity }}
                className="inline-block w-2 h-4 ml-1 bg-accent align-middle rounded-sm"
              />
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
