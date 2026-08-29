"""API route pour lister les modèles Gemini disponibles."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.crew_manager import get_available_models

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=list[str])
async def list_models():
    """Retourne la liste des modèles Gemini disponibles pour le compte."""
    return get_available_models()
