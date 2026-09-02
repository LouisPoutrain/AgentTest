"""
core/path_manager.py — Centralisation de la résolution et de la sécurisation des chemins.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

class PathManager:
    def __init__(self, root_dir: Union[str, Path]):
        self.root = Path(root_dir).resolve()

    def resolve(self, path: Union[str, Path]) -> Path:
        """
        Résout un chemin par rapport à la racine et s'assure qu'il ne sort pas du périmètre.

        Args:
            path: Le chemin à résoudre (absolu ou relatif).

        Returns:
            Le chemin Path résolu et sécurisé.

        Raises:
            PermissionError: Si le chemin tente de sortir de la racine (Path Traversal).
        """
        if not path:
            return self.root

        p = Path(path)

        # Si le chemin est absolu, on vérifie s'il commence par la racine
        if p.is_absolute():
            resolved = p.resolve()
        else:
            # Sinon, on le résout relativement à la racine
            resolved = (self.root / p).resolve()

        # Sécurité : Vérification du Path Traversal
        if not str(resolved).startswith(str(self.root)):
            raise PermissionError(
                f"Accès non autorisé : le chemin {resolved} est en dehors de la racine {self.root}"
            )

        return resolved

    def normalize_project_path(self, provided_path: str) -> str:
        """
        S'assure que le project_path injecté aux agents est propre et non redondant.
        """
        try:
            resolved = self.resolve(provided_path)
            return str(resolved)
        except PermissionError:
            # En cas d'erreur sur le project_path initial, on retourne la racine par défaut
            return str(self.root)

# Instance globale pour faciliter l'utilisation dans les outils
# La racine est initialisée dynamiquement lors du premier appel ou via une config
_global_manager: PathManager | None = None

def get_path_manager(root: str | None = None) -> PathManager:
    global _global_manager
    if _global_manager is None:
        # Fallback : on tente de trouver la racine du projet (backend/..)
        root_path = root or os.getenv("PROJECT_ROOT") or str(Path(__file__).resolve().parent.parent.parent)
        _global_manager = PathManager(root_path)
    return _global_manager

def safe_resolve(path: str) -> Path:
    """Helper rapide pour résoudre un chemin via le manager global."""
    return get_path_manager().resolve(path)
