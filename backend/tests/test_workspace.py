"""Tests for api/workspace.py — _detect_stack() with various project structures."""

import json
from pathlib import Path

import pytest

from app.api.workspace import _detect_stack


class TestDetectStackNodeJS:
    """Tests for Node.js / JavaScript / TypeScript project detection."""

    def test_detects_nodejs_with_package_json(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Node.js"
        assert "Node.js" in tags

    def test_detects_nextjs(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"next": "14.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Next.js"
        assert "Next.js" in tags

    def test_detects_react(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "18.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "React"
        assert "React" in tags

    def test_detects_vue(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"vue": "3.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Vue"
        assert "Vue" in tags

    def test_detects_svelte(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@sveltejs/kit": "2.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Svelte"
        assert "Svelte" in tags

    def test_detects_express(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"express": "4.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Node.js API"
        assert "Node.js" in tags

    def test_detects_fastify(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"fastify": "4.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Node.js API"
        assert "Node.js" in tags

    def test_detects_typescript_from_deps(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"typescript": "5.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "TypeScript" in tags

    def test_detects_typescript_from_tsconfig(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(json.dumps({}))
        (tmp_path / "tsconfig.json").write_text("{}")
        framework, tags = _detect_stack(tmp_path)
        assert "TypeScript" in tags

    def test_detects_prisma_from_deps(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"prisma": "5.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Prisma" in tags

    def test_detects_prisma_from_client(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"@prisma/client": "5.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Prisma" in tags

    def test_detects_prisma_from_directory(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(json.dumps({}))
        (tmp_path / "prisma").mkdir()
        framework, tags = _detect_stack(tmp_path)
        assert "Prisma" in tags

    def test_detects_tailwind(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"tailwindcss": "3.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Tailwind" in tags

    def test_detects_vitest(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"devDependencies": {"vitest": "1.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Vitest" in tags

    def test_detects_jest(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"devDependencies": {"jest": "29.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Jest" in tags

    def test_prefers_vitest_over_jest(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"devDependencies": {"vitest": "1.0.0", "jest": "29.0.0"}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert "Vitest" in tags
        assert "Jest" not in tags

    def test_handles_invalid_json(self, tmp_path: Path):
        (tmp_path / "package.json").write_text("not valid json {{{")
        framework, tags = _detect_stack(tmp_path)
        # Should fall back gracefully
        assert "Node.js" in tags

    def test_handles_missing_package_json(self, tmp_path: Path):
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Projet"
        assert "Dossier" in tags


class TestDetectStackPython:
    """Tests for Python project detection."""

    def test_detects_python_from_py_files(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("print('hello')")
        framework, tags = _detect_stack(tmp_path)
        assert "Python" in tags

    def test_detects_python_from_requirements(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("flask==3.0.0")
        framework, tags = _detect_stack(tmp_path)
        assert "Python" in tags

    def test_detects_python_from_pyproject(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'myapp'")
        framework, tags = _detect_stack(tmp_path)
        assert "Python" in tags

    def test_detects_fastapi_from_requirements(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\nuvicorn==0.23.0")
        framework, tags = _detect_stack(tmp_path)
        assert "FastAPI" in tags
        assert framework == "FastAPI"

    def test_detects_fastapi_from_app_dir(self, tmp_path: Path):
        (tmp_path / "app").mkdir()
        (tmp_path / "main.py").write_text("")
        framework, tags = _detect_stack(tmp_path)
        assert "FastAPI" in tags
        assert framework == "FastAPI"

    def test_detects_crewai(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("crewai==0.1.0")
        framework, tags = _detect_stack(tmp_path)
        assert "CrewAI" in tags

    def test_detects_pytest(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("pytest==7.0.0")
        framework, tags = _detect_stack(tmp_path)
        assert "Pytest" in tags

    def test_detects_django(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("django==4.0.0")
        framework, tags = _detect_stack(tmp_path)
        assert "Django" in tags
        assert framework == "Django"

    def test_python_detected_alongside_nodejs(self, tmp_path: Path):
        """When both Node.js and Python are detected, both should appear in tags."""
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "18.0.0"}})
        )
        (tmp_path / "requirements.txt").write_text("flask==3.0.0")
        framework, tags = _detect_stack(tmp_path)
        assert "React" in tags
        assert "Python" in tags

    def test_django_overrides_python(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("django==4.0.0")
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Django"


class TestDetectStackGit:
    """Tests for Git repository detection."""

    def test_detects_git_directory(self, tmp_path: Path):
        (tmp_path / ".git").mkdir()
        framework, tags = _detect_stack(tmp_path)
        assert "Git" in tags

    def test_no_git_directory(self, tmp_path: Path):
        framework, tags = _detect_stack(tmp_path)
        assert "Git" not in tags


class TestDetectStackMixed:
    """Tests for projects with multiple technologies."""

    def test_mixed_nodejs_and_python(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "18.0.0"}})
        )
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0")
        framework, tags = _detect_stack(tmp_path)
        assert "React" in tags
        assert "Python" in tags
        assert "FastAPI" in tags

    def test_full_stack_project(self, tmp_path: Path):
        """A project with package.json, tsconfig, requirements.txt, and .git."""
        (tmp_path / "package.json").write_text(
            json.dumps({
                "dependencies": {"next": "14.0.0", "typescript": "5.0.0"},
                "devDependencies": {"vitest": "1.0.0"}
            })
        )
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0")
        (tmp_path / ".git").mkdir()
        (tmp_path / "tsconfig.json").write_text("{}")

        framework, tags = _detect_stack(tmp_path)
        assert "Next.js" in tags
        assert "TypeScript" in tags
        assert "Vitest" in tags
        assert "FastAPI" in tags
        assert "Python" in tags
        assert "Git" in tags

    def test_empty_directory(self, tmp_path: Path):
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Projet"
        assert "Dossier" in tags
        assert len(tags) == 1

    def test_only_git_directory(self, tmp_path: Path):
        (tmp_path / ".git").mkdir()
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Projet"
        assert "Git" in tags


class TestDetectStackEdgeCases:
    """Tests for edge cases and robustness."""

    def test_package_json_with_both_deps_and_devdeps(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({
                "dependencies": {"react": "18.0.0"},
                "devDependencies": {"vitest": "1.0.0"}
            })
        )
        framework, tags = _detect_stack(tmp_path)
        assert "React" in tags
        assert "Vitest" in tags

    def test_package_json_with_empty_deps(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {}, "devDependencies": {}})
        )
        framework, tags = _detect_stack(tmp_path)
        assert framework == "Node.js"
        assert "Node.js" in tags

    def test_requirements_with_multiple_frameworks(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text(
            "fastapi==0.100.0\ndjango==4.0.0\npytest==7.0.0"
        )
        framework, tags = _detect_stack(tmp_path)
        # FastAPI is checked first, then Django
        assert "FastAPI" in tags
        assert "Django" in tags
        assert "Pytest" in tags

    def test_unicode_in_package_json(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "18.0.0"}}, ensure_ascii=False)
        )
        framework, tags = _detect_stack(tmp_path)
        assert "React" in tags

    def test_nested_deps_object(self, tmp_path: Path):
        """Dependencies may be nested in unexpected structures."""
        (tmp_path / "package.json").write_text(
            json.dumps({
                "dependencies": {"react": "18.0.0"},
                "optionalDependencies": {"fsevents": "2.3.0"}
            })
        )
        framework, tags = _detect_stack(tmp_path)
        assert "React" in tags

    def test_detects_prisma_from_directory_and_deps(self, tmp_path: Path):
        """Both prisma directory and prisma dep should be detected."""
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"prisma": "5.0.0"}})
        )
        (tmp_path / "prisma").mkdir()
        framework, tags = _detect_stack(tmp_path)
        assert "Prisma" in tags
