"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ChevronDown, Cpu, Globe, Terminal, Cloud, Settings2, Check, Sliders } from "lucide-react";

interface ModelPickerModalProps {
  currentModel: string;
  models: string[];
  onSelect: (model: string) => void;
  allowDefault?: boolean;
  triggerClassName?: string;
}

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
  const geminiModels = models.filter((m) => m.startsWith("gemini/"));
  const customModels = models.filter((m) => m.startsWith("openai/"));
  const otherModels = models.filter(
    (m) => !m.startsWith("ollama/") && !m.startsWith("gemini/") && !m.startsWith("openai/")
  );

  const filterModels = (list: string[]) =>
    list.filter((m) => m.toLowerCase().includes(search.toLowerCase()));

  const filteredOllama = filterModels(ollamaModels);
  const filteredGemini = filterModels(geminiModels);
  const filteredCustom = filterModels(customModels);
  const filteredOther = filterModels(otherModels);

  const ModelList = ({
    title,
    icon,
    list,
  }: {
    title: string;
    icon: React.ReactNode;
    list: string[];
  }) => {
    if (list.length === 0 && search === "") return null;
    return (
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-text-secondary flex items-center gap-2 uppercase tracking-wider">
          <span className="text-accent">{icon}</span> {title} ({list.length})
        </h4>
        {list.length === 0 ? (
          <div className="text-xs text-text-secondary italic">Aucun modèle trouvé.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {list.map((m) => {
              const isSelected = currentModel === m;
              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => {
                    onSelect(m);
                    setOpen(false);
                  }}
                  className={`flex items-center justify-between text-left px-3 py-2.5 rounded-lg border text-sm transition-all ${
                    isSelected
                      ? "bg-accent/15 border-accent text-accent font-medium shadow-sm"
                      : "bg-bg-primary/70 border-border text-text-primary hover:border-text-secondary hover:bg-bg-tertiary/40"
                  }`}
                >
                  <span className="truncate w-full font-mono text-xs">
                    {m.replace(/^(ollama|gemini|openai)\//, "")}
                  </span>
                  {isSelected && <Check className="h-3.5 w-3.5 text-accent shrink-0 ml-1.5" />}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const getDisplayLabel = () => {
    if (currentModel === "default" || !currentModel) {
      return "Modèles définis dans le Crew (Défaut)";
    }
    return currentModel.replace(/^(ollama|gemini|openai)\//, "");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        type="button"
        className={`w-full h-9 px-3 text-sm bg-bg-secondary/80 border border-border/80 rounded-lg text-left flex items-center justify-between hover:border-accent/60 transition-colors truncate focus:outline-none focus:ring-1 focus:ring-accent ${triggerClassName}`}
      >
        <span className="truncate flex items-center gap-2">
          <Cpu className="h-4 w-4 text-accent shrink-0" />
          <span className="truncate font-medium">{getDisplayLabel()}</span>
        </span>
        <ChevronDown size={14} className="opacity-50 shrink-0 ml-2" />
      </DialogTrigger>

      <DialogContent className="max-w-2xl bg-bg-secondary border-border p-0 overflow-hidden flex flex-col text-text-primary gap-0 shadow-2xl">
        <DialogHeader className="p-4 border-b border-border shrink-0 bg-bg-primary">
          <DialogTitle className="text-lg flex items-center gap-2">
            <Cpu className="h-5 w-5 text-accent" />
            Sélectionner un modèle LLM
          </DialogTitle>
          <div className="mt-2">
            <Input
              placeholder="Rechercher un modèle (ex: qwen, gemini, llama, mistral)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 bg-bg-tertiary border-border focus-visible:ring-accent"
              autoFocus
            />
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-4 space-y-6 max-h-[60vh]">
          {allowDefault && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-text-secondary flex items-center gap-2 uppercase tracking-wider">
                <Sliders className="h-3.5 w-3.5 text-accent" /> Configuration Standard
              </h4>
              <button
                type="button"
                onClick={() => {
                  onSelect("default");
                  setOpen(false);
                }}
                className={`flex items-center justify-between w-full text-left px-3.5 py-2.5 rounded-lg border text-sm transition-all ${
                  currentModel === "default" || !currentModel
                    ? "bg-accent/15 border-accent text-accent font-medium shadow-sm"
                    : "bg-bg-primary/70 border-border text-text-primary hover:border-text-secondary hover:bg-bg-tertiary/40"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Settings2 className="h-4 w-4 text-accent" />
                  <div>
                    <div className="font-semibold text-xs">Modèles configurés par défaut dans le Crew</div>
                    <div className="text-[11px] text-text-secondary">
                      Chaque agent utilise son modèle spécifique défini dans le fichier YAML.
                    </div>
                  </div>
                </div>
                {(currentModel === "default" || !currentModel) && (
                  <span className="text-accent text-xs font-bold">Actif</span>
                )}
              </button>
            </div>
          )}

          {filteredCustom.length > 0 && (
            <ModelList title="Serveur Distant (Custom API)" icon={<Globe className="h-3.5 w-3.5" />} list={filteredCustom} />
          )}
          {filteredOllama.length > 0 && (
            <ModelList title="Modèles Locaux (Ollama)" icon={<Terminal className="h-3.5 w-3.5" />} list={filteredOllama} />
          )}
          {filteredGemini.length > 0 && (
            <ModelList title="Google Gemini (Cloud)" icon={<Cloud className="h-3.5 w-3.5" />} list={filteredGemini} />
          )}
          {filteredOther.length > 0 && (
            <ModelList title="Autres Fournisseurs" icon={<Cpu className="h-3.5 w-3.5" />} list={filteredOther} />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
