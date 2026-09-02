import json
import logging
import os
from typing import Dict, Any, Optional
import litellm
from pathlib import Path

from app.core.crew_manager import get_all_crews, get_crew
from app.core.history_manager import history_manager

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CAPABILITIES_PATH = CONFIG_DIR / "capabilities.json"

def load_capabilities() -> Dict[str, Any]:
    try:
        if CAPABILITIES_PATH.exists():
            return json.loads(CAPABILITIES_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        logger.error(f"Erreur chargement capabilities: {e}")
    return {"crews": {}, "model_tiers": {}}

def get_model_for_tier(tier: str) -> str:
    caps = load_capabilities()
    tiers = caps.get("model_tiers", {})
    # Fallback si le tier n'est pas défini
    return tiers.get(tier, "openai/qwen-3.6-35b-instruct")

def build_system_prompt() -> str:
    caps = load_capabilities()
    crews_info = caps.get("crews", {})

    crews_str = ""
    for name, info in crews_info.items():
        crews_str += f"- **{name}**: {info.get('description', 'Pas de description')}\n"

    prompt = f"""Tu es l'Agent Orchestrateur (Meta-Routeur) d'une plateforme d'IA.
Ton rôle est d'analyser la demande de l'utilisateur, de prendre en compte l'historique de la conversation, et de décider de la meilleure action à prendre.

Voici les Crews (équipes d'agents spécialisés) dont tu disposes :
{crews_str}

Tu DOIS répondre UNIQUEMENT au format JSON strict avec la structure suivante :
{{
    "thought": "Ton raisonnement étape par étape",
    "action": "direct_reply" | "call_crew" | "ask_clarification",
    "reply": "Ton message de réponse directe ou de demande de précision (si applicable, sinon null)",
    "crew_name": "Le nom exact du crew à appeler (si action=call_crew, sinon null)",
    "crew_inputs": {{ "project_path": "...", "topic": "..." }},
    "llm_tier": "fast" | "balanced" | "expert"
}}

Directives :
1. Si la question est simple ou conversationnelle, utilise "direct_reply".
2. Si la tâche demande du code, de l'audit, de la recherche ou une action sur des fichiers, utilise "call_crew".
3. Ne demande pas à l'utilisateur de copier-coler du code, utilise les crews qui ont accès au filesystem.
4. Choisis le 'llm_tier' selon la complexité : 'fast' pour le chat, 'balanced' pour le dev, 'expert' pour l'architecture/sécurité.
"""
    return prompt

def route_request(session_id: str, user_message: str, context_inputs: Dict[str, Any] = None) -> Dict[str, Any]:
    history = history_manager.get_history(session_id, limit=10)

    sys_content = build_system_prompt()
    if context_inputs:
        context_str = json.dumps(context_inputs, ensure_ascii=False, indent=2)
        sys_content += f"\\n\\n[CONTEXTE UI ACTUEL]\\nL'utilisateur a configuré les variables suivantes :\\n{context_str}"

    messages = [{"role": "system", "content": sys_content}]

    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        content = msg["content"]
        if msg.get("crew_used"):
            content = f"[Rapport du Crew {msg['crew_used']}]\\n{content}"
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    try:
        model = get_model_for_tier("fast")
        kwargs = {}
        if model.startswith("openai/"):
            kwargs["api_key"] = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
            kwargs["api_base"] = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_API_BASE")

        # Le routeur lui-même utilise un modèle "fast" pour être réactif
        response = litellm.completion(
            model=model,
            messages=messages,
            **kwargs
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]

        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"Erreur du Routeur : {e}")
        return {
            "thought": f"Erreur interne: {e}",
            "action": "direct_reply",
            "reply": "Désolé, j'ai rencontré une erreur lors de l'analyse de votre demande."
        }
