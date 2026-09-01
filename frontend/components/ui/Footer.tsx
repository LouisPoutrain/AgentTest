import { cn } from "@/lib/utils";
import { transitionClasses } from "@/src/theme";

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  return (
    <footer className={cn(
      "h-12 border-t border-border bg-bg-secondary/50 flex items-center justify-center px-4 text-xs text-text-secondary",
      transitionClasses.base,
      className
    )}>
      <span>© {new Date().getFullYear()} AgentTest. Tous droits réservés.</span>
    </footer>
  );
}
