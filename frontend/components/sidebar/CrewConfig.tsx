"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings, Users, CheckSquare, Plus, Trash2, Pencil, Save, X, ChevronDown, ChevronRight, Zap } from "lucide-react";
import type { CrewDetail, AgentConfig, TaskConfig } from "@/lib/types";
import {
  updateCrewSettings,
  addAgent,
  updateAgent,
  deleteAgent,
  addTask,
  updateTask,
  deleteTask,
  listModels,
  listTools,
  listAllAgents,
} from "@/lib/api";

interface CrewConfigProps {
  crewDetail: CrewDetail;
  onUpdate?: (updated: CrewDetail) => void;
}

import { ModelPickerModal } from "@/components/chat/ModelPickerModal";

/* ── Inline Agent Editor ─────────────────────────────────────────────────── */

function AgentEditor({
  agent,
  models,
  availableTools,
  onSave,
  onCancel,
}: {
  agent?: AgentConfig;
  models: string[];
  availableTools: string[];
  onSave: (data: AgentConfig) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(agent?.name || "");
  const [role, setRole] = useState(agent?.role || "");
  const [goal, setGoal] = useState(agent?.goal || "");
  const [backstory, setBackstory] = useState(agent?.backstory || "");
  const [llm, setLlm] = useState(agent?.llm || "gemini/gemini-2.5-flash");
  const [tools, setTools] = useState<string[]>(agent?.tools || []);
  const [verbose, setVerbose] = useState(agent?.verbose ?? true);
  const [allowDelegation, setAllowDelegation] = useState(agent?.allow_delegation ?? false);
  const [toolSearch, setToolSearch] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ name, role, goal, backstory, llm, tools, verbose, allow_delegation: allowDelegation });
  };

  const toggleTool = (tool: string) => {
    setTools(prev => prev.includes(tool) ? prev.filter(t => t !== tool) : [...prev, tool]);
  };

  const filteredTools = availableTools.filter(t => t.toLowerCase().includes(toolSearch.toLowerCase()));

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-bg-primary/50 p-4 rounded-lg border border-accent/30 animate-in fade-in-0 slide-in-from-top-2 duration-200">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Nom</Label>
          <Input value={name} onChange={e => setName(e.target.value)} placeholder="analyste_senior" className="h-8 text-sm bg-bg-tertiary border-border" required />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Modèle LLM</Label>
          <ModelPickerModal currentModel={llm} models={models} onSelect={setLlm} />
        </div>
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Rôle</Label>
        <Input value={role} onChange={e => setRole(e.target.value)} placeholder="Analyste de données" className="h-8 text-sm bg-bg-tertiary border-border" required />
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Objectif (Goal)</Label>
        <Textarea value={goal} onChange={e => setGoal(e.target.value)} className="text-sm bg-bg-tertiary border-border min-h-[60px]" required />
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Backstory</Label>
        <Textarea value={backstory} onChange={e => setBackstory(e.target.value)} className="text-sm bg-bg-tertiary border-border min-h-[60px]" required />
      </div>

      {/* Tools */}
      {availableTools.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Outils</Label>
            <Input 
              placeholder="Rechercher un outil..." 
              value={toolSearch} 
              onChange={e => setToolSearch(e.target.value)} 
              className="h-6 text-[10px] w-32 bg-bg-tertiary border-border px-2"
            />
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1 bg-bg-tertiary/50 rounded-md border border-border/50">
            {filteredTools.map(tool => (
              <button
                key={tool}
                type="button"
                onClick={() => toggleTool(tool)}
                className={`px-2 py-0.5 rounded text-xs border transition-colors ${
                  tools.includes(tool)
                    ? "bg-accent/20 border-accent text-accent"
                    : "bg-bg-tertiary border-border text-text-secondary hover:border-text-secondary"
                }`}
              >
                {tool}
              </button>
            ))}
            {filteredTools.length === 0 && (
              <span className="text-xs text-text-secondary italic">Aucun outil trouvé</span>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center gap-4 text-xs">
        <label className="flex items-center gap-2">
          <Switch checked={verbose} onCheckedChange={setVerbose} className="scale-75" /> Verbose
        </label>
        <label className="flex items-center gap-2">
          <Switch checked={allowDelegation} onCheckedChange={setAllowDelegation} className="scale-75" /> Délégation
        </label>
      </div>

      <div className="flex gap-2 pt-1">
        <Button type="submit" size="sm" className="bg-accent hover:bg-accent-hover text-white text-xs h-7 gap-1">
          <Save size={12} /> Enregistrer
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onCancel} className="text-xs h-7 gap-1 border-border">
          <X size={12} /> Annuler
        </Button>
      </div>
    </form>
  );
}

