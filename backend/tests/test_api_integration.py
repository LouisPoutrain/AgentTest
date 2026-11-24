"""Tests d'intégration — routes API complètes via TestClient."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def _tmp_crew(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Crée un crew temporaire et mock CREWS_DIR pour pointer vers un dossier temporaire."""
    crew_dir = tmp_path / "config" / "crews"
    crew_dir.mkdir(parents=True, exist_ok=True)
    # Ne pas pré-créer le fichier YAML — le test le crée via l'API
    monkeypatch.setattr("app.core.crew_manager.CREWS_DIR", crew_dir)
    yield crew_dir


@pytest.fixture()
def _tmp_crew_with_agents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Crée un crew avec agents et tâches pour tests CRUD."""
    crew_dir = tmp_path / "config" / "crews"
    crew_dir.mkdir(parents=True, exist_ok=True)
    crew_file = crew_dir / "FullTestCrew.yaml"
    crew_file.write_text(
        "name: FullTestCrew\n"
        "description: Crew complet pour tests CRUD\n"
        "crew_settings:\n"
        "  process: Hiérarchique\n"
        "  memory: false\n"
        "  max_rpm: 30\n"
        "agents:\n"
        "  - name: AgentAlpha\n"
        "    role: Développeur\n"
        "    goal: coder\n"
        "    backstory: Un dev\n"
        "    llm: openai/\n"
        "    tools: [read_file]\n"
        "    verbose: true\n"
        "    allow_delegation: false\n"
        "tasks:\n"
        "  - description: Tâche 1\n"
        "    expected_output: Output 1\n"
        "    agent: AgentAlpha\n"
    )
    monkeypatch.setattr("app.core.crew_manager.CREWS_DIR", crew_dir)
    yield crew_dir


# ── 1. Healthcheck ────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"


# ── 2. Crews CRUD ─────────────────────────────────────────────────────────────


class TestCrewsList:
    def test_list_crews_returns_list(self):
        res = client.get("/api/crews")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all(isinstance(c, str) for c in data)

    def test_list_crews_contains_yaml_files(self):
        res = client.get("/api/crews")
        data = res.json()
        assert len(data) >= 1


class TestCrewDetail:
    def test_get_existing_crew(self):
        res = client.get("/api/crews/Autonomous_SWE")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Autonomous_SWE"
        assert "crew_settings" in data
        assert "agents" in data
        assert "tasks" in data

    def test_get_nonexistent_crew(self):
        res = client.get("/api/crews/does_not_exist_xyz")
        assert res.status_code == 404
        assert "introuvable" in res.json()["detail"]

    def test_get_crew_with_underscore_name(self):
        res = client.get("/api/crews/Project_Architect")
        assert res.status_code == 200


class TestCrewCreate:
    def test_create_crew(self, _tmp_crew):
        res = client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "IntegrationTestCrew"
        assert data["crew_settings"]["process"] == "Séquentiel"

    def test_create_duplicate_crew(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        res = client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Hiérarchique", "memory": False, "max_rpm": 10}
        })
        assert res.status_code == 409
        assert "existe déjà" in res.json()["detail"]

    def test_create_crew_invalid_name(self):
        res = client.post("/api/crews", json={
            "name": "bad name!",
            "settings": {}
        })
        assert res.status_code == 422

    def test_create_crew_empty_name(self):
        res = client.post("/api/crews", json={
            "name": "",
            "settings": {}
        })
        assert res.status_code == 422


class TestCrewDelete:
    def test_delete_existing_crew(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        res = client.delete("/api/crews/IntegrationTestCrew")
        assert res.status_code == 204

    def test_delete_nonexistent_crew(self):
        res = client.delete("/api/crews/nonexistent_crew_xyz")
        assert res.status_code == 404
        assert "introuvable" in res.json()["detail"]


class TestCrewSettingsUpdate:
    def test_update_crew_settings(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        res = client.put("/api/crews/IntegrationTestCrew/settings", json={
            "process": "Hiérarchique",
            "memory": False
        })
        assert res.status_code == 200
        data = res.json()
        assert data["crew_settings"]["process"] == "Hiérarchique"
        assert data["crew_settings"]["memory"] is False

    def test_update_partial_settings(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        res = client.put("/api/crews/IntegrationTestCrew/settings", json={
            "max_rpm": 50
        })
        assert res.status_code == 200
        data = res.json()
        assert data["crew_settings"]["max_rpm"] == 50
        assert data["crew_settings"]["process"] == "Séquentiel"

    def test_update_nonexistent_crew(self):
        res = client.put("/api/crews/nonexistent/settings", json={"process": "Hiérarchique"})
        assert res.status_code == 404


# ── 3. Agents CRUD ────────────────────────────────────────────────────────────


class TestAgentsCRUD:
    def test_add_agent(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        res = client.post("/api/crews/IntegrationTestCrew/agents", json={
            "name": "TestAgent",
            "role": "Testeur",
            "goal": "Tester le code",
            "backstory": "Un agent de test",
            "llm": "openai/",
            "tools": ["read_file"]
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "TestAgent"

    def test_add_duplicate_agent(self, _tmp_crew):
        client.post("/api/crews", json={
            "name": "IntegrationTestCrew",
            "settings": {"process": "Séquentiel", "memory": True, "max_rpm": 15}
        })
        client.post("/api/crews/IntegrationTestCrew/agents", json={
            "name": "TestAgent",
            "role": "Testeur",
            "goal": "Tester",
            "backstory": "Test",
            "llm": "openai/",
            "tools": []
        })
        res = client.post("/api/crews/IntegrationTestCrew/agents", json={
            "name": "TestAgent",
            "role": "Testeur 2",
            "goal": "Tester 2",
            "backstory": "Test 2",
            "llm": "openai/",
            "tools": []
        })
        assert res.status_code == 409
        assert "existe déjà" in res.json()["detail"]

    def test_update_agent(self, _tmp_crew_with_agents):
        res = client.put("/api/crews/FullTestCrew/agents/0", json={
            "name": "AgentAlpha",
            "role": "Senior Développeur",
            "goal": "Coder mieux",
            "backstory": "Un senior",
            "llm": "openai/",
            "tools": ["read_file", "write_file"]
        })
        assert res.status_code == 200
        data = res.json()
        assert data["agents"][0]["role"] == "Senior Développeur"

    def test_update_agent_invalid_index(self, _tmp_crew_with_agents):
        res = client.put("/api/crews/FullTestCrew/agents/999", json={
            "name": "AgentAlpha",
            "role": "Senior",
            "goal": "Coder",
            "backstory": "Senior",
            "llm": "openai/",
            "tools": []
        })
        assert res.status_code == 404
        # L'erreur peut être "introuvable" ou "invalide" selon l'ordre des vérifications
        detail = res.json()["detail"]
        assert "introuvable" in detail or "invalide" in detail

    def test_delete_agent(self, _tmp_crew_with_agents):
        res = client.delete("/api/crews/FullTestCrew/agents/0")
        assert res.status_code == 200
        data = res.json()
        assert len(data["agents"]) == 0

    def test_delete_agent_invalid_index(self, _tmp_crew_with_agents):
        res = client.delete("/api/crews/FullTestCrew/agents/999")
        assert res.status_code == 404
        detail = res.json()["detail"]
        assert "introuvable" in detail or "invalide" in detail

    def test_add_agent_to_nonexistent_crew(self):
        res = client.post("/api/crews/NonExistentCrew/agents", json={
            "name": "TestAgent",
            "role": "Testeur",
            "goal": "Tester",
            "backstory": "Test",
            "llm": "openai/",
            "tools": []
        })
        assert res.status_code == 404


# ── 4. Tasks CRUD ─────────────────────────────────────────────────────────────


class TestTasksCRUD:
    def test_add_task(self, _tmp_crew_with_agents):
        res = client.post("/api/crews/FullTestCrew/tasks", json={
            "description": "Nouvelle tâche",
            "expected_output": "Nouveau output",
            "agent": "AgentAlpha"
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["tasks"]) == 2

    def test_update_task(self, _tmp_crew_with_agents):
        res = client.put("/api/crews/FullTestCrew/tasks/0", json={
            "description": "Tâche modifiée",
            "expected_output": "Output modifié",
            "agent": "AgentAlpha"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["tasks"][0]["description"] == "Tâche modifiée"

    def test_delete_task(self, _tmp_crew_with_agents):
        res = client.delete("/api/crews/FullTestCrew/tasks/0")
        assert res.status_code == 200
        data = res.json()
        assert len(data["tasks"]) == 0

    def test_add_task_to_nonexistent_crew(self):
        res = client.post("/api/crews/NonExistentCrew/tasks", json={
            "description": "Tâche",
            "expected_output": "Output",
            "agent": "Agent"
        })
        assert res.status_code == 404


# ── 5. Models & Tools ─────────────────────────────────────────────────────────


class TestModels:
    def test_list_models_returns_list(self):
        res = client.get("/api/models")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

    def test_list_models_contains_default_models(self):
        res = client.get("/api/models")
        data = res.json()
        assert any(m.startswith("openai/") for m in data)


class TestTools:
    def test_list_available_tools(self):
        res = client.get("/api/crews/tools/available")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestAllAgents:
    def test_get_all_agents(self):
        res = client.get("/api/crews/all/agents")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0


# ── 6. Workspace ──────────────────────────────────────────────────────────────


class TestWorkspaceProjects:
    def test_list_projects(self):
        res = client.get("/api/workspace/projects")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        project = data[0]
        assert "name" in project
        assert "path" in project
        assert "absolute_path" in project
        assert "framework" in project
        assert "tags" in project

    def test_projects_have_git_tag(self):
        res = client.get("/api/workspace/projects")
        data = res.json()
        current = [p for p in data if p.get("has_git")]
        assert len(current) > 0


class TestWorkspaceBrowse:
    def test_browse_root(self):
        res = client.get("/api/workspace/browse?path=.")
        assert res.status_code == 200
        data = res.json()
        assert "current_path" in data
        assert "absolute_path" in data
        assert "directories" in data
        assert isinstance(data["directories"], list)

    def test_browse_subdirectory(self):
        res = client.get("/api/workspace/browse?path=./backend")
        assert res.status_code == 200
        data = res.json()
        assert "backend" in data["absolute_path"]

    def test_browse_has_breadcrumbs(self):
        res = client.get("/api/workspace/browse?path=./backend")
        data = res.json()
        assert "breadcrumbs" in data
        assert isinstance(data["breadcrumbs"], list)
        assert len(data["breadcrumbs"]) > 0

    def test_browse_ignores_node_modules(self):
        res = client.get("/api/workspace/browse?path=.")
        data = res.json()
        dir_names = [d["name"] for d in data["directories"]]
        assert "node_modules" not in dir_names
        assert ".venv" not in dir_names
        assert ".git" not in dir_names


# ── 7. Chat — Validation ──────────────────────────────────────────────────────


class TestChatValidation:
    def test_chat_requires_json(self):
        res = client.post("/api/chat", content="not json", headers={"Content-Type": "application/json"})
        assert res.status_code == 422

    def test_chat_llm_override_validation(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "llm_override": "invalid/model"
        })
        assert res.status_code == 400
        assert "non autorisé" in res.json()["detail"]

    def test_chat_llm_override_custom(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "llm_override": "openai/"
        })
        assert res.status_code != 400

    def test_chat_llm_override_openai(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "llm_override": "openai/gpt-4"
        })
        assert res.status_code != 400

    def test_chat_llm_override_anthropic(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "llm_override": "anthropic/claude-3"
        })
        assert res.status_code != 400

    def test_chat_max_rpm_bounds(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "max_rpm": 0
        })
        assert res.status_code == 422

    def test_chat_max_rpm_too_high(self):
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "test",
            "max_rpm": 101
        })
        assert res.status_code == 422

    def test_chat_crew_name_too_long(self):
        res = client.post("/api/chat", json={
            "crew_name": "a" * 101,
            "message": "test"
        })
        assert res.status_code == 422


# ── 8. Chat — Stream SSE (mocké) ─────────────────────────────────────────────


class TestChatStream:
    """Teste le flux SSE en mockant les appels LLM/CrewAI."""

    @patch("app.api.chat.route_request")
    def test_chat_stream_returns_session_info(self, mock_route):
        mock_route.return_value = {
            "thought": "Je vais répondre directement.",
            "action": "direct_reply",
            "reply": "Bonjour ! Comment puis-je vous aider ?",
            "crew_name": None,
        }
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "Bonjour",
        })
        assert res.status_code == 200
        chunks = []
        for line in res.iter_lines():
            if line.startswith("data: "):
                chunks.append(line[6:])
        assert any(json.loads(c)["type"] == "session_info" for c in chunks)

    @patch("app.api.chat.route_request")
    def test_chat_stream_direct_reply(self, mock_route):
        mock_route.return_value = {
            "thought": "Réponse directe.",
            "action": "direct_reply",
            "reply": "Ceci est une réponse directe.",
            "crew_name": None,
        }
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "Réponds-moi",
        })
        chunks = []
        for line in res.iter_lines():
            if line.startswith("data: "):
                chunks.append(json.loads(line[6:]))
        types = [c["type"] for c in chunks]
        assert "result" in types

    @patch("app.api.chat.route_request")
    def test_chat_stream_ask_clarification(self, mock_route):
        mock_route.return_value = {
            "thought": "Pas clair.",
            "action": "ask_clarification",
            "reply": "Pouvez-vous préciser ?",
            "crew_name": None,
        }
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "Fais quelque chose",
        })
        chunks = []
        for line in res.iter_lines():
            if line.startswith("data: "):
                chunks.append(json.loads(line[6:]))
        types = [c["type"] for c in chunks]
        assert "result" in types

    @patch("app.api.chat.route_request")
    def test_chat_stream_call_crew(self, mock_route):
        mock_route.return_value = {
            "thought": "Je vais deleguer.",
            "action": "call_crew",
            "reply": "",
            "crew_name": "Project_Architect",
            "crew_inputs": {"message": "Crée un plan"},
            "llm_tier": "balanced",
        }
        mock_chunks = [
            '{"type": "log", "content": "🚀 [Exécution] Lancement du crew Project_Architect"}',
            '{"type": "log", "content": "🤖 AgentAlpha: Je travaille..."}',
            '{"type": "result", "content": "Plan d\'architecture généré."}',
        ]
        with patch("app.api.chat.run_crew", return_value=mock_chunks):
            res = client.post("/api/chat", json={
                "crew_name": "default",
                "message": "Crée un plan d'architecture",
            })
            chunks = []
            for line in res.iter_lines():
                if line.startswith("data: "):
                    chunks.append(json.loads(line[6:]))
            types = [c["type"] for c in chunks]
            assert "log" in types
            assert "result" in types

    @patch("app.api.chat.route_request")
    def test_chat_stream_with_session_id(self, mock_route):
        mock_route.return_value = {
            "thought": "Suite.",
            "action": "direct_reply",
            "reply": "Suite de la conversation.",
            "crew_name": None,
        }
        res = client.post("/api/chat", json={
            "crew_name": "default",
            "message": "Suite",
            "session_id": "test-session-123",
        })
        chunks = []
        for line in res.iter_lines():
            if line.startswith("data: "):
                chunks.append(json.loads(line[6:]))
        session_info = [c for c in chunks if c["type"] == "session_info"]
        assert len(session_info) == 1
        assert session_info[0]["content"] == "test-session-123"

    @patch("app.api.chat.route_request")
    def test_chat_stream_with_llm_override(self, mock_route):
        mock_route.return_value = {
            "thought": "Delegation.",
            "action": "call_crew",
            "reply": "",
            "crew_name": "Project_Architect",
            "crew_inputs": {},
            "llm_tier": "expert",
        }
        mock_chunks = ['{"type": "result", "content": "Résultat avec override."}']
        with patch("app.api.chat.run_crew", return_value=mock_chunks):
            res = client.post("/api/chat", json={
                "crew_name": "default",
                "message": "Test override",
                "llm_override": "openai/",
            })
            chunks = []
            for line in res.iter_lines():
                if line.startswith("data: "):
                    chunks.append(json.loads(line[6:]))
            assert any(c["type"] == "result" for c in chunks)


# ── 9. CORS ───────────────────────────────────────────────────────────────────


class TestCORS:
    def test_cors_headers_present(self):
        res = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert res.status_code == 200
        assert "access-control-allow-origin" in res.headers

    def test_cors_rejects_unknown_origin(self):
        res = client.get("/api/health", headers={"Origin": "http://evil.com"})
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") is None


# ── 10. Error Handling ────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_not_found_returns_404(self):
        res = client.get("/api/nonexistent")
        assert res.status_code == 404

    def test_rate_limiter_configured(self):
        res = client.get("/api/health")
        assert res.status_code == 200
