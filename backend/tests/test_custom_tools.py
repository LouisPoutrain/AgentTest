"""Tests for tools/custom_tools.py — safe command validation and whitelisted execution."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.tools.custom_tools import (
    _is_safe_command,
    _build_safe_command,
    ALLOWED_COMMAND_PREFIXES,
)


class TestIsSafeCommand:
    """Tests for _is_safe_command — regex-based character whitelist."""

    def test_empty_string(self):
        assert _is_safe_command("") is False

    def test_none(self):
        assert _is_safe_command(None) is False

    def test_too_long(self):
        assert _is_safe_command("a" * 501) is False

    def test_safe_simple_command(self):
        assert _is_safe_command("npm test") is True

    def test_safe_command_with_args(self):
        assert _is_safe_command("pytest tests/unit/") is True

    def test_safe_command_with_dashes(self):
        assert _is_safe_command("go build -o myapp") is True

    def test_safe_command_with_underscores(self):
        assert _is_safe_command("python -m pytest my_test_file.py") is True

    def test_safe_command_with_dots(self):
        assert _is_safe_command("node index.js") is True

    def test_safe_command_with_slashes(self):
        assert _is_safe_command("npm run build -- --config ./webpack.config.js") is True

    def test_rejects_parentheses(self):
        # Parentheses are shell metacharacters and must be rejected
        assert _is_safe_command("echo (hello)") is False

    def test_rejects_commas(self):
        # Commas are not in the allowed character set
        assert _is_safe_command("npm test, file") is False

    def test_rejects_shell_metacharacters_semicolon(self):
        assert _is_safe_command("npm test; rm -rf /") is False

    def test_rejects_shell_metacharacters_pipe(self):
        assert _is_safe_command("npm test | cat /etc/passwd") is False

    def test_rejects_shell_metacharacters_redirect(self):
        assert _is_safe_command("npm test > /dev/null") is False

    def test_rejects_shell_metacharacters_backtick(self):
        assert _is_safe_command("npm test `whoami`") is False

    def test_rejects_shell_metacharacters_dollar(self):
        assert _is_safe_command("npm test $(whoami)") is False

    def test_rejects_shell_metacharacters_ampersand(self):
        assert _is_safe_command("npm test & npm run lint") is False

    def test_rejects_shell_metacharacters_quotes(self):
        assert _is_safe_command('npm test "rm -rf /"') is False

    def test_rejects_shell_metacharacters_single_quotes(self):
        assert _is_safe_command("npm test 'rm -rf /'") is False

    def test_rejects_shell_metacharacters_star(self):
        assert _is_safe_command("npm test *.py") is False

    def test_rejects_shell_metacharacters_question(self):
        assert _is_safe_command("npm test ?.py") is False

    def test_rejects_shell_metacharacters_brackets(self):
        assert _is_safe_command("npm test [test]") is False

    def test_rejects_shell_metacharacters_exclamation(self):
        assert _is_safe_command("npm test !true") is False

    def test_rejects_shell_metacharacters_hash(self):
        assert _is_safe_command("npm test # comment") is False

    def test_rejects_colons(self):
        # Colons are not in the allowed character set
        assert _is_safe_command("cargo clippy -- -A clippy::all") is False

    def test_rejects_windows_paths(self):
        # Backslashes are not in the allowed character set
        assert _is_safe_command("C:\\Windows\\System32") is False

    def test_rejects_equals_sign(self):
        # Equals is not in the allowed character set
        assert _is_safe_command("pytest --tb=short") is False


class TestBuildSafeCommand:
    """Tests for _build_safe_command — shlex-based splitting."""

    def test_simple_command(self):
        assert _build_safe_command("npm test") == ["npm", "test"]

    def test_command_with_quoted_args(self):
        assert _build_safe_command('echo "hello world"') == ["echo", "hello world"]

    def test_command_with_single_quotes(self):
        assert _build_safe_command("echo 'hello world'") == ["echo", "hello world"]

    def test_command_with_multiple_args(self):
        assert _build_safe_command("pytest tests/unit/ -v") == ["pytest", "tests/unit/", "-v"]


class TestAllowedCommandPrefixes:
    """Tests that ALLOWED_COMMAND_PREFIXES covers expected languages/tooling."""

    def test_contains_npm_prefixes(self):
        assert "npm test" in ALLOWED_COMMAND_PREFIXES
        assert "npm run" in ALLOWED_COMMAND_PREFIXES

    def test_contains_pytest_prefixes(self):
        assert "pytest" in ALLOWED_COMMAND_PREFIXES
        assert "python -m pytest" in ALLOWED_COMMAND_PREFIXES

    def test_contains_python_prefix(self):
        assert "python -c" in ALLOWED_COMMAND_PREFIXES

    def test_contains_node_prefixes(self):
        assert "node" in ALLOWED_COMMAND_PREFIXES
        assert "npx" in ALLOWED_COMMAND_PREFIXES

    def test_contains_pip_prefixes(self):
        assert "pip install" in ALLOWED_COMMAND_PREFIXES
        assert "pip list" in ALLOWED_COMMAND_PREFIXES

    def test_contains_go_prefixes(self):
        assert "go test" in ALLOWED_COMMAND_PREFIXES
        assert "go build" in ALLOWED_COMMAND_PREFIXES
        assert "go vet" in ALLOWED_COMMAND_PREFIXES

    def test_contains_rust_prefixes(self):
        assert "cargo test" in ALLOWED_COMMAND_PREFIXES
        assert "cargo build" in ALLOWED_COMMAND_PREFIXES
        assert "cargo clippy" in ALLOWED_COMMAND_PREFIXES

    def test_contains_java_prefixes(self):
        assert "gradle" in ALLOWED_COMMAND_PREFIXES
        assert "mvn test" in ALLOWED_COMMAND_PREFIXES
        assert "mvn compile" in ALLOWED_COMMAND_PREFIXES

    def test_contains_ruby_prefixes(self):
        assert "bundle exec rspec" in ALLOWED_COMMAND_PREFIXES
        assert "bundle exec rake" in ALLOWED_COMMAND_PREFIXES

    def test_contains_dotnet_prefixes(self):
        assert "dotnet test" in ALLOWED_COMMAND_PREFIXES
        assert "dotnet build" in ALLOWED_COMMAND_PREFIXES

    def test_contains_make_prefixes(self):
        assert "make" in ALLOWED_COMMAND_PREFIXES
        assert "make test" in ALLOWED_COMMAND_PREFIXES

    def test_contains_linters(self):
        assert "flake8" in ALLOWED_COMMAND_PREFIXES
        assert "pylint" in ALLOWED_COMMAND_PREFIXES
        assert "mypy" in ALLOWED_COMMAND_PREFIXES
        assert "eslint" in ALLOWED_COMMAND_PREFIXES
        assert "prettier" in ALLOWED_COMMAND_PREFIXES
        assert "black" in ALLOWED_COMMAND_PREFIXES
        assert "ruff" in ALLOWED_COMMAND_PREFIXES


class TestRunTestCommand:
    """Tests for run_test_command — whitelist enforcement and subprocess execution."""

    @pytest.fixture()
    def run_test_command_func(self):
        """Get the unwrapped function from the @tool decorator."""
        from app.tools import custom_tools
        return custom_tools.run_test_command.func

    @pytest.fixture()
    def project_root(self):
        """Return the actual project root path (inside the safe_resolve root)."""
        return Path(__file__).resolve().parent.parent

    def test_rejects_empty_command(self, run_test_command_func):
        result = run_test_command_func("/tmp", "")
        assert "Erreur de sécurité" in result

    def test_rejects_unsafe_characters(self, run_test_command_func):
        result = run_test_command_func("/tmp", "npm test; rm -rf /")
        assert "Erreur de sécurité" in result

    def test_rejects_command_not_in_whitelist(self, run_test_command_func):
        result = run_test_command_func("/tmp", "rm -rf /")
        assert "n'est pas dans la liste blanche" in result

    def test_rejects_command_with_shell_metacharacters(self, run_test_command_func):
        result = run_test_command_func("/tmp", "npm test | cat /etc/passwd")
        assert "Erreur de sécurité" in result

    def test_accepts_whitelisted_npm_test(self, project_root: Path, run_test_command_func):
        """Whitelisted command should proceed to subprocess (mocked)."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "passed 5 tests"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "npm test")

        assert "EXIT_CODE: 0" in result
        assert "passed 5 tests" in result

    def test_accepts_whitelisted_pytest(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "FAILED tests/test_foo.py"

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "pytest tests/")

        assert "EXIT_CODE: 1" in result
        assert "FAILED tests/test_foo.py" in result

    def test_accepts_whitelisted_go_test(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "ok  \tmylib 0.001s"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "go test ./...")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_cargo_test(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "test result: ok."
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "cargo test")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_make(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "echo 'tests passed'"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "make test")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_npx(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "npx vitest run")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_dotnet_test(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Passed! - Failed: 0, Passed: 10"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "dotnet test")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_flake8(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "flake8 src/")

        assert "EXIT_CODE: 0" in result

    def test_accepts_whitelisted_pylint(self, project_root: Path, run_test_command_func):
        mock_process = MagicMock()
        mock_process.returncode = 7
        mock_process.stdout = "Your code has been rated at 0.00/10"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "pylint src/")

        assert "EXIT_CODE: 7" in result

    def test_handles_timeout(self, project_root: Path, run_test_command_func):
        with patch("app.tools.custom_tools.subprocess.run", side_effect=subprocess.TimeoutExpired("npm test", 120)):
            result = run_test_command_func(str(project_root), "npm test")

        assert "délai" in result or "dépassé" in result

    def test_handles_generic_exception(self, project_root: Path, run_test_command_func):
        with patch("app.tools.custom_tools.subprocess.run", side_effect=PermissionError("Permission denied")):
            result = run_test_command_func(str(project_root), "npm test")

        assert "Erreur" in result

    def test_command_startswith_prefix_case_sensitive(self, project_root: Path, run_test_command_func):
        """Commands must start with the prefix — 'pytest' should match but 'xpytest' should not."""
        result = run_test_command_func(str(project_root), "xpytest tests/")
        assert "n'est pas dans la liste blanche" in result

    def test_command_with_safe_extra_args(self, project_root: Path, run_test_command_func):
        """Whitelisted prefix with additional safe arguments should work."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "ok"
        mock_process.stderr = ""

        with patch("app.tools.custom_tools.subprocess.run", return_value=mock_process):
            result = run_test_command_func(str(project_root), "pytest tests/ -v")

        assert "EXIT_CODE: 0" in result


# ── search_scholar ─────────────────────────────────────────────────────────────


class TestSearchScholar:
    """Tests for search_scholar — Semantic Scholar API wrapper."""

    @pytest.fixture()
    def search_scholar_func(self):
        from app.tools import custom_tools
        return custom_tools.search_scholar.func

    def test_empty_query(self, search_scholar_func):
        result = search_scholar_func("")
        assert "Erreur" in result and "vide" in result

    def test_empty_query_whitespace(self, search_scholar_func):
        result = search_scholar_func("   ")
        assert "Erreur" in result and "vide" in result

    def test_limit_too_low(self, search_scholar_func):
        result = search_scholar_func("test", limit=0)
        assert "Erreur" in result

    def test_limit_too_high(self, search_scholar_func):
        result = search_scholar_func("test", limit=200)
        assert "Erreur" in result

    def test_valid_limit_range(self, search_scholar_func):
        # limit=1 should not be rejected by validation
        result = search_scholar_func("test", limit=1)
        # May be error from network, but not from validation
        assert "vide" not in result

    def test_limit_100(self, search_scholar_func):
        result = search_scholar_func("test", limit=100)
        assert "vide" not in result

    def test_connection_error(self, search_scholar_func):
        with patch("app.tools.custom_tools.requests.get", side_effect=requests.ConnectionError()):
            result = search_scholar_func("machine learning")
            assert "Erreur" in result or "connexion" in result

    def test_timeout(self, search_scholar_func):
        with patch("app.tools.custom_tools.requests.get", side_effect=requests.Timeout()):
            result = search_scholar_func("machine learning")
            assert "délai" in result or "timeout" in result or "Timeout" in result or "Dépassé" in result

    def test_rate_limit(self, search_scholar_func):
        mock_response = MagicMock()
        mock_response.status_code = 429
        with patch("app.tools.custom_tools.requests.get", return_value=mock_response):
            result = search_scholar_func("machine learning")
            assert "limite de taux" in result or "rate" in result.lower() or "429" in result

    def test_successful_response(self, search_scholar_func):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 2,
            "data": [
                {
                    "title": "Deep Learning",
                    "authors": [{"name": "Yann LeCun"}, {"name": "Yoshua Bengio"}],
                    "year": 2015,
                    "citationCount": 50000,
                    "url": "https://arxiv.org/abs/1500.0001",
                    "tldr": {"text": "A comprehensive survey of deep learning."},
                    "venue": "Nature",
                    "openAccessPdf": {"url": "https://example.com/paper.pdf"},
                }
            ],
        }
        with patch("app.tools.custom_tools.requests.get", return_value=mock_response):
            result = search_scholar_func("deep learning", limit=5)
            assert "Deep Learning" in result
            assert "Yann LeCun" in result
            assert "50000" in result
            assert "Nature" in result
            assert "arxiv.org" in result
            assert "example.com/paper.pdf" in result

    def test_no_results(self, search_scholar_func):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total": 0, "data": []}
        with patch("app.tools.custom_tools.requests.get", return_value=mock_response):
            result = search_scholar_func("nonexistent_topic_xyz")
            assert "Aucun résultat" in result or "0" in result


# ── http_request ────────────────────────────────────────────────────────────────


class TestHttpRequest:
    """Tests for http_request — generic HTTP tool with security."""

    @pytest.fixture()
    def http_request_func(self):
        from app.tools import custom_tools
        return custom_tools.http_request.func

    def test_rejects_empty_url(self, http_request_func):
        result = http_request_func("")
        assert "Erreur" in result

    def test_rejects_invalid_scheme(self, http_request_func):
        result = http_request_func("ftp://example.com")
        assert "Erreur de sécurité" in result or "schéma" in result

    def test_rejects_no_scheme(self, http_request_func):
        result = http_request_func("example.com")
        assert "Erreur de sécurité" in result or "schéma" in result

    def test_rejects_file_scheme(self, http_request_func):
        result = http_request_func("file:///etc/passwd")
        assert "Erreur de sécurité" in result or "schéma" in result

    def test_rejects_localhost(self, http_request_func):
        result = http_request_func("http://localhost:8080/api")
        assert "Erreur de sécurité" in result or "privé" in result

    def test_rejects_127_0_0_1(self, http_request_func):
        result = http_request_func("http://127.0.0.1:8080/api")
        assert "Erreur de sécurité" in result or "privé" in result

    def test_rejects_192_168(self, http_request_func):
        result = http_request_func("http://192.168.1.1/api")
        assert "Erreur de sécurité" in result or "privé" in result

    def test_rejects_10_xxx(self, http_request_func):
        result = http_request_func("http://10.0.0.1/api")
        assert "Erreur de sécurité" in result or "privé" in result

    def test_rejects_invalid_method(self, http_request_func):
        result = http_request_func("https://example.com", method="HACK")
        assert "Erreur" in result and "non autorisée" in result

    def test_rejects_invalid_headers_json(self, http_request_func):
        result = http_request_func("https://example.com", headers="not json")
        assert "Erreur" in result and "JSON invalide" in result

    def test_rejects_invalid_body_json(self, http_request_func):
        result = http_request_func("https://example.com", body="not json")
        assert "Erreur" in result and "JSON invalide" in result

    def test_successful_get(self, http_request_func):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status":"ok"}'
        mock_response.headers = {"Content-Type": "application/json"}
        with patch("app.tools.custom_tools.requests.request", return_value=mock_response):
            result = http_request_func("https://api.example.com/data", method="GET")
            assert "200" in result
            assert "ok" in result

    def test_successful_post(self, http_request_func):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id":123}'
        mock_response.headers = {"Content-Type": "application/json"}
        with patch("app.tools.custom_tools.requests.request", return_value=mock_response) as mock_req:
            result = http_request_func(
                "https://api.example.com/create",
                method="POST",
                headers='{"Content-Type": "application/json"}',
                body='{"name": "test"}'
            )
            assert "201" in result
            assert "123" in result
            # Verify the request was called with correct args
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args
            assert call_kwargs.kwargs.get("method") == "POST"
            assert call_kwargs.kwargs.get("url") == "https://api.example.com/create"
            assert call_kwargs.kwargs.get("headers") == {"Content-Type": "application/json"}
            assert call_kwargs.kwargs.get("json") == {"name": "test"}

    def test_rejects_authorization_header(self, http_request_func):
        result = http_request_func(
            "https://api.example.com/data",
            headers='{"Authorization": "Bearer token123"}'
        )
        assert "Erreur de sécurité" in result and "Authorization" in result

    def test_rejects_proxy_authorization_header(self, http_request_func):
        result = http_request_func(
            "https://api.example.com/data",
            headers='{"Proxy-Authorization": "Basic abc123"}'
        )
        assert "Erreur de sécurité" in result and "Proxy-Authorization" in result

    def test_timeout(self, http_request_func):
        with patch("app.tools.custom_tools.requests.request", side_effect=requests.Timeout()):
            result = http_request_func("https://slow.api.com/data")
            assert "Délai" in result or "timeout" in result or "Dépassé" in result

    def test_connection_error(self, http_request_func):
        with patch("app.tools.custom_tools.requests.request", side_effect=requests.ConnectionError()):
            result = http_request_func("https://unreachable.api.com/data")
            assert "Erreur" in result or "connexion" in result

    def test_response_truncation(self, http_request_func):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "x" * 60000  # 60KB, over the 50KB limit
        mock_response.headers = {}
        with patch("app.tools.custom_tools.requests.request", return_value=mock_response):
            result = http_request_func("https://big.api.com/data")
            assert "TRONQUÉE" in result

    def test_truncation_not_applied_for_small_response(self, http_request_func):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "small"
        mock_response.headers = {}
        with patch("app.tools.custom_tools.requests.request", return_value=mock_response):
            result = http_request_func("https://small.api.com/data")
            assert "TRONQUÉE" not in result
            assert "small" in result

    def test_all_allowed_methods(self, http_request_func):
        """GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS should all be accepted."""
        allowed = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        for method in allowed:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "ok"
            mock_response.headers = {}
            with patch("app.tools.custom_tools.requests.request", return_value=mock_response):
                result = http_request_func("https://example.com", method=method)
                assert "200" in result or "ok" in result

    def test_case_insensitive_method(self, http_request_func):
        """Lowercase 'get' should be accepted."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_response.headers = {}
        with patch("app.tools.custom_tools.requests.request", return_value=mock_response):
            result = http_request_func("https://example.com", method="get")
            assert "200" in result or "ok" in result
