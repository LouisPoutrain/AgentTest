"""API routes pour le chat (exécution de Crew en SSE streaming et Orchestration Meta-Routeur)."""

from __future__ import annotations

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.crew_runner import run_crew
from app.schemas.chat import ChatRequest
from app.core.router import route_request, get_model_for_tier
from app.core.history_manager import history_manager

router = APIRouter(prefix="/api", tags=["chat"])

def _make_chunk(chunk_type: str, content: str, **kwargs) -> str:
    """Crée un chunk JSON formaté pour le SSE."""
    payload = {
        "type": chunk_type,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    payload.update(kwargs)
    return json.dumps(payload)

@router.post("/chat")
async def chat(request: ChatRequest):
    """Lance l'exécution d'un Crew ou de l'Orchestrateur et streame les logs en SSE."""
    
    if request.llm_override:
        if not (request.llm_override.startswith("openai/") or request.llm_override.startswith("gemini/") or request.llm_override.startswith("anthropic/")):
            raise HTTPException(status_code=400, detail="Modèle LLM non autorisé.")

    # 1. Gestion de la session
    session_id = history_manager.get_or_create_session(request.session_id)

    # 2. Sauvegarde du message utilisateur
    history_manager.add_message(session_id, role="user", content=request.message)

    def event_generator():
        # Transmettre le session_id au client dès le début
        yield f"data: {_make_chunk('session_info', session_id, session_id=session_id)}\n\n"
        
        # Si un crew est forcé manuellement (ex: depuis l'UI spécifique)
        if request.crew_name and request.crew_name != "default":
            target_crew_name = request.crew_name
            crew_inputs = request.inputs or {}
            llm_to_use = request.llm_override
            yield f"data: {_make_chunk('log', f'🚀 [Exécution Manuelle] Lancement du crew {target_crew_name}')}\n\n"
        else:
            # --- META-ROUTEUR (ReAct Loop) ---
            yield f"data: {_make_chunk('log', '🧠 [Routeur] Analyse de votre demande...')}\n\n"
            
            route_result = route_request(session_id, request.message, context_inputs=request.inputs)
            thought = route_result.get("thought", "")
            action = route_result.get("action", "direct_reply")
            reply = route_result.get("reply", "")
            target_crew_name = route_result.get("crew_name")
            crew_inputs = route_result.get("crew_inputs", {})
            llm_tier = route_result.get("llm_tier", "balanced")
            
            # Stream du Thought
            if thought:
                yield f"data: {_make_chunk('log', f'💡 [Réflexion] {thought}')}\n\n"
                
            if action in ["direct_reply", "ask_clarification"]:
                history_manager.add_message(session_id, role="assistant", content=reply)
                yield f"data: {_make_chunk('result', reply)}\n\n"
                return
                
            elif action == "call_crew" and target_crew_name:
                llm_to_use = request.llm_override or get_model_for_tier(llm_tier)
                yield f"data: {_make_chunk('log', f'⚡ [Action] Délégation au crew {target_crew_name} (Modèle: {llm_tier})')}\n\n"
            else:
                fallback_msg = "Je n'ai pas pu déterminer l'action appropriée."
                history_manager.add_message(session_id, role="assistant", content=fallback_msg)
                yield f"data: {_make_chunk('result', fallback_msg)}\n\n"
                return

        # --- EXECUTION DU CREW ---
        final_result = ""
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
            
        # Sauvegarde du résultat en DB
        if final_result:
            history_manager.add_message(session_id, role="assistant", content=final_result, crew_used=target_crew_name)
        else:
            history_manager.add_message(session_id, role="assistant", content="[Exécution terminée sans résultat textuel]", crew_used=target_crew_name)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
