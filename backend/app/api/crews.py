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


@router.get(
        "",
        response_model=list[str],
        summary="List all crews",
        description="Return a list of all available crew names.",
        tags=["crews"],
        responses={
            200: {"description": "List of crew names returned successfully."},
        },
    )
async def list_crews():
    """List all available crews.

    Returns a list of crew names defined in the configuration directory.
    Crews are YAML files stored in backend/config/crews/.
    """
    return get_all_crews()


@router.get(
        "/all/agents",
        response_model=list[dict],
        summary="Get all available agents",
        description="Return all unique agent names defined across all crews.",
        tags=["crews"],
        responses={
            200: {"description": "List of agent definitions returned successfully."},
        },
    )
async def get_all_available_agents():
    """Return all unique agent names defined across all crews.

    Scans every crew configuration and collects distinct agent names.
    Useful for populating agent dropdown selectors in the UI.
    """
    from app.core.crew_manager import get_all_agents
    return get_all_agents()


@router.get(
        "/{name}",
        response_model=CrewResponse,
        summary="Get crew details",
        description="Return the full details of a crew including settings, agents, and tasks.",
        tags=["crews"],
        responses={
            200: {"description": "Crew details returned successfully."},
            404: {"description": "Crew not found."},
        },
    )
async def get_crew_detail(name: str):
    """Return the full details of a crew including settings, agents, and tasks.

    Args:
        name: The crew name (must match the YAML filename without .yaml extension).

    Returns:
        Full crew configuration including global settings, agent definitions, and tasks.

    Raises:
        HTTPException 404: If the crew does not exist.
    """
    try:
        return get_crew(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


@router.post(
        "",
        response_model=CrewResponse,
        status_code=201,
        summary="Create a new crew",
        description="Create a new crew with global settings (process, memory, max_rpm).",
        tags=["crews"],
        responses={
            201: {"description": "Crew created successfully."},
            400: {"description": "Invalid request body."},
            409: {"description": "Crew with this name already exists."},
        },
    )
async def create_new_crew(body: CrewCreate):
    """Create a new crew with global settings (process, memory, max_rpm).

    Args:
        body: CrewCreate schema containing name and CrewSettings.

    Raises:
        HTTPException 409: If a crew with this name already exists.
        HTTPException 400: If the request body is invalid.
    """
    try:
        return create_crew(
            crew_name=body.name,
            process=body.settings.process,
            memory=body.settings.memory,
            max_rpm=body.settings.max_rpm,
        )
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Le Crew '{body.name}' existe déjà.")


@router.delete(
        "/{name}",
        status_code=204,
        summary="Delete a crew",
        description="Permanently delete a crew and all its agents and tasks.",
        tags=["crews"],
        responses={
            204: {"description": "Crew deleted successfully."},
            404: {"description": "Crew not found."},
        },
    )
async def delete_existing_crew(name: str):
    """Permanently delete a crew and all its agents and tasks.

    Args:
        name: The crew name to delete.

    Raises:
        HTTPException 404: If the crew does not exist.
    """
    try:
        delete_crew(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


class CrewSettingsUpdate(BaseModel):
    process: Optional[str] = None
    memory: Optional[bool] = None
    max_rpm: Optional[int] = None


@router.put(
        "/{name}/settings",
        response_model=CrewResponse,
        summary="Update crew settings",
        description="Update global settings for an existing crew (process, memory, max_rpm).",
        tags=["crews"],
        responses={
            200: {"description": "Crew settings updated successfully."},
            400: {"description": "Invalid request body."},
            404: {"description": "Crew not found."},
        },
    )
async def update_crew_settings_route(name: str, body: CrewSettingsUpdate):
    """Update global settings for an existing crew (process, memory, max_rpm).

    Only provided fields are updated; omitted fields remain unchanged.

    Args:
        name: The crew name.
        body: CrewSettingsUpdate with optional process, memory, max_rpm fields.

    Raises:
        HTTPException 404: If the crew does not exist.
    """
    try:
        settings = {k: v for k, v in body.model_dump().items() if v is not None}
        return update_crew_settings(name, settings)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


# ── Agents ───────────────────────────────────────────────────────────────────


@router.post(
        "/{name}/agents",
        response_model=CrewResponse,
        summary="Add an agent to a crew",
        description="Add a new agent to an existing crew with role, goal, backstory, and tools.",
        tags=["crews"],
        responses={
            201: {"description": "Agent added successfully."},
            400: {"description": "Invalid request body."},
            404: {"description": "Crew not found."},
            409: {"description": "Agent name conflict or validation error."},
        },
    )
async def add_agent_to_crew(name: str, body: AgentCreate):
    """Add a new agent to an existing crew with role, goal, backstory, and tools.

    Args:
        name: The crew name.
        body: AgentCreate schema with role, goal, backstory, llm, and tools.

    Raises:
        HTTPException 404: If the crew does not exist.
        HTTPException 409: If the agent name conflicts or validation fails.
    """
    try:
        return add_agent(name, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
        "/{name}/agents/{index}",
        response_model=CrewResponse,
        summary="Update an agent in a crew",
        description="Update the definition of an existing agent within a crew by its index.",
        tags=["crews"],
        responses={
            200: {"description": "Agent updated successfully."},
            400: {"description": "Invalid request body."},
            404: {"description": "Crew or agent index not found."},
        },
    )
async def update_agent_in_crew(name: str, index: int, body: AgentCreate):
    """Update the definition of an existing agent within a crew by its index.

    Args:
        name: The crew name.
        index: Zero-based index of the agent in the crew's agent list.
        body: Updated agent definition.

    Raises:
        HTTPException 404: If the crew or agent index does not exist.
    """
    try:
        return update_agent(name, index, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
        "/{name}/agents/{index}",
        response_model=CrewResponse,
        summary="Delete an agent from a crew",
        description="Remove an agent from a crew by its zero-based index.",
        tags=["crews"],
        responses={
            200: {"description": "Agent deleted successfully."},
            404: {"description": "Crew or agent index not found."},
        },
    )
async def delete_agent_from_crew(name: str, index: int):
    """Remove an agent from a crew by its zero-based index.

    Args:
        name: The crew name.
        index: Zero-based index of the agent to remove.

    Raises:
        HTTPException 404: If the crew or agent index does not exist.
    """
    try:
        return delete_agent(name, index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Tasks ────────────────────────────────────────────────────────────────────


@router.post(
        "/{name}/tasks",
        response_model=CrewResponse,
        summary="Add a task to a crew",
        description="Add a new task to an existing crew, assigned to a specific agent.",
        tags=["crews"],
        responses={
            201: {"description": "Task added successfully."},
            400: {"description": "Invalid request body."},
            404: {"description": "Crew not found."},
        },
    )
async def add_task_to_crew(name: str, body: TaskCreate):
    """Add a new task to an existing crew, assigned to a specific agent.

    Args:
        name: The crew name.
        body: TaskCreate schema with description, expected_output, and agent assignment.

    Raises:
        HTTPException 404: If the crew does not exist.
    """
    try:
        return add_task(name, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")


@router.put(
        "/{name}/tasks/{index}",
        response_model=CrewResponse,
        summary="Update a task in a crew",
        description="Update the definition of an existing task within a crew by its index.",
        tags=["crews"],
        responses={
            200: {"description": "Task updated successfully."},
            400: {"description": "Invalid request body."},
            404: {"description": "Crew or task index not found."},
        },
    )
async def update_task_in_crew(name: str, index: int, body: TaskCreate):
    """Update the definition of an existing task within a crew by its index.

    Args:
        name: The crew name.
        index: Zero-based index of the task in the crew's task list.
        body: Updated task definition.

    Raises:
        HTTPException 404: If the crew or task index does not exist.
    """
    try:
        return update_task(name, index, body.model_dump())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
        "/{name}/tasks/{index}",
        response_model=CrewResponse,
        summary="Delete a task from a crew",
        description="Remove a task from a crew by its zero-based index.",
        tags=["crews"],
        responses={
            200: {"description": "Task deleted successfully."},
            404: {"description": "Crew or task index not found."},
        },
    )
async def delete_task_from_crew(name: str, index: int):
    """Remove a task from a crew by its zero-based index.

    Args:
        name: The crew name.
        index: Zero-based index of the task to remove.

    Raises:
        HTTPException 404: If the crew or task index does not exist.
    """
    try:
        return delete_task(name, index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Crew '{name}' introuvable.")
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Import & Tools ──────────────────────────────────────────────────────────


@router.post(
        "/{name}/import",
        response_model=CrewResponse,
        summary="Import a crew from GitHub",
        description="Import a crew configuration from a raw YAML file hosted on GitHub.",
        tags=["crews"],
        responses={
            201: {"description": "Crew imported successfully."},
            400: {"description": "Invalid URL or import error."},
            404: {"description": "Crew not found (if updating)."},
        },
    )
async def import_crew_from_github(name: str, body: GitImportRequest):
    """Import a crew configuration from a raw YAML file hosted on GitHub.

    Validates that the URL points to github.com or raw.githubusercontent.com
    to prevent directory traversal attacks.

    Args:
        name: The crew name (created if not exists, updated if exists).
        body: GitImportRequest with raw_url pointing to a GitHub YAML file.

    Raises:
        HTTPException 400: If the URL is not a GitHub URL or import fails.
    """
    if not (body.raw_url.startswith("https://github.com/") or body.raw_url.startswith("https://raw.githubusercontent.com/")):
        raise HTTPException(status_code=400, detail="Erreur de sécurité : Seules les URL de GitHub sont autorisées.")
    try:
        return import_from_github(body.raw_url, name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'import : {str(e)}")


@router.get(
        "/tools/available",
        response_model=list[str],
        summary="List available tools",
        description="Return the list of all tools available for use by agents in crews.",
        tags=["crews"],
        responses={
            200: {"description": "List of available tools returned successfully."},
        },
    )
async def list_available_tools():
    """Return the list of all tools available for use by agents in crews.

    Tools are registered in the tool registry and include file operations,
    search, and custom CrewAI tools.
    """
    return get_tool_names()
