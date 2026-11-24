"""Tests for PathManager — path resolution and traversal prevention."""

from pathlib import Path

import pytest

from app.core.path_manager import PathManager


class TestPathManagerInit:
    def test_accepts_string_root(self, tmp_path: Path):
        pm = PathManager(str(tmp_path))
        assert pm.root == tmp_path.resolve()

    def test_accepts_path_root(self, tmp_path: Path):
        pm = PathManager(tmp_path)
        assert pm.root == tmp_path.resolve()

    def test_resolves_symlinks(self, tmp_path: Path):
        """Root should be resolved (symlinks followed)."""
        pm = PathManager(str(tmp_path))
        assert str(pm.root) == str(tmp_path.resolve())


class TestPathManagerResolve:
    @pytest.fixture()
    def pm(self, tmp_path: Path) -> PathManager:
        return PathManager(tmp_path)

    # --- Normal resolution ---

    def test_returns_root_for_empty_path(self, pm: PathManager):
        assert pm.resolve("") == pm.root
        assert pm.resolve(None) == pm.root

    def test_resolves_relative_path(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve("subdir/file.txt")
        assert result == tmp_path / "subdir" / "file.txt"

    def test_resolves_simple_filename(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve("file.txt")
        assert result == tmp_path / "file.txt"

    def test_resolves_dot_path(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve(".")
        assert result == tmp_path

    def test_resolves_double_dot_path(self, pm: PathManager, tmp_path: Path):
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        result = pm.resolve("a/b/..")
        assert result == tmp_path / "a"

    def test_resolves_absolute_path_within_root(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve(str(tmp_path / "subdir"))
        assert result == tmp_path / "subdir"

    def test_normalizes_trailing_slash(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve("subdir/")
        assert result == tmp_path / "subdir"

    # --- Path traversal prevention ---

    def test_blocks_simple_traversal(self, pm: PathManager):
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("../etc/passwd")

    def test_blocks_double_traversal(self, pm: PathManager):
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("../../etc/passwd")

    def test_blocks_traversal_with_intermediate_dir(self, pm: PathManager, tmp_path: Path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("subdir/../../etc/passwd")

    def test_blocks_absolute_path_outside_root(self, pm: PathManager):
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("/etc/passwd")

    def test_blocks_absolute_path_to_home(self, pm: PathManager):
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("/home/user/.ssh/id_rsa")

    def test_allows_path_at_root_boundary(self, pm: PathManager, tmp_path: Path):
        """A path that resolves exactly to root should be allowed."""
        # ".." from root escapes the root, so it should raise PermissionError.
        # Test a path that stays at root instead.
        with pytest.raises(PermissionError, match="en dehors de la racine"):
            pm.resolve("..")
        result = pm.resolve("")
        assert result == pm.root

    def test_allows_deeply_nested_safe_path(self, pm: PathManager, tmp_path: Path):
        deep = "a/b/c/d/e/f/g"
        result = pm.resolve(deep)
        assert str(result).startswith(str(tmp_path))

    def test_path_with_spaces(self, pm: PathManager, tmp_path: Path):
        result = pm.resolve("my folder/my file.txt")
        assert result == tmp_path / "my folder" / "my file.txt"

    def test_path_with_unicode(self, tmp_path: Path):
        pm = PathManager(tmp_path)
        result = pm.resolve("dossier_français/fichier.txt")
        assert "dossier_français" in str(result)


class TestPathManagerNormalizeProjectPath:
    @pytest.fixture()
    def pm(self, tmp_path: Path) -> PathManager:
        return PathManager(tmp_path)

    def test_returns_resolved_path(self, pm: PathManager, tmp_path: Path):
        result = pm.normalize_project_path("subdir/../subdir")
        assert result == str(tmp_path / "subdir")

    def test_returns_root_on_traversal(self, pm: PathManager):
        result = pm.normalize_project_path("../etc/passwd")
        assert result == str(pm.root)

    def test_returns_root_on_absolute_outside(self, pm: PathManager):
        result = pm.normalize_project_path("/etc/passwd")
        assert result == str(pm.root)


class TestGlobalHelpers:
    def test_get_path_manager_creates_singleton(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from app.core.path_manager import get_path_manager, _global_manager
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        # Force reset of global
        import app.core.path_manager as pm_mod
        pm_mod._global_manager = None
        pm1 = get_path_manager()
        pm2 = get_path_manager()
        assert pm1 is pm2

    def test_safe_resolve_uses_global(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from app.core.path_manager import safe_resolve
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        import app.core.path_manager as pm_mod
        pm_mod._global_manager = None
        result = safe_resolve("test.txt")
        assert result == tmp_path / "test.txt"
