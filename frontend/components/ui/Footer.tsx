import { cn } from "@/lib/utils";
import { Zap } from "lucide-react";
import { transitionClasses } from "@/src/theme";

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  return (
    <footer className={cn(
      "h-10 border-t border-border bg-bg-secondary/50 flex items-center justify-center px-4 text-[10px] text-text-tertiary font-medium tracking-wide",
      transitionClasses.base,
      className
    )}>
      <div className="flex items-center gap-1.5">
        <Zap className="h-3 w-3 text-accent" />
        <span>© {new Date().getFullYear()} Agent Test. Tous droits réservés.</span>
      </div>
    </footer>
  );
}
