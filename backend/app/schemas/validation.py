"""
YAML validation schema for crew configurations.
Ensures crews are valid before writing to disk.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator


class CrewSettingsSchema(BaseModel):
    process: str = "Séquentiel"
    memory: bool = True
    max_rpm: int = Field(default=15, ge=1, le=100)


class AgentSchema(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str
    llm: str = "openai/"
    tools: List[str] = Field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Le nom de l'agent ne peut pas être vide")
        return v.strip()


class TaskSchema(BaseModel):
    description: str
    expected_output: str
    agent: str

    @validator("description")
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("La description de la tâche ne peut pas être vide")
        return v.strip()

    @validator("expected_output")
    def expected_output_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Le résultat attendu ne peut pas être vide")
        return v.strip()


class CrewYamlSchema(BaseModel):
    name: str
    description: str = ""
    crew_settings: CrewSettingsSchema = Field(default_factory=CrewSettingsSchema)
    agents: List[AgentSchema] = Field(default_factory=list, min_length=1)
    tasks: List[TaskSchema] = Field(default_factory=list, min_length=1)

    @validator("name")
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError("Le nom du crew ne peut pas être vide")
        if not all(c.isalnum() or c in ('_', '-', '.') for c in v):
            raise ValueError("Le nom du crew ne doit contenir que des caractères alphanumériques, _, - et .")
        return v.strip()

    @validator("agents")
    def unique_agent_names(cls, v):
        names = [a.name for a in v]
        if len(names) != len(set(names)):
            raise ValueError("Les noms d'agents doivent être uniques")
        return v

    @validator("tasks")
    def tasks_reference_valid_agents(cls, v):
        agent_names = {a.name for a in v}
        for task in v:
            if task.agent not in agent_names:
                raise ValueError("La tâche référence un agent inconnu: " + task.agent)
        return v
