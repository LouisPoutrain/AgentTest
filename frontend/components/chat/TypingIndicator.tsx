import { BrainCircuit } from "lucide-react";
import { motion } from "framer-motion";

/**
 * A status indicator shown while the assistant is processing a user message.
 *
 * Renders a small brain icon followed by three animated dots and the French
 * label "Agent Test réfléchit..." to signal that a response is being
 * generated. It is placed inside the chat message list between the last user
 * message and the incoming streamed content.
 *
 * @example
 * // Inside a chat message list, conditionally rendered while streaming:
 * {isStreaming && <TypingIndicator />}
 *
 * @returns {JSX.Element} A div containing the animated dots and label.
 */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 px-4 md:px-8 py-3 w-full mt-2" role="status" aria-live="polite">
      <div className="max-w-3xl flex gap-3 w-full items-center">
        <div className="w-7 flex justify-center mt-0.5">
          <BrainCircuit size={14} className="text-accent" aria-hidden="true" />
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <motion.div
              className="w-2 h-2 rounded-full bg-accent"
              initial={{ opacity: 0.5, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0 }}
            />
            <motion.div
              className="w-2 h-2 rounded-full bg-accent"
              initial={{ opacity: 0.5, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0.15 }}
            />
            <motion.div
              className="w-2 h-2 rounded-full bg-accent"
              initial={{ opacity: 0.5, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: 0.3 }}
            />
          </div>
          <span className="text-xs text-text-secondary italic font-medium">
            Agent Test réfléchit...
          </span>
        </div>
      </div>
    </div>
  );
}
