"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ModelPickerModal } from "./ModelPickerModal";
import { FolderPickerModal } from "./FolderPickerModal";
import {
  Play,
  Settings2,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  Cpu,
  Target,
  FileText,
  FolderOpen,
} from "lucide-react";
import { getCrewDescription } from "@/lib/utils";
import { getWorkspaceProjects } from "@/lib/api";
import type { CrewDetail } from "@/lib/types";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

/** Extract all {variable} placeholders from a string. */
function extractTemplateVariables(text: string): string[] {
  const matches = text.match(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g) || [];
  return [...new Set(matches.map((m) => m.slice(1, -1)))];
}

/** Infer the best field type for a variable name. */
function inferFieldType(key: string): "text" | "textarea" | "path" | "pdf" {
  const lower = key.toLowerCase();
  if (lower.includes("pdf") || lower.includes("file") || lower.includes("document")) return "pdf";
  if (lower.includes("path") || lower.includes("dir") || lower.includes("output") || lower.includes("folder")) return "path";
  if (lower.includes("message") || lower.includes("prompt") || lower.includes("description")) return "textarea";
  return "text";
}

/** Human-readable label for a variable key. */
function fieldLabel(key: string): string {
  const labels: Record<string, string> = {
    pdf_path: "Fichier PDF d'entrée",
    output_dir: "Dossier de sortie",
    message: "Message / Paramètres de la mission",
    project_path: "Chemin du projet",
  };
  return labels[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Placeholder text for a variable key. */
function fieldPlaceholder(key: string): string {
  const placeholders: Record<string, string> = {
    pdf_path: "Ex: ../cours_python.pdf ou glissez un fichier ici",
    output_dir: "Ex: ./output/course_2024",
    message: "Décrivez l'objectif ou entrez les paramètres de démarrage pour ce Crew...",
    project_path: "Ex: ./mon_projet",
  };
  return placeholders[key] || `Entrez la valeur pour ${fieldLabel(key)}`;
}

/**
 * Parameters passed to the crew launch callback.
 *
 * @example
 * ```tsx
 * // Launch a crew with custom inputs and model override
 * onLaunch({
 *   message: "Analyser le fichier PDF et extraire les points clés",
 *   inputs: { pdf_path: "./data/report.pdf" },
 *   options: { llm_override: "openai/gpt-4o", max_rpm: 10 },
 * });
 * ```
 */
export interface LaunchParams {
  /** The synthesized message sent to the crew, combining field values. */
  message: string;
  /** Key-value pairs of field inputs collected from the form. */
  inputs: Record<string, unknown>;
  /** Optional runtime overrides for model and rate limiting. */
  options?: {
    /** Override the default LLM model (e.g. `"openai/gpt-4o"`). */
    llm_override?: string;
    /** Maximum requests per minute for the crew execution. */
    max_rpm?: number;
  };
}

/**
 * Props for the CrewLaunchPad component.
 *
 * @example
 * ```tsx
 * // Basic usage with a crew detail object
 * <CrewLaunchPad
 *   crewDetail={crew}
 *   crewName="Code Reviewer"
 *   onLaunch={handleLaunch}
 *   isStreaming={isStreaming}
 *   availableModels={["openai/gpt-4o", "anthropic/claude-3.5"]}
 * />
 * ```
 */
export interface CrewLaunchPadProps {
  /** Full crew configuration loaded from YAML. `null` when no crew is selected. */
  crewDetail: CrewDetail | null;
  /** Display name of the crew, shown in the header and launch button. */
  crewName: string;
  /** Callback invoked when the user clicks "Lancer". Receives {@link LaunchParams}. */
  onLaunch: (params: LaunchParams) => void;
  /** Whether a crew is currently streaming results. Disables the launch button. */
  isStreaming: boolean;
  /** List of available LLM model identifiers for the advanced options picker. */
  availableModels?: string[];
}

/**
 * A form-based panel that collects inputs and launches a CrewAI crew.
 *
 * Auto-detects template variables (`{variable}`) from the crew's task descriptions
 * and renders corresponding input fields. Supports path/PDF pickers, textareas,
 * and text inputs. Advanced options include LLM model override and RPM limit.
 *
 * @example
 * ```tsx
 * // Used inside a chat layout to let the user configure and launch a crew
 * <ChatWindow>
 *   <CrewLaunchPad
 *     crewDetail={selectedCrew}
 *     crewName="Data Analyst"
 *     onLaunch={(params) => startStreaming(params)}
 *     isStreaming={streaming}
 *   />
 * </ChatWindow>
 * ```
 *
 * @returns A card component with crew info, dynamic input fields, advanced options,
 *          and a launch button. Includes a folder picker modal for path-type fields.
 */
export function CrewLaunchPad({
  crewDetail,
  crewName,
  onLaunch,
  isStreaming,
  availableModels = [],
}: CrewLaunchPadProps) {
  const DEFAULT_MODEL = "default";
  const DEFAULT_MAX_RPM = 15;

  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>(DEFAULT_MODEL);
  const [maxRpm, setMaxRpm] = useState<number>(DEFAULT_MAX_RPM);

  // Dynamic folder picker state
  const [folderPickerOpen, setFolderPickerOpen] = useState(false);
  const [activeFolderFieldKey, setActiveFolderFieldKey] = useState<string | null>(null);
  // Load dynamically discovered projects on mount (reserved for future folder picker integration)
  useEffect(() => {
    getWorkspaceProjects()
      .catch(() => {});
  }, []);

  // Auto-detect template variables from crew task descriptions
  const fields = useMemo(() => {
    const allText = [
      crewDetail?.crew_settings?.process || "",
      ...(crewDetail?.agents?.map((a) => a.backstory || "") || []),
      ...(crewDetail?.tasks?.map((t) => t.description || "") || []),
    ].join("\n");

    const variables = extractTemplateVariables(allText);

    // Build fields from detected variables
    const detectedFields: { key: string; label: string; placeholder: string; type: "text" | "textarea" | "path" | "pdf"; required: boolean }[] =
      variables.map((key) => ({
        key,
        label: fieldLabel(key),
        placeholder: fieldPlaceholder(key),
        type: inferFieldType(key),
        required: true,
      }));

    // If no variables detected, fall back to a simple message field
    if (detectedFields.length === 0) {
      detectedFields.push({
        key: "message",
        label: "Message / Paramètres de la mission",
        placeholder: "Décrivez l'objectif ou entrez les paramètres de démarrage pour ce Crew...",
        type: "textarea",
        required: true,
      });
    }

    return detectedFields;
  }, [crewDetail]);

  const inputsWithDefaults = useMemo(() => ({ ...inputs }), [inputs]);

  const handleInputChange = (key: string, value: string) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const handleLaunch = () => {
    if (isStreaming) return;

    // Check required fields
    const missing = fields.filter((f) => f.required && !inputs[f.key]?.trim());
    if (missing.length > 0) {
      return; // Could show a toast — for now just prevent launch
    }

    const entries = Object.entries(inputs).filter(([, v]) => v && v.trim());
    const synthesizedMessage = entries.length > 0
      ? entries.map(([k, v]) => k + ": " + v.trim()).join("\n")
      : `Lancement de ${crewName}`;

    const options = {
      llm_override: selectedModel !== DEFAULT_MODEL ? selectedModel : undefined,
      max_rpm: maxRpm,
    };

    onLaunch({
      message: synthesizedMessage,
      inputs: inputsWithDefaults,
      options,
    });
  };

  return (
    <div className="w-full mx-auto py-4 px-3 flex flex-col gap-4 animate-in fade-in duration-300">
      {/* Header Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="border-border bg-bg-elevated shadow-sm hover:shadow-md transition-shadow duration-200">
          <CardHeader className="pb-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <motion.div
                  className="h-11 w-11 rounded-xl bg-accent-subtle border border-accent/20 flex items-center justify-center text-accent"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Sparkles className="h-5 w-5" />
                </motion.div>
                <div>
                  <CardTitle className="text-xl font-bold flex items-center gap-2 text-text-primary">
                    {crewName}
                    <Badge variant="outline" className="text-[10px] font-medium border-accent/30 text-accent bg-accent-subtle">
                      {typeof crewDetail?.crew_settings?.process === "string" ? crewDetail.crew_settings.process : "Séquentiel"}
                    </Badge>
                  </CardTitle>
                  <CardDescription className="text-text-tertiary text-xs mt-0.5">
                    {crewDetail?.agents.length || 0} agent(s) • {crewDetail?.tasks.length || 0} étape(s)
                  </CardDescription>
                </div>
              </div>
            </div>

            {/* Short Crew Mission Description */}
            <div className="mt-3 p-3 rounded-xl bg-bg-secondary/50 border border-border/60 text-xs text-text-primary leading-relaxed flex items-start gap-2.5">
              <Target className="h-3.5 w-3.5 text-accent shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-text-tertiary uppercase text-[9px] tracking-widest block mb-0.5">
                  Mission
                </span>
                <p className="text-text-primary/90 leading-relaxed">
                  {getCrewDescription(crewName, crewDetail ?? undefined)}
                </p>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 pt-2">
            {/* Message Input */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-semibold text-text-primary flex items-center gap-1.5 uppercase tracking-wider">
                  <Layers className="h-3.5 w-3.5 text-accent" />
                  Paramètres
                </Label>
              </div>

              {fields.map((field) => {
                const isPath = field.type === "path" || field.type === "pdf";
                return (
                  <div key={field.key} className="space-y-1.5 bg-bg-secondary/50 p-3 rounded-xl border border-border/60">
                    <Label htmlFor={field.key} className="text-[11px] font-medium text-text-secondary flex items-center gap-1.5">
                      {field.type === "pdf" && <FileText className="h-3 w-3 text-red-400" />}
                      {field.type === "path" && <FolderOpen className="h-3 w-3 text-accent" />}
                      {field.type === "textarea" && <FileText className="h-3 w-3 text-text-secondary" />}
                      {field.label}
                      {field.required && <span className="text-red-400">*</span>}
                    </Label>

                    {isPath ? (
                      <div className="flex gap-2">
                        <Input
                          id={field.key}
                          value={inputs[field.key] || ""}
                          onChange={(e) => handleInputChange(field.key, e.target.value)}
                          placeholder={field.placeholder}
                          className="flex-1 bg-bg-elevated/80 border-border/60 focus-visible:ring-accent/50 text-xs h-9"
                          readOnly
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-9 text-[11px] gap-1 bg-bg-elevated/50"
                          onClick={() => {
                            setActiveFolderFieldKey(field.key);
                            setFolderPickerOpen(true);
                          }}
                        >
                          <FolderOpen className="h-3.5 w-3.5" />
                          Parcourir
                        </Button>
                      </div>
                    ) : (
                      <Textarea
                        id={field.key}
                        value={inputs[field.key] || ""}
                        onChange={(e) => handleInputChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="min-h-[60px] bg-bg-elevated/80 border-border/60 focus-visible:ring-accent/50 text-xs resize-y"
                      />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Advanced Options */}
            <div className="border-t border-border/50 pt-3">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center justify-between w-full py-1 text-[11px] text-text-tertiary hover:text-text-primary transition-colors"
              >
                <span className="flex items-center gap-1.5 font-medium">
                  <Settings2 className="h-3.5 w-3.5 text-accent" />
                  Options avancées
                </span>
                {showAdvanced ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </button>

              <AnimatePresence initial={false}>
                {showAdvanced && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 bg-bg-secondary/40 p-3 rounded-xl border border-border/60">
                      <div className="space-y-1.5">
                        <Label className="text-[11px] text-text-tertiary flex items-center gap-1.5">
                          <Cpu className="h-3.5 w-3.5 text-accent" />
                          Surcharge du Modèle LLM
                        </Label>
                        <ModelPickerModal
                          currentModel={selectedModel}
                          models={availableModels}
                          onSelect={setSelectedModel}
                          allowDefault={true}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-[11px] text-text-tertiary flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5 text-accent" />
                          Requêtes max / minute (RPM)
                        </Label>
                        <Input
                          type="number"
                          min={1}
                          max={60}
                          value={maxRpm}
                          onChange={(e) => setMaxRpm(parseInt(e.target.value) || 15)}
                          className="bg-bg-elevated/80 border-border/60 text-[11px]"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Launch Action */}
            <div className="pt-1 flex items-center justify-end gap-3">
              <Button
                size="lg"
                onClick={handleLaunch}
                disabled={isStreaming}
                className={cn(
                  "w-full sm:w-auto min-w-[200px] text-white font-semibold shadow-sm transition-all gap-2 h-10 px-5 rounded-xl",
                  "gradient-accent hover:shadow-md hover:opacity-90",
                  isStreaming && "opacity-50 cursor-not-allowed"
                )}
              >
                <Play className="h-4 w-4 fill-current" />
                Lancer {crewName}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <FolderPickerModal
        isOpen={folderPickerOpen}
        onClose={() => {
          setFolderPickerOpen(false);
          setActiveFolderFieldKey(null);
        }}
        onSelect={(selectedPath) => {
          if (activeFolderFieldKey) {
            handleInputChange(activeFolderFieldKey, selectedPath);
          }
        }}
        currentValue={activeFolderFieldKey ? inputs[activeFolderFieldKey] : "."}
        title="Sélectionner le dossier cible du projet"
      />
    </div>
  );
}
