"""
core/crew_manager.py — Gestion CRUD des Crews (sans aucune dépendance UI).

Fonctions pour lister, charger, créer, supprimer des Crews,
ajouter des agents/tâches, importer depuis GitHub, et lister les modèles Gemini.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

import yaml
import google.generativeai as genai

from app.core.git_importer import download_yaml_from_github

# ── Configuration ────────────────────────────────────────────────────────────

CREWS_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "crews"
CREWS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODELS = [
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-pro",
]


# ── CRUD Crews ───────────────────────────────────────────────────────────────


def get_all_crews() -> list[str]:
    """Retourne la liste des noms de fichiers YAML dans config/crews/."""
    return sorted(f.stem for f in CREWS_DIR.glob("*.yaml"))


def get_crew(crew_name: str) -> dict[str, Any]:
    """Charge un Crew complet (settings, agents, tasks) depuis son YAML."""
    path = _resolve_path(crew_name)
    if not path.exists():
        raise FileNotFoundError(f"Crew '{crew_name}' introuvable.")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "name": crew_name,
        "description": data.get("description", "Aucune description fournie."),
        "crew_settings": data.get("crew_settings", {}),
        "agents": data.get("agents", []),
        "tasks": data.get("tasks", []),
    }


def get_all_agents() -> list[dict[str, Any]]:
    """Retourne la liste de tous les agents (uniques par nom) de tous les Crews."""
    all_agents = []
    seen = set()
    for crew_name in get_all_crews():
        crew = get_crew(crew_name)
        for agent in crew.get("agents", []):
            name = agent.get("name")
            if name and name not in seen:
                all_agents.append(agent)
                seen.add(name)
    return all_agents


def create_crew(
    crew_name: str,
    process: str = "Séquentiel",
    memory: bool = True,
    max_rpm: int = 15,
) -> dict[str, Any]:
    """Crée un nouveau fichier YAML pour un Crew."""
    path = _resolve_path(crew_name)
    if path.exists():
        raise FileExistsError(f"Le Crew '{crew_name}' existe déjà.")

    config = {
        "crew_settings": {
            "process": process,
            "memory": memory,
            "max_rpm": max_rpm,
        },
        "agents": [],
        "tasks": [],
    }
    _save_yaml(path, config)
    return get_crew(crew_name)


def delete_crew(crew_name: str) -> None:
    """Supprime le fichier YAML d'un Crew."""
    path = _resolve_path(crew_name)
    if not path.exists():
        raise FileNotFoundError(f"Crew '{crew_name}' introuvable.")
    path.unlink()


def add_agent(crew_name: str, agent_data: dict[str, Any]) -> dict[str, Any]:
    """Ajoute un agent à un Crew existant."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)

    agents = config.setdefault("agents", [])
    existing_names = [a.get("name") for a in agents]
    if agent_data.get("name") in existing_names:
        raise ValueError(f"L'agent '{agent_data['name']}' existe déjà dans {crew_name}.")

    agents.append(agent_data)
    _save_yaml(path, config)
    return get_crew(crew_name)


def update_crew_settings(crew_name: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Met à jour les paramètres globaux d'un Crew."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    config["crew_settings"] = {**config.get("crew_settings", {}), **settings}
    _save_yaml(path, config)
    return get_crew(crew_name)


def update_agent(crew_name: str, agent_index: int, agent_data: dict[str, Any]) -> dict[str, Any]:
    """Met à jour un agent existant par son index."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    agents = config.get("agents", [])
    if agent_index < 0 or agent_index >= len(agents):
        raise IndexError(f"Index d'agent {agent_index} invalide (total: {len(agents)}).")
    agents[agent_index] = agent_data
    _save_yaml(path, config)
    return get_crew(crew_name)


def delete_agent(crew_name: str, agent_index: int) -> dict[str, Any]:
    """Supprime un agent par son index."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    agents = config.get("agents", [])
    if agent_index < 0 or agent_index >= len(agents):
        raise IndexError(f"Index d'agent {agent_index} invalide (total: {len(agents)}).")
    agents.pop(agent_index)
    _save_yaml(path, config)
    return get_crew(crew_name)


def add_task(crew_name: str, task_data: dict[str, Any]) -> dict[str, Any]:
    """Ajoute une tâche à un Crew existant."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    config.setdefault("tasks", []).append(task_data)
    _save_yaml(path, config)
    return get_crew(crew_name)


def update_task(crew_name: str, task_index: int, task_data: dict[str, Any]) -> dict[str, Any]:
    """Met à jour une tâche existante par son index."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    tasks = config.get("tasks", [])
    if task_index < 0 or task_index >= len(tasks):
        raise IndexError(f"Index de tâche {task_index} invalide (total: {len(tasks)}).")
    tasks[task_index] = task_data
    _save_yaml(path, config)
    return get_crew(crew_name)


def delete_task(crew_name: str, task_index: int) -> dict[str, Any]:
    """Supprime une tâche par son index."""
    path = _resolve_path(crew_name)
    config = _load_yaml(path)
    tasks = config.get("tasks", [])
    if task_index < 0 or task_index >= len(tasks):
        raise IndexError(f"Index de tâche {task_index} invalide (total: {len(tasks)}).")
    tasks.pop(task_index)
    _save_yaml(path, config)
    return get_crew(crew_name)


def import_from_github(raw_url: str, crew_name: str) -> dict[str, Any]:
    """Importe un Crew depuis GitHub."""
    download_yaml_from_github(raw_url, CREWS_DIR, crew_name)
    return get_crew(crew_name)


# ── Modèles Gemini ──────────────────────────────────────────────────────────

_models_cache: list[str] | None = None


def get_available_models() -> list[str]:
    """Récupère dynamiquement les modèles Gemini, Ollama et Custom (LLM_BASE_URL)."""
    global _models_cache
    if _models_cache is not None:
        return _models_cache

    models = []

    # 1. Récupération des modèles locaux Ollama
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                for m in data.get("models", []):
                    name = m.get("name")
                    if name:
                        models.append(f"ollama/{name}")
    except Exception:
        pass  # Ollama non disponible, on ignore silencieusement

    # 2. Récupération des modèles Custom (LLM_BASE_URL)
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_api_key = os.getenv("LLM_API_KEY")
    if llm_base_url and llm_api_key:
        try:
            req = urllib.request.Request(f"{llm_base_url}/models", method="GET")
            req.add_header("Authorization", f"Bearer {llm_api_key}")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    for m in data.get("data", []):
                        name = m.get("id")
                        if name:
                            models.append(f"openai/{name}")
        except Exception:
            pass

    # 3. Récupération des modèles Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            gemini_models = genai.list_models()
            models.extend([
                f"gemini/{m.name.replace('models/', '')}"
                for m in gemini_models
                if "generateContent" in m.supported_generation_methods
            ])
        except Exception:
            pass

    # Fallback si rien n'est trouvé
    if not models:
        models = DEFAULT_MODELS

    _models_cache = models
    return _models_cache


# ── Helpers privés ───────────────────────────────────────────────────────────


def _resolve_path(crew_name: str) -> Path:
    """Transforme un nom de crew en chemin absolu vers le YAML."""
    filename = crew_name if crew_name.endswith(".yaml") else f"{crew_name}.yaml"
    return CREWS_DIR / filename


def _load_yaml(path: Path) -> dict:
    """Charge un YAML et retourne son contenu."""
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: dict) -> None:
    """Sauvegarde un dictionnaire en YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

