"""API routes pour le chat (exécution de Crew en SSE streaming)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.crew_runner import run_crew
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


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

    def event_generator():
        for chunk in run_crew(
            crew_name=request.crew_name,
            message=request.message,
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
