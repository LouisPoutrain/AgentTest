"""
core/router.py — Meta-Routeur ReAct avec outils individuels et dispatch de crews.

Le routeur analyse la demande utilisateur, décide de l'action à prendre,
et peut enchaîner plusieurs outils (ReAct loop) avant de répondre.

Actions possibles :
- direct_reply : réponse simple sans outil
- call_tool : appeler un outil individuel (wikipedia_search, read_pdf, arxiv_search, ...)
- call_crew : dispatcher vers un crew complet
- ask_clarification : demander des précisions à l'utilisateur
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict
from functools import lru_cache

import litellm

from app.core.crew_manager import get_all_crews, get_crew
from app.core.history_manager import history_manager
from app.core.tool_registry import AVAILABLE_TOOLS, get_tool_names

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CAPABILITIES_PATH = CONFIG_DIR / "capabilities.json"


def load_capabilities() -> Dict[str, Any]:
    """Charge les métadonnées de capacités depuis *capabilities.json*.

    Retourne un dictionnaire avec les clés ``crews`` et ``model_tiers``.
    En cas d'erreur de lecture ou de parsing, retourne un dictionnaire
    vide et log l'erreur.

    Returns:
        Dictionnaire de capacités ou dictionnaire vide en cas d'erreur.
    """
    try:
        if CAPABILITIES_PATH.exists():
            return json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Erreur chargement capabilities: %s", e)
    return {"crews": {}, "model_tiers": {}}


def get_model_for_tier(tier: str) -> str:
    """Retourne l'identifiant du modèle LLM associé à un *tier* donné.

    Args:
        tier: Un des niveaux ``"fast"``, ``"balanced"`` ou ``"expert"``.

    Returns:
        L'identifiant du modèle (ex. ``"openai/qwen-3.6-35b-instruct"``).
        En cas de tier inconnu, retourne le modèle par défaut.
    """
    caps = load_capabilities()
    tiers = caps.get("model_tiers", {})
    return tiers.get(tier, "openai/qwen-3.6-35b-instruct")


def _build_tool_list_prompt() -> str:
    """Construit la liste des outils disponibles avec descriptions."""
    tool_descriptions = []
    for name, tool_obj in AVAILABLE_TOOLS.items():
        # Extraire la docstring de l'outil
        if hasattr(tool_obj, "func") and tool_obj.func.__doc__:
            doc = tool_obj.func.__doc__.strip().split("\n")[0]
        elif hasattr(tool_obj, "__doc__") and tool_obj.__doc__:
            doc = tool_obj.__doc__.strip().split("\n")[0]
        else:
            doc = "Outil sans description."
        tool_descriptions.append(f"  - `{name}` : {doc}")
    return "\n".join(tool_descriptions)


def _build_crews_str(crews_info: Dict[str, Any]) -> str:
    """Construit la chaîne de description des crews depuis les infos de capabilities."""
    config_dir = Path(__file__).resolve().parent.parent.parent / "config" / "crews"
    crews_str = ""
    for name, info in crews_info.items():
        desc = info.get("description", "Pas de description")
        yaml_path = config_dir / f"{name}.yaml"
        req_vars = []
        if yaml_path.exists():
            content = yaml_path.read_text(encoding="utf-8")
            variables = set(re.findall(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})", content))
            req_vars = [v for v in variables if v != "message"]
        var_hint = (
            f" (Variables requises: {', '.join(req_vars)})" if req_vars else ""
        )
        crews_str += f"- **{name}**: {desc}{var_hint}\n"

    # Ajouter les crews YAML non listés dans capabilities
    if config_dir.exists():
        for yaml_path in config_dir.glob("*.yaml"):
            name = yaml_path.stem
            if name not in crews_info:
                crews_str += f"- **{name}**: Crew technique disponible.\n"
    return crews_str


@lru_cache(maxsize=1)
def build_system_prompt() -> str:
    """Construit le prompt système du routeur avec liste des outils et crews.

    Le résultat est mis en cache via LRU avec un seul slot.
    Pour invalider le cache (ex: après modification d'un fichier YAML),
    appeler ``build_system_prompt.cache_clear()``.
    """
    caps = load_capabilities()
    crews_info = caps.get("crews", {})
    crews_str = _build_crews_str(crews_info)

    tools_list = _build_tool_list_prompt()

    prompt = f"""Tu es l'Agent Orchestrateur (Meta-Routeur) d'une plateforme d'IA.
Ton rôle est d'analyser la demande de l'utilisateur, de prendre en compte l'historique de la conversation, et de décider de la meilleure action à prendre.

## Outils disponibles (tu peux les utiliser individuellement) :
{tools_list}

## Crews (équipes d'agents spécialisés) :
{crews_str}

Tu DOIS répondre UNIQUEMENT au format JSON strict avec la structure suivante :
{{
    "thought": "Ton raisonnement étape par étape",
    "action": "direct_reply" | "call_tool" | "call_crew" | "ask_clarification",
    "reply": "Ton message de réponse directe ou de demande de précision (si applicable, sinon null)",
    "tool_name": "Le nom exact de l'outil à appeler (si action=call_tool, sinon null)",
    "tool_args": {{ "nom_arg": "valeur" }},
    "crew_name": "Le nom exact du crew à appeler (si action=call_crew, sinon null)",
    "crew_inputs": {{ "Insère ici toutes les variables requises par le crew choisi en analysant la demande": "..." }},
    "llm_tier": "fast" | "balanced" | "expert"
}}

## Directives :
1. Si la question est simple ou conversationnelle, utilise "direct_reply".
2. Si la tâche nécessite un outil individuel (recherche, lecture PDF, scraping, etc.), utilise "call_tool" avec le nom et les arguments appropriés.
3. Si la tâche est complexe et nécessite plusieurs étapes ou un crew complet, utilise "call_crew".
4. Si tu as besoin de précisions, utilise "ask_clarification".
5. Tu peux enchaîner plusieurs outils dans une conversation (ReAct loop) : exécute un outil, analyse le résultat, puis décide de la prochaine action.
6. Choisis le 'llm_tier' selon la complexité : 'fast' pour le chat, 'balanced' pour le dev, 'expert' pour l'architecture/sécurité.
7. Pour les outils individuels, utilise toujours les arguments exacts demandés par l'outil (voir la liste ci-dessus).
8. Ne demande pas à l'utilisateur de copier-coler du code, utilise les outils qui ont accès au filesystem.

## Règles spécifiques pour les PDF et cours interactifs :
- Si l'utilisateur mentionne des PDF, un cours, une formation, ou un document à transformer en cours :
  1. Le crew `InteractiveCourseCreator` gère désormais des dossiers avec UN OU PLUSIEURS PDF.
     Il inventorie et analyse TOUS les PDF du dossier (en boucle, avec vérification).
  2. Tu DOIS fournir `project_path` dans `crew_inputs` : le chemin du dossier contenant les PDF.
     - Si l'utilisateur donne un dossier, utilise-le directement.
     - Si l'utilisateur donne un seul fichier PDF, utilise le dossier parent comme `project_path`.
  3. Tu peux aussi fournir `pdf_path` (un PDF principal) et `pdf_alternatives` (les autres),
     mais ce n'est plus obligatoire : le crew les détecte lui-même via `list_pdfs`.
  4. Le `output_dir` peut être généré automatiquement (ex: `./output/course_<nom_du_dossier>`).
- Exemple de `crew_inputs` pour InteractiveCourseCreator :
  {{ "project_path": "/chemin/vers/le/dossier_de_cours" }}
"""
    return prompt


def _execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Exécute un outil par son nom avec les arguments donnés."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if not tool:
        return f"Erreur : outil '{tool_name}' introuvable dans le registre."

    try:
        # Extraire la fonction sous-jacente si décorée par @tool
        func = getattr(tool, "func", tool)
        result = func(**tool_args)
        return str(result)
    except TypeError as e:
        return f"Erreur : arguments incompatibles pour '{tool_name}' : {str(e)}"
    except Exception as e:
        return f"Erreur lors de l'exécution de '{tool_name}' : {str(e)}"


def _parse_llm_response(content: str) -> Dict[str, Any]:
    """Extrait et parse le JSON d'une réponse LLM.

    Handles nested braces correctly by tracking depth and finding the
    LAST valid closing brace (where depth returns to 0), rather than
    stopping at the first one. This prevents premature truncation when
    the LLM response contains nested JSON objects (e.g. crew_inputs
    with nested dicts).
    """
    first_brace = content.find("{")
    if first_brace == -1:
        raise ValueError("No JSON object found in LLM response")

    depth = 0
    last_valid = -1
    for i, ch in enumerate(content[first_brace:]):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last_valid = first_brace + i

    if last_valid == -1:
        raise ValueError("No valid JSON object found in LLM response")

    json_str = content[first_brace : last_valid + 1]
    return json.loads(json_str)


def route_request(
    session_id: str,
    user_message: str,
    context_inputs: Dict[str, Any] = None,
    max_iterations: int = 5,
) -> Dict[str, Any]:
    """
    Route la demande utilisateur avec une boucle ReAct.

    Le routeur peut enchaîner plusieurs appels LLM + outils avant de répondre.

    Parameters
    ----------
    session_id : str
        ID de la session de conversation.
    user_message : str
        Message de l'utilisateur.
    context_inputs : dict, optional
        Contexte UI actuel (thème, langue, etc.).
    max_iterations : int
        Nombre maximum d'itérations ReAct (par défaut 5).

    Returns
    -------
    dict
        {
            "thought": str,
            "action": "direct_reply" | "call_crew" | "ask_clarification",
            "reply": str,
            "tool_name": str | None,
            "tool_result": str | None,
            "crew_name": str | None,
            "crew_inputs": dict,
            "llm_tier": str,
            "intermediate_logs": list[str],  # Logs intermédiaires du ReAct loop
        }
    """
    history = history_manager.get_history(session_id, limit=10)

    sys_content = build_system_prompt()
    if context_inputs:
        context_str = json.dumps(context_inputs, ensure_ascii=False, indent=2)
        sys_content += (
            "\n\n[CONTEXTE UI ACTUEL]\nL'utilisateur a configuré les variables suivantes :\n"
            + context_str
            + "\n\nSi 'project_path' est présent dans le contexte, utilise-le comme dossier de base pour list_directory."
        )

    # Messages de la boucle ReAct : on commence avec l'historique + le message actuel
    messages = [{"role": "system", "content": sys_content}]

    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        content = msg["content"]
        if msg.get("crew_used"):
            content = f"[Rapport du Crew {msg['crew_used']}]\\n{content}"
        messages.append({"role": role, "content": content})

    # On ajoute un placeholder pour le message utilisateur actuel
    # (il sera remplacé à chaque itération par le message + résultats intermédiaires)
    intermediate_logs: list[str] = []
    tool_results_context = ""

    final_result = None

    for iteration in range(max_iterations):
        # Construire le message complet pour cette itération
        current_messages = list(messages)
        if tool_results_context:
            current_messages.append(
                {
                    "role": "user",
                    "content": f"[RÉSULTATS D'OUTILS PRÉCÉDENTS]\n{tool_results_context}\n\n---\n\nMessage utilisateur : {user_message}",
                }
            )
        else:
            current_messages.append(
                {"role": "user", "content": user_message}
            )

        try:
            model = get_model_for_tier("fast")
            kwargs = {}
            if model.startswith("openai/"):
                kwargs["api_key"] = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
                kwargs["api_base"] = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_API_BASE")

            response = litellm.completion(
                model=model,
                messages=current_messages,
                **kwargs,
            )

            content = response.choices[0].message.content.strip()
            decision = _parse_llm_response(content)

        except Exception as e:
            logger.error("Erreur du Routeur (itération %d) : %s", iteration + 1, e)
            return {
                "thought": f"Erreur interne : {e}",
                "action": "direct_reply",
                "reply": "Désolé, j'ai rencontré une erreur lors de l'analyse de votre demande.",
                "tool_name": None,
                "tool_result": None,
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast",
                "intermediate_logs": intermediate_logs,
            }

        action = decision.get("action", "direct_reply")
        thought = decision.get("thought", "")
        reply = decision.get("reply")
        tool_name = decision.get("tool_name")
        tool_args = decision.get("tool_args", {})
        crew_name = decision.get("crew_name")
        crew_inputs = decision.get("crew_inputs", {})
        llm_tier = decision.get("llm_tier", "balanced")

        if action == "direct_reply":
            final_result = {
                "thought": thought,
                "action": "direct_reply",
                "reply": reply or "Je n'ai pas de réponse à vous fournir.",
                "tool_name": None,
                "tool_result": None,
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": llm_tier,
                "intermediate_logs": intermediate_logs,
            }
            break

        elif action == "ask_clarification":
            final_result = {
                "thought": thought,
                "action": "ask_clarification",
                "reply": reply or "Pouvez-vous préciser votre demande ?",
                "tool_name": None,
                "tool_result": None,
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": llm_tier,
                "intermediate_logs": intermediate_logs,
            }
            break

        elif action == "call_tool" and tool_name:
            log_msg = f"🔧 [Outil] {tool_name}: {json.dumps(tool_args, ensure_ascii=False)}"
            intermediate_logs.append(log_msg)

            tool_result = _execute_tool(tool_name, tool_args)
            result_log = f"📋 [Résultat {tool_name}] {tool_result[:500]}{'...' if len(tool_result) > 500 else ''}"
            intermediate_logs.append(result_log)

            tool_results_context += f"\n## Outil: {tool_name}\nRésultat: {tool_result}\n"

        elif action == "call_crew" and crew_name:
            log_msg = f"🚀 [Crew] {crew_name}: {json.dumps(crew_inputs, ensure_ascii=False)}"
            intermediate_logs.append(log_msg)

            # Fusionner le contexte UI (project_path / folderContext) pour que
            # le crew utilise toujours le dossier sélectionné par l'utilisateur.
            # On ne surcharge pas si le routeur a déjà extrait un chemin explicite
            # du message de l'utilisateur.
            if context_inputs and isinstance(context_inputs, dict):
                for key in ("project_path", "folderContext"):
                    folder = context_inputs.get(key)
                    if folder and folder != "." and "project_path" not in crew_inputs:
                        resolved = str(Path(folder).resolve())
                        crew_inputs["project_path"] = resolved
                        if "output_dir" not in crew_inputs:
                            crew_inputs["output_dir"] = resolved
                        break

            # Pour le crew, on retourne les infos nécessaires au chat.py
            # Le crew sera exécuté dans chat.py (pas ici pour éviter les blocages)
            final_result = {
                "thought": thought,
                "action": "call_crew",
                "reply": None,
                "tool_name": None,
                "tool_result": None,
                "crew_name": crew_name,
                "crew_inputs": crew_inputs,
                "llm_tier": llm_tier,
                "intermediate_logs": intermediate_logs,
            }
            break

        else:
            # Action non reconnue → fallback direct_reply
            intermediate_logs.append(f"⚠️ [Action inconnue] {action}")
            final_result = {
                "thought": thought or "Action non reconnue",
                "action": "direct_reply",
                "reply": "Je n'ai pas pu déterminer l'action appropriée.",
                "tool_name": None,
                "tool_result": None,
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast",
                "intermediate_logs": intermediate_logs,
            }
            break

    # Si on a atteint max_iterations sans décision finale, on force direct_reply
    if final_result is None:
        final_result = {
            "thought": "Nombre maximum d'itérations atteint.",
            "action": "direct_reply",
            "reply": "J'ai atteint la limite de traitement. Veuillez reformuler votre demande.",
            "tool_name": None,
            "tool_result": None,
            "crew_name": None,
            "crew_inputs": {},
            "llm_tier": "fast",
            "intermediate_logs": intermediate_logs,
        }

    return final_result
