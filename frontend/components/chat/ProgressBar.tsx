import React from "react";
import { cn } from "@/lib/utils";

interface ProgressBarProps {
  label: string;
  status: "pending" | "running" | "completed" | "error";
  tokens?: number;
  cost?: number;
  className?: string;
}

export function ProgressBar({ label, status, tokens, cost, className }: ProgressBarProps) {
  const isRunning = status === "running";
  const isCompleted = status === "completed";
  const isError = status === "error";

  return (
    <div className={cn("flex flex-col gap-2 p-3 border rounded-lg bg-bg-secondary", className)}>
      <div className="flex justify-between items-center text-sm">
        <span className="font-medium text-text-primary">{label}</span>
        <span className={cn(
          "text-xs px-2 py-0.5 rounded-full",
          isRunning && "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
          isCompleted && "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
          isError && "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
          status === "pending" && "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
        )}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>
      
      {/* Jauge animée */}
      <div className="h-1.5 w-full bg-border rounded-full overflow-hidden">
        <div className={cn(
          "h-full rounded-full transition-all duration-500",
          isRunning ? "w-1/2 bg-blue-500 animate-pulse" : "",
          isCompleted ? "w-full bg-green-500" : "",
          isError ? "w-full bg-red-500" : "",
          status === "pending" ? "w-0" : ""
        )} />
      </div>

      {/* Métriques */}
      {(tokens !== undefined || cost !== undefined) && (
        <div className="flex gap-4 text-xs text-text-secondary mt-1">
          {tokens !== undefined && (
            <span>Tokens: <span className="font-mono text-text-primary">{tokens}</span></span>
          )}
          {cost !== undefined && (
            <span>Coût: <span className="font-mono text-text-primary">${cost.toFixed(4)}</span></span>
          )}
        </div>
      )}
    </div>
  );
}
