"""Tests for core/agent_parser.py — YAML → CrewAI agent/task creation."""

from pathlib import Path

import pytest
import yaml

from app.core.agent_parser import (
    create_agents_from_yaml,
    create_tasks_from_yaml,
    get_crew_settings_from_yaml,
)
from app.core.tool_registry import AVAILABLE_TOOLS

CREWS_DIR = Path(__file__).resolve().parent.parent / "config" / "crews"


class TestCreateTasksFromYaml:
    """Tests that tasks are created with correct context linking."""

    def test_tasks_have_context_linking(self):
        """Sequential tasks should have context pointing to the previous task."""
        yaml_path = CREWS_DIR / "InteractiveCourseCreator.yaml"
        if not yaml_path.exists():
            pytest.skip("InteractiveCourseCreator.yaml not found")

        agents = create_agents_from_yaml(yaml_path, available_tools=AVAILABLE_TOOLS)
        tasks = create_tasks_from_yaml(yaml_path, agents)

        assert len(tasks) >= 2, "InteractiveCourseCreator should have at least 2 tasks"

        # First task should have no context
        assert tasks[0].context is None or tasks[0].context == []

        # Subsequent tasks should have context pointing to the previous task
        for i in range(1, len(tasks)):
            assert tasks[i].context is not None, f"Task {i} should have context"
            assert len(tasks[i].context) == 1, f"Task {i} should reference exactly 1 previous task"
            assert tasks[i].context[0] is tasks[i - 1], f"Task {i} context should be task {i-1}"

    def test_single_task_has_no_context(self):
        """A crew with a single task should have no context linking."""
        import tempfile
        import yaml

        crew_config = {
            "name": "TestSingleTask",
            "description": "Test",
            "crew_settings": {"process": "Séquentiel", "memory": False, "max_rpm": 15},
            "agents": [
                {
                    "name": "TestAgent",
                    "role": "Test role",
                    "goal": "Test goal",
                    "backstory": "Test backstory",
                    "llm": "openai/test",
                    "tools": [],
                    "verbose": False,
                    "allow_delegation": False,
                }
            ],
            "tasks": [
                {
                    "description": "Do something",
                    "expected_output": "Something done",
                    "agent": "TestAgent",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", encoding="utf-8", delete=False) as f:
            yaml.dump(crew_config, f)
            tmp_path = Path(f.name)

        try:
            agents = create_agents_from_yaml(tmp_path, available_tools=AVAILABLE_TOOLS)
            tasks = create_tasks_from_yaml(tmp_path, agents)
            assert len(tasks) == 1
            assert tasks[0].context is None or tasks[0].context == []
        finally:
            tmp_path.unlink()


class TestCreateAgentsFromYaml:
    """Tests that agents are created correctly from YAML."""

    def test_agent_count_matches_yaml(self):
        """Number of created agents should match the YAML."""
        yaml_path = CREWS_DIR / "InteractiveCourseCreator.yaml"
        if not yaml_path.exists():
            pytest.skip("InteractiveCourseCreator.yaml not found")

        agents = create_agents_from_yaml(yaml_path, available_tools=AVAILABLE_TOOLS)
        expected = len(yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["agents"])
        assert len(agents) == expected

    def test_agent_roles_match_yaml(self):
        """Agent roles should match the YAML configuration."""
        yaml_path = CREWS_DIR / "InteractiveCourseCreator.yaml"
        if not yaml_path.exists():
            pytest.skip("InteractiveCourseCreator.yaml not found")

        agents = create_agents_from_yaml(yaml_path, available_tools=AVAILABLE_TOOLS)
        roles = [a.role for a in agents]
        expected_roles = [
            "Inventoriste de documents PDF",
            "Expert en extraction et analyse de documents PDF",
            "Vérificateur de complétude de l'analyse PDF",
            "Chercheur pédagogique et expert web",
            "Architecte pédagogique spécialisé en Bloom's Taxonomy",
            "Rédacteur pédagogique senior",
            "Concepteur d'exercices interactifs multi-formats",
            "Designer UI/UX web moderne et minimaliste",
            "Développeur Frontend spécialisé en HTML/CSS/JS",
            "Intégrateur de contenu pédagogique dans le site web",
            "Revueur qualité et complétude pédagogique",
            "Correcteur qualité et intégrité du cours",
        ]
        for expected in expected_roles:
            assert expected in roles


class TestGetCrewSettingsFromYaml:
    """Tests that crew settings are parsed correctly."""

    def test_sequential_process(self):
        yaml_path = CREWS_DIR / "InteractiveCourseCreator.yaml"
        if not yaml_path.exists():
            pytest.skip("InteractiveCourseCreator.yaml not found")

        settings = get_crew_settings_from_yaml(yaml_path)
        assert settings["process"].value == "sequential"
        assert settings["memory"] is True
        assert settings["max_rpm"] == 15
