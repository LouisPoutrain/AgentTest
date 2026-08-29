"""
core/agent_parser.py — Parseur de configuration YAML pour agents et tâches CrewAI.

Lit un fichier YAML standardisé et instancie dynamiquement
des objets ``Agent`` et ``Task`` natifs de CrewAI.

Formats supportés :
- **Crew complet** : clés ``agents`` + ``tasks`` au même niveau.
- **Agents seuls** : clé ``agents`` (liste) ou agent unique (legacy).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Task, Process


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_yaml(yaml_path: str | Path) -> dict:
    """Charge et retourne le contenu brut d'un fichier YAML."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_agent(
    config: dict[str, Any],
    available_tools: dict[str, Any],
    source_name: str,
) -> Agent:
    """Instancie un ``Agent`` CrewAI à partir d'un dictionnaire de config.

    Raises
    ------
    KeyError
        Si une clé obligatoire est absente.
    ValueError
        Si un outil référencé n'existe pas dans *available_tools*.
    """
    # Validation des clés obligatoires
    required_keys = {"role", "goal", "backstory"}
    missing = required_keys - config.keys()
    if missing:
        agent_id = config.get("name", "inconnu")
        raise KeyError(
            f"Clés manquantes pour l'agent « {agent_id} » "
            f"dans {source_name} : {', '.join(missing)}"
        )

    # Résolution des outils
    tool_names: list[str] = config.get("tools") or []
    resolved_tools = []
    for name in tool_names:
        if name not in available_tools:
            raise ValueError(
                f"Outil « {name} » référencé dans {source_name} "
                f"mais absent de available_tools : {list(available_tools.keys())}"
            )
        resolved_tools.append(available_tools[name])

    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        verbose=config.get("verbose", False),
        allow_delegation=config.get("allow_delegation", False),
        tools=resolved_tools,
        llm=config.get("llm"),
    )


# ── API publique ─────────────────────────────────────────────────────────────


def create_agents_from_yaml(
    yaml_path: str | Path,
    available_tools: dict[str, Any] | None = None,
    llm_override: str | None = None,
) -> list[Agent]:
    """Charge **tous** les agents définis dans un fichier YAML.

    Le fichier peut contenir :
    - Une clé ``agents`` (liste de configurations d'agents).
    - Ou directement les clés d'un agent unique (rétro-compatible).

    Returns
    -------
    list[Agent]
        Liste d'agents CrewAI instanciés, dans l'ordre du YAML.
    """
    raw = _load_yaml(yaml_path)
    tools = available_tools or {}
    source = Path(yaml_path).name

    # Format « crew » : clé agents contenant une liste
    if "agents" in raw and isinstance(raw["agents"], list):
        agents_to_build = []
        for agent_cfg in raw["agents"]:
            if llm_override:
                agent_cfg["llm"] = llm_override
            agents_to_build.append(_build_agent(agent_cfg, tools, source))
        return agents_to_build

    # Format legacy : agent unique à la racine
    if llm_override:
        raw["llm"] = llm_override
    return [_build_agent(raw, tools, source)]


def create_tasks_from_yaml(
    yaml_path: str | Path,
    agents_list: list[Agent],
) -> list[Task]:
    """Charge les tâches définies dans la section ``tasks`` du YAML.

    Chaque tâche référence un agent par son ``name`` (clé ``agent``).
    L'objet Agent correspondant est retrouvé dans *agents_list* via
    le mapping ``name → Agent`` construit à partir du YAML.

    Parameters
    ----------
    yaml_path:
        Chemin vers le fichier YAML contenant la section ``tasks``.
    agents_list:
        Liste d'agents déjà instanciés (depuis ``create_agents_from_yaml``).

    Returns
    -------
    list[Task]
        Liste de tâches CrewAI instanciées, dans l'ordre du YAML.

    Raises
    ------
    ValueError
        Si la section ``tasks`` est absente ou si un agent référencé
        n'existe pas dans la liste fournie.
    """
    raw = _load_yaml(yaml_path)
    source = Path(yaml_path).name

    task_configs = raw.get("tasks")
    if not task_configs:
        raise ValueError(f"Aucune section « tasks » trouvée dans {source}")

    # Construire le mapping name → Agent à partir du YAML source
    agents_raw = raw.get("agents", [])
    name_to_agent: dict[str, Agent] = {}
    for i, agent_cfg in enumerate(agents_raw):
        agent_name = agent_cfg.get("name")
        if agent_name and i < len(agents_list):
            name_to_agent[agent_name] = agents_list[i]

    tasks: list[Task] = []
    for task_cfg in task_configs:
        agent_name = task_cfg.get("agent")
        if agent_name not in name_to_agent:
            raise ValueError(
                f"Tâche référence l'agent « {agent_name} » "
                f"mais aucun agent avec ce nom n'existe dans {source}. "
                f"Agents disponibles : {list(name_to_agent.keys())}"
            )

        tasks.append(
            Task(
                description=task_cfg["description"],
                expected_output=task_cfg["expected_output"],
                agent=name_to_agent[agent_name],
            )
        )

    return tasks


def get_crew_settings_from_yaml(yaml_path: str | Path) -> dict[str, Any]:
    """Extrait la configuration globale du Crew depuis la section crew_settings.

    Returns
    -------
    dict
        Dictionnaire contenant 'process', 'memory', et 'max_rpm' avec des valeurs par défaut.
    """
    raw = _load_yaml(yaml_path)
    settings = raw.get("crew_settings", {})
    
    # Processus : Séquentiel par défaut
    process_str = settings.get("process", "Séquentiel")
    process_enum = Process.hierarchical if process_str == "Hiérarchique" else Process.sequential
    
    return {
        "process": process_enum,
        "memory": settings.get("memory", True),
        "max_rpm": settings.get("max_rpm", 15),
    }


# ── Alias rétro-compatible (Phase 2–3) ───────────────────────────────────────


def create_agent_from_yaml(
    yaml_path: str | Path,
    available_tools: dict[str, Any] | None = None,
) -> Agent:
    """Rétro-compatibilité — retourne le premier agent du fichier."""
    agents = create_agents_from_yaml(yaml_path, available_tools)
    return agents[0]
