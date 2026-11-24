/**
 * Registry declaratif des templates d'automatisation.
 * Remplace la logique hardcoded de matching par type de crew dans CrewLaunchPad.
 */

import type { LucideIcon } from "lucide-react";
import {
  Code2,
  TestTube2,
  BookOpen,
  Search,
  Building2,
  Wrench,
  ArrowUpRight,
  FileCode,
  ShieldCheck,
  BrainCircuit,
  Sparkles,
  PlusCircle,
} from "lucide-react";

export type FieldType = "text" | "textarea" | "path" | "select" | "url" | "toggle";

export interface TemplateField {
  key: string;
  label: string;
  placeholder?: string;
  defaultValue?: string;
  type: FieldType;
  options?: string[];
  description?: string;
  required?: boolean;
  presets?: { label: string; value: string }[];
}

export interface TemplateCategory {
  name: string;
  icon: LucideIcon;
  color: string;
  description: string;
}

export interface AutomationTemplate {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  category: string;
  crewName?: string;
  fields: TemplateField[];
  messageTemplate?: string;
  isCustom?: boolean;
  complexity: "simple" | "moderate" | "advanced";
  estimatedTime: string;
  tags: string[];
}

export const TEMPLATE_CATEGORIES: Record<string, TemplateCategory> = {
  development: {
    name: "Developpement",
    icon: Code2,
    color: "text-blue-500",
    description: "Generation, refonte et amelioration de code",
  },
  testing: {
    name: "Testing & QA",
    icon: TestTube2,
    color: "text-emerald-500",
    description: "Tests automatisés, audit et correction",
  },
  documentation: {
    name: "Documentation",
    icon: BookOpen,
    color: "text-amber-500",
    description: "Generation de docs, diagrammes et rapports",
  },
  research: {
    name: "Recherche",
    icon: Search,
    color: "text-purple-500",
    description: "Veille technologique et recherche web",
  },
  architecture: {
    name: "Architecture",
    icon: Building2,
    color: "text-cyan-500",
    description: "Analyse architecturale et conception",
  },
};

