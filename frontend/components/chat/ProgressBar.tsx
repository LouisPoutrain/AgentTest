import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, Loader2, AlertCircle, Clock } from "lucide-react";
import { motion } from "framer-motion";

/**
 * Props for the ProgressBar component.
 *
 * @interface ProgressBarProps
 */
interface ProgressBarProps {
  /** Human-readable label displayed for the progress item (e.g. agent name or task title). */
  label: string;
  /** Current execution status of the progress item. */
  status: "pending" | "running" | "completed" | "error";
  /** Number of tokens consumed, if available. */
  tokens?: number;
  /** Monetary cost in USD, if available. */
  cost?: number;
  /** Optional CSS class names applied to the root container. */
  className?: string;
}

/**
 * A status-aware progress bar component that displays the state of a running
 * or completed task (e.g. an agent execution step). It shows a label, a status
 * badge, an animated progress indicator, and optional token/cost metrics.
 *
 * @param {ProgressBarProps} props - The component props.
 * @returns {JSX.Element} A styled progress bar with status indicators and metrics.
 *
 * @example
 * // Basic usage with a running status
 * <ProgressBar label="Data Analysis Agent" status="running" />
 *
 * @example
 * // Full usage with metrics
 * <ProgressBar
 *   label="Report Generation"
 *   status="completed"
 *   tokens={12450}
 *   cost={0.0342}
 *   className="my-custom-class"
 * />
 */
export function ProgressBar({ label, status, tokens, cost, className }: ProgressBarProps) {
  const isRunning = status === "running";
  const isCompleted = status === "completed";
  const isError = status === "error";

  const progressWidth = isRunning ? "66%" : isCompleted || isError ? "100%" : "0%";

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex flex-col gap-2 p-3.5 border rounded-xl bg-bg-elevated/80 shadow-sm",
        isRunning && "animate-border-glow",
        className
      )}
      role="progressbar"
      aria-valuenow={isCompleted || isError ? 100 : isRunning ? 66 : 0}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          {isCompleted && <CheckCircle2 size={14} className="text-emerald-500" />}
          {isRunning && <Loader2 size={14} className="text-accent animate-spin" />}
          {isError && <AlertCircle size={14} className="text-red-500" />}
          {status === "pending" && <Clock size={14} className="text-text-tertiary" />}
          <span className="font-medium text-sm text-text-primary">{label}</span>
        </div>
        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded-full font-semibold",
          isRunning && "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
          isCompleted && "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
          isError && "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
          status === "pending" && "bg-bg-tertiary text-text-tertiary"
        )}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>

      {/* Animated progress bar */}
      <div className="h-1.5 w-full bg-bg-tertiary rounded-full overflow-hidden" aria-hidden="true">
        <motion.div
          className={cn(
            "h-full rounded-full transition-all duration-700 ease-out",
            isRunning ? "gradient-accent" : "",
            isCompleted ? "bg-emerald-500" : "",
            isError ? "bg-red-500" : ""
          )}
          style={{ width: progressWidth }}
          animate={isRunning ? { opacity: [0.7, 1, 0.7] } : { opacity: 1 }}
          transition={isRunning ? { duration: 1.5, repeat: Infinity } : {}}
        />
      </div>

      {/* Metrics */}
      {(tokens !== undefined || cost !== undefined) && (
        <div className="flex gap-4 text-[10px] text-text-tertiary mt-0.5 font-mono">
          {tokens !== undefined && (
            <span>Tokens: <span className="text-text-secondary tabular-nums">{tokens}</span></span>
          )}
          {cost !== undefined && (
            <span>Coût: <span className="text-text-secondary tabular-nums">${cost.toFixed(4)}</span></span>
          )}
        </div>
      )}
    </motion.div>
  );
}
