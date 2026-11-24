"""
Centralized crew registry with caching and validation.
Provides metadata for the Automation Lab frontend without loading full YAMLs.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.crew_manager import get_all_crews, get_crew

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CAPABILITIES_PATH = CONFIG_DIR / "capabilities.json"


class CrewRegistry:
    """Centralized registry of crew metadata with TTL cache."""

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a hash of all crew YAML files to detect changes."""
        crews_dir = CONFIG_DIR / "crews"
        if not crews_dir.exists():
            return ""
        files = sorted(str(p) for p in crews_dir.glob("*.yaml"))
        return str(hash(tuple(files)))

    def _invalidate_if_needed(self):
        """Clear cache if crew files have changed."""
        new_hash = self._compute_hash()
        if new_hash != self._hash:
            self._cache.clear()
            self._cache_time.clear()
            self._hash = new_hash

    def get_all_crews(self) -> List[Dict[str, Any]]:
        """Return metadata for all crews (lightweight, no full YAML parsing)."""
        self._invalidate_if_needed()
        cache_key = "all_crews"
        if cache_key in self._cache:
            return self._cache[cache_key]

        crews = []
        for name in get_all_crews():
            crew = get_crew(name)
            if crew:
                crews.append({
                    "name": name,
                    "description": crew.get("crew_settings", {}).get("description", ""),
                    "process": crew.get("crew_settings", {}).get("process", "Séquentiel"),
                    "memory": crew.get("crew_settings", {}).get("memory", False),
                    "max_rpm": crew.get("crew_settings", {}).get("max_rpm", 15),
                    "agent_count": len(crew.get("agents", [])),
                    "task_count": len(crew.get("tasks", [])),
                })

        self._cache[cache_key] = crews
        self._cache_time[cache_key] = time.time()
        return crews

    def get_crew_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the configuration schema for a specific crew."""
        self._invalidate_if_needed()
        cache_key = "schema_" + name
        if cache_key in self._cache:
            return self._cache[cache_key]

        crew = get_crew(name)
        if not crew:
            return None

        result = {
            "name": name,
            "settings": crew.get("crew_settings", {}),
            "agents": [
                {
                    "name": a.get("name"),
                    "role": a.get("role"),
                    "goal": a.get("goal"),
                    "backstory": a.get("backstory"),
                    "llm": a.get("llm"),
                    "tools": a.get("tools", []),
                    "verbose": a.get("verbose", True),
                    "allow_delegation": a.get("allow_delegation", False),
                }
                for a in crew.get("agents", [])
            ],
            "tasks": [
                {
                    "description": t.get("description"),
                    "expected_output": t.get("expected_output"),
                    "agent": t.get("agent"),
                }
                for t in crew.get("tasks", [])
            ],
        }

        self._cache[cache_key] = result
        self._cache_time[cache_key] = time.time()
        return result

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Return available templates with UI metadata."""
        self._invalidate_if_needed()
        cache_key = "templates"
        if cache_key in self._cache:
            return self._cache[cache_key]

        caps = self._load_capabilities()
        crew_defs = caps.get("crews", {})

        templates = []
        for name, info in crew_defs.items():
            templates.append({
                "id": name.lower().replace(" ", "-"),
                "name": name,
                "description": info.get("description", ""),
                "category": info.get("category", "general"),
                "crew_name": name,
                "tags": info.get("keywords", []),
            })

        self._cache[cache_key] = templates
        self._cache_time[cache_key] = time.time()
        return templates

    def get_agents(self) -> List[Dict[str, Any]]:
        """Return all unique agents across all crews."""
        self._invalidate_if_needed()
        cache_key = "agents"
        if cache_key in self._cache:
            return self._cache[cache_key]

        agents = []
        seen = set()
        for name in get_all_crews():
            crew = get_crew(name)
            if not crew:
                continue
            for agent in crew.get("agents", []):
                agent_name = agent.get("name", "")
                if agent_name not in seen:
                    seen.add(agent_name)
                    agents.append({
                        "name": agent_name,
                        "role": agent.get("role", ""),
                        "goal": agent.get("goal", ""),
                        "llm": agent.get("llm"),
                        "tools": agent.get("tools", []),
                    })

        self._cache[cache_key] = agents
        self._cache_time[cache_key] = time.time()
        return agents

    def _load_capabilities(self) -> Dict[str, Any]:
        try:
            if CAPABILITIES_PATH.exists():
                return json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Erreur chargement capabilities: %s", e)
        return {"crews": {}, "model_tiers": {}}

    def invalidate(self):
        """Manually invalidate the cache (call when a crew is modified)."""
        self._cache.clear()
        self._cache_time.clear()
        self._hash = self._compute_hash()


# Singleton instance
crew_registry = CrewRegistry()
