"use client";

import React, { useState, useRef, useEffect } from "react";
import { Zap, ChevronDown, Check, Search, Sparkles } from "lucide-react";
import { getCrewDescription } from "@/lib/utils";
import { Input } from "@/components/ui/input";

interface CrewSelectorProps {
  selectedCrew: string;
  availableCrews: string[];
  onSelectCrew?: (crewName: string) => void;
  disabled?: boolean;
}

export function CrewSelector({
  selectedCrew,
  availableCrews,
  onSelectCrew,
  disabled = false,
}: CrewSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      // Auto-focus search input
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
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

  const filteredCrews = availableCrews.filter((c) =>
    c.toLowerCase().includes(search.toLowerCase()) ||
    getCrewDescription(c).toLowerCase().includes(search.toLowerCase())
  );

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
        className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl border transition-all text-left group ${
          isOpen
            ? "bg-bg-tertiary border-accent/60 shadow-md ring-1 ring-accent/30"
            : "bg-bg-secondary/80 hover:bg-bg-tertiary border-border/80 hover:border-border"
        } ${disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
      >
        <div className="h-6 w-6 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shrink-0 group-hover:scale-105 transition-transform">
          <Zap className="h-3.5 w-3.5 fill-current" />
        </div>

        <span className="font-semibold text-base text-text-primary tracking-tight truncate max-w-[200px] sm:max-w-[280px]">
          {selectedCrew || "Sélectionnez un Crew"}
        </span>

        <ChevronDown
          className={`h-4 w-4 text-text-secondary transition-transform duration-200 shrink-0 ${
            isOpen ? "rotate-180 text-accent" : "group-hover:text-text-primary"
          }`}
        />
      </button>

      {/* Popover Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-[340px] sm:w-[420px] rounded-2xl bg-bg-secondary/95 backdrop-blur-xl border border-border shadow-2xl z-50 overflow-hidden animate-in fade-in-0 zoom-in-95 duration-150 origin-top-left flex flex-col">
          {/* Search Header */}
          <div className="p-3 border-b border-border/60 bg-bg-primary/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
              <Input
                ref={searchInputRef}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Rechercher un Crew par nom ou mission..."
                className="pl-9 h-9 text-xs bg-bg-secondary border-border/70 focus-visible:ring-accent"
              />
            </div>
          </div>

          {/* Crews List */}
          <div className="max-h-[360px] overflow-y-auto p-2 space-y-1.5">
            {filteredCrews.length === 0 ? (
              <div className="py-8 text-center text-xs text-text-secondary italic">
                Aucun Crew ne correspond à votre recherche.
              </div>
            ) : (
              filteredCrews.map((c) => {
                const isSelected = c === selectedCrew;
                const desc = getCrewDescription(c);

                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => handleSelect(c)}
                    className={`w-full text-left p-3 rounded-xl border transition-all flex items-start gap-3 group/item ${
                      isSelected
                        ? "bg-accent/15 border-accent/60 shadow-sm"
                        : "bg-bg-primary/40 hover:bg-bg-tertiary/70 border-border/40 hover:border-border"
                    }`}
                  >
                    {/* Icon container */}
                    <div
                      className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                        isSelected
                          ? "bg-accent text-white"
                          : "bg-bg-tertiary border border-border text-text-secondary group-hover/item:text-accent group-hover/item:border-accent/40"
                      }`}
                    >
                      <Zap className="h-4 w-4 fill-current" />
                    </div>

                    {/* Text Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`font-semibold text-sm truncate ${
                            isSelected ? "text-accent font-bold" : "text-text-primary"
                          }`}
                        >
                          {c}
                        </span>
                        {isSelected && (
                          <span className="flex items-center gap-1 text-[11px] font-semibold text-accent bg-accent/10 px-2 py-0.5 rounded-full border border-accent/20 shrink-0">
                            <Check className="h-3 w-3" /> Actif
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      <p className="text-xs text-text-secondary/90 leading-relaxed mt-1 line-clamp-2">
                        {desc}
                      </p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
