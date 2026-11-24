"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ChevronDown, Cpu, Globe, Terminal, Settings2, Check, Sliders } from "lucide-react";

/**
 * Props for the ModelPickerModal component.
 */
interface ModelPickerModalProps {
  /** The currently selected model identifier string. */
  currentModel: string;
  /** Complete list of available model identifiers, e.g. `["ollama/llama3", "openai/gpt-4"]`. */
  models: string[];
  /** Callback invoked when the user selects a model. Receives the chosen model string. */
  onSelect: (model: string) => void;
  /** Whether to show the "default crew configuration" option at the top of the picker. Defaults to `false`. */
  allowDefault?: boolean;
  /** Additional CSS classes applied to the trigger button element. */
  triggerClassName?: string;
}

/**
 * Props for the internal ModelList sub-component.
 */
interface ModelListProps {
  /** Display title for the model group, rendered as a section heading. */
  title: string;
  /** Icon element rendered next to the section title. */
  icon: React.ReactNode;
  /** Array of model identifiers belonging to this group. */
  list: string[];
  /** Current search filter text applied to the list. */
  search: string;
  /** The currently selected model, used to highlight the active item. */
  currentModel: string;
  /** Callback invoked when the user clicks a model. Receives the chosen model string. */
  onSelect: (model: string) => void;
  /** Callback invoked to close the parent dialog after a selection. */
  onOpenChange: (open: boolean) => void;
}

/**
 * Renders a grouped list of models with search filtering and selection highlighting.
 *
 * This is an internal sub-component used by `ModelPickerModal` to display
 * a single category of models (e.g. "Local Models (Ollama)", "Remote Models").
 *
 * @example
 * // Used internally by ModelPickerModal; not typically called directly.
 * <ModelList
 *   title="Modèles Locaux (Ollama)"
 *   icon={<Terminal className="h-3 w-3" />}
 *   list={["ollama/llama3", "ollama/mistral"]}
 *   search="llama"
 *   currentModel="ollama/llama3"
 *   onSelect={(m) => setSelected(m)}
 *   onOpenChange={(o) => setOpen(o)}
 * />
 */
