"""API routes pour le chat (exécution de Crew en SSE streaming)."""

from __future__ import annotations

import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.crew_runner import run_crew
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


def should_delegate_to_upgrader(user_message: str) -> bool:
    """Détecte si la demande de l'utilisateur nécessite l'Upgrader crew.
    
    Analyse le message pour identifier des intentions liées à la mise à jour,
    au refactoring ou à la sécurité.
    """
    if not user_message:
        return False
    
    message_lower = user_message.lower()
    
    # Liste de mots-clés déclencheurs regex
    triggers = [
        r"\bupgrade\b", 
        r"\bmise\s+a\s+jour\b", 
        r"\brefactor\b", 
        r"\bupdate\s+dependencies\b",
        r"\bcve\b",
        r"\bvulnérabilite\b", 
        r"\bvulnerability\b"
    ]
    
    for trigger in triggers:
        if re.search(trigger, message_lower):
            return True
    
    return False


@router.post("/chat")
async def chat(request: ChatRequest):
    """Lance l'exécution d'un Crew et streame les logs en SSE.

    Chaque ligne envoyée est un JSON :
    - type "log" : message de progression
    - type "result" : résultat final du kickoff
    - type "error" : erreur (dont 429 avec modèles alternatifs)
    """
    from fastapi import HTTPException
    
    if request.llm_override:
        # Liste blanche basique pour éviter les injections de modèles aléatoires
        if not (request.llm_override.startswith("openai/") or request.llm_override.startswith("gemini/") or request.llm_override.startswith("anthropic/")):
            raise HTTPException(status_code=400, detail="Modèle LLM non autorisé.")

    # LOGIQUE DE DÉLÉGATION
    target_crew_name = request.crew_name
    
    # Si l'utilisateur n'a pas spécifié de crew ou a utilisé la valeur par défaut,
    # on vérifie si l'intention correspond à l'Upgrader
    is_default_crew = not request.crew_name or request.crew_name == "default"
    
    if should_delegate_to_upgrader(request.message) and is_default_crew:
        target_crew_name = "upgrader"
    
    def event_generator():
        for chunk in run_crew(
            crew_name=target_crew_name,
            message=request.message,
            inputs=request.inputs,
            max_rpm=request.max_rpm,
            llm_override=request.llm_override,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
