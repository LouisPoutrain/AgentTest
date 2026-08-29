"""API routes pour le CRUD des Crews."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.core.crew_manager import (
    get_all_crews,
    get_crew,
    create_crew,
    delete_crew,
    update_crew_settings,
    add_agent,
    update_agent,
    delete_agent,
    add_task,
    update_task,
    delete_task,
    import_from_github,
)
from app.core.tool_registry import get_tool_names
from app.schemas.crews import (
    CrewCreate,
    CrewResponse,
    AgentCreate,
    TaskCreate,
    GitImportRequest,
)

router = APIRouter(prefix="/api/crews", tags=["crews"])


# ── Crews ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[str])
async def list_crews():
    """Liste tous les Crews disponibles."""
    return get_all_crews()


@router.get("/all/agents", response_model=list[dict])
async def get_all_available_agents():
    """Retourne tous les agents uniques définis dans tous les Crews."""
    from app.core.crew_manager import get_all_agents
    return get_all_agents()


@router.get("/{name}", response_model=CrewResponse)
async def get_crew_detail(name: str):
    """Retourne les détails d'un Crew (settings, agents, tasks)."""
    try:
        return get_crew(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


@router.post("", response_model=CrewResponse, status_code=201)
async def create_new_crew(body: CrewCreate):
    """Crée un nouveau Crew avec ses paramètres globaux."""
    try:
        return create_crew(
            crew_name=body.name,
            process=body.settings.process,
            memory=body.settings.memory,
            max_rpm=body.settings.max_rpm,
        )
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Le Crew '{body.name}' existe déjà.")


@router.delete("/{name}", status_code=204)
async def delete_existing_crew(name: str):
    """Supprime un Crew."""
    try:
        delete_crew(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


class CrewSettingsUpdate(BaseModel):
    process: Optional[str] = None
    memory: Optional[bool] = None
    max_rpm: Optional[int] = None


@router.put("/{name}/settings", response_model=CrewResponse)
async def update_crew_settings_route(name: str, body: CrewSettingsUpdate):
    """Met à jour les paramètres globaux d'un Crew."""
    try:
        settings = {k: v for k, v in body.model_dump().items() if v is not None}
        return update_crew_settings(name, settings)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


# ── Agents ───────────────────────────────────────────────────────────────────


@router.post("/{name}/agents", response_model=CrewResponse)
async def add_agent_to_crew(name: str, body: AgentCreate):
    """Ajoute un agent à un Crew existant."""
    try:
        return add_agent(name, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{name}/agents/{index}", response_model=CrewResponse)
async def update_agent_in_crew(name: str, index: int, body: AgentCreate):
    """Met à jour un agent existant dans un Crew."""
    try:
        return update_agent(name, index, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{name}/agents/{index}", response_model=CrewResponse)
async def delete_agent_from_crew(name: str, index: int):
    """Supprime un agent d'un Crew."""
    try:
        return delete_agent(name, index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Tasks ────────────────────────────────────────────────────────────────────


@router.post("/{name}/tasks", response_model=CrewResponse)
async def add_task_to_crew(name: str, body: TaskCreate):
    """Ajoute une tâche à un Crew existant."""
    try:
        return add_task(name, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


@router.put("/{name}/tasks/{index}", response_model=CrewResponse)
async def update_task_in_crew(name: str, index: int, body: TaskCreate):
    """Met à jour une tâche existante dans un Crew."""
    try:
        return update_task(name, index, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{name}/tasks/{index}", response_model=CrewResponse)
async def delete_task_from_crew(name: str, index: int):
    """Supprime une tâche d'un Crew."""
    try:
        return delete_task(name, index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Import & Tools ──────────────────────────────────────────────────────────


@router.post("/{name}/import", response_model=CrewResponse)
async def import_crew_from_github(name: str, body: GitImportRequest):
    """Importe un Crew depuis un fichier YAML brut sur GitHub."""
    if not (body.raw_url.startswith("https://github.com/") or body.raw_url.startswith("https://raw.githubusercontent.com/")):
        raise HTTPException(status_code=400, detail="Erreur de sécurité : Seules les URL de GitHub sont autorisées.")
    try:
        return import_from_github(body.raw_url, name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'import : {str(e)}")


@router.get("/tools/available", response_model=list[str])
async def list_available_tools():
    """Retourne la liste des outils disponibles pour les agents."""
    return get_tool_names()
