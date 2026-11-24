"""
core/crew_builder.py — Génère un Crew YAML à partir d'une description en langage naturel.

Utilise un LLM pour analyser la demande utilisateur et produire un YAML CrewAI
valide (agents + tâches) qui sera sauvegardé et exécuté automatiquement.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import litellm

from app.core.config import CREWS_DIR, LLM_API_KEY, LLM_BASE_URL
from app.core.crew_manager import create_crew, add_agent, add_task, get_crew
from app.core.tool_registry import get_tool_names

logger = logging.getLogger(__name__)

# ── Prompt système pour le builder ───────────────────────────────────────────

BUILDER_SYSTEM_PROMPT = """Tu es le Builder Agent d'une plateforme d'automatisation IA.
Ta mission est de générer un fichier YAML CrewAI valide à partir d'une description en langage naturel.

Règles strictes :
1. Réponds UNIQUEMENT avec un JSON valide (pas de markdown, pas de texte autour).
2. Le JSON doit avoir la structure suivante :
{{
    "crew_name": "nom_du_crew_en_snake_case",
    "description": "Description courte du crew",
    "agents": [
        {{
            "name": "nom_agent",
            "role": "Rôle court",
            "goal": "Objectif détaillé",
            "backstory": "Contexte de l'agent",
            "llm": "openai/",
            "tools": ["outil1", "outil2"],
            "verbose": true,
            "allow_delegation": false
        }}
    ],
    "tasks": [
        {{
            "description": "Description de la tâche",
            "expected_output": "Résultat attendu",
            "agent": "nom_agent"
        }}
    ]
}}
3. Crée au moins 1 agent et 1 tâche.
4. Les noms d'agents doivent être en snake_case.
5. Les outils doivent être choisis parmi cette liste : {available_tools}
6. Si la demande est simple, un seul agent suffit.
7. Si la demande est complexe, crée plusieurs agents en séquence.
8. Le crew_name doit être unique et descriptif.
9. L'agent principal (premier) doit avoir allow_delegation: true si d'autres agents existent.
10. Les tâches doivent être enchaînées logiquement.
"""


def _get_litellm_kwargs() -> dict[str, str]:
    """Retourne les kwargs LiteLLM configurés."""
    kwargs: dict[str, str] = {}
    api_key = LLM_API_KEY or ""
    base_url = LLM_BASE_URL or ""
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    return kwargs


def _extract_json(text: str) -> str:
    """Extrait le premier bloc JSON valide d'une réponse LLM."""
    # Essayer de trouver un bloc JSON entre ```json ... ```
    json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if json_match:
        return json_match.group(1).strip()

    # Chercher le premier { et le dernier } correspondant
    first_brace = text.find("{")
    if first_brace == -1:
        raise ValueError("No JSON object found in LLM response")

    depth = 0
    last_valid = -1
    for i, ch in enumerate(text[first_brace:]):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last_valid = first_brace + i
                break

    if last_valid == -1:
        raise ValueError("No valid JSON object found in LLM response")

    return text[first_brace : last_valid + 1]


def build_crew_from_description(
    description: str,
    project_path: str = ".",
) -> dict[str, Any]:
    """
    Génère un Crew YAML à partir d'une description en langage naturel.

    1. Appelle un LLM pour générer le YAML structuré
    2. Sauvegarde le YAML sur disque
    3. Retourne le crew créé

    Raises
    ------
    RuntimeError
        Si le LLM échoue ou retourne un JSON invalide.
    """
    available_tools = get_tool_names()
    tool_list = ", ".join(available_tools)

    user_prompt = (
        f"L'utilisateur veut créer une automatisation pour : {description}\n\n"
        f"Projet cible : {project_path}\n\n"
        f"Génère le YAML CrewAI correspondant."
    )

    try:
        model = "openai/"
        kwargs = _get_litellm_kwargs()

        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": BUILDER_SYSTEM_PROMPT.format(available_tools=tool_list),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
            **kwargs,
        )

        content = response.choices[0].message.content.strip()
        json_str = _extract_json(content)
        crew_config = json.loads(json_str)

    except Exception as e:
        logger.error("Crew builder LLM error: %s", e, exc_info=True)
        raise RuntimeError(f"Le Builder n'a pas pu générer le crew : {e}")

    # ── Valider la structure ──────────────────────────────────────────────
    if "crew_name" not in crew_config:
        raise RuntimeError("Le Builder n'a pas fourni de crew_name")
    if "agents" not in crew_config or not isinstance(crew_config["agents"], list):
        raise RuntimeError("Le Builder n'a pas fourni de agents")
    if "tasks" not in crew_config or not isinstance(crew_config["tasks"], list):
        raise RuntimeError("Le Builder n'a pas fourni de tasks")
    if len(crew_config["agents"]) == 0:
        raise RuntimeError("Le Builder n'a créé aucun agent")
    if len(crew_config["tasks"]) == 0:
        raise RuntimeError("Le Builder n'a créé aucune tâche")

    # ── Créer le crew dans le système ─────────────────────────────────────
    crew_name = crew_config["crew_name"]

    # S'assurer que le nom est unique
    existing = CREWS_DIR.glob(f"{crew_name}*.yaml")
    for f in existing:
        f.unlink()  # Supprimer l'ancien s'il existe

    # Créer le YAML de base
    create_crew(
        crew_name=crew_name,
        process="Séquentiel",
        memory=True,
        max_rpm=15,
    )

    # Ajouter les agents
    for agent_data in crew_config["agents"]:
        # Appliquer les valeurs par défaut
        agent_data.setdefault("llm", "openai/")
        agent_data.setdefault("tools", [])
        agent_data.setdefault("verbose", True)
        agent_data.setdefault("allow_delegation", False)
        add_agent(crew_name, agent_data)

    # Ajouter les tâches
    for task_data in crew_config["tasks"]:
        add_task(crew_name, task_data)

    return get_crew(crew_name)


def build_and_run_crew(
    description: str,
    project_path: str = ".",
) -> dict[str, Any]:
    """
    Construit un crew depuis une description ET le lance immédiatement.

    Retourne le résultat de l'exécution.
    """
    from app.core.crew_runner import run_crew

    # 1. Construire le crew
    crew_info = build_crew_from_description(description, project_path)
    crew_name = crew_info["name"]

    # 2. Lancer l'exécution
    result_chunks = list(run_crew(
        crew_name=crew_name,
        message=description,
        inputs={"message": description, "project_path": project_path},
    ))

    # 3. Extraire le résultat final
    final_result = ""
    for chunk in result_chunks:
        try:
            data = json.loads(chunk)
            if data.get("type") == "result":
                final_result = data.get("content", "")
        except Exception:
            pass

    return {
        "crew_name": crew_name,
        "result": final_result,
        "logs": [c for c in result_chunks if json.loads(c).get("type") == "log"],
    }
