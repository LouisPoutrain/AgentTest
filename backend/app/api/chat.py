"""API routes pour le chat (exécution de Crew en SSE streaming et Orchestration Meta-Routeur)."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.crew_runner import run_crew, run_multi_crew
from app.schemas.chat import ChatRequest
from app.core.router import route_request, get_model_for_tier
from app.core.history_manager import history_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# Dossiers prioritaires pour la recherche de PDFs éducatifs
_EDUCATION_DIR_NAMES = {
    "cours", "formation", "documents", "docs", "learn",
    "education", "teaching", "lecture", "notes", "support",
    "cours_etudiants", "ressources", "materials",
}

# Mots-clés académiques pour les PDFs
_ACADEMIC_KEYWORDS = {
    "sw", "owl", "reasoning", "semantic", "web", "course",
    "lecture", "tp", "td", "exercises", "exam", "thesis",
}


def _pdf_relevance_score(path: str) -> int:
    """
    Score de pertinence d'un PDF pour un cours.
    Plus le score est élevé, plus le PDF est pertinent.

    Critères :
    - Dossiers éducatifs dans le chemin : +10 par occurrence
    - Mots-clés académiques : +5 par occurrence
    - Profondeur du fichier (plus proche de la racine = mieux) : -1 par niveau
    """
    parts = Path(path).parts
    score = 0
    depth = len(parts)
    for part in parts:
        lower = part.lower()
        if lower in _EDUCATION_DIR_NAMES:
            score += 10
        if lower in _ACADEMIC_KEYWORDS:
            score += 5
    # Pénaliser les fichiers très profonds (probablement dans des sous-dossiers de projets)
    score -= max(0, depth - 6)
    return score


def _find_pdfs_in_directory(directory: str) -> list[str]:
    """
    Recherche récursivement tous les fichiers .pdf dans un dossier.
    Retourne une liste de chemins absolus triés par pertinence.

    Stratégie de recherche :
    1. Si directory est un chemin valide -> on scanne uniquement ce dossier
    2. Les PDFs sont triés par pertinence (dossiers éducatifs en premier)
    3. Si rien trouvé -> on retourne une liste vide
    """
    try:
        base = Path(directory).resolve()
        if not base.is_dir():
            return []

        # Scan uniquement le dossier spécifié, pas de remontée parentale.
        # L'utilisateur contrôle où chercher via project_path.
        pdfs = sorted(str(p) for p in base.rglob("*.pdf"))
        return sorted(pdfs, key=_pdf_relevance_score, reverse=True)
    except Exception as e:
        logger.warning("Failed to find PDFs in %s: %s", directory, e)
        return []


def _make_chunk(chunk_type: str, content: str, **kwargs) -> str:
    """Crée un chunk JSON formaté pour le SSE."""
    payload = {
        "type": chunk_type,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    payload.update(kwargs)
    return json.dumps(payload)


def _inject_pdf_inputs(crew_inputs: dict[str, Any], project_path: str):
    """Injecte les chemins PDF et output_dir dans les inputs du crew.

    Résout le chemin du projet, ajoute ``pdf_path`` / ``pdf_alternatives``
    si des PDF sont trouvés, et fixe ``output_dir`` à un sous-dossier
    ``cours_interactif``.

    Args:
        crew_inputs: Dictionnaire des inputs du crew (modifié en place).
        project_path: Chemin du dossier projet à scanner.

    Yields:
        Des chunks SSE de type ``log`` pour informer l'utilisateur.
    """
    resolved_project = str(Path(project_path).resolve())
    crew_inputs["project_path"] = resolved_project
    crew_inputs["output_dir"] = str(Path(resolved_project) / "cours_interactif")

    pdfs = _find_pdfs_in_directory(str(project_path))
    if pdfs:
        crew_inputs["pdf_path"] = pdfs[0]
        if "pdf_alternatives" not in crew_inputs:
            crew_inputs["pdf_alternatives"] = pdfs[1:] if len(pdfs) > 1 else []
        yield f"data: {_make_chunk('log', f'📄 {len(pdfs)} PDF(s) détecté(s) dans {project_path}')}\n\n"
    else:
        yield f"data: {_make_chunk('log', f'⚠️ Aucun PDF trouvé dans {project_path}')}\n\n"


@router.post(
    "/chat",
    summary="Send a message and receive SSE streaming results",
    description=(
        "POST /api/chat — Server-Sent Events (SSE) streaming endpoint.\n\n"
        "The client sends a ChatRequest and receives a stream of JSON chunks.\n"
        "Each chunk has a 'type' field indicating its purpose:\n\n"
        "  - session_info: Sent first. Contains the session_id for the conversation.\n"
        "    Payload: {\"type\": \"session_info\", \"content\": \"<session_id>\", \"session_id\": \"...\"}\n\n"
        "  - log: Streaming log messages from the crew execution or meta-router.\n"
        "    Payload: {\"type\": \"log\", \"content\": \"<log message>\"}\n\n"
        "  - result: The final result of the crew execution or direct reply.\n"
        "    Payload: {\"type\": \"result\", \"content\": \"<final result text>\"}\n\n"
        "  - error: An error occurred during execution.\n"
        "    Payload: {\"type\": \"error\", \"content\": \"<error message>\"}\n\n"
        "  - step: Crew execution step status updates.\n"
        "    Payload: {\"type\": \"step\", \"content\": \"<step description>\", \"status\": \"running|completed|error\", \"stepKey\": \"...\"}\n\n"
        "  - metrics: Token and cost metrics for the execution.\n"
        "    Payload: {\"type\": \"metrics\", \"content\": \"<metrics summary>\", \"tokens\": 0, \"cost\": 0.0}\n\n"
        "Streaming lifecycle:\n"
        "1. session_info is sent immediately to establish the session.\n"
        "2. Log messages stream in real-time as the crew executes.\n"
        "3. A final result or error chunk is sent when execution completes.\n"
        "4. The connection closes after the final chunk.\n\n"
        "The meta-router (ReAct loop) may:\n"
        "- Reply directly (direct_reply)\n"
        "- Ask for clarification (ask_clarification)\n"
        "- Delegate to a crew (call_crew)\n\n"
        "Multi-crew mode: if crew_names is provided, multiple crews execute\n"
        "sequentially or in parallel based on execution_mode."
    ),
    tags=["chat"],
    responses={
        200: {"description": "SSE stream started successfully."},
        400: {"description": "Invalid request body or unauthorized LLM model."},
    },
)
async def chat(request: ChatRequest):
    """Launch crew execution or the meta-router and stream logs via SSE.

    This is the main chat endpoint. It handles:
    - Direct LLM replies (meta-router direct_reply)
    - Clarification requests (meta-router ask_clarification)
    - Crew delegation (meta-router call_crew)
    - Multi-crew sequential/parallel execution
    - PDF-based interactive course creation

    The response is an SSE stream with chunk types: session_info, log, result, error.
    """

    if request.llm_override:
        if not (request.llm_override.startswith("openai/") or request.llm_override.startswith("anthropic/") or request.llm_override.startswith("gemini/")):
            raise HTTPException(status_code=400, detail="Modèle LLM non autorisé.")

    # 1. Gestion de la session
    session_id = history_manager.get_or_create_session(request.session_id)

    # 2. Sauvegarde du message utilisateur
    history_manager.add_message(session_id, role="user", content=request.message)

    def event_generator():
        # Initialize target_crew_name to avoid UnboundLocalError
        # when the meta-router takes direct_reply or ask_clarification.
        target_crew_name: str | None = None
        crew_inputs: dict[str, Any] = {}
        llm_to_use: str | None = None
        final_result: str = ""
        crew_used: str | None = None

        try:
            # Transmettre le session_id au client dès le début
            yield f"data: {_make_chunk('session_info', session_id, session_id=session_id)}\n\n"

            # --- MULTI-CREW EXECUTION ---
            if request.crew_names and len(request.crew_names) > 0:
                mode_label = "séquentiel" if request.execution_mode == "sequential" else "parallèle"
                yield f"data: {_make_chunk('log', f'🚀 [Mission] Lancement de {len(request.crew_names)} crew(s) en mode {mode_label}')}\n\n"

                for crew_name in request.crew_names:
                    yield f"data: {_make_chunk('log', f'  - {crew_name} [en attente]', crewName=crew_name)}\n\n"

                for chunk in run_multi_crew(
                    crew_names=request.crew_names,
                    message=request.message,
                    execution_mode=request.execution_mode,
                    inputs=request.inputs or {},
                    max_rpm=request.max_rpm,
                    llm_override=request.llm_override,
                ):
                    try:
                        data = json.loads(chunk)
                        if data.get("type") == "result":
                            final_result = data.get("content", "")
                    except Exception:
                        pass
                    yield f"data: {chunk}\n\n"

                crew_used = ", ".join(request.crew_names)

            # Si un crew est forcé manuellement (ex: depuis l'UI spécifique)
            elif request.crew_name and request.crew_name != "default":
                target_crew_name = request.crew_name
                crew_inputs = request.inputs or {}
                llm_to_use = request.llm_override

                # Injection automatique des PDF pour InteractiveCourseCreator (chemin manuel)
                if target_crew_name == "InteractiveCourseCreator":
                    project_path = crew_inputs.get("project_path", ".")
                    for chunk in _inject_pdf_inputs(crew_inputs, project_path):
                        yield chunk

                yield f"data: {_make_chunk('log', f'🚀 [Exécution Manuelle] Lancement du crew {target_crew_name}')}\n\n"
            else:
                # --- META-ROUTEUR (ReAct Loop) ---
                yield f"data: {_make_chunk('log', '🧠 [Routeur] Analyse de votre demande...')}\n\n"

                route_result = route_request(
                    session_id,
                    request.message,
                    context_inputs=request.inputs,
                )

                thought = route_result.get("thought", "")
                action = route_result.get("action", "direct_reply")
                reply = route_result.get("reply")
                target_crew_name = route_result.get("crew_name")
                crew_inputs = route_result.get("crew_inputs", {})
                llm_tier = route_result.get("llm_tier", "balanced")
                intermediate_logs = route_result.get("intermediate_logs", [])
                tool_result = route_result.get("tool_result")

                # Stream du Thought
                if thought:
                    yield f"data: {_make_chunk('log', f'💡 [Réflexion] {thought}')}\n\n"

                # Stream des logs intermédiaires (outils exécutés)
                for log in intermediate_logs:
                    yield f"data: {_make_chunk('log', log)}\n\n"

                if action in ["direct_reply", "ask_clarification"]:
                    if reply:
                        history_manager.add_message(session_id, role="assistant", content=reply)
                        yield f"data: {_make_chunk('result', reply)}\n\n"
                    return

                elif action == "call_crew" and target_crew_name:
                    llm_to_use = request.llm_override or get_model_for_tier(llm_tier)

                    # Injection automatique des PDF pour InteractiveCourseCreator
                    if target_crew_name == "InteractiveCourseCreator":
                        project_path = (request.inputs or {}).get("project_path", ".")
                        for chunk in _inject_pdf_inputs(crew_inputs, project_path):
                            yield chunk

                    yield f"data: {_make_chunk('log', f'⚡ [Action] Délégation au crew {target_crew_name} (Modèle: {llm_tier})')}\n\n"
                else:
                    fallback_msg = "Je n'ai pas pu déterminer l'action appropriée."
                    history_manager.add_message(session_id, role="assistant", content=fallback_msg)
                    yield f"data: {_make_chunk('result', fallback_msg)}\n\n"
                    return

            # --- EXECUTION DU CREW ---
            if target_crew_name:
                for chunk in run_crew(
                    crew_name=target_crew_name,
                    message=request.message,
                    inputs=crew_inputs,
                    max_rpm=request.max_rpm,
                    llm_override=llm_to_use,
                ):
                    # Parse chunk to get final result if it's a result chunk
                    try:
                        data = json.loads(chunk)
                        if data.get("type") == "result":
                            final_result = data.get("content", "")
                    except Exception:
                        pass

                    yield f"data: {chunk}\n\n"

                crew_used = target_crew_name

        finally:
            # Always persist the assistant response, even on error or early termination
            if final_result:
                history_manager.add_message(
                    session_id,
                    role="assistant",
                    content=final_result,
                    crew_used=crew_used,
                )
            else:
                history_manager.add_message(
                    session_id,
                    role="assistant",
                    content="[Exécution terminée sans résultat textuel]",
                    crew_used=crew_used,
                )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
