"""
Registry API - Serve metadata for the Automation Lab frontend.
Provides template listings, crew schemas, and agent metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.crew_manager import get_all_crews, get_crew

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/registry", tags=["registry"])


class TemplateField(BaseModel):
    key: str
    label: str
    type: str = "text"
    placeholder: Optional[str] = None
    required: bool = False
    description: Optional[str] = None
    presets: Optional[List[Dict[str, str]]] = None


class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: str
    category: str
    crew_name: Optional[str] = None
    fields: List[TemplateField] = Field(default_factory=list)
    complexity: str = "simple"
    estimated_time: str = "1-5 min"
    tags: List[str] = Field(default_factory=list)


class AgentMetadata(BaseModel):
    name: str
    role: str
    goal: str
    llm: Optional[str] = None
    tools: List[str] = Field(default_factory=list)


class RegistryResponse(BaseModel):
    templates: List[TemplateMetadata]
    crews: List[Dict[str, Any]]
    agents: List[AgentMetadata]


# ── Template Definitions ─────────────────────────────────────────────────────

TEMPLATES: List[TemplateMetadata] = [
    # Development
    TemplateMetadata(
        id="autonomous-swe",
        name="Developpeur Autonome",
        description="Un agent SWE autonome qui code, teste et corrige en boucle",
        category="development",
        crew_name="Autonomous_SWE",
        complexity="advanced",
        estimated_time="5-15 min",
        tags=["code", "test", "fix", "autonome"],
        fields=[
            TemplateField(key="project_path", label="Dossier du projet", type="path", required=True),
            TemplateField(key="feature_request", label="Fonctionnalite a implémenter", type="textarea", required=True),
        ],
    ),
    TemplateMetadata(
        id="better",
        name="Analyste & Innovateur",
        description="Analyse la stack et propose des ameliorations architecturales",
        category="development",
        crew_name="Better",
        complexity="moderate",
        estimated_time="3-8 min",
        tags=["refacto", "stack", "architecture"],
        fields=[
            TemplateField(key="project_path", label="Dossier du projet", type="path", required=True),
            TemplateField(key="objective", label="Objectif cible", type="textarea", required=False),
        ],
    ),
    TemplateMetadata(
        id="upgrader",
        name="Évolution & Features",
        description="Implémente de nouvelles fonctionnalités sur une codebase existante",
        category="development",
        crew_name="Upgrader",
        complexity="moderate",
        estimated_time="5-10 min",
        tags=["feature", "upgrade", "refacto"],
        fields=[
            TemplateField(key="project_path", label="Dossier du projet", type="path", required=True),
            TemplateField(key="feature_request", label="Fonctionnalité à ajouter", type="textarea", required=True),
            TemplateField(key="constraints", label="Contraintes techniques", type="text", required=False),
        ],
    ),
    TemplateMetadata(
        id="dev",
        name="Apply Plan",
        description="Applique les modifications de code recommandées étape par étape",
        category="development",
        crew_name="dev_assistant",
        complexity="moderate",
        estimated_time="5-15 min",
        tags=["plan", "apply", "code"],
        fields=[
            TemplateField(key="project_path", label="Dossier du projet", type="path", required=True),
            TemplateField(key="plan_path", label="Fichier du plan", type="text", required=True),
        ],
    ),
    TemplateMetadata(
        id="toolmaker",
        name="Createur d'Outils",
        description="Conçoit de nouveaux outils Python personnalisés",
        category="development",
        crew_name="ToolMaker",
        complexity="moderate",
        estimated_time="3-7 min",
        tags=["tool", "python", "custom"],
        fields=[
            TemplateField(key="tool_description", label="Outil à concevoir", type="textarea", required=True),
        ],
    ),
    # Testing
    TemplateMetadata(
        id="reviewer",
        name="Code Review & Audit",
        description="Audite le code pour détecter vulnérabilités et bugs",
        category="testing",
        crew_name="Reviewer",
        complexity="simple",
        estimated_time="2-5 min",
        tags=["audit", "security", "review"],
        fields=[
            TemplateField(key="target_path", label="Dossier cible", type="path", required=True),
            TemplateField(key="focus", label="Focus spécifique", type="textarea", required=False),
        ],
    ),
    TemplateMetadata(
        id="tester",
        name="Generateur de Tests",
        description="Génère une suite complète de tests automatisés",
        category="testing",
        crew_name="IntegrationTestCrew",
        complexity="moderate",
        estimated_time="3-8 min",
        tags=["test", "qa", "automation"],
        fields=[
            TemplateField(key="project_path", label="Dossier cible", type="path", required=True),
            TemplateField(key="focus", label="Focus de test", type="textarea", required=False),
        ],
    ),
    TemplateMetadata(
        id="fixer",
        name="Correcteur de Bugs",
        description="Corrige les bugs et vulnérabilités détectés",
        category="testing",
        crew_name="Fixer",
        complexity="moderate",
        estimated_time="3-7 min",
        tags=["fix", "bug", "patch"],
        fields=[
            TemplateField(key="project_path", label="Dossier du projet", type="path", required=True),
            TemplateField(key="instructions", label="Consignes", type="textarea", required=False),
        ],
    ),
    # Documentation
    TemplateMetadata(
        id="archifier",
        name="Diagramme d'Architecture",
        description="Génère un diagramme d'architecture interactif",
        category="documentation",
        crew_name="Directory_Archifier",
        complexity="simple",
        estimated_time="1-3 min",
        tags=["diagram", "architecture", "visualization"],
        fields=[
            TemplateField(key="directory_path", label="Dossier cible", type="path", required=True),
        ],
    ),
    TemplateMetadata(
        id="documentaliste",
        name="Documentaliste",
        description="Synthétise des informations en documents structurés",
        category="documentation",
        crew_name="Documentaliste",
        complexity="simple",
        estimated_time="2-5 min",
        tags=["doc", "synthesis", "report"],
        fields=[
            TemplateField(key="topic", label="Sujet à documenter", type="textarea", required=True),
        ],
    ),
    # Research
    TemplateMetadata(
        id="web-researcher",
        name="Recherche Web",
        description="Explore le web et GitHub pour synthétiser des références",
        category="research",
        crew_name="Web_Researcher",
        complexity="simple",
        estimated_time="2-5 min",
        tags=["web", "search", "research"],
        fields=[
            TemplateField(key="query", label="Sujet à explorer", type="textarea", required=True),
            TemplateField(key="focus", label="Angle d'analyse", type="text", required=False),
        ],
    ),
    TemplateMetadata(
        id="stateoftheart",
        name="État de l'Art",
        description="Trouve les papers de référence et génère un PDF complet",
        category="research",
        crew_name="StateOfTheArtCrew",
        complexity="advanced",
        estimated_time="5-10 min",
        tags=["sota", "research", "academic"],
        fields=[
            TemplateField(key="topic", label="Sujet de recherche", type="textarea", required=True),
            TemplateField(key="output_dir", label="Dossier de destination", type="path", required=True),
        ],
    ),
    TemplateMetadata(
        id="git-scraper",
        name="Scraper GitHub",
        description="Déniche les meilleurs projets open-source sur GitHub",
        category="research",
        crew_name="git_scraper",
        complexity="simple",
        estimated_time="2-5 min",
        tags=["github", "search", "discovery"],
        fields=[
            TemplateField(key="search_query", label="Sujet GitHub", type="textarea", required=True),
            TemplateField(key="criteria", label="Critères de sélection", type="text", required=False),
        ],
    ),
    # Architecture
    TemplateMetadata(
        id="project-architect",
        name="Architecte d'Applications",
        description="Transforme une idée en plan d'architecture Markdown",
        category="architecture",
        crew_name="Project_Architect",
        complexity="advanced",
        estimated_time="5-10 min",
        tags=["architecture", "design", "mvp"],
        fields=[
            TemplateField(key="app_idea", label="Description de l'idée", type="textarea", required=True),
            TemplateField(key="tech_preferences", label="Préférences tech", type="text", required=False),
        ],
    ),
    TemplateMetadata(
        id="god",
        name="Reverse Engineer",
        description="Clone un dépôt et génère un agent CrewAI fidèle",
        category="architecture",
        crew_name="God",
        complexity="advanced",
        estimated_time="5-15 min",
        tags=["reverse", "clone", "crewai"],
        fields=[
            TemplateField(key="repo_url", label="URL du dépôt GitHub", type="text", required=True),
            TemplateField(key="focus", label="Focus d'analyse", type="textarea", required=False),
        ],
    ),
    TemplateMetadata(
        id="crewmanager",
        name="Generateur de Crews",
        description="Génère un Crew YAML à partir d'un plan Markdown",
        category="architecture",
        crew_name="CrewManager",
        complexity="advanced",
        estimated_time="5-10 min",
        tags=["crew", "yaml", "generator"],
        fields=[
            TemplateField(key="plan_path", label="Chemin du document Markdown", type="text", required=True),
            TemplateField(key="instructions", label="Consignes", type="textarea", required=False),
        ],
    ),
    TemplateMetadata(
        id="educational",
        name="Createur de Cours",
        description="Convertit des recherches en cours éducatifs structurés",
        category="documentation",
        crew_name="EducationalContentCreator",
        complexity="moderate",
        estimated_time="3-7 min",
        tags=["education", "course", "learning"],
        fields=[
            TemplateField(key="topic", label="Sujet du cours", type="textarea", required=True),
            TemplateField(key="project_path", label="Dossier cible", type="path", required=True),
        ],
    ),
]


@router.get("/templates", response_model=RegistryResponse)
async def get_templates():
    """List all automation templates with metadata."""
    crews = []
    agents: List[AgentMetadata] = []

    for name in get_all_crews():
        crew = get_crew(name)
        if crew:
            crews.append({
                "name": name,
                "description": crew.get("crew_settings", {}).get("description", ""),
                "process": crew.get("crew_settings", {}).get("process", ""),
            })
            for agent in crew.get("agents", []):
                agents.append(AgentMetadata(
                    name=agent.get("name", ""),
                    role=agent.get("role", ""),
                    goal=agent.get("goal", ""),
                    llm=agent.get("llm"),
                    tools=agent.get("tools", []),
                ))

    return RegistryResponse(
        templates=TEMPLATES,
        crews=crews,
        agents=agents,
    )


@router.get("/schema/{crew_name}")
async def get_crew_schema(crew_name: str):
    """Get the configuration schema for a specific crew."""
    crew = get_crew(crew_name)
    if not crew:
        return {"error": "Crew '{}' not found".format(crew_name)}

    return {
        "name": crew_name,
        "settings": crew.get("crew_settings", {}),
        "agents": [
            {
                "name": a.get("name"),
                "role": a.get("role"),
                "goal": a.get("goal"),
                "backstory": a.get("backstory"),
                "llm": a.get("llm"),
                "tools": a.get("tools", []),
                "verbose": a.get("verbose", True),
                "allow_delegation": a.get("allow_delegation", False),
            }
            for a in crew.get("agents", [])
        ],
        "tasks": [
            {
                "description": t.get("description"),
                "expected_output": t.get("expected_output"),
                "agent": t.get("agent"),
            }
            for t in crew.get("tasks", [])
        ],
    }


@router.get("/agents")
async def get_agents():
    """List all unique agents across all crews."""
    agents: List[AgentMetadata] = []
    seen = set()

    for name in get_all_crews():
        crew = get_crew(name)
        if not crew:
            continue
        for agent in crew.get("agents", []):
            agent_name = agent.get("name", "")
            if agent_name not in seen:
                seen.add(agent_name)
                agents.append(AgentMetadata(
                    name=agent_name,
                    role=agent.get("role", ""),
                    goal=agent.get("goal", ""),
                    llm=agent.get("llm"),
                    tools=agent.get("tools", []),
                ))

    return agents
