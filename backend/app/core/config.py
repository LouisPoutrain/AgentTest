"""
core/config.py — Configuration centralisée du backend.

Lit les chemins et paramètres depuis les variables d'environnement
avec des valeurs par défaut sûres. Remplace les chemins magiques
parents[N] qui cassent si on déplace un fichier.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────────

# Racine étendue : dossier parent contenant tous les projets (AgentTest, Cours/, etc.)
# Par défaut : on remonte de 3 niveaux depuis ce fichier (core/ → app/ → backend/ → racine → Code/)
# Override via PROJECT_ROOT pour la flexibilité.
_DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT: Path = Path(os.getenv("PROJECT_ROOT", _DEFAULT_PROJECT_ROOT)).resolve()

# Dossier des Crews YAML — toujours dans le projet AgentTest, pas dans la racine étendue
_CREWS_DIR_DEFAULT = Path(__file__).resolve().parent.parent.parent / "config" / "crews"
CREWS_DIR: Path = Path(os.getenv("CREWS_DIR", str(_CREWS_DIR_DEFAULT))).resolve()
CREWS_DIR.mkdir(parents=True, exist_ok=True)

# Dossier de config global — toujours dans le projet AgentTest
_CONFIG_DIR_DEFAULT = Path(__file__).resolve().parent.parent.parent / "config"
CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", str(_CONFIG_DIR_DEFAULT))).resolve()

# Base de données SQLite
DB_PATH: Path = Path(os.getenv("SESSIONS_DB", str(PROJECT_ROOT / "sessions.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Validation des variables d'environnement requises ──────────────────────────

_REQUIRED_ENV_VARS: dict[str, str] = {
    "LLM_API_KEY": "Clé API LLM (requis pour les appels LLM)",
    "LLM_BASE_URL": "URL de base du serveur LLM (requis pour les appels LLM)",
}


def validate_env() -> list[str]:
    """
    Vérifie que les variables d'environnement requises sont définies.

    Returns
    -------
    list[str]
        Liste des messages d'erreur (vide si tout est bon).
    """
    errors: list[str] = []
    for var, description in _REQUIRED_ENV_VARS.items():
        if not os.getenv(var):
            errors.append(f"Variable d'environnement manquante : {var} — {description}")
    return errors