export const AUTOMATION_TEMPLATES: AutomationTemplate[] = [
  // ── Developpement ──
  {
    id: "autonomous-swe",
    name: "Developpeur Autonome",
    description: "Un agent SWE autonome qui code, teste et corrige en boucle",
    icon: Code2,
    category: "development",
    crewName: "Autonomous_SWE",
    complexity: "advanced",
    estimatedTime: "5-15 min",
    tags: ["code", "test", "fix", "autonome"],
    fields: [
      {
        key: "project_path",
        label: "Dossier du projet",
        placeholder: "Ex: ../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "Dossier du projet sur lequel l'agent va travailler",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Frontend", value: "./frontend" },
          { label: "Backend", value: "./backend" },
        ],
      },
      {
        key: "feature_request",
        label: "Fonctionnalite a implémenter",
        placeholder: "Ex: Ajoute un système d'authentification JWT...",
        type: "textarea",
        required: true,
        description: "L'instruction détaillée pour l'agent autonome",
      },
    ],
    messageTemplate: "project_path: {project_path}\nfeature_request: {feature_request}",
  },
  {
    id: "better",
    name: "Analyste & Innovateur",
    description: "Analyse la stack et propose des ameliorations architecturales",
    icon: BrainCircuit,
    category: "development",
    crewName: "Better",
    complexity: "moderate",
    estimatedTime: "3-8 min",
    tags: ["refacto", "stack", "architecture"],
    fields: [
      {
        key: "project_path",
        label: "Dossier du projet",
        placeholder: "/Users/poutrainlouis/Code/AgentTest",
        defaultValue: ".",
        type: "path",
        required: true,
        description: "Dossier source dont la stack sera analysée",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
        ],
      },
      {
        key: "objective",
        label: "Objectif ou technologie ciblée (Optionnel)",
        placeholder: "Ex: Passer à React 19 / Suspense, moderniser la sécurité...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "project_path: {project_path}\nobjective: {objective}",
  },
  {
    id: "upgrader",
    name: "Évolution & Features",
    description: "Implémente de nouvelles fonctionnalités et refactorisations",
    icon: ArrowUpRight,
    category: "development",
    crewName: "Upgrader",
    complexity: "moderate",
    estimatedTime: "5-10 min",
    tags: ["feature", "upgrade", "refacto", "evolution"],
    fields: [
      {
        key: "project_path",
        label: "Dossier du projet à faire évoluer",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "Dossier source à faire évoluer",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Frontend", value: "./frontend" },
          { label: "Backend", value: "./backend" },
        ],
      },
      {
        key: "feature_request",
        label: "Fonctionnalité à ajouter",
        placeholder: "Ex: Ajouter l'authentification multi-utilisateurs avec sessions JWT...",
        type: "textarea",
        required: true,
        description: "Precisez les nouvelles fonctionnalités à intégrer",
        presets: [
          { label: "Mode Sombre & Thèmes", value: "Ajouter un sélecteur de thème (Dark / Light / System) avec persistance localStorage" },
          { label: "Support Nouveaux LLMs", value: "Ajouter le support des providers Anthropic (Claude 3.5 Sonnet) et Mistral AI" },
          { label: "Gestion Auth & Profils", value: "Ajouter un système complet d'authentification utilisateur et gestion des profils" },
          { label: "Export & Partage Chat", value: "Ajouter l'export des conversations au format Markdown / PDF" },
        ],
      },
      {
        key: "constraints",
        label: "Contraintes techniques (Optionnel)",
        placeholder: "Ex: Conserver SQLite, utiliser Tailwind pour les styles...",
        type: "text",
        required: false,
      },
    ],
    messageTemplate: "project_path: {project_path}\nfeature_request: {feature_request}\nconstraints: {constraints}",
  },
  {
    id: "dev",
    name: "Apply Plan",
    description: "Applique concretement les modifications de code recommandées étape par étape",
    icon: FileCode,
    category: "development",
    crewName: "dev_assistant",
    complexity: "moderate",
    estimatedTime: "5-15 min",
    tags: ["plan", "apply", "code", "migration"],
    fields: [
      {
        key: "project_path",
        label: "Dossier du projet",
        defaultValue: ".",
        type: "path",
        required: true,
        description: "Dossier où appliquer les modifications",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Frontend", value: "./frontend" },
          { label: "Backend", value: "./backend" },
        ],
      },
      {
        key: "plan_path",
        label: "Fichier du plan d'étape",
        defaultValue: "frontend/ARCHITECTURE_PROPOSAL.md",
        type: "text",
        required: true,
        description: "Document source contenant les étapes à appliquer",
      },
    ],
    messageTemplate: "project_path: {project_path}\nplan_path: {plan_path}",
  },
  {
    id: "toolmaker",
    name: "Createur d'Outils",
    description: "Conçoit et implémente de nouveaux outils Python personnalisés",
    icon: Wrench,
    category: "development",
    crewName: "ToolMaker",
    complexity: "moderate",
    estimatedTime: "3-7 min",
    tags: ["tool", "python", "custom", "crewai"],
    fields: [
      {
        key: "tool_description",
        label: "Outil à concevoir",
        placeholder: "Ex: Un outil Python pour convertir des CSV en JSON...",
        type: "textarea",
        required: true,
        description: "Décrivez ce que le nouvel outil CrewAI doit accomplir",
      },
    ],
    messageTemplate: "tool_description: {tool_description}",
  },
  // ── Testing & QA ──
  {
    id: "reviewer",
    name: "Code Review & Audit",
    description: "Audite le code source pour détecter vulnérabilités, bugs critiques et optimisations",
    icon: ShieldCheck,
    category: "testing",
    crewName: "Reviewer",
    complexity: "simple",
    estimatedTime: "2-5 min",
    tags: ["audit", "security", "review", "bug"],
    fields: [
      {
        key: "target_path",
        label: "Dossier cible à auditer",
        placeholder: "/Users/poutrainlouis/Code/AgentTest/backend",
        defaultValue: "./backend",
        type: "path",
        required: true,
        description: "Chemin absolu ou relatif du code source à inspecter",
        presets: [
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
          { label: "Racine (.)", value: "." },
        ],
      },
      {
        key: "focus",
        label: "Focus / Consigne spécifique (Optionnel)",
        placeholder: "Ex: Sécurité RCE/SSRF, injection de prompt, optimisation perfs...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "target_path: {target_path}\nfocus: {focus}",
  },
  {
    id: "tester",
    name: "Generateur de Tests",
    description: "Explore le projet, génère une suite complète de tests automatisés et rédige un rapport",
    icon: TestTube2,
    category: "testing",
    crewName: "IntegrationTestCrew",
    complexity: "moderate",
    estimatedTime: "3-8 min",
    tags: ["test", "qa", "automation", "report"],
    fields: [
      {
        key: "project_path",
        label: "Dossier cible du projet à tester",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "L'ingénieur QA va explorer le projet et générer les tests",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
        ],
      },
      {
        key: "focus",
        label: "Focus spécifique de test (Optionnel)",
        placeholder: "Ex: Tests des routes SSE, tests des actions Zustand...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "project_path: {project_path}\nfocus: {focus}",
  },
  {
    id: "fixer",
    name: "Correcteur de Bugs",
    description: "Lit les rapports de review et de test pour corriger chirurgicalement les bugs et vulnérabilités",
    icon: Wrench,
    category: "testing",
    crewName: "Fixer",
    complexity: "moderate",
    estimatedTime: "3-7 min",
    tags: ["fix", "bug", "patch", "repair"],
    fields: [
      {
        key: "project_path",
        label: "Dossier du projet à corriger",
        placeholder: "../mon_projet",
        defaultValue: "../mon_projet",
        type: "path",
        required: true,
        description: "Le Fixer va lire les rapports et modifier les fichiers",
        presets: [
          { label: "Racine (.)", value: "." },
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
        ],
      },
      {
        key: "instructions",
        label: "Consignes spécifiques (Optionnel)",
        placeholder: "Ex: Traiter en priorité les vulnérabilités critiques...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "project_path: {project_path}\ninstructions: {instructions}",
  },
  // ── Documentation ──
  {
    id: "archifier",
    name: "Diagramme d'Architecture",
    description: "Parcourt un dossier, analyse le code source et génère un diagramme d'architecture interactif",
    icon: Building2,
    category: "documentation",
    crewName: "Directory_Archifier",
    complexity: "simple",
    estimatedTime: "1-3 min",
    tags: ["diagram", "architecture", "visualization", "folder"],
    fields: [
      {
        key: "directory_path",
        label: "Dossier cible à analyser",
        placeholder: "./backend",
        defaultValue: "./backend",
        type: "path",
        required: true,
        description: "L'Archifier va analyser ce dossier et générer le diagramme HTML",
        presets: [
          { label: "Backend", value: "./backend" },
          { label: "Frontend", value: "./frontend" },
          { label: "Racine", value: "." },
        ],
      },
    ],
    messageTemplate: "directory_path: {directory_path}",
  },
  {
    id: "documentaliste",
    name: "Documentaliste",
    description: "Recherche, organise et synthétise des informations en documents structurés",
    icon: BookOpen,
    category: "documentation",
    crewName: "Documentaliste",
    complexity: "simple",
    estimatedTime: "2-5 min",
    tags: ["doc", "synthesis", "organization", "report"],
    fields: [
      {
        key: "topic",
        label: "Sujet à documenter",
        placeholder: "Ex: Architecture microservices vs monolithe...",
        type: "textarea",
        required: true,
        description: "Le sujet sur lequel le documentaliste va travailler",
      },
    ],
    messageTemplate: "topic: {topic}",
  },
  // ── Recherche ──
  {
    id: "web-researcher",
    name: "Recherche Web",
    description: "Explore le web et GitHub pour synthétiser documentations, actualités et références",
    icon: Search,
    category: "research",
    crewName: "Web_Researcher",
    complexity: "simple",
    estimatedTime: "2-5 min",
    tags: ["web", "search", "research", "synthesis"],
    fields: [
      {
        key: "query",
        label: "Sujet ou question à explorer",
        placeholder: "Ex: Nouveautés React 19 et Next.js 16...",
        type: "textarea",
        required: true,
        description: "Le sujet à rechercher et synthétiser",
        presets: [
          { label: "React 19 & Next.js 16", value: "Quelles sont les dernières fonctionnalités et bonnes pratiques de React 19 et Next.js 16 ?" },
          { label: "Bases Vectorielles 2026", value: "Comparatif des meilleures bases de données vectorielles" },
          { label: "Systèmes Multi-Agents IA", value: "État de l'art pour orchestrer des systèmes multi-agents en 2026" },
        ],
      },
      {
        key: "focus",
        label: "Angle d'analyse (Optionnel)",
        placeholder: "Ex: Prioriser les benchmarks récents...",
        type: "text",
        required: false,
      },
    ],
    messageTemplate: "query: {query}\nfocus: {focus}",
  },
  {
    id: "stateoftheart",
    name: "État de l'Art",
    description: "Trouve les papers et repos de référence, génère un PDF complet et une page interactive",
    icon: Search,
    category: "research",
    crewName: "StateOfTheArtCrew",
    complexity: "advanced",
    estimatedTime: "5-10 min",
    tags: ["sota", "research", "pdf", "academic"],
    fields: [
      {
        key: "topic",
        label: "Sujet de recherche",
        placeholder: "Ex: Modèles de langage spécialisés dans le code...",
        type: "textarea",
        required: true,
        description: "Le sujet de recherche de l'état de l'art",
        presets: [
          { label: "RAG & Knowledge Graphs", value: "État de l'art du Retrieval-Augmented Generation couplé aux Knowledge Graphs" },
          { label: "Agents IA Autonomes", value: "Architectures récentes pour les systèmes multi-agents IA autonomes" },
          { label: "IA & Génération Vidéo", value: "Modèles fondationnels récents pour la génération de vidéos par IA" },
        ],
      },
      {
        key: "output_dir",
        label: "Dossier de destination",
        placeholder: "./research_results",
        defaultValue: "./research_results",
        type: "path",
        required: true,
      },
    ],
    messageTemplate: "topic: {topic}\noutput_dir: {output_dir}",
  },
  {
    id: "git-scraper",
    name: "Scraper GitHub",
    description: "Fouille GitHub pour dénicher et sélectionner le Top 3 à 5 des meilleurs projets open-source",
    icon: Sparkles,
    category: "research",
    crewName: "git_scraper",
    complexity: "simple",
    estimatedTime: "2-5 min",
    tags: ["github", "search", "discovery", "repos"],
    fields: [
      {
        key: "search_query",
        label: "Sujet ou mot-clé GitHub",
        placeholder: "Ex: Framework multi-agents Python, templates Next.js...",
        type: "textarea",
        required: true,
        description: "Le sujet pour lequel chercher des projets GitHub",
        presets: [
          { label: "Agents IA Python", value: "Frameworks et architectures pour agents IA autonomes en Python" },
          { label: "Next.js et Shadcn", value: "Boilerplates modernes Next.js App Router avec Shadcn UI" },
          { label: "FastAPI et CrewAI", value: "Exemples de projets combinant FastAPI et CrewAI" },
        ],
      },
      {
        key: "criteria",
        label: "Critères de sélection (Optionnel)",
        placeholder: "Ex: Projets populaires, actifs en 2026, zéro dépendance lourde...",
        type: "text",
        required: false,
      },
    ],
    messageTemplate: "search_query: {search_query}\ncriteria: {criteria}",
  },
  // ── Architecture ──
  {
    id: "project-architect",
    name: "Architecte d'Applications",
    description: "Transforme une idée brute en un plan d'architecture Markdown complet (MVP, stack, arborescence)",
    icon: Building2,
    category: "architecture",
    crewName: "Project_Architect",
    complexity: "advanced",
    estimatedTime: "5-10 min",
    tags: ["architecture", "design", "mvp", "planning"],
    fields: [
      {
        key: "app_idea",
        label: "Description de l'idée d'application",
        placeholder: "Ex: Une application SaaS de facturation pour freelances avec Next.js, FastAPI et Stripe...",
        type: "textarea",
        required: true,
        description: "Le Product Manager et l'Architecte vont concevoir le MVP et la stack complète",
        presets: [
          { label: "SaaS Facturation", value: "Une application SaaS moderne de devis et facturation pour freelances avec exports PDF" },
          { label: "Marketplace Prompts IA", value: "Une plateforme collaborative pour tester, partager et vendre des prompts LLM" },
          { label: "Dashboard Analytics", value: "Un tableau de bord interactif en temps réel pour suivre les métriques d'usage" },
        ],
      },
      {
        key: "tech_preferences",
        label: "Préférences technologiques (Optionnel)",
        placeholder: "Ex: Next.js 16, React 19, FastAPI, Tailwind 4, SQLite...",
        type: "text",
        required: false,
      },
    ],
    messageTemplate: "app_idea: {app_idea}\ntech_preferences: {tech_preferences}",
  },
  {
    id: "god",
    name: "Reverse Engineer",
    description: "Clone un dépôt GitHub, analyse son architecture et génère un agent CrewAI 100% fidèle au code source",
    icon: Sparkles,
    category: "architecture",
    crewName: "God",
    complexity: "advanced",
    estimatedTime: "5-15 min",
    tags: ["reverse", "clone", "analysis", "crewai"],
    fields: [
      {
        key: "repo_url",
        label: "URL du dépôt GitHub",
        placeholder: "https://github.com/LouisPoutrain/AgentTest.git",
        type: "url",
        required: true,
        description: "L'Architecte va cloner ce dépôt, analyser le code et générer un YAML d'agent",
        presets: [
          { label: "AgentTest", value: "https://github.com/LouisPoutrain/AgentTest.git" },
          { label: "CrewAI", value: "https://github.com/crewAIInc/crewAI.git" },
          { label: "FastAPI", value: "https://github.com/fastapi/fastapi.git" },
        ],
      },
      {
        key: "focus",
        label: "Focus d'analyse (Optionnel)",
        placeholder: "Ex: Recherche des composants d'agents, prompt système, outils...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "repo_url: {repo_url}\nfocus: {focus}",
  },
  {
    id: "crewmanager",
    name: "Generateur de Crews",
    description: "Découpe un plan d'architecture Markdown et génère un Crew de Build complet et modulaire",
    icon: FileCode,
    category: "architecture",
    crewName: "CrewManager",
    complexity: "advanced",
    estimatedTime: "5-10 min",
    tags: ["crew", "yaml", "generator", "modular"],
    fields: [
      {
        key: "plan_path",
        label: "Chemin du document Markdown",
        placeholder: "frontend/ARCHITECTURE_PROPOSAL.md",
        defaultValue: "frontend/ARCHITECTURE_PROPOSAL.md",
        type: "text",
        required: true,
        description: "Le CrewManager lira ce document et générera un fichier YAML dans config/crews/",
        presets: [
          { label: "ARCHITECTURE_PROPOSAL.md", value: "frontend/ARCHITECTURE_PROPOSAL.md" },
          { label: "Racine", value: "ARCHITECTURE_PROPOSAL.md" },
        ],
      },
      {
        key: "instructions",
        label: "Nom ou consignes particulières (Optionnel)",
        placeholder: "Ex: Nommer le crew 'Refacto_Next.yaml'...",
        type: "textarea",
        required: false,
      },
    ],
    messageTemplate: "plan_path: {plan_path}\ninstructions: {instructions}",
  },
  // ── Éducatif ──
  {
    id: "educational",
    name: "Createur de Cours",
    description: "Convertit des recherches en cours éducatifs structurés avec ressources et exercices",
    icon: BookOpen,
    category: "documentation",
    crewName: "EducationalContentCreator",
    complexity: "moderate",
    estimatedTime: "3-7 min",
    tags: ["education", "course", "learning", "resources"],
    fields: [
      {
        key: "topic",
        label: "Sujet du cours",
        placeholder: "Ex: Les architectures JEPA et les World Models...",
        type: "textarea",
        required: true,
        description: "Le sujet sur lequel créer le cours éducatif",
        presets: [
          { label: "JEPA & World Models", value: "architectures JEPA et world modèle" },
          { label: "React & Next.js", value: "React 19 et Next.js 16 pour débutants" },
        ],
      },
      {
        key: "project_path",
        label: "Dossier cible",
        placeholder: "../SOTA_JEPA:WM",
        defaultValue: "../SOTA_JEPA:WM",
        type: "path",
        required: true,
      },
    ],
    messageTemplate: "topic: {topic}\nproject_path: {project_path}",
  },
  // ── Template Personnalisé ──
  {
    id: "custom",
    name: "Personnalisé",
    description: "Créez votre propre automatisation avec des paramètres libres",
    icon: PlusCircle,
    category: "development",
    complexity: "simple",
    estimatedTime: "1 min",
    tags: ["custom", "freeform", "any"],
    isCustom: true,
    fields: [
      {
        key: "message",
        label: "Décrivez votre automatisation",
        placeholder: "Ex: Je veux un agent qui analyse les logs de production et génère un rapport quotidien...",
        type: "textarea",
        required: true,
        description: "Décrivez librement ce que vous souhaitez automatiser",
      },
    ],
    messageTemplate: "{message}",
  },
];

/**
 * Get templates filtered by category.
 */
export function getTemplatesByCategory(category: string): AutomationTemplate[] {
  return AUTOMATION_TEMPLATES.filter((t) => t.category === category);
}

/**
 * Search templates by query string.
 */
export function searchTemplates(query: string): AutomationTemplate[] {
  if (!query.trim()) return AUTOMATION_TEMPLATES;
  const q = query.toLowerCase();
  return AUTOMATION_TEMPLATES.filter(
    (t) =>
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.tags.some((tag) => tag.toLowerCase().includes(q))
  );
}

/**
 * Get a template by ID.
 */
export function getTemplateById(id: string): AutomationTemplate | undefined {
  return AUTOMATION_TEMPLATES.find((t) => t.id === id);
}

/**
 * Get all unique tags across templates.
 */
export function getAllTags(): string[] {
  const tags = new Set<string>();
  AUTOMATION_TEMPLATES.forEach((t) => t.tags.forEach((tag) => tags.add(tag)));
  return Array.from(tags).sort();
}

/**
 * Build the synthesized message from a template and its field values.
 */
export function buildMessageFromTemplate(
  template: AutomationTemplate,
  inputs: Record<string, string>
): string {
  if (!template.messageTemplate) {
    // Fallback: join all non-empty inputs
    const entries = Object.entries(inputs).filter(([, v]) => v && v.trim());
    if (entries.length === 1) return entries[0][1].trim();
    return entries.map(([k, v]) => k + ": " + v.trim()).join("\n");
  }

  let msg = template.messageTemplate;
  for (const [key, value] of Object.entries(inputs)) {
    if (value && value.trim()) {
      msg = msg.replace("{" + key + "}", value.trim());
    }
  }
  // Remove any remaining empty placeholders
  msg = msg.replace(/\{[^}]*\}/g, "").replace(/\n\n+/g, "\n").trim();
  return msg || template.name;
}
