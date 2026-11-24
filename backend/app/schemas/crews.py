"""Schémas Pydantic pour les endpoints Crews (CRUD)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CrewSettings(BaseModel):
    """Paramètres globaux d'un Crew."""

    process: Literal["Séquentiel", "Hiérarchique"] = "Séquentiel"
    memory: bool = True
    max_rpm: int = Field(default=15, ge=1, le=100)


class CrewCreate(BaseModel):
    """Corps de la requête POST /api/crews."""

    name: str = Field(..., min_length=1, description="Nom du Crew (sans .yaml)")
    settings: CrewSettings = Field(default_factory=CrewSettings)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate crew name for safety and format."""
        if not v:
            raise ValueError("Crew name cannot be empty")
        if len(v) > 100:
            raise ValueError("Crew name cannot exceed 100 characters")
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Crew name cannot contain path traversal characters")
        if not all(c.isalnum() or c in ("_", "-") for c in v):
            raise ValueError(
                "Crew name can only contain alphanumeric characters, underscores, and hyphens"
            )
        return v


class AgentCreate(BaseModel):
    """Corps de la requête POST /api/crews/{name}/agents."""

    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    backstory: str = Field(..., min_length=1)
    llm: str = Field(default="openai/")
    tools: list[str] = Field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False


class TaskCreate(BaseModel):
    """Corps de la requête POST /api/crews/{name}/tasks."""

    description: str = Field(..., min_length=1)
    expected_output: str = Field(..., min_length=1)
    agent: str = Field(..., min_length=1, description="Nom de l'agent assigné")


class GitImportRequest(BaseModel):
    """Corps de la requête POST /api/crews/{name}/import."""

    raw_url: str = Field(..., description="URL brute du YAML sur GitHub")


class CrewResponse(BaseModel):
    """Réponse pour un Crew complet."""

    name: str
    crew_settings: dict = Field(default_factory=dict)
    agents: list[dict] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