/* ── Inline Task Editor ──────────────────────────────────────────────────── */

function TaskEditor({
  task,
  agentNames,
  onSave,
  onCancel,
}: {
  task?: TaskConfig;
  agentNames: string[];
  onSave: (data: TaskConfig) => void;
  onCancel: () => void;
}) {
  const [description, setDescription] = useState(task?.description || "");
  const [expectedOutput, setExpectedOutput] = useState(task?.expected_output || "");
  const [agent, setAgent] = useState(task?.agent || agentNames[0] || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ description, expected_output: expectedOutput, agent });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-bg-primary/50 p-4 rounded-lg border border-accent/30 animate-in fade-in-0 slide-in-from-top-2 duration-200">
      <div className="space-y-1">
        <Label className="text-xs">Agent assigné</Label>
        {agentNames.length > 0 ? (
          <Select value={agent} onValueChange={(val) => val && setAgent(val)}>
            <SelectTrigger className="h-8 text-sm bg-bg-tertiary border-border"><SelectValue /></SelectTrigger>
            <SelectContent>
              {agentNames.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
            </SelectContent>
          </Select>
        ) : (
          <Input value={agent} onChange={e => setAgent(e.target.value)} placeholder="nom_agent" className="h-8 text-sm bg-bg-tertiary border-border" required />
        )}
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Description</Label>
        <Textarea value={description} onChange={e => setDescription(e.target.value)} className="text-sm bg-bg-tertiary border-border min-h-[60px]" required />
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Résultat attendu</Label>
        <Textarea value={expectedOutput} onChange={e => setExpectedOutput(e.target.value)} className="text-sm bg-bg-tertiary border-border min-h-[60px]" required />
      </div>
      <div className="flex gap-2 pt-1">
        <Button type="submit" size="sm" className="bg-accent hover:bg-accent-hover text-white text-xs h-7 gap-1">
          <Save size={12} /> Enregistrer
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onCancel} className="text-xs h-7 gap-1 border-border">
          <X size={12} /> Annuler
        </Button>
      </div>
    </form>
  );
}

/* ── Main CrewConfig Component ───────────────────────────────────────────── */

