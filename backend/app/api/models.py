"""API route pour lister les modèles disponibles."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.crew_manager import get_available_models

router = APIRouter(prefix="/api", tags=["models"])


@router.get(
    "/models",
    response_model=list[str],
    summary="List available LLM models",
    description="Return the list of all LLM models available for use with agents and crews. Models are loaded from the LiteLLM configuration.",
    tags=["models"],
    responses={
        200: {"description": "List of available model identifiers returned successfully."},
    },
)
async def list_models():
    """Return the list of all LLM models available for use with agents and crews.

    Models are loaded from the LiteLLM configuration and include both local
    and remote model identifiers (e.g. 'openai/gpt-4', 'gemini/gemini-pro').
    """
    return get_available_models()
