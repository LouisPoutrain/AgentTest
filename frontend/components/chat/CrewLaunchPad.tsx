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
  Folder, 
  FolderOpen,
  HardDrive,
  Bot, 
  Sparkles, 
  Layers, 
  ChevronDown,
  ChevronUp,
  Cpu,
  Search,
  GitBranch,
  Code2,
  FileCode,
  Compass,
  Target,
  FileText,
  Globe,
  FlaskConical,
  Wrench,
  ArrowUpCircle
} from "lucide-react";
import { getCrewDescription } from "@/lib/utils";
import { getWorkspaceProjects } from "@/lib/api";
import type { CrewDetail, CrewLaunchField, ProjectInfo } from "@/lib/types";

interface ExtendedCrewLaunchField extends CrewLaunchField {
  presets?: { label: string; value: string }[];
}

interface CrewLaunchPadProps {
  crewDetail: CrewDetail | null;
  crewName: string;
  onLaunch: (params: {
    message: string;
    inputs: Record<string, any>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => void;
  isStreaming: boolean;
  availableModels?: string[];
}

export function CrewLaunchPad({
  crewDetail,
  crewName,
  onLaunch,
  isStreaming,
  availableModels = [],
}: CrewLaunchPadProps) {
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>("default");
  const [maxRpm, setMaxRpm] = useState<number>(15);

  // Dynamic folder picker state
  const [folderPickerOpen, setFolderPickerOpen] = useState(false);
  const [activeFolderFieldKey, setActiveFolderFieldKey] = useState<string | null>(null);
  const [discoveredProjects, setDiscoveredProjects] = useState<ProjectInfo[]>([]);

  // Load dynamically discovered projects on mount
  useEffect(() => {
    getWorkspaceProjects()
      .then((projs) => setDiscoveredProjects(projs))
      .catch(() => {});
  }, []);

  // Analyze crew and generate specialized dynamic fields based on crew semantics
  const fields = useMemo<ExtendedCrewLaunchField[]>(() => {
    const lowerCrew = crewName.toLowerCase().trim();
    const dynamicFields: ExtendedCrewLaunchField[] = [];

    // 0. PROJECT ARCHITECT: Design brand new applications from scratch into ARCHITECTURE_PROPOSAL.md
    if (lowerCrew.includes("project_architect") || lowerCrew.includes("architect") || lowerCrew.includes("ideator")) {
      dynamicFields.push({
        key: "app_idea",
        label: "Description de votre idée d'application ou besoin",
        placeholder: "Ex: Je veux créer une application SaaS de facturation pour freelances avec Next.js, FastAPI et Stripe...",
        type: "textarea",
        required: true,
        description: "Le Product Manager et l'Architecte vont concevoir le MVP, la stack et l'arborescence complète dans 'ARCHITECTURE_PROPOSAL.md'.",
        presets: [
          { label: "SaaS Facturation & Devis", value: "Une application SaaS moderne de devis et facturation pour freelances avec exports PDF, gestion clients et dashboard de revenus" },
          { label: "Marketplace Prompts IA", value: "Une plateforme collaborative pour tester, partager et vendre des prompts pour modèles LLM avec votes et tags" },
          { label: "Dashboard Analytics & KPIs", value: "Un tableau de bord interactif en temps réel pour suivre les métriques d'usage, erreurs et performances d'une API" },
          { label: "Outil de Scraping & Veille", value: "Un service automatisé pour surveiller les prix et les sorties de produits e-commerce avec alertes par email" },
        ],
      });
      dynamicFields.push({
        key: "tech_preferences",
        label: "Préférences technologiques ou stack souhaitée (Optionnel)",
        placeholder: "Ex: Next.js 16, React 19, FastAPI, Tailwind 4, SQLite...",
        type: "text",
        required: false,
      });
    }
    // 1. GOD CREW: Reverse engineer & Agent generator from a GitHub Repo
    else if (lowerCrew.includes("god")) {
      dynamicFields.push({
        key: "repo_url",
        label: "URL du dépôt GitHub à analyser et cloner",
        placeholder: "https://github.com/LouisPoutrain/AgentTest.git",
        type: "text",
        required: true,
        description: "L'Architecte va cloner ce dépôt, analyser le code et générer un YAML d'agent CrewAI fidèle.",
        presets: [
          { label: "AgentTest (Ce projet)", value: "https://github.com/LouisPoutrain/AgentTest.git" },
          { label: "CrewAI (Framework)", value: "https://github.com/crewAIInc/crewAI.git" },
          { label: "FastAPI", value: "https://github.com/fastapi/fastapi.git" },
        ],
      });
      dynamicFields.push({
        key: "focus",
        label: "Focus d'analyse (Optionnel)",
        placeholder: "Ex: Recherche des composants d'agents, prompt système, outils ou routes API...",
        type: "textarea",
        required: false,
      });
    }
    // 2. GIT SCRAPPER CREW: Search & discover GitHub repositories (NO Git repo input required!)
    else if (lowerCrew.includes("git")) {
      dynamicFields.push({
        key: "search_query",
        label: "Sujet, mot-clé ou type de projets GitHub à dénicher",
        placeholder: "Ex: Framework multi-agents Python, templates Next.js avec Shadcn, outils CLI Rust...",
        type: "textarea",
        required: true,
        description: "Le Git Scrapper va fouiller GitHub via le web et sélectionner le Top 3 à 5 des meilleurs repos récents.",
        presets: [
          { label: "Agents IA Python", value: "Frameworks et architectures pour agents IA autonomes en Python" },
          { label: "Next.js et Shadcn", value: "Boilerplates modernes Next.js App Router avec Shadcn UI et Tailwind" },
          { label: "FastAPI et CrewAI", value: "Exemples de projets et templates combinant FastAPI et CrewAI" },
          { label: "Outils DevSecOps", value: "Outils open-source d'audit de sécurité et analyse statique de code" },
        ],
      });
      dynamicFields.push({
        key: "criteria",
        label: "Critères particuliers de sélection (Optionnel)",
        placeholder: "Ex: Projets populaires avec documentation en français, actifs en 2026, zéro dépendance lourde...",
        type: "text",
        required: false,
      });
    }
    // 2bis. WEB RESEARCHER CREW: General web search, tech watch and synthesis
    else if (lowerCrew.includes("web") || lowerCrew.includes("researcher")) {
      dynamicFields.push({
        key: "query",
        label: "Sujet, question ou recherche web à explorer",
        placeholder: "Ex: Nouveautés de React 19 et Next.js 16, Comparatif des bases de données vectorielles, état de l'art...",
        type: "textarea",
        required: true,
        description: "L'analyste va fouiller le web, extraire les références GitHub (repos/code) pour tout sujet technique et rédiger une synthèse complète.",
        presets: [
          { label: "React 19 & Next.js 16", value: "Quelles sont les dernières fonctionnalités et bonnes pratiques de React 19 et Next.js 16 ?" },
          { label: "Bases Vectorielles 2026", value: "Comparatif des meilleures bases de données vectorielles (Pinecone, Qdrant, Chroma, PGVector) : performances et cas d'usage" },
          { label: "Systèmes Multi-Agents IA", value: "État de l'art et architectures de référence pour orchestrer des systèmes multi-agents en 2026" },
          { label: "Sécurité & FastAPI", value: "Bonnes pratiques de sécurité et de robustesse pour une API FastAPI en production" },
        ],
      });
      dynamicFields.push({
        key: "focus",
        label: "Angle d'analyse ou critères spécifiques (Optionnel)",
        placeholder: "Ex: Prioriser les benchmarks récents, documentations officielles, cas concrets d'usage...",
        type: "text",
        required: false,
      });
    }
    // 2ter. STATE OF THE ART CREW: Academic research and PDF generation
    else if (lowerCrew.includes("stateoftheart")) {
      dynamicFields.push({
        key: "topic",
        label: "Sujet de recherche de l'État de l'Art",
        placeholder: "Ex: Modèles de langage spécialisés dans le code, RAG avec graphes de connaissances...",
        type: "textarea",
        required: true,
        description: "Le chercheur va trouver les papers et repos de référence, puis générer un PDF complet et une page interactive.",
        presets: [
          { label: "RAG & Knowledge Graphs", value: "État de l'art du Retrieval-Augmented Generation couplé aux bases de données orientées graphe (Knowledge Graphs)" },
          { label: "Agents IA Autonomes", value: "Architectures récentes pour les systèmes multi-agents IA autonomes et leur coopération en 2026" },
          { label: "IA & Génération Vidéo", value: "Modèles fondationnels récents pour la génération et l'édition de vidéos par IA" },
        ],
      });
      dynamicFields.push({
        key: "output_dir",
        label: "Dossier de destination (où enregistrer les PDF, HTML et ressources)",
        placeholder: "./research_results",
        defaultValue: "./research_results",
        type: "path",
        required: true,
      });
    }
    // 2.quater EDUCATIONAL CONTENT CREATOR: Convert research into educational courses
    else if (lowerCrew.includes("educational")) {
      dynamicFields.push({
        key: "topic",
        label: "Sujet du cours / de la ressource éducative",
        placeholder: "Ex: Les architectures JEPA et les World Models...",
        type: "textarea",
        required: true,
        description: "Le pédagogue va chercher des informations sur ce sujet, en se basant sur les fichiers existants du dossier.",
        presets: [
          { label: "JEPA & World Models", value: "architectures JEPA et world modèle" },
          { label: "React & Next.js", value: "React 19 et Next.js 16 pour débutants" },
        ],
      });
      dynamicFields.push({
        key: "project_path",
        label: "Dossier cible (où lire l'État de l'art et générer les cours)",
        placeholder: "../SOTA_JEPA:WM",
        defaultValue: "../SOTA_JEPA:WM",
        type: "path",
        required: true,
      });
    }
    // 3. CREW MANAGER: Dynamic Crew generator from any Markdown Architecture/Audit file
    else if (lowerCrew.includes("crewmanager") || lowerCrew.includes("manager")) {
      dynamicFields.push({
        key: "plan_path",
        label: "Chemin du document Markdown (Plan / Code Review)",
        placeholder: "frontend/ARCHITECTURE_PROPOSAL.md",
        defaultValue: "frontend/ARCHITECTURE_PROPOSAL.md",
        type: "text",
        required: true,
        description: "Le CrewManager lira ce document et générera automatiquement un fichier YAML dans 'backend/config/crews/'.",
        presets: [
          { label: "ARCHITECTURE_PROPOSAL.md (Frontend)", value: "frontend/ARCHITECTURE_PROPOSAL.md" },
          { label: "ARCHITECTURE_PROPOSAL.md (Racine)", value: "ARCHITECTURE_PROPOSAL.md" },
          { label: "CODE_REVIEW.md (Crews)", value: "backend/config/crews/CODE_REVIEW.md" },
          { label: "CODE_REVIEW.md (Backend)", value: "backend/CODE_REVIEW.md" },
        ],
      });
      dynamicFields.push({
        key: "instructions",
        label: "Nom souhaité ou consignes particulières (Optionnel)",
        placeholder: "Ex: Nommer le crew 'Refacto_Next.yaml', cibler uniquement les Server Actions...",
        type: "textarea",
        required: false,
      });
    }
    // 3bis. DIRECTORY ARCHIFIER: Generate Architecture Diagram from Folder
    else if (lowerCrew.includes("archifier")) {
      dynamicFields.push({
        key: "directory_path",
        label: "Dossier cible à analyser",
        placeholder: "./backend",
        defaultValue: "./backend",
        type: "path",
        required: true,
        description: "L'Archifier va analyser ce dossier et générer un diagramme HTML de son architecture.",
        presets: [
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
          { label: "Racine", value: "." },
        ],
      });
    }
    // 4. REVIEWER CREW: Code Review & Security Audit
    else if (lowerCrew.includes("reviewer") || lowerCrew.includes("audit")) {
      dynamicFields.push({
        key: "target_path",
        label: "Dossier cible à auditer",
        placeholder: "/Users/poutrainlouis/Code/AgentTest/backend",
        defaultValue: "./backend",
        type: "path",
        required: true,
        description: "Chemin absolu ou relatif du code source à inspecter.",
        presets: [
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
          { label: "Racine (.)", value: "." },
        ],
      });
      dynamicFields.push({
        key: "focus",
        label: "Focus / Consigne spécifique d'audit (Optionnel)",
        placeholder: "Ex: Sécurité RCE/SSRF, injection de prompt, gestion des secrets ou optimisation de perfs...",
        type: "textarea",
        required: false,
      });
    }
    // 4bis. TESTER CREW: Automated test suite generator & QA validation
    else if (lowerCrew.includes("tester") || lowerCrew.includes("qa") || lowerCrew === "test") {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier cible du projet à tester",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "L'ingénieur QA va explorer le projet, écrire les suites de tests unitaires/intégration et rédiger 'TEST_REPORT.md'.",
        presets: [
          { label: "Mon Projet (../mon_projet)", value: "../mon_projet" },
          { label: "Backend (./backend)", value: "./backend" },
          { label: "Frontend (./frontend)", value: "./frontend" },
          { label: "Racine (.)", value: "." },
        ],
      });
      dynamicFields.push({
        key: "focus",
        label: "Focus spécifique de test (Optionnel)",
        placeholder: "Ex: Tests des routes streaming SSE, tests des actions Zustand, gestion des erreurs 400/500...",
        type: "textarea",
        required: false,
      });
    }
    // 4ter. FIXER CREW: Apply patches and bug fixes based on Reviewer and Tester reports
    else if (lowerCrew.includes("fixer") || lowerCrew.includes("repair") || lowerCrew.includes("patch")) {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier du projet à corriger / réparer",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "Le Fixer va lire 'CODE_REVIEW.md' et 'TEST_REPORT.md', modifier chirurgicalement les fichiers et générer 'CHANGELOG_FIXES.md'.",
        presets: [
          { label: "Mon Projet (../mon_projet)", value: "../mon_projet" },
          { label: "Racine (.)", value: "." },
          { label: "Backend (./backend)", value: "./backend" },
          { label: "Frontend (./frontend)", value: "./frontend" },
        ],
      });
      dynamicFields.push({
        key: "instructions",
        label: "Consignes spécifiques de réparation (Optionnel)",
        placeholder: "Ex: Traiter en priorité les vulnérabilités critiques et les erreurs de typage TypeScript...",
        type: "textarea",
        required: false,
      });
    }
    // 4quater. UPGRADER CREW: Implement new features and refactorings on existing codebases
    else if (lowerCrew.includes("upgrader") || lowerCrew.includes("upgrade") || lowerCrew.includes("feature")) {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier du projet à faire évoluer",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "L'Architecte d'Évolution et le Lead Développeur vont analyser la codebase, installer les packages nécessaires et implémenter la nouvelle fonctionnalité.",
        presets: [
          { label: "Mon Projet (../mon_projet)", value: "../mon_projet" },
          { label: "Racine (.)", value: "." },
          { label: "Frontend (./frontend)", value: "./frontend" },
          { label: "Backend (./backend)", value: "./backend" },
        ],
      });
      dynamicFields.push({
        key: "feature_request",
        label: "Fonctionnalité à ajouter ou modification souhaitée",
        placeholder: "Ex: Ajouter l'authentification multi-utilisateurs avec sessions JWT, ajouter un sélecteur de thèmes et dark mode...",
        type: "textarea",
        required: true,
        description: "Précisez en détail les nouvelles fonctionnalités, modèles de données ou pages à intégrer.",
        presets: [
          { label: "Mode Sombre & Thèmes", value: "Ajouter un sélecteur de thème (Dark / Light / System) avec persistance localStorage et refactoriser les composants UI" },
          { label: "Support Nouveaux LLMs", value: "Ajouter le support des providers Anthropic (Claude 3.5 Sonnet) et Mistral AI dans le client LLM et l'interface de sélection" },
          { label: "Gestion Auth & Profils", value: "Ajouter un système complet d'authentification utilisateur, gestion des profils et stockage sécurisé des clés API" },
          { label: "Export & Partage Chat", value: "Ajouter la possibilité d'exporter les conversations au format Markdown / PDF et de copier les blocs de code en un clic" },
        ],
      });
      dynamicFields.push({
        key: "constraints",
        label: "Contraintes techniques ou architecturales (Optionnel)",
        placeholder: "Ex: Conserver la base SQLite/Prisma, utiliser Tailwind pour les styles, TypeScript strict...",
        type: "text",
        required: false,
      });
    }
    // 5. AUTONOMOUS_SWE
    else if (lowerCrew.includes("autonomous")) {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier du projet",
        placeholder: "Ex: ../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "Dossier du projet sur lequel le meta-agent va travailler en autonomie complète (Code, Test, Fix).",
        presets: [
          { label: "Mon Projet (../mon_projet)", value: "../mon_projet" },
          { label: "Racine (.)", value: "." },
          { label: "Frontend", value: "./frontend" },
          { label: "Backend", value: "./backend" },
        ],
      });
      dynamicFields.push({
        key: "feature_request",
        label: "Fonctionnalité à implémenter",
        placeholder: "Ex: Ajoute un système d'authentification et assure-toi que les tests passent...",
        type: "textarea",
        required: true,
        description: "L'instruction détaillée pour l'agent. Il a conscience des autres agents et peut leur déléguer des sous-tâches.",
      });
    }
    // 6. BETTER CREW: Stack Analyzer & Architectural Innovation
    else if (lowerCrew.includes("better") || lowerCrew.includes("refacto")) {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier du projet",
        placeholder: "/Users/poutrainlouis/Code/AgentTest",
        defaultValue: ".",
        type: "path",
        required: true,
        description: "Dossier source dont la stack technologique sera analysée pour proposer l'état de l'art.",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
        ],
      });
      dynamicFields.push({
        key: "objective",
        label: "Objectif ou technologie ciblée (Optionnel)",
        placeholder: "Ex: Passer à React 19 / Suspense, moderniser la sécurité, micro-services, conteneurisation...",
        type: "textarea",
        required: false,
      });
    }
    // 6. TOOLMAKER CREW: Create new custom tools
    else if (lowerCrew.includes("toolmaker") || lowerCrew.includes("tool")) {
      dynamicFields.push({
        key: "tool_description",
        label: "Outil à concevoir / Description des fonctionnalités",
        placeholder: "Ex: Un outil Python pour convertir des fichiers CSV en JSON ou analyser la validité d'une URL...",
        type: "textarea",
        required: true,
        description: "Décrivez ce que le nouvel outil CrewAI doit accomplir et comment il sera utilisé.",
      });
    }
    // 7. DEV CREW: Step-by-step code migration execution
    else if (lowerCrew.includes("dev")) {
      dynamicFields.push({
        key: "project_path",
        label: "Dossier du projet",
        defaultValue: ".",
        type: "path",
        required: true,
        description: "Dossier où appliquer les modifications de code.",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Frontend", value: "./frontend" },
          { label: "Backend", value: "./backend" },
        ],
      });
      dynamicFields.push({
        key: "plan_path",
        label: "Fichier du plan d'étape",
        defaultValue: "frontend/ARCHITECTURE_PROPOSAL.md",
        type: "text",
        required: true,
        description: "Document source contenant les étapes à appliquer.",
      });
    }
    // 8. FALLBACK: Generic launcher
    else {
      dynamicFields.push({
        key: "message",
        label: "Message / Paramètres de la mission",
        placeholder: "Décrivez l'objectif ou entrez les paramètres de démarrage pour ce Crew...",
        type: "textarea",
        required: true,
      });
    }

    return dynamicFields;
  }, [crewDetail, crewName]);

  // Initialize input defaults
  useEffect(() => {
    const initial: Record<string, string> = {};
    fields.forEach((f) => {
      if (f.defaultValue) {
        initial[f.key] = f.defaultValue;
      }
    });
    setInputs(initial);
  }, [fields]);

  const handleInputChange = (key: string, value: string) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyPreset = (key: string, value: string) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const handleLaunch = () => {
    if (isStreaming) return;

    // Build synthesized prompt / message for the crew
    const entries = Object.entries(inputs).filter(([_, v]) => v && v.trim());
    let synthesizedMessage = "";

    const lowerCrew = crewName.toLowerCase();

    // Specific formatting for known crews so prompt matches YAML task templates
    if (lowerCrew.includes("project_architect") || lowerCrew.includes("architect") || lowerCrew.includes("ideator")) {
      synthesizedMessage = inputs.app_idea ? inputs.app_idea.trim() : "";
      if (inputs.tech_preferences && inputs.tech_preferences.trim()) {
        synthesizedMessage += ` (Préférences techniques : ${inputs.tech_preferences.trim()})`;
      }
    } else if (lowerCrew.includes("god")) {
      synthesizedMessage = inputs.repo_url ? inputs.repo_url.trim() : "";
      if (inputs.focus && inputs.focus.trim()) {
        synthesizedMessage += `\nConsignes complémentaires : ${inputs.focus.trim()}`;
      }
    } else if (lowerCrew.includes("git")) {
      synthesizedMessage = inputs.search_query ? inputs.search_query.trim() : "";
      if (inputs.criteria && inputs.criteria.trim()) {
        synthesizedMessage += ` (Critères : ${inputs.criteria.trim()})`;
      }
    } else if (lowerCrew.includes("web") || lowerCrew.includes("researcher")) {
      synthesizedMessage = inputs.query ? inputs.query.trim() : (inputs.search_query ? inputs.search_query.trim() : "");
      if (inputs.focus && inputs.focus.trim()) {
        synthesizedMessage += ` (Angle d'analyse / Précisions : ${inputs.focus.trim()})`;
      }
    } else if (lowerCrew.includes("stateoftheart")) {
      const topic = inputs.topic ? inputs.topic.trim() : "";
      const outDir = inputs.output_dir || "./research_results";
      synthesizedMessage = `Sujet : ${topic}\nDossier de sortie : ${outDir}`;
    } else if (lowerCrew.includes("educational")) {
      const topic = inputs.topic ? inputs.topic.trim() : "";
      const proj = inputs.project_path || "../SOTA_JEPA:WM";
      synthesizedMessage = `Sujet : ${topic}\nDossier : ${proj}`;
    } else if (lowerCrew.includes("crewmanager") || lowerCrew.includes("manager")) {
      const plan = inputs.plan_path ? inputs.plan_path.trim() : "frontend/ARCHITECTURE_PROPOSAL.md";
      synthesizedMessage = plan;
      if (inputs.instructions && inputs.instructions.trim()) {
        synthesizedMessage += ` (Consignes : ${inputs.instructions.trim()})`;
      }
    } else if (lowerCrew.includes("tester") || lowerCrew.includes("qa") || lowerCrew === "test") {
      const proj = inputs.project_path || "../mon_projet";
      synthesizedMessage = proj;
      if (inputs.focus && inputs.focus.trim()) {
        synthesizedMessage += ` (Focus de test : ${inputs.focus.trim()})`;
      }
    } else if (lowerCrew.includes("fixer") || lowerCrew.includes("repair") || lowerCrew.includes("patch")) {
      const proj = inputs.project_path || "../mon_projet";
      synthesizedMessage = proj;
      if (inputs.instructions && inputs.instructions.trim()) {
        synthesizedMessage += ` (Consignes : ${inputs.instructions.trim()})`;
      }
    } else if (lowerCrew.includes("upgrader") || lowerCrew.includes("upgrade") || lowerCrew.includes("feature")) {
      const proj = inputs.project_path || "../mon_projet";
      const feat = inputs.feature_request || "";
      synthesizedMessage = `Projet cible : ${proj}\nDemande d'évolution : ${feat}`;
      if (inputs.constraints && inputs.constraints.trim()) {
        synthesizedMessage += `\nContraintes techniques : ${inputs.constraints.trim()}`;
      }
    } else if (lowerCrew.includes("dev")) {
      const proj = inputs.project_path || ".";
      const plan = inputs.plan_path || "frontend/ARCHITECTURE_PROPOSAL.md";
      synthesizedMessage = `Dossier projet : ${proj} | Document : ${plan}`;
    } else if (inputs.message) {
      synthesizedMessage = inputs.message.trim();
    } else if (entries.length === 1) {
      synthesizedMessage = entries[0][1].trim();
    } else {
      synthesizedMessage = entries.map(([k, v]) => `${formatFieldLabel(k)}: ${v.trim()}`).join("\n");
    }

    const options = {
      llm_override: selectedModel !== "default" ? selectedModel : undefined,
      max_rpm: maxRpm,
    };

    onLaunch({
      message: synthesizedMessage || `Lancement de ${crewName}`,
      inputs,
      options,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleLaunch();
    }
  };

  return (
    <div className="w-full mx-auto py-4 px-3 flex flex-col gap-4 animate-in fade-in duration-300">
      {/* Header Info Card */}
      <Card className="border-border/60 bg-gradient-to-br from-bg-secondary/90 via-bg-secondary/60 to-bg-tertiary/40 backdrop-blur-md shadow-lg">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shadow-inner">
                {crewName.toLowerCase().includes("git") ? (
                  <Compass className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("web") || crewName.toLowerCase().includes("researcher") ? (
                  <Globe className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("god") ? (
                  <GitBranch className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("manager") ? (
                  <FileCode className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("tester") || crewName.toLowerCase().includes("qa") ? (
                  <FlaskConical className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("fixer") || crewName.toLowerCase().includes("repair") ? (
                  <Wrench className="h-6 w-6" />
                ) : crewName.toLowerCase().includes("upgrader") || crewName.toLowerCase().includes("upgrade") ? (
                  <ArrowUpCircle className="h-6 w-6" />
                ) : (
                  <Sparkles className="h-6 w-6" />
                )}
              </div>
              <div>
                <CardTitle className="text-2xl font-bold flex items-center gap-2 text-text-primary">
                  {crewName}
                  <Badge variant="outline" className="text-xs font-normal border-accent/40 text-accent bg-accent/5">
                    {typeof crewDetail?.crew_settings?.process === "string" ? crewDetail.crew_settings.process : "Séquentiel"}
                  </Badge>
                  {crewDetail?.crew_settings?.memory && (
                    <Badge variant="outline" className="text-xs font-normal border-purple-500/40 text-purple-400 bg-purple-500/5">
                      Mémoire active
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-text-secondary text-sm mt-0.5">
                  {crewDetail?.agents.length || 0} agent(s) mobilisé(s) • {crewDetail?.tasks.length || 0} étape(s) d'exécution
                </CardDescription>
              </div>
            </div>

            {/* Quick Agent Avatars / Badges */}
            <div className="flex flex-wrap gap-1.5 max-w-md">
              {crewDetail?.agents.map((ag) => (
                <Badge
                  key={ag.name}
                  variant="secondary"
                  className="bg-bg-tertiary/70 border border-border/50 text-xs py-1 px-2.5 flex items-center gap-1.5"
                  title={`${ag.role} (${ag.llm || "Modèle par défaut"})`}
                >
                  <Bot className="h-3.5 w-3.5 text-accent" />
                  <span className="font-medium">{ag.name}</span>
                </Badge>
              ))}
            </div>
          </div>

          {/* Short Crew Mission Description */}
          <div className="mt-3.5 p-3 rounded-xl bg-bg-primary/50 border border-border/50 text-xs text-text-primary leading-relaxed flex items-start gap-2.5 shadow-inner">
            <Target className="h-4 w-4 text-accent shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-text-secondary uppercase text-[10px] tracking-wider block mb-0.5">
                Mission et Objectif :
              </span>
              <p className="text-text-primary/90 leading-normal">
                {getCrewDescription(crewName, crewDetail)}
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-2">
          {/* Dynamic Inputs Form */}
          <div className="space-y-4" onKeyDown={handleKeyDown}>
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <Layers className="h-4 w-4 text-accent" />
                Paramètres requis pour ce Crew
              </Label>
              <span className="text-xs text-text-secondary">
                Raccourci : <kbd className="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border text-[10px]">⌘ + Entrée</kbd>
              </span>
            </div>

            <div className="grid gap-4">
              {fields.map((field) => (
                <div key={field.key} className="space-y-2 bg-bg-primary/40 p-3.5 rounded-xl border border-border/40">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={field.key} className="text-xs font-semibold text-text-secondary flex items-center gap-1.5">
                      {field.label}
                      {field.required && <span className="text-red-400">*</span>}
                    </Label>
                    {field.description && (
                      <span className="text-[11px] text-text-secondary/70 italic">{field.description}</span>
                    )}
                  </div>

                  {field.type === "textarea" ? (
                    <Textarea
                      id={field.key}
                      value={inputs[field.key] || ""}
                      onChange={(e) => handleInputChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="min-h-[90px] bg-bg-secondary/70 border-border/60 focus-visible:ring-accent text-sm resize-y"
                    />
                  ) : field.type === "path" ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                          <Folder className="absolute left-3 top-2.5 h-4 w-4 text-accent" />
                          <Input
                            id={field.key}
                            value={inputs[field.key] || ""}
                            onChange={(e) => handleInputChange(field.key, e.target.value)}
                            placeholder={field.placeholder || "Ex: ../mon_projet ou ."}
                            className="pl-9 font-mono bg-bg-secondary/70 border-border/60 focus-visible:ring-accent text-xs h-9"
                          />
                        </div>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setActiveFolderFieldKey(field.key);
                            setFolderPickerOpen(true);
                          }}
                          className="h-9 px-3 text-xs gap-1.5 shrink-0 bg-accent/15 hover:bg-accent/25 border border-accent/40 text-accent font-semibold shadow-sm transition-all hover:scale-[1.02]"
                        >
                          <FolderOpen className="h-4 w-4" />
                          Parcourir...
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Input
                        id={field.key}
                        value={inputs[field.key] || ""}
                        onChange={(e) => handleInputChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="bg-bg-secondary/70 border-border/60 focus-visible:ring-accent text-sm"
                      />
                    </div>
                  )}

                  {/* Dynamic Suggestions for Path fields */}
                  {field.type === "path" && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      <span className="text-[11px] text-text-secondary flex items-center gap-1 mr-1">
                        <HardDrive className="h-3 w-3 text-accent" />
                        Accès rapides :
                      </span>
                      {/* Standard Presets */}
                      {(field.presets || [
                        { label: "Racine (.)", value: "." },
                        { label: "Frontend", value: "./frontend" },
                        { label: "Backend", value: "./backend" },
                      ]).map((preset) => (
                        <button
                          key={preset.label}
                          type="button"
                          onClick={() => handleApplyPreset(field.key, preset.value)}
                          className={`text-[11px] px-2 py-0.5 rounded-md border transition-all ${
                            inputs[field.key] === preset.value
                              ? "bg-accent/20 border-accent text-accent font-medium shadow-sm"
                              : "bg-bg-tertiary/60 border-border hover:bg-bg-tertiary text-text-secondary hover:text-text-primary"
                          }`}
                        >
                          {preset.label}
                        </button>
                      ))}

                      {/* Top Discovered Sibling Projects */}
                      {discoveredProjects
                        .filter((p) => !p.is_current && p.path !== "./frontend" && p.path !== "./backend")
                        .slice(0, 4)
                        .map((proj) => (
                          <button
                            key={proj.path}
                            type="button"
                            onClick={() => handleApplyPreset(field.key, proj.path)}
                            className={`text-[11px] px-2 py-0.5 rounded-md border transition-all flex items-center gap-1 ${
                              inputs[field.key] === proj.path
                                ? "bg-accent/20 border-accent text-accent font-medium shadow-sm"
                                : "bg-bg-tertiary/40 border-border/60 hover:bg-bg-tertiary text-text-secondary hover:text-text-primary"
                            }`}
                            title={`Projet détecté : ${proj.framework} (${proj.tags.join(", ")})`}
                          >
                            <span className="font-mono text-[10px] text-accent/80">📁</span>
                            {proj.name}
                          </button>
                        ))}
                    </div>
                  )}

                  {/* Preset chips for non-path fields (URLs, Search queries, ideas) */}
                  {field.type !== "path" && field.presets && field.presets.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      <span className="text-[11px] text-text-secondary flex items-center gap-1 mr-1">
                        <Sparkles className="h-3 w-3 text-accent" />
                        Suggestions :
                      </span>
                      {field.presets.map((preset) => (
                        <button
                          key={preset.label}
                          type="button"
                          onClick={() => handleApplyPreset(field.key, preset.value)}
                          className={`text-[11px] px-2 py-0.5 rounded-md border transition-all ${
                            inputs[field.key] === preset.value
                              ? "bg-accent/20 border-accent text-accent font-medium shadow-sm"
                              : "bg-bg-tertiary/60 border-border hover:bg-bg-tertiary text-text-secondary hover:text-text-primary"
                          }`}
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Advanced Options Accordion */}
          <div className="border-t border-border/40 pt-3">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full py-1 text-xs text-text-secondary hover:text-text-primary transition-colors"
            >
              <span className="flex items-center gap-1.5 font-medium">
                <Settings2 className="h-3.5 w-3.5 text-accent" />
                Options d'orchestration avancées (Modèle LLM et Vitesse)
              </span>
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pt-3 bg-bg-primary/30 p-3.5 rounded-xl border border-border/40 animate-in fade-in duration-200">
                <div className="space-y-1.5">
                  <Label className="text-xs text-text-secondary flex items-center gap-1.5">
                    <Cpu className="h-3.5 w-3.5 text-accent" />
                    Surcharge du Modèle LLM (Override)
                  </Label>
                  <ModelPickerModal
                    currentModel={selectedModel}
                    models={availableModels}
                    onSelect={setSelectedModel}
                    allowDefault={true}
                  />
                  <p className="text-[10px] text-text-secondary/70">Recherche et catégorisation (Custom API, Ollama, Gemini).</p>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs text-text-secondary flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-accent" />
                    Requêtes max par minute (RPM)
                  </Label>
                  <Input
                    type="number"
                    min={1}
                    max={60}
                    value={maxRpm}
                    onChange={(e) => setMaxRpm(parseInt(e.target.value) || 15)}
                    className="bg-bg-secondary border-border/60 text-xs"
                  />
                  <p className="text-[10px] text-text-secondary/70">Évite les erreurs 429 de Rate Limit (Défaut : 15 RPM).</p>
                </div>
              </div>
            )}
          </div>

          {/* Launch Action Button */}
          <div className="pt-2 flex items-center justify-end gap-3">
            <Button
              size="lg"
              onClick={handleLaunch}
              disabled={isStreaming}
              className="w-full sm:w-auto min-w-[220px] bg-accent hover:bg-accent-hover text-white font-semibold shadow-md shadow-accent/20 transition-all hover:scale-[1.01] active:scale-[0.99] gap-2 h-11 px-6 rounded-xl"
            >
              <Play className="h-4 w-4 fill-current" />
              Lancer l'orchestration {crewName}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Dynamic Interactive Folder & Project Picker Modal */}
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

function formatFieldLabel(key: string): string {
  const labels: Record<string, string> = {
    target_path: "Dossier cible",
    project_path: "Chemin du projet",
    plan_path: "Plan d'architecture",
    repo_url: "URL du Repository GitHub",
    search_query: "Recherche GitHub",
    criteria: "Critères de sélection",
    instructions: "Instructions complémentaires",
    message: "Consignes",
    focus: "Axe d'analyse",
    objective: "Objectif de refonte",
    query: "Recherche Web",
    tool_description: "Spécification du Tool",
  };

  if (labels[key]) return labels[key];
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
