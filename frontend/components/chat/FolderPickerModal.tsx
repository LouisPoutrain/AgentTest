"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Folder,
  FolderOpen,
  Search,
  Check,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  GitBranch,
  History,
  HardDrive,
  RefreshCw,
  FlaskConical
} from "lucide-react";
import { getWorkspaceProjects, browseWorkspaceDirectory } from "@/lib/api";
import type { ProjectInfo, BrowseResponse } from "@/lib/types";

interface FolderPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
  currentValue?: string;
  title?: string;
}

export function FolderPickerModal({
  isOpen,
  onClose,
  onSelect,
  currentValue = ".",
  title = "Sélectionner un projet ou un dossier",
}: FolderPickerModalProps) {
  const [activeTab, setActiveTab] = useState<"projects" | "browse" | "recents">("projects");
  const [searchQuery, setSearchQuery] = useState("");
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  // Browse state
  const [browsePath, setBrowsePath] = useState(currentValue || ".");
  const [browseData, setBrowseData] = useState<BrowseResponse | null>(null);
  const [loadingBrowse, setLoadingBrowse] = useState(false);
  const [browseError, setBrowseError] = useState<string | null>(null);

  // Selected path preview
  const [selectedPath, setSelectedPath] = useState(currentValue || ".");
  const [recents, setRecents] = useState<string[]>([]);

  // Load recents from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("agenttest_recent_folders");
      if (stored) {
        setRecents(JSON.parse(stored));
      }
    } catch {
      // Ignore
    }
  }, []);

  const saveRecent = (path: string) => {
    try {
      const updated = [path, ...recents.filter((p) => p !== path)].slice(0, 8);
      setRecents(updated);
      localStorage.setItem("agenttest_recent_folders", JSON.stringify(updated));
    } catch {
      // Ignore
    }
  };

  // Fetch projects on open
  useEffect(() => {
    if (isOpen) {
      setSelectedPath(currentValue || ".");
      setBrowsePath(currentValue || ".");
      loadProjects();
    }
  }, [isOpen, currentValue]);

  const loadProjects = async () => {
    setLoadingProjects(true);
    try {
      const list = await getWorkspaceProjects();
      setProjects(list);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoadingProjects(false);
    }
  };

  // Load browse directory data
  useEffect(() => {
    if (isOpen && activeTab === "browse") {
      loadBrowse(browsePath);
    }
  }, [isOpen, activeTab, browsePath]);

  const loadBrowse = async (path: string) => {
    setLoadingBrowse(true);
    setBrowseError(null);
    try {
      const data = await browseWorkspaceDirectory(path);
      setBrowseData(data);
    } catch (err: any) {
      setBrowseError(err.message || "Erreur de lecture du dossier");
    } finally {
      setLoadingBrowse(false);
    }
  };

  const filteredProjects = useMemo(() => {
    if (!searchQuery.trim()) return projects;
    const q = searchQuery.toLowerCase().trim();
    return projects.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.path.toLowerCase().includes(q) ||
        p.framework.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [projects, searchQuery]);

  const handleConfirm = (pathToUse?: string) => {
    const finalPath = pathToUse || selectedPath;
    if (finalPath) {
      saveRecent(finalPath);
      onSelect(finalPath);
      onClose();
    }
  };

  const getFrameworkColor = (fw: string) => {
    const lower = fw.toLowerCase();
    if (lower.includes("next")) return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    if (lower.includes("fastapi")) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    if (lower.includes("python")) return "bg-green-500/10 text-green-400 border-green-500/30";
    if (lower.includes("react")) return "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
    if (lower.includes("node")) return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    return "bg-slate-500/10 text-slate-400 border-slate-500/30";
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] flex flex-col p-0 gap-0 overflow-hidden bg-bg-secondary border-border/80 shadow-2xl">
        {/* Header */}
        <DialogHeader className="p-5 pb-3 border-b border-border/60 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shadow-inner">
                <FolderOpen className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle className="text-lg font-bold text-text-primary flex items-center gap-2">
                  {title}
                </DialogTitle>
                <DialogDescription className="text-xs text-text-secondary">
                  Sélectionnez un projet détecté ou naviguez librement dans l'arborescence
                </DialogDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={loadProjects}
              className="h-8 text-xs text-text-secondary hover:text-text-primary gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingProjects ? "animate-spin" : ""}`} />
              Actualiser
            </Button>
          </div>

          {/* Navigation Tabs */}
          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as any)}
            className="w-full mt-3"
          >
            <TabsList className="grid grid-cols-3 w-full bg-bg-tertiary/70 border border-border/50">
              <TabsTrigger value="projects" className="gap-2 text-xs">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                Projets Détectés ({projects.length})
              </TabsTrigger>
              <TabsTrigger value="browse" className="gap-2 text-xs">
                <Folder className="h-3.5 w-3.5 text-blue-400" />
                Explorateur de dossiers
              </TabsTrigger>
              <TabsTrigger value="recents" className="gap-2 text-xs">
                <History className="h-3.5 w-3.5 text-amber-400" />
                Raccourcis & Récents
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </DialogHeader>

        {/* Content Body */}
        <div className="flex-1 min-h-0 p-5 pt-3 overflow-hidden">
          {/* TAB 1: PROJETS DÉTECTÉS */}
          {activeTab === "projects" && (
            <div className="flex flex-col h-full gap-3">
              {/* Search Bar */}
              <div className="relative shrink-0">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-secondary/60" />
                <Input
                  placeholder="Rechercher un projet par nom, stack ou tag (ex: mon_projet, Next.js, Prisma)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 bg-bg-tertiary/60 border-border/60 text-xs h-9"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-2.5 top-2.5 text-xs text-text-secondary hover:text-text-primary"
                  >
                    Effacer
                  </button>
                )}
              </div>

              {/* Projects Grid Container with native smooth scrolling */}
              <div className="flex-1 overflow-y-auto max-h-[420px] pr-2 space-y-2.5">
                {loadingProjects ? (
                  <div className="flex flex-col items-center justify-center h-48 text-text-secondary gap-2">
                    <RefreshCw className="h-6 w-6 animate-spin text-accent" />
                    <span className="text-xs">Scan des projets locaux en cours...</span>
                  </div>
                ) : filteredProjects.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-48 text-text-secondary gap-2 border border-dashed border-border/60 rounded-xl p-6">
                    <Folder className="h-8 w-8 text-text-secondary/40" />
                    <span className="text-sm font-medium">Aucun projet correspondant</span>
                    <span className="text-xs text-center text-text-secondary/80">
                      Essayez un autre mot-clé ou basculez vers l'onglet "Explorateur de dossiers".
                    </span>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pb-2">
                    {filteredProjects.map((proj) => {
                      const isSelected = selectedPath === proj.path;
                      return (
                        <div
                          key={proj.path}
                          onClick={() => {
                            setSelectedPath(proj.path);
                          }}
                          onDoubleClick={() => handleConfirm(proj.path)}
                          className={`group relative flex flex-col justify-between p-3.5 rounded-xl border transition-all cursor-pointer text-left ${
                            isSelected
                              ? "bg-accent/10 border-accent shadow-md shadow-accent/5"
                              : "bg-bg-tertiary/40 hover:bg-bg-tertiary/80 border-border/50 hover:border-border"
                          }`}
                        >
                          <div>
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2 min-w-0">
                                <div className={`p-1.5 rounded-lg ${isSelected ? "bg-accent/20 text-accent" : "bg-bg-primary text-text-secondary"}`}>
                                  {proj.is_current ? (
                                    <HardDrive className="h-4 w-4" />
                                  ) : (
                                    <Folder className="h-4 w-4" />
                                  )}
                                </div>
                                <span className="font-semibold text-sm text-text-primary truncate">
                                  {proj.name}
                                </span>
                              </div>
                              <Badge
                                variant="outline"
                                className={`text-[10px] px-1.5 py-0 shrink-0 font-medium ${getFrameworkColor(proj.framework)}`}
                              >
                                {proj.framework}
                              </Badge>
                            </div>

                            {/* Path */}
                            <div className="mt-2 text-xs font-mono text-text-secondary/80 bg-bg-primary/50 px-2 py-1 rounded border border-border/40 truncate">
                              {proj.path}
                            </div>

                            {/* Tags */}
                            <div className="flex flex-wrap gap-1 mt-2.5">
                              {proj.tags.slice(0, 4).map((tag) => (
                                <Badge
                                  key={tag}
                                  variant="secondary"
                                  className="text-[9px] px-1.5 py-0 bg-bg-secondary border border-border/40 text-text-secondary font-normal"
                                >
                                  {tag}
                                </Badge>
                              ))}
                              {proj.has_git && (
                                <span className="inline-flex items-center text-[9px] text-text-secondary/70 gap-0.5 ml-1">
                                  <GitBranch className="h-2.5 w-2.5" /> git
                                </span>
                              )}
                              {proj.has_tests && (
                                <span className="inline-flex items-center text-[9px] text-emerald-400/90 gap-0.5 ml-1">
                                  <FlaskConical className="h-2.5 w-2.5" /> tests
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="mt-3 pt-2 border-t border-border/30 flex items-center justify-between text-xs">
                            <span className="text-[10px] text-text-secondary/60">
                              Double-clic pour valider
                            </span>
                            <Button
                              size="sm"
                              variant={isSelected ? "default" : "secondary"}
                              className={`h-6 text-[11px] px-2.5 ${isSelected ? "bg-accent hover:bg-accent/90 text-white" : ""}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleConfirm(proj.path);
                              }}
                            >
                              {isSelected ? "Sélectionné" : "Choisir"}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: EXPLORATEUR INTERACTIF */}
          {activeTab === "browse" && (
            <div className="flex flex-col h-full gap-3">
              {/* Breadcrumb Navigation Bar */}
              <div className="flex items-center gap-1.5 p-2 rounded-lg bg-bg-tertiary/70 border border-border/60 overflow-x-auto text-xs shrink-0">
                {browseData?.parent_path && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 shrink-0 text-text-secondary hover:text-text-primary"
                    title="Dossier parent"
                    onClick={() => {
                      if (browseData.parent_path) {
                        setBrowsePath(browseData.parent_path);
                        setSelectedPath(browseData.parent_path);
                      }
                    }}
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                  </Button>
                )}

                <div className="flex items-center gap-1 flex-1 font-mono text-xs overflow-x-auto py-0.5">
                  {browseData?.breadcrumbs.map((b, idx) => (
                    <React.Fragment key={idx}>
                      {idx > 0 && <ChevronRight className="h-3 w-3 text-text-secondary/40 shrink-0" />}
                      <button
                        onClick={() => {
                          setBrowsePath(b.path);
                          setSelectedPath(b.path);
                        }}
                        className={`hover:bg-bg-secondary px-1.5 py-0.5 rounded transition-colors whitespace-nowrap ${
                          idx === browseData.breadcrumbs.length - 1
                            ? "font-bold text-accent"
                            : "text-text-secondary hover:text-text-primary"
                        }`}
                      >
                        {b.name}
                      </button>
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Directory Listing with native scrolling */}
              <div className="flex-1 overflow-y-auto max-h-[400px] border border-border/50 rounded-xl bg-bg-tertiary/30 p-2 pr-3">
                {loadingBrowse ? (
                  <div className="flex flex-col items-center justify-center h-48 text-text-secondary gap-2">
                    <RefreshCw className="h-5 w-5 animate-spin text-accent" />
                    <span className="text-xs">Chargement du dossier...</span>
                  </div>
                ) : browseError ? (
                  <div className="flex flex-col items-center justify-center h-48 text-destructive gap-2 p-4 text-center">
                    <span className="text-sm font-semibold">Impossible de charger le dossier</span>
                    <span className="text-xs text-text-secondary">{browseError}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2 text-xs"
                      onClick={() => {
                        setBrowsePath(".");
                        setSelectedPath(".");
                      }}
                    >
                      Revenir à la racine (.)
                    </Button>
                  </div>
                ) : browseData?.directories.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-40 text-text-secondary gap-2 text-center p-4">
                    <Folder className="h-6 w-6 text-text-secondary/40" />
                    <span className="text-xs">Aucun sous-dossier dans ce répertoire</span>
                    <span className="text-[11px] text-text-secondary/70">
                      ({browseData.files_count} fichier(s) présent(s))
                    </span>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {browseData?.directories.map((dir) => {
                      const isSelected = selectedPath === dir.path;
                      return (
                        <div
                          key={dir.path}
                          className={`flex items-center justify-between p-2 rounded-lg transition-all cursor-pointer group ${
                            isSelected
                              ? "bg-accent/15 border border-accent text-accent"
                              : "hover:bg-bg-tertiary border border-transparent text-text-primary"
                          }`}
                          onClick={() => {
                            setSelectedPath(dir.path);
                          }}
                          onDoubleClick={() => {
                            setBrowsePath(dir.path);
                            setSelectedPath(dir.path);
                          }}
                        >
                          <div className="flex items-center gap-2.5 min-w-0 flex-1">
                            <Folder className={`h-4 w-4 shrink-0 ${isSelected ? "text-accent" : "text-blue-400"}`} />
                            <span className="font-medium text-xs font-mono truncate">{dir.name}</span>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {dir.has_subdirs && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 px-2 text-[10px] text-text-secondary hover:text-text-primary gap-1"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setBrowsePath(dir.path);
                                  setSelectedPath(dir.path);
                                }}
                              >
                                Ouvrir <ChevronRight className="h-3 w-3" />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant={isSelected ? "default" : "secondary"}
                              className={`h-6 text-[11px] px-2 ${isSelected ? "bg-accent text-white" : ""}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleConfirm(dir.path);
                              }}
                            >
                              Choisir
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: RACCOURCIS & RÉCENTS */}
          {activeTab === "recents" && (
            <div className="flex flex-col h-full max-h-[440px] overflow-y-auto pr-2 gap-4">
              <div>
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Raccourcis Standards
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                  {[
                    { label: "AgentTest - Racine (.)", path: ".", desc: "Projet courant complet" },
                    { label: "Frontend Next.js (./frontend)", path: "./frontend", desc: "Application UI & Pages" },
                    { label: "Backend FastAPI (./backend)", path: "./backend", desc: "API Python & Orchestrateur" },
                    { label: "mon_projetw (../mon_projet)", path: "../mon_projet", desc: "Projet mon_projetw généré" },
                  ].map((short) => (
                    <div
                      key={short.path}
                      onClick={() => handleConfirm(short.path)}
                      className="p-3 rounded-xl border border-border/50 bg-bg-tertiary/40 hover:bg-accent/10 hover:border-accent/50 cursor-pointer transition-all flex flex-col justify-between group"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <Folder className="h-4 w-4 text-accent" />
                          <span className="font-semibold text-xs text-text-primary">{short.label}</span>
                        </div>
                        <span className="text-[11px] text-text-secondary mt-1 block">{short.desc}</span>
                      </div>
                      <div className="mt-2 text-[10px] font-mono text-accent bg-accent/5 px-2 py-0.5 rounded border border-accent/20 w-fit">
                        {short.path}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {recents.length > 0 && (
                <div className="flex-1">
                  <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Dossiers Récemment Utilisés
                  </span>
                  <div className="space-y-1.5 mt-2">
                    {recents.map((recPath) => (
                      <div
                        key={recPath}
                        onClick={() => handleConfirm(recPath)}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-border/40 bg-bg-tertiary/30 hover:bg-bg-tertiary cursor-pointer text-xs"
                      >
                        <div className="flex items-center gap-2 font-mono text-text-primary">
                          <History className="h-3.5 w-3.5 text-amber-400" />
                          <span>{recPath}</span>
                        </div>
                        <Button size="sm" variant="ghost" className="h-6 text-[11px] px-2 text-accent">
                          Appliquer
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer with Selected Path Confirmation */}
        <DialogFooter className="p-4 bg-bg-tertiary/60 border-t border-border/60 flex flex-row items-center justify-between sm:justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span className="text-xs text-text-secondary shrink-0 font-medium">Dossier sélectionné :</span>
            <div className="flex items-center gap-1.5 bg-bg-primary px-3 py-1.5 rounded-lg border border-border text-xs font-mono text-text-primary truncate flex-1 shadow-inner">
              <Folder className="h-3.5 w-3.5 text-accent shrink-0" />
              <input
                type="text"
                value={selectedPath}
                onChange={(e) => setSelectedPath(e.target.value)}
                className="bg-transparent border-none outline-none text-xs font-mono w-full text-text-primary"
                placeholder="Ex: ../mon_projetw ou ."
              />
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm" onClick={onClose} className="h-9 text-xs">
              Annuler
            </Button>
            <Button
              size="sm"
              onClick={() => handleConfirm()}
              disabled={!selectedPath.trim()}
              className="h-9 px-4 text-xs font-semibold bg-accent hover:bg-accent/90 text-white gap-1.5 shadow-md shadow-accent/20"
            >
              <Check className="h-4 w-4" />
              Valider ce dossier
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
