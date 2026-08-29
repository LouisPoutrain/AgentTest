"""Schémas Pydantic pour les endpoints Chat (SSE)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Corps de la requête POST /api/chat."""

    crew_name: str = Field(..., max_length=100, description="Nom du Crew à exécuter")
    message: str = Field(default="", max_length=10000, description="Message de l'utilisateur pour le Crew")
    max_rpm: int = Field(default=15, ge=1, le=100, description="Limite de requêtes par minute")
    llm_override: str | None = Field(default=None, max_length=100, description="Modèle LLM de secours (override)")


class ChatChunk(BaseModel):
    """Un chunk de réponse SSE."""

    type: Literal["log", "result", "error"] = Field(..., description="Type du chunk")
    content: str = Field(..., description="Contenu du chunk")
    timestamp: str = Field(..., description="Horodatage ISO 8601")
    code: int | None = Field(default=None, description="Code d'erreur HTTP (si erreur)")
    available_models: list[str] | None = Field(default=None, description="Modèles disponibles (si 429)")
