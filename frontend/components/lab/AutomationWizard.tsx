"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  TEMPLATE_CATEGORIES,
  searchTemplates,
  buildMessageFromTemplate,
  type AutomationTemplate,
  type TemplateField,
} from "@/lib/registry/templates";
import {
  Sparkles,
  ArrowLeft,
  ArrowRight,
  Check,
  Search,
  Settings,
  Play,
  X,
  ChevronRight,
} from "lucide-react";

type WizardStep = "templates" | "configure" | "review";

interface WizardState {
  selectedTemplate: AutomationTemplate | null;
  inputs: Record<string, string>;
  step: WizardStep;
}

interface AutomationWizardProps {
  onLaunch: (params: {
    message: string;
    inputs: Record<string, unknown>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => void;
  availableModels?: string[];
  crewName?: string; // used for context in the wizard
  maxRpm?: number;
}

const STEPS = [
  { key: "templates" as const, label: "Template", num: 1 },
  { key: "configure" as const, label: "Configurer", num: 2 },
  { key: "review" as const, label: "Lancer", num: 3 },
];

export function AutomationWizard({
  onLaunch,
  availableModels = [],
  maxRpm = 15,
}: AutomationWizardProps) {
  const [state, setState] = useState<WizardState>({
    selectedTemplate: null,
    inputs: {},
    step: "templates",
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedModel, setSelectedModel] = useState("default");

  // Search templates
  const filteredTemplates = useMemo(() => {
    const results = searchTemplates(searchQuery);
    return activeCategory === "all"
      ? results
      : results.filter((t) => t.category === activeCategory);
  }, [searchQuery, activeCategory]);

  // Group templates by category for display
  const groupedTemplates = useMemo(() => {
    const groups: Record<string, AutomationTemplate[]> = {};
    filteredTemplates.forEach((t) => {
      if (!groups[t.category]) groups[t.category] = [];
      groups[t.category].push(t);
    });
    return groups;
  }, [filteredTemplates]);

  const handleSelectTemplate = (template: AutomationTemplate) => {
    setState((prev) => ({
      ...prev,
      selectedTemplate: template,
      inputs: {},
      step: "configure",
    }));
  };

  const handleInputChange = (key: string, value: string) => {
    setState((prev) => ({
      ...prev,
      inputs: { ...prev.inputs, [key]: value },
    }));
  };

  const handleBack = () => {
    if (state.step === "configure") {
      setState((prev) => ({ ...prev, step: "templates" }));
    } else if (state.step === "review") {
      setState((prev) => ({ ...prev, step: "configure" }));
    }
  };

  const handleNext = () => {
    if (state.step === "templates") {
      setState((prev) => ({ ...prev, step: "configure" }));
    } else if (state.step === "configure") {
      setState((prev) => ({ ...prev, step: "review" }));
    }
  };

  const handleLaunch = () => {
    if (!state.selectedTemplate) return;

    const message = buildMessageFromTemplate(state.selectedTemplate, state.inputs);
    const options = {
      llm_override: selectedModel !== "default" ? selectedModel : undefined,
      max_rpm: maxRpm,
    };

    onLaunch({
      message,
      inputs: state.inputs,
      options,
    });
  };

  const handleReset = () => {
    setState({
      selectedTemplate: null,
      inputs: {},
      step: "templates",
    });
    setSearchQuery("");
    setActiveCategory("all");
  };

  const currentStepIndex = STEPS.findIndex((s) => s.key === state.step);
  const isFirstStep = state.step === "templates";

  // ── Step 1: Template Selection ──────────────────────────────────────────
  const renderTemplateSelection = () => (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary" />
        <Input
          placeholder="Rechercher un template..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-bg-secondary/50 border-border/60 text-sm h-10"
        />
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setActiveCategory("all")}
          className={cn(
            "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
            activeCategory === "all"
              ? "bg-accent-subtle border border-accent/40 text-accent"
              : "bg-bg-tertiary/50 border border-border/60 text-text-tertiary hover:text-text-primary"
          )}
        >
          Tous
        </button>
        {Object.entries(TEMPLATE_CATEGORIES).map(([key, cat]) => (
          <button
            key={key}
            onClick={() => setActiveCategory(key)}
            className={cn(
              "px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5",
              activeCategory === key
                ? "bg-accent-subtle border border-accent/40 text-accent"
                : "bg-bg-tertiary/50 border border-border/60 text-text-tertiary hover:text-text-primary"
            )}
          >
            <cat.icon className="h-3 w-3" />
            {cat.name}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      <div className="space-y-6">
        {Object.entries(groupedTemplates).map(([category, templates]) => {
          const catInfo = TEMPLATE_CATEGORIES[category];
          if (!catInfo) return null;
          return (
            <div key={category}>
              <div className="flex items-center gap-2 mb-3">
                <catInfo.icon className={cn("h-4 w-4", catInfo.color)} />
                <h3 className="text-sm font-semibold text-text-primary">{catInfo.name}</h3>
                <Separator className="flex-1" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {templates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    onSelect={() => handleSelectTemplate(template)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // ── Step 2: Configuration ───────────────────────────────────────────────
  const renderConfiguration = () => {
    if (!state.selectedTemplate) return null;
    const { fields } = state.selectedTemplate;

    return (
      <div className="space-y-4">
        {/* Template Header */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-bg-secondary/50 border border-border/60">
          <state.selectedTemplate.icon className="h-5 w-5 text-accent" />
          <div className="flex-1">
            <h3 className="font-semibold text-sm text-text-primary">{state.selectedTemplate.name}</h3>
            <p className="text-xs text-text-tertiary">{state.selectedTemplate.description}</p>
          </div>
          <Badge variant="outline" className="text-[10px]">
            {state.selectedTemplate.complexity === "simple" ? "Simple" : state.selectedTemplate.complexity === "moderate" ? "Modéré" : "Avancé"}
          </Badge>
        </div>

        {/* Fields */}
        <div className="space-y-3">
          {fields.map((field) => (
            <FormField key={field.key} field={field} value={state.inputs[field.key] || ""} onChange={(v) => handleInputChange(field.key, v)} />
          ))}
        </div>

        {/* Advanced Options */}
        <div className="border-t border-border/50 pt-3">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full py-1 text-xs text-text-tertiary hover:text-text-primary transition-colors"
          >
            <span className="flex items-center gap-1.5 font-medium">
              <Settings className="h-3.5 w-3.5 text-accent" />
              Options avancées
            </span>
            {showAdvanced ? <ChevronRight className="h-3.5 w-3.5 rotate-90" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 bg-bg-secondary/40 p-3 rounded-lg border border-border/60">
              <div className="space-y-1.5">
                <label className="text-xs text-text-tertiary">Modèle LLM</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full h-8 px-2 text-xs bg-bg-elevated/80 border border-border/60 rounded-md"
                >
                  <option value="default">Par défaut</option>
                  {availableModels.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-text-tertiary">RPM</label>
                <input
                  type="number"
                  min={1}
                  max={60}
                  value={maxRpm}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    if (val >= 1 && val <= 60) {
                      // maxRpm is passed as prop; in a real app this would be lifted to state
                    }
                  }}
                  className="w-full h-8 px-2 text-xs bg-bg-elevated/80 border border-border/60 rounded-md"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ── Step 3: Review & Launch ─────────────────────────────────────────────
  const renderReview = () => {
    if (!state.selectedTemplate) return null;
    const message = buildMessageFromTemplate(state.selectedTemplate, state.inputs);

    return (
      <div className="space-y-4">
        {/* Summary */}
        <div className="p-4 rounded-lg bg-bg-secondary/50 border border-border/60 space-y-3">
          <div className="flex items-center gap-2">
            <state.selectedTemplate.icon className="h-5 w-5 text-accent" />
            <h3 className="font-semibold text-sm text-text-primary">{state.selectedTemplate.name}</h3>
          </div>

          <div>
            <span className="text-[10px] text-text-tertiary uppercase tracking-wider">Champs configurés</span>
            <div className="mt-1 space-y-1">
              {Object.entries(state.inputs).filter(([, v]) => v.trim()).map(([key, value]) => (
                <div key={key} className="text-xs">
                  <span className="text-text-tertiary">{key}: </span>
                  <span className="text-text-primary">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <span className="text-[10px] text-text-tertiary uppercase tracking-wider">Message envoyé</span>
            <pre className="mt-1 p-3 rounded-md bg-bg-primary text-xs text-text-secondary font-mono whitespace-pre-wrap border border-border/40 max-h-40 overflow-y-auto">
              {message}
            </pre>
          </div>
        </div>

        {/* Launch Button */}
        <Button
          onClick={handleLaunch}
          className="w-full bg-accent hover:bg-accent-hover text-white font-semibold shadow-sm gap-2 h-11"
        >
          <Play className="h-4 w-4 fill-current" />
          Lancer l&apos;automatisation
        </Button>
      </div>
    );
  };

  return (
    <div className="w-full h-full flex flex-col bg-bg-primary">
      {/* Progress Bar */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center gap-0">
          {STEPS.map((step, i) => (
            <div key={step.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold transition-all duration-200",
                  "shadow-sm",
                  i < currentStepIndex
                    ? "bg-accent text-white shadow-accent/20"
                    : i === currentStepIndex
                      ? "bg-accent/20 text-accent border border-accent/40"
                      : "bg-bg-tertiary text-text-tertiary border border-border/40"
                )}>
                  {i < currentStepIndex ? <Check className="h-3.5 w-3.5" /> : step.num}
                </div>
                <span className={cn(
                  "text-[10px] font-medium mt-1.5 hidden sm:block",
                  i <= currentStepIndex ? "text-text-primary" : "text-text-tertiary"
                )}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="flex-1 h-0.5 mx-2 rounded-full overflow-hidden bg-bg-tertiary">
                  <div className={cn(
                    "h-full rounded-full transition-all duration-500 ease-out",
                    i < currentStepIndex ? "gradient-accent" : "bg-transparent"
                  )} style={{ width: i < currentStepIndex ? "100%" : "0%" }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <AnimatePresence mode="wait">
          <motion.div
            key={state.step}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          >
            {state.step === "templates" && renderTemplateSelection()}
            {state.step === "configure" && renderConfiguration()}
            {state.step === "review" && renderReview()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer Navigation */}
      <div className="px-4 py-3 border-t border-border/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {!isFirstStep && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBack}
              className="text-xs gap-1 h-8 border-border/60"
            >
              <ArrowLeft className="h-3 w-3" />
              Retour
            </Button>
          )}
        </div>

        {state.step !== "review" && (
          <Button
            size="sm"
            onClick={handleNext}
            disabled={state.step === "templates" && !state.selectedTemplate}
            className="text-xs gap-1 h-8 bg-accent hover:bg-accent-hover text-white"
          >
            Suivant
            <ArrowRight className="h-3 w-3" />
          </Button>
        )}

        {state.step === "templates" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="text-xs text-text-tertiary h-8"
          >
            <X className="h-3 w-3" />
            Réinitialiser
          </Button>
        )}
      </div>
    </div>
  );
}

/* ── Template Card ───────────────────────────────────────────────────────── */

function TemplateCard({
  template,
  onSelect,
}: {
  template: AutomationTemplate;
  onSelect: () => void;
}) {
  return (
    <Card
      onClick={onSelect}
      className={cn(
        "cursor-pointer transition-all duration-200 hover:shadow-md hover:border-accent/30 group",
        "border-border/60 bg-bg-secondary/30"
      )}
    >
      <CardContent className="p-4 space-y-2.5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-accent-subtle border border-accent/20 flex items-center justify-center text-accent group-hover:bg-accent/20 transition-colors">
              <template.icon className="h-4.5 w-4.5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-text-primary group-hover:text-accent transition-colors">
                {template.name}
              </h4>
              <p className="text-[11px] text-text-tertiary leading-relaxed line-clamp-2">
                {template.description}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[9px] font-normal border-border/50 text-text-tertiary">
            {template.complexity === "simple" ? "Simple" : template.complexity === "moderate" ? "Modéré" : "Avancé"}
          </Badge>
          <span className="text-[9px] text-text-tertiary">{template.estimatedTime}</span>
        </div>

        <div className="flex flex-wrap gap-1">
          {template.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="px-1.5 py-0.5 bg-bg-tertiary/50 rounded text-[9px] text-text-tertiary">
              #{tag}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* ── Form Field Renderer ─────────────────────────────────────────────────── */

function FormField({
  field,
  value,
  onChange,
}: {
  field: TemplateField;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5 bg-bg-secondary/30 p-3 rounded-lg border border-border/50">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-medium text-text-secondary flex items-center gap-1.5">
          {field.label}
          {field.required && <span className="text-red-400">*</span>}
        </label>
        {field.description && (
          <span className="text-[10px] text-text-tertiary italic">{field.description}</span>
        )}
      </div>

      {field.type === "textarea" ? (
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className="min-h-[70px] bg-bg-elevated/60 border-border/50 text-xs resize-y"
        />
      ) : field.type === "path" ? (
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Input
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder={field.placeholder || "Ex: ../mon_projet"}
              className="pl-8 font-mono bg-bg-elevated/60 border-border/50 text-[11px] h-8"
            />
          </div>
        </div>
      ) : (
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className="bg-bg-elevated/60 border-border/50 text-xs"
        />
      )}

      {/* Presets */}
      {field.presets && field.presets.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
          <span className="text-[9px] text-text-tertiary flex items-center gap-0.5">
            <Sparkles className="h-2.5 w-2.5 text-accent" />
            Suggestions :
          </span>
          {field.presets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => onChange(preset.value)}
              className={cn(
                "text-[9px] px-1.5 py-0.5 rounded-md border transition-all",
                value === preset.value
                  ? "bg-accent-subtle border-accent/40 text-accent font-medium"
                  : "bg-bg-tertiary/50 border-border/60 hover:bg-bg-tertiary text-text-tertiary hover:text-text-primary"
              )}
            >
              {preset.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