export function CrewConfig({ crewDetail: initialDetail, onUpdate }: CrewConfigProps) {
  const [crew, setCrew] = useState(initialDetail);
  const [models, setModels] = useState<string[]>([]);
  const [availableTools, setAvailableTools] = useState<string[]>([]);
  const [allExistingAgents, setAllExistingAgents] = useState<AgentConfig[]>([]);
  const [open, setOpen] = useState(false);

  // Settings editing
  const [editingSettings, setEditingSettings] = useState(false);
  const [settingsProcess, setSettingsProcess] = useState(crew.crew_settings?.process || "Séquentiel");
  const [settingsMemory, setSettingsMemory] = useState(crew.crew_settings?.memory ?? true);
  const [settingsRpm, setSettingsRpm] = useState(crew.crew_settings?.max_rpm || 15);

  // Agent editing
  const [editingAgentIndex, setEditingAgentIndex] = useState<number | null>(null);
  const [addingAgent, setAddingAgent] = useState(false);

  // Task editing
  const [editingTaskIndex, setEditingTaskIndex] = useState<number | null>(null);
  const [addingTask, setAddingTask] = useState(false);

  // Section collapse
  const [sectionsOpen, setSectionsOpen] = useState({ settings: true, agents: true, tasks: true });

  useEffect(() => {
    setCrew(initialDetail);
    setSettingsProcess(initialDetail.crew_settings?.process || "Séquentiel");
    setSettingsMemory(initialDetail.crew_settings?.memory ?? true);
    setSettingsRpm(initialDetail.crew_settings?.max_rpm || 15);
  }, [initialDetail]);

  useEffect(() => {
    if (open) {
      listModels().then(setModels).catch(() => setModels(["gemini/gemini-2.5-flash", "gemini/gemini-1.5-pro"]));
      listTools().then(setAvailableTools).catch(() => setAvailableTools([]));
      listAllAgents().then(setAllExistingAgents).catch(() => setAllExistingAgents([]));
    }
  }, [open]);

  const refresh = (updated: CrewDetail) => {
    setCrew(updated);
    onUpdate?.(updated);
  };

  const toggleSection = (key: keyof typeof sectionsOpen) => {
    setSectionsOpen(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // ── Settings handlers ──
  const handleSaveSettings = async () => {
    try {
      const updated = await updateCrewSettings(crew.name, {
        process: settingsProcess as "Séquentiel" | "Hiérarchique",
        memory: settingsMemory,
        max_rpm: settingsRpm,
      });
      refresh(updated);
      setEditingSettings(false);
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  // ── Agent handlers ──
  const handleSaveAgent = async (data: AgentConfig, index?: number) => {
    try {
      let updated: CrewDetail;
      if (index !== undefined) {
        updated = await updateAgent(crew.name, index, data);
      } else {
        updated = await addAgent(crew.name, data);
      }
      refresh(updated);
      setEditingAgentIndex(null);
      setAddingAgent(false);
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  const handleDeleteAgent = async (index: number) => {
    if (!confirm(`Supprimer l'agent "${crew.agents[index]?.name}" ?`)) return;
    try {
      const updated = await deleteAgent(crew.name, index);
      refresh(updated);
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  // ── Task handlers ──
  const handleSaveTask = async (data: TaskConfig, index?: number) => {
    try {
      let updated: CrewDetail;
      if (index !== undefined) {
        updated = await updateTask(crew.name, index, data);
      } else {
        updated = await addTask(crew.name, data);
      }
      refresh(updated);
      setEditingTaskIndex(null);
      setAddingTask(false);
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  const handleDeleteTask = async (index: number) => {
    if (!confirm(`Supprimer la tâche ${index + 1} ?`)) return;
    try {
      const updated = await deleteTask(crew.name, index);
      refresh(updated);
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  const agentNames = crew.agents?.map(a => a.name) || [];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-transparent px-3 h-8 text-sm font-medium shadow-sm hover:bg-bg-tertiary transition-colors">
        <Settings size={16} />
        Configuration
      </DialogTrigger>
      <DialogContent className="max-w-[95vw] sm:max-w-[95vw] w-[95vw] sm:w-[1200px] h-[90vh] bg-bg-secondary border-border p-0 overflow-hidden flex flex-col text-text-primary gap-0">
        <DialogHeader className="p-6 border-b border-border shrink-0">
          <DialogTitle className="text-xl flex items-center gap-2">
            <Zap className="h-4 w-4 text-accent fill-current" /> {crew.name}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          {/* ── Global Settings ─────────────────────────────────────── */}
          <section className="border-b border-border">
            <button
              onClick={() => toggleSection("settings")}
              className="w-full flex items-center justify-between p-4 hover:bg-bg-tertiary/30 transition-colors"
            >
              <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary flex items-center gap-2">
                <Settings size={14} /> Paramètres Globaux
              </h3>
              {sectionsOpen.settings ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
            </button>

            {sectionsOpen.settings && (
              <div className="px-4 pb-4">
                {editingSettings ? (
                  <div className="space-y-3 bg-bg-primary/50 p-4 rounded-lg border border-accent/30">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Processus</Label>
                        <Select value={settingsProcess} onValueChange={(val) => val && setSettingsProcess(val as "Séquentiel" | "Hiérarchique")}>
                          <SelectTrigger className="h-8 text-sm bg-bg-tertiary border-border"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Séquentiel">Séquentiel</SelectItem>
                            <SelectItem value="Hiérarchique">Hiérarchique</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Limite RPM</Label>
                        <Input type="number" value={settingsRpm} onChange={e => setSettingsRpm(parseInt(e.target.value))} min={1} max={100} className="h-8 text-sm bg-bg-tertiary border-border" />
                      </div>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <Switch checked={settingsMemory} onCheckedChange={setSettingsMemory} /> Mémoire activée
                    </label>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={handleSaveSettings} className="bg-accent hover:bg-accent-hover text-white text-xs h-7 gap-1">
                        <Save size={12} /> Enregistrer
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => setEditingSettings(false)} className="text-xs h-7 gap-1 border-border">
                        <X size={12} /> Annuler
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="relative group">
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div className="bg-bg-tertiary p-3 rounded-lg border border-border">
                        <div className="text-text-secondary text-xs mb-1">Processus</div>
                        <div className="font-medium">{crew.crew_settings?.process || "Séquentiel"}</div>
                      </div>
                      <div className="bg-bg-tertiary p-3 rounded-lg border border-border">
                        <div className="text-text-secondary text-xs mb-1">Mémoire</div>
                        <div className="font-medium">{crew.crew_settings?.memory ? "Actif" : "Désactivé"}</div>
                      </div>
                      <div className="bg-bg-tertiary p-3 rounded-lg border border-border">
                        <div className="text-text-secondary text-xs mb-1">RPM</div>
                        <div className="font-medium">{crew.crew_settings?.max_rpm || 15}/min</div>
                      </div>
                    </div>
                    <button
                      onClick={() => setEditingSettings(true)}
                      className="absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 p-1.5 bg-bg-tertiary border border-border rounded-md hover:border-accent transition-all"
                      title="Modifier"
                    >
                      <Pencil size={12} className="text-text-secondary" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* ── Agents ───────────────────────────────────────────────── */}
          <section className="border-b border-border">
            <button
              onClick={() => toggleSection("agents")}
              className="w-full flex items-center justify-between p-4 hover:bg-bg-tertiary/30 transition-colors"
            >
              <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary flex items-center gap-2">
                <Users size={14} /> Agents ({crew.agents?.length || 0})
              </h3>
              {sectionsOpen.agents ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
            </button>

            {sectionsOpen.agents && (
              <div className="px-4 pb-4 space-y-3">
                {crew.agents?.map((agent, i) => (
                  <div key={i}>
                    {editingAgentIndex === i ? (
                      <AgentEditor
                        agent={agent}
                        models={models}
                        availableTools={availableTools}
                        onSave={(data) => handleSaveAgent(data, i)}
                        onCancel={() => setEditingAgentIndex(null)}
                      />
                    ) : (
                      <div className="group bg-bg-tertiary p-4 rounded-lg border border-border space-y-2 text-sm relative">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-semibold text-accent">{agent.role}</div>
                            <div className="text-text-secondary text-xs italic">"{agent.name}"</div>
                          </div>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => setEditingAgentIndex(i)} className="p-1.5 hover:bg-bg-primary rounded transition-colors" title="Modifier">
                              <Pencil size={12} className="text-text-secondary hover:text-accent" />
                            </button>
                            <button onClick={() => handleDeleteAgent(i)} className="p-1.5 hover:bg-bg-primary rounded transition-colors" title="Supprimer">
                              <Trash2 size={12} className="text-text-secondary hover:text-red-500" />
                            </button>
                          </div>
                        </div>
                        <div className="text-xs"><span className="text-text-secondary">LLM:</span> {agent.llm}</div>
                        <div className="text-text-secondary text-xs">{agent.goal}</div>
                        {agent.tools && agent.tools.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {agent.tools.map(t => (
                              <span key={t} className="px-2 py-0.5 bg-bg-primary border border-border rounded text-xs">{t}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {addingAgent ? (
                  <AgentEditor
                    models={models}
                    availableTools={availableTools}
                    onSave={(data) => handleSaveAgent(data)}
                    onCancel={() => setAddingAgent(false)}
                  />
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAddingAgent(true)}
                      className="flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border border-dashed border-border hover:border-accent hover:bg-bg-tertiary/30 text-text-secondary hover:text-accent text-sm transition-all"
                    >
                      <Plus size={14} /> Créer un agent
                    </button>
                    {allExistingAgents.length > 0 && (
                      <div className="flex-1">
                        <Select onValueChange={(val) => {
                          const ag = allExistingAgents.find(a => a.name === val);
                          if (ag) handleSaveAgent(ag);
                        }}>
                          <SelectTrigger className="w-full h-full flex items-center justify-center gap-2 p-3 rounded-lg border border-dashed border-border hover:border-accent hover:bg-bg-tertiary/30 text-text-secondary hover:text-accent text-sm transition-all bg-transparent shadow-none focus:ring-0">
                            <SelectValue placeholder="Importer un agent existant" />
                          </SelectTrigger>
                          <SelectContent>
                            {allExistingAgents.map(a => (
                              <SelectItem key={a.name} value={a.name}>{a.name} - {a.role}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>

          {/* ── Tasks ────────────────────────────────────────────────── */}
          <section>
            <button
              onClick={() => toggleSection("tasks")}
              className="w-full flex items-center justify-between p-4 hover:bg-bg-tertiary/30 transition-colors"
            >
              <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary flex items-center gap-2">
                <CheckSquare size={14} /> Tâches ({crew.tasks?.length || 0})
              </h3>
              {sectionsOpen.tasks ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
            </button>

            {sectionsOpen.tasks && (
              <div className="px-4 pb-4 space-y-3">
                {crew.tasks?.map((task, i) => (
                  <div key={i}>
                    {editingTaskIndex === i ? (
                      <TaskEditor
                        task={task}
                        agentNames={agentNames}
                        onSave={(data) => handleSaveTask(data, i)}
                        onCancel={() => setEditingTaskIndex(null)}
                      />
                    ) : (
                      <div className="group bg-bg-tertiary p-4 rounded-lg border border-border space-y-2 text-sm relative">
                        <div className="flex items-start justify-between">
                          <div className="font-semibold">Tâche {i + 1}</div>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => setEditingTaskIndex(i)} className="p-1.5 hover:bg-bg-primary rounded transition-colors" title="Modifier">
                              <Pencil size={12} className="text-text-secondary hover:text-accent" />
                            </button>
                            <button onClick={() => handleDeleteTask(i)} className="p-1.5 hover:bg-bg-primary rounded transition-colors" title="Supprimer">
                              <Trash2 size={12} className="text-text-secondary hover:text-red-500" />
                            </button>
                          </div>
                        </div>
                        <div className="text-text-secondary text-xs">Agent: <span className="text-accent">{task.agent}</span></div>
                        <div className="text-text-primary text-xs mt-1">{task.description}</div>
                        <div className="text-text-secondary text-xs mt-2 border-t border-border pt-2">
                          <span className="font-medium">Sortie :</span> {task.expected_output}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {addingTask ? (
                  <TaskEditor
                    agentNames={agentNames}
                    onSave={(data) => handleSaveTask(data)}
                    onCancel={() => setAddingTask(false)}
                  />
                ) : (
                  <button
                    onClick={() => setAddingTask(true)}
                    className="w-full flex items-center justify-center gap-2 p-3 rounded-lg border border-dashed border-border hover:border-accent hover:bg-bg-tertiary/30 text-text-secondary hover:text-accent text-sm transition-all"
                  >
                    <Plus size={14} /> Ajouter une tâche
                  </button>
                )}
              </div>
            )}
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
