"""Tests for core/router.py — route_request error handling with mocked litellm."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def router_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up a clean import of the router module with a temp DB path."""
    monkeypatch.setenv("SESSIONS_DB", str(tmp_path / "sessions.db"))
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("app.core"):
            del sys.modules[mod_name]
    from app.core import router
    return router


@pytest.fixture()
def mock_session(router_module, tmp_path: Path):
    """Create a session in the temp DB so get_history doesn't fail."""
    from app.core.history_manager import history_manager
    return history_manager.get_or_create_session("router-test", "user_1")


class TestRouteRequestErrorHandling:
    """Tests for route_request when litellm returns malformed or unexpected responses."""

    def test_returns_error_on_bad_json(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "this is not json at all"
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_empty_response(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = ""
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_no_json_braces(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "just plain text, no braces"
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_malformed_json(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"thought": "ok", action: broken}'
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_litellm_exception(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_completion.side_effect = Exception("Network timeout")

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_api_key_error(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_completion.side_effect = Exception("Invalid API key")

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_rate_limit(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_completion.side_effect = Exception("Rate limit exceeded")

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()

    def test_returns_error_on_model_not_found(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_completion.side_effect = Exception("Model 'nonexistent-model' not found")

            result = router_module.route_request(mock_session, "hello")

        assert result["action"] == "direct_reply"
        assert "Erreur" in result["thought"] or "error" in result["thought"].lower()


class TestRouteRequestSuccess:
    """Tests for route_request with valid litellm responses."""

    def test_parses_valid_direct_reply(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "This is a simple question",
                "action": "direct_reply",
                "reply": "I can help with that!",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "What is 2+2?")

        assert result["action"] == "direct_reply"
        assert result["reply"] == "I can help with that!"
        assert result["thought"] == "This is a simple question"
        assert result["llm_tier"] == "fast"
        assert result["tool_name"] is None
        assert result["crew_name"] is None

    def test_parses_call_crew(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "analyzing",
                "action": "call_crew",
                "reply": None,
                "tool_name": None,
                "tool_args": {},
                "crew_name": "code_review",
                "crew_inputs": {"code": "some code"},
                "llm_tier": "balanced"
            })
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "Review my code")

        assert result["action"] == "call_crew"
        assert result["crew_name"] == "code_review"
        assert result["crew_inputs"] == {"code": "some code"}
        assert result["llm_tier"] == "balanced"

    def test_parses_call_tool_then_direct_reply(self, mock_session: str, router_module):
        """ReAct loop: first call_tool, then direct_reply with the result."""
        with patch.object(router_module.litellm, "completion") as mock_completion:
            # First call: decide to call wikipedia_search
            mock_response1 = MagicMock()
            mock_response1.choices = [MagicMock()]
            mock_response1.choices[0].message.content = json.dumps({
                "thought": "search wikipedia for ML",
                "action": "call_tool",
                "reply": None,
                "tool_name": "wikipedia_search",
                "tool_args": {"query": "machine learning"},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            # Second call: decide to reply with the result
            mock_response2 = MagicMock()
            mock_response2.choices = [MagicMock()]
            mock_response2.choices[0].message.content = json.dumps({
                "thought": "I found the info on wikipedia",
                "action": "direct_reply",
                "reply": "Machine learning is a subset of AI...",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.side_effect = [mock_response1, mock_response2]

            result = router_module.route_request(mock_session, "What is ML?")

        assert result["action"] == "direct_reply"
        assert "Machine learning" in result["reply"]
        assert len(result["intermediate_logs"]) >= 2  # tool call + result logs

    def test_parses_json_with_extra_text_around(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "Here's my analysis:\n"
                '{"thought": "analyzing", "action": "call_crew", "reply": null, '
                '"tool_name": null, "tool_args": {}, '
                '"crew_name": "code_review", "crew_inputs": {}, "llm_tier": "balanced"}\n'
                "That's my recommendation."
            )
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "Review my code")

        assert result["action"] == "call_crew"
        assert result["crew_name"] == "code_review"
        assert result["llm_tier"] == "balanced"

    def test_calls_litellm_with_correct_model(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "ok",
                "action": "direct_reply",
                "reply": "ok",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            router_module.route_request(mock_session, "hello")

            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args.kwargs
            assert call_kwargs["model"] == "openai/llama-3.1-8b"

    def test_includes_history_in_messages(self, mock_session: str, router_module, monkeypatch: pytest.MonkeyPatch, temp_db: Path):
        import importlib
        import app.core.config
        importlib.reload(app.core.config)
        import app.core.history_manager
        importlib.reload(app.core.history_manager)
        import app.core.router
        importlib.reload(app.core.router)
        hm = app.core.history_manager.history_manager
        hm.add_message(mock_session, "user", "Previous question")
        hm.add_message(mock_session, "assistant", "Previous answer")

        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "ok",
                "action": "direct_reply",
                "reply": "ok",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            router_module.route_request(mock_session, "New question")

            call_args = mock_completion.call_args.kwargs["messages"]
            assert len(call_args) == 4
            assert call_args[0]["role"] == "system"
            assert call_args[1]["role"] == "user"
            assert call_args[1]["content"] == "Previous question"
            assert call_args[2]["role"] == "assistant"
            assert call_args[2]["content"] == "Previous answer"
            assert call_args[3]["role"] == "user"
            assert call_args[3]["content"] == "New question"

    def test_includes_crew_used_in_history(self, mock_session: str, router_module, monkeypatch: pytest.MonkeyPatch, temp_db: Path):
        import importlib
        import app.core.config
        importlib.reload(app.core.config)
        import app.core.history_manager
        importlib.reload(app.core.history_manager)
        import app.core.router
        importlib.reload(app.core.router)
        hm = app.core.history_manager.history_manager
        hm.add_message(
            mock_session, "assistant", "Code review complete", crew_used="code_review"
        )

        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "ok",
                "action": "direct_reply",
                "reply": "ok",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            router_module.route_request(mock_session, "What did the review say?")

            call_args = mock_completion.call_args.kwargs["messages"]
            assert "[Rapport du Crew code_review]" in call_args[1]["content"]

    def test_includes_context_inputs(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "ok",
                "action": "direct_reply",
                "reply": "ok",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            context = {"theme": "dark", "language": "fr"}
            router_module.route_request(mock_session, "hello", context_inputs=context)

            call_args = mock_completion.call_args.kwargs["messages"]
            sys_content = call_args[0]["content"]
            assert "CONTEXTE UI ACTUEL" in sys_content
            assert "theme" in sys_content
            assert "dark" in sys_content

    def test_strips_whitespace_from_response(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "  \n  {\"thought\": \"ok\", \"action\": \"direct_reply\", \"reply\": \"ok\", "
                "\"tool_name\": null, \"tool_args\": {}, \"crew_name\": null, "
                "\"crew_inputs\": {}, \"llm_tier\": \"fast\"}  \n  "
            )
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")
            assert result["action"] == "direct_reply"

    def test_ask_clarification(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "need more info",
                "action": "ask_clarification",
                "reply": "Quel fichier souhaitez-vous analyser ?",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "Analyse mon code")

        assert result["action"] == "ask_clarification"
        assert result["reply"] == "Quel fichier souhaitez-vous analyser ?"

    def test_intermediate_logs_included(self, mock_session: str, router_module):
        with patch.object(router_module.litellm, "completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "thought": "ok",
                "action": "direct_reply",
                "reply": "ok",
                "tool_name": None,
                "tool_args": {},
                "crew_name": None,
                "crew_inputs": {},
                "llm_tier": "fast"
            })
            mock_completion.return_value = mock_response

            result = router_module.route_request(mock_session, "hello")

        assert "intermediate_logs" in result
        assert isinstance(result["intermediate_logs"], list)
