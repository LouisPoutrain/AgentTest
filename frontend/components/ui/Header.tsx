"use client";
import { Button } from "./button";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/utils";
import { theme, transitionClasses } from "@/src/theme";

interface HeaderProps {
  title?: string;
  logo?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function Header({ title = "AgentTest", logo, actions, className }: HeaderProps) {
  return (
    <header className={cn(
      "h-16 border-b border-border bg-bg-secondary/80 backdrop-blur-md flex items-center justify-between px-4 md:px-8 sticky top-0 z-50",
      transitionClasses.base,
      className
    )}>
      <div className="flex items-center gap-3">
        {logo || <span className="text-xl font-bold text-text-primary">{title}</span>}
      </div>
      <div className="flex items-center gap-4">
        {actions}
        <ThemeToggle />
      </div>
    </header>
  );
}
