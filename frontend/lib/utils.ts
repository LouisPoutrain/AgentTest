import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getCrewDescription(crewName: string, crewDetail?: any): string {
  const lower = (crewName || "").toLowerCase().trim();

  if (lower.includes("project_architect") || lower.includes("architect") || lower.includes("ideator")) {
    return "Transforme votre idée brute en un plan d'architecture Markdown complet (MVP, stack moderne, arborescence) prêt pour le CrewManager.";
  }
  if (lower.includes("reviewer") || lower.includes("audit")) {
    return "Audite le code source pour détecter les vulnérabilités de sécurité, bugs critiques et optimisations.";
  }
  if (lower.includes("better") || lower.includes("refacto")) {
    return "Analyse la stack technologique, effectue une veille sur l'état de l'art et propose une refonte architecturale.";
  }
  if (lower.includes("git")) {
    return "Fouille GitHub sur le web pour dénicher et sélectionner le Top 3 à 5 des meilleurs projets open-source.";
  }
  if (lower.includes("web") || lower.includes("researcher") || lower.includes("search")) {
    return "Explore le web et GitHub pour synthétiser des documentations, actualités et références de code/dépôts open-source.";
  }
  if (lower.includes("god")) {
    return "Clone un dépôt GitHub, analyse son architecture et génère un agent CrewAI 100% fidèle au code source.";
  }
  if (lower.includes("crewmanager") || lower.includes("manager")) {
    return "Découpe un plan d'architecture (Markdown) et génère un Crew de Build complet et modulaire (Backend + Frontend).";
  }
  if (lower.includes("tester") || lower.includes("test")) {
    return "Explore le projet, génère une suite complète de tests automatisés (Vitest/Pytest) et rédige un rapport TEST_REPORT.md.";
  }
  if (lower.includes("fixer") || lower.includes("repair") || lower.includes("patch")) {
    return "Lit les conclusions de CODE_REVIEW.md et TEST_REPORT.md pour corriger chirurgicalement les bugs et vulnérabilités.";
  }
  if (lower.includes("toolmaker") || lower.includes("tool")) {
    return "Conçoit et implémente de nouveaux outils Python personnalisés pour étendre les capacités de vos agents.";
  }
  if (lower.includes("upgrader") || lower.includes("upgrade") || lower.includes("feature")) {
    return "Analyse une codebase existante et y implémente de nouvelles fonctionnalités ou refactorisations à la demande.";
  }
  if (lower.includes("build")) {
    return "Génère et initialise tous les fichiers d'un nouveau projet de zéro dans son dossier dédié (Backend + Frontend).";
  }
  if (lower.includes("archifier")) {
    return "Parcourt un dossier, analyse son code source et génère automatiquement un diagramme d'architecture interactif complet.";
  }
  if (lower.includes("dev")) {
    return "Applique concrètement les modifications de code recommandées dans le plan d'architecture étape par étape.";
  }
  if (lower.includes("dev_assistant") || lower.includes("assistant")) {
    return "Assistant de développement autonome capable de lire, écrire et exécuter du code pour gérer votre projet.";
  }

  if (crewDetail?.agents?.[0]?.goal) {
    return crewDetail.agents[0].goal;
  }

  return "Orchestration multi-agents automatisée pour vos projets logiciels.";
}