function ModelList({ title, icon, list, search, currentModel, onSelect, onOpenChange }: ModelListProps) {
  const filtered = list.filter((m) => m.toLowerCase().includes(search.toLowerCase()));

  if (filtered.length === 0 && search === "") return null;

  return (
    <div className="space-y-2">
      <h4 className="text-[10px] font-semibold text-text-tertiary flex items-center gap-1.5 uppercase tracking-widest">
        <span className="text-accent">{icon}</span> {title} ({filtered.length})
      </h4>
      {filtered.length === 0 ? (
        <div className="text-[11px] text-text-tertiary italic">Aucun modèle trouvé.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          {filtered.map((m) => {
            const isSelected = currentModel === m;
            return (
              <button
                key={m}
                type="button"
                onClick={() => {
                  onSelect(m);
                  onOpenChange(false);
                }}
                className={`flex items-center justify-between text-left px-2.5 py-2 rounded-md border text-xs transition-all ${
                  isSelected
                    ? "bg-accent-subtle border-accent/40 text-accent font-medium"
                    : "bg-bg-secondary/50 border-border/60 text-text-primary hover:border-border hover:bg-bg-tertiary/50"
                }`}
              >
                <span className="truncate font-mono text-[11px]">
                  {m.replace(/^(ollama|openai|anthropic)\//, "")}
                </span>
                {isSelected && <Check className="h-3 w-3 text-accent shrink-0 ml-1.5" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * A modal dialog that lets the user browse and select an LLM model from a categorized list.
 *
 * Models are grouped into sections (Remote, Local/Ollama, Other) based on their
 * provider prefix (`openai/`, `ollama/`, `anthropic/`, or other). A search input
 * filters models within each section. The dialog is built on Radix UI's `Dialog`
 * component and uses the project's design tokens for theming.
 *
 * @example
 * // Basic usage — show the default crew configuration option and a custom trigger style.
 * <ModelPickerModal
 *   currentModel={selectedModel}
 *   models={availableModels}
 *   onSelect={setSelectedModel}
 *   allowDefault
 *   triggerClassName="w-48"
 * />
 *
 * @example
 * // Without the default option — useful when the UI already has a separate control for crew defaults.
 * <ModelPickerModal
 *   currentModel={selectedModel}
 *   models={availableModels}
 *   onSelect={setSelectedModel}
 * />
 */
export function ModelPickerModal({
  currentModel,
  models,
  onSelect,
  allowDefault = false,
  triggerClassName = "",
}: ModelPickerModalProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const ollamaModels = models.filter((m) => m.startsWith("ollama/"));
  const customModels = models.filter((m) => m.startsWith("openai/"));
  const otherModels = models.filter(
    (m) => !m.startsWith("ollama/") && !m.startsWith("openai/") && !m.startsWith("anthropic/")
  );

  const getDisplayLabel = () => {
    if (currentModel === "default" || !currentModel) {
      return "Défaut (configuré dans le Crew)";
    }
    return currentModel.replace(/^(ollama|openai|anthropic)\//, "");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        type="button"
        className={`w-full h-8 px-2.5 text-[11px] bg-bg-secondary/60 border border-border/60 rounded-md text-left flex items-center justify-between hover:border-accent/40 transition-colors truncate focus:outline-none focus:ring-1 focus:ring-accent/50 ${triggerClassName}`}
      >
        <span className="truncate flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-accent shrink-0" />
          <span className="truncate font-medium">{getDisplayLabel()}</span>
        </span>
        <ChevronDown size={12} className="opacity-40 shrink-0 ml-1" />
      </DialogTrigger>

      <DialogContent className="max-w-2xl bg-bg-primary border-border p-0 overflow-hidden flex flex-col text-text-primary gap-0 shadow-xl">
        <DialogHeader className="p-4 border-b border-border shrink-0">
          <DialogTitle className="text-sm flex items-center gap-2">
            <Cpu className="h-4 w-4 text-accent" />
            Sélectionner un modèle LLM
          </DialogTitle>
          <div className="mt-2">
            <Input
              placeholder="Rechercher un modèle..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-8 bg-bg-secondary/60 border-border/60 focus-visible:ring-accent/50 text-xs"
              autoFocus
            />
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-4 space-y-5 max-h-[60vh]">
          {allowDefault && (
            <div className="space-y-2">
              <h4 className="text-[10px] font-semibold text-text-tertiary flex items-center gap-1.5 uppercase tracking-widest">
                <Sliders className="h-3 w-3 text-accent" /> Configuration Standard
              </h4>
              <button
                type="button"
                onClick={() => {
                  onSelect("default");
                  setOpen(false);
                }}
                className={`flex items-center justify-between w-full text-left px-3 py-2.5 rounded-lg border text-xs transition-all ${
                  currentModel === "default" || !currentModel
                    ? "bg-accent-subtle border-accent/40 text-accent font-medium"
                    : "bg-bg-secondary/50 border-border/60 text-text-primary hover:border-border hover:bg-bg-tertiary/50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Settings2 className="h-3.5 w-3.5 text-accent" />
                  <div>
                    <div className="font-medium text-[11px]">Modèles configurés par défaut dans le Crew</div>
                    <div className="text-[10px] text-text-tertiary">
                      Chaque agent utilise son modèle spécifique défini dans le fichier YAML.
                    </div>
                  </div>
                </div>
                {(currentModel === "default" || !currentModel) && (
                  <span className="text-accent text-[10px] font-bold">Actif</span>
                )}
              </button>
            </div>
          )}

          {customModels.length > 0 && (
            <ModelList title="Serveur Distant (Custom API)" icon={<Globe className="h-3 w-3" />} list={customModels} search={search} currentModel={currentModel} onSelect={onSelect} onOpenChange={setOpen} />
          )}
          {ollamaModels.length > 0 && (
            <ModelList title="Modèles Locaux (Ollama)" icon={<Terminal className="h-3 w-3" />} list={ollamaModels} search={search} currentModel={currentModel} onSelect={onSelect} onOpenChange={setOpen} />
          )}
          {otherModels.length > 0 && (
            <ModelList title="Autres Fournisseurs" icon={<Cpu className="h-3 w-3" />} list={otherModels} search={search} currentModel={currentModel} onSelect={onSelect} onOpenChange={setOpen} />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
