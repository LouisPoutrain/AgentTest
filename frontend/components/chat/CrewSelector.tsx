"use client";

import * as React from "react";
import { Zap, ChevronDown, Check, Search } from "lucide-react";
import { getCrewDescription } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

/**
 * Props for the CrewSelector component.
 *
 * @example
 * <CrewSelector
 *   selectedCrew="Code Review"
 *   availableCrews={["Code Review", "Debug Assistant", "Documentation"]}
 *   onSelectCrew={(name) => setSelectedCrew(name)}
 * />
 */
interface CrewSelectorProps {
  /** The currently selected crew name. */
  selectedCrew: string;
  /** List of all available crew names to display in the dropdown. */
  availableCrews: string[];
  /** Callback invoked when the user selects a crew. Receives the crew name. */
  onSelectCrew?: (crewName: string) => void;
  /** When true, disables the dropdown trigger button. */
  disabled?: boolean;
}

/**
 * A searchable dropdown component for selecting an active Crew from a list.
 *
 * Renders a trigger button showing the currently selected crew and an animated
 * popover dropdown with a search input that filters crews by name or description.
 * Supports keyboard (Escape to close) and click-outside-to-close behavior.
 *
 * @example
 * // Basic usage with controlled state
 * const [crew, setCrew] = useState("Code Review");
 * <CrewSelector
 *   selectedCrew={crew}
 *   availableCrews={crews}
 *   onSelectCrew={setCrew}
 * />
 *
 * @example
 * // Disabled state (e.g. while a crew is running)
 * <CrewSelector
 *   selectedCrew={crew}
 *   availableCrews={crews}
 *   disabled={isRunning}
 * />
 *
 * @returns A self-contained dropdown selector with search filtering,
 *   animated open/close transitions, and visual active-state indicator.
 */
export function CrewSelector({
  selectedCrew,
  availableCrews,
  onSelectCrew,
  disabled = false,
}: CrewSelectorProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const containerRef = React.useRef<HTMLDivElement>(null);
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  React.useEffect(() => {
    function handleKeyDown(e: globalThis.KeyboardEvent) {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const filteredCrews = React.useMemo(() =>
    availableCrews.filter((c) =>
      c.toLowerCase().includes(search.toLowerCase()) ||
      getCrewDescription(c).toLowerCase().includes(search.toLowerCase())
    ), [availableCrews, search]);

  const handleSelect = (crewName: string) => {
    onSelectCrew?.(crewName);
    setIsOpen(false);
    setSearch("");
  };

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-xl border transition-all duration-200 text-left group",
          isOpen
            ? "bg-bg-tertiary border-accent/50 shadow-md"
            : "bg-bg-secondary/80 hover:bg-bg-tertiary border-border/80 hover:border-border",
          disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
        )}
      >
        <div className={cn(
          "h-5 w-5 rounded-md flex items-center justify-center text-accent shrink-0 group-hover:scale-110 transition-transform duration-200",
          "bg-gradient-to-br from-accent/20 to-accent/10 border border-accent/30"
        )}>
          <Zap className="h-3 w-3 fill-current" />
        </div>

        <span className="font-semibold text-sm text-text-primary tracking-tight truncate max-w-[180px] sm:max-w-[240px]">
          {selectedCrew || "Sélectionnez un Crew"}
        </span>

        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-text-tertiary transition-transform duration-200 shrink-0",
            isOpen ? "rotate-180 text-accent" : "group-hover:text-text-primary"
          )}
        />
      </button>

      {/* Popover Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.97 }}
            transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "absolute left-0 mt-2 w-[340px] sm:w-[420px] rounded-2xl bg-bg-elevated/95 backdrop-blur-xl border border-border shadow-xl z-60 overflow-hidden",
              "flex flex-col"
            )}
          >
            {/* Search Header */}
            <div className="p-2.5 border-b border-border/60 bg-bg-secondary/50">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary" />
                <Input
                  ref={searchInputRef}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher un Crew..."
                  className="pl-8 h-8 text-xs bg-bg-secondary border-border/70 focus-visible:ring-accent/50"
                />
              </div>
            </div>

            {/* Crews List */}
            <div className="max-h-[360px] overflow-y-auto p-2 space-y-1">
              {filteredCrews.length === 0 ? (
                <div className="py-8 text-center text-xs text-text-tertiary italic">
                  Aucun Crew trouvé.
                </div>
              ) : (
                filteredCrews.map((c) => {
                  const isSelected = c === selectedCrew;
                  const desc = getCrewDescription(c);

                  return (
                    <motion.button
                      key={c}
                      type="button"
                      onClick={() => handleSelect(c)}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      className={cn(
                        "w-full text-left p-2.5 rounded-xl border transition-all duration-200 flex items-start gap-2.5 group/item",
                        isSelected
                          ? "bg-accent-subtle border-accent/40"
                          : "bg-bg-secondary/30 hover:bg-bg-tertiary/60 border-transparent hover:border-border"
                      )}
                    >
                      {/* Icon container */}
                      <div
                        className={cn(
                          "h-7 w-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 transition-colors duration-200",
                          isSelected
                            ? "bg-accent text-white"
                            : "bg-bg-tertiary border border-border text-text-tertiary group-hover/item:text-accent group-hover/item:border-accent/30"
                        )}
                      >
                        <Zap className="h-3.5 w-3.5 fill-current" />
                      </div>

                      {/* Text Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={cn(
                              "font-semibold text-sm truncate",
                              isSelected ? "text-accent" : "text-text-primary"
                            )}
                          >
                            {c}
                          </span>
                          {isSelected && (
                            <span className="flex items-center gap-1 text-[10px] font-semibold text-accent bg-accent/10 px-1.5 py-0.5 rounded-full border border-accent/20 shrink-0">
                              <Check className="h-2.5 w-2.5" /> Actif
                            </span>
                          )}
                        </div>

                        {/* Description */}
                        <p className="text-[11px] text-text-tertiary/90 leading-relaxed mt-0.5 line-clamp-2">
                          {desc}
                        </p>
                      </div>
                    </motion.button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
