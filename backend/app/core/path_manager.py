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
    """Retourne l'instance globale de ``PathManager``.

    Crée l'instance à la demande si elle n'existe pas encore.
    La racine est déterminée dans l'ordre : paramètre *root*,
    variable d'environnement ``PROJECT_ROOT``, ou parent du projet.

    Args:
        root: Chemin racine optionnel. Si omis, utilise les
              sources de configuration par défaut.

    Returns:
        L'instance singleton de ``PathManager``.
    """
    global _global_manager
    if _global_manager is None:
        # Fallback : racine étendue (parent de backend/ → Code/)
        root_path = root or os.getenv("PROJECT_ROOT") or str(Path(__file__).resolve().parent.parent.parent.parent)
        _global_manager = PathManager(root_path)
    return _global_manager

def safe_resolve(path: str, external_root: str | None = None) -> Path:
    """
    Résout un chemin via le manager global.

    Si ``external_root`` est fourni et que le chemin est absolu,
    la validation de périmètre est faite contre ``external_root``
    au lieu du projet racine.  Cela permet aux agents d'écrire
    dans un dossier externe (ex. ``/Users/.../Cours/SWO``) quand
    l'utilisateur le spécifie explicitement.
    """
    if not path:
        return get_path_manager().resolve(path)

    p = Path(path)
    if p.is_absolute() and external_root:
        # Chemin absolu externe : validation contre external_root
        resolved = p.resolve()
        ext_root = Path(external_root).resolve()
        if not str(resolved).startswith(str(ext_root)):
            raise PermissionError(
                f"Accès non autorisé : le chemin {resolved} est en dehors de la racine externe {ext_root}"
            )
        return resolved

    return get_path_manager().resolve(path)


def safe_resolve_external(path: str) -> Path:
    """
    Résout un chemin absolu en autorisant l'accès uniquement aux
    racines externes explicites (ALLOWED_EXTERNAL_ROOTS).

    Si aucune racine externe n'est configurée, l'accès est restreint
    au PROJECT_ROOT par défaut.

    Args:
        path: Chemin absolu à résoudre.

    Returns:
        Le chemin Path résolu et validé.

    Raises:
        PermissionError: Si le chemin n'est pas dans une racine autorisée.
    """
    import os

    p = Path(path)
    if not p.is_absolute():
        return get_path_manager().resolve(path)

    resolved = p.resolve()

    # Get configured external roots from environment
    external_roots_env = os.getenv("ALLOWED_EXTERNAL_ROOTS", "")
    allowed_roots: list[Path] = []
    if external_roots_env:
        for root_str in external_roots_env.split(":"):
            root_str = root_str.strip()
            if root_str:
                allowed_roots.append(Path(root_str).resolve())

    # If no external roots configured, fall back to PROJECT_ROOT
    if not allowed_roots:
        allowed_roots = [get_path_manager().root]

    # Check if resolved path is under any allowed root
    for allowed_root in allowed_roots:
        try:
            resolved.relative_to(allowed_root)
            return resolved
        except ValueError:
            continue

    raise PermissionError(
        f"Accès non autorisé : le chemin {resolved} n'est pas dans une racine externe autorisée. "
        f"Racines autorisées : {', '.join(str(r) for r in allowed_roots)}"
    )
