"use client";

import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";
import { Bot } from "lucide-react";

interface HeaderProps {
  title?: string;
  logo?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function Header({ title = "Agent Zouglou", logo, actions, className }: HeaderProps) {
  return (
    <header className={cn(
      "h-14 border-b border-border bg-bg-secondary/80 backdrop-blur-md flex items-center justify-between px-4 md:px-6 sticky top-0 z-50",
      "transition-all duration-200",
      "bg-gradient-to-r from-bg-secondary/90 via-bg-secondary/80 to-bg-secondary/60",
      className
    )}>
      <div className="flex items-center gap-3">
        {logo || (
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-accent-subtle border border-accent/20 flex items-center justify-center">
              <Bot className="h-4 w-4 text-accent" />
            </div>
            <span className="text-base font-semibold text-text-primary tracking-tight">{title}</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        {actions}
        <ThemeToggle />
      </div>
    </header>
  );
}
