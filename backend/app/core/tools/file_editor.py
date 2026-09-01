"""
Outil CrewAI pour la lecture, l'écriture et la recherche dans les fichiers.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool


class FileEditorTool(BaseTool):
    """Outil pour éditer les fichiers du projet."""

    name: str = "File Editor"
    description: str = (
        "Un outil pour lire, écrire et rechercher du contenu dans les fichiers du projet. "
        "Utilisez-le pour : "
        "1. Lire un fichier : read(file_path='path/to/file.py') "
        "2. Écrire un fichier : write(file_path='path/to/file.py', content='nouveau contenu') "
        "3. Rechercher du texte : search(directory='.', pattern='mot_clé') "
        "4. Lister les fichiers : list(directory='.') "
        "Les chemins sont relatifs au répertoire de travail actuel."
    )

    def _run(
        self,
        action: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        pattern: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> str:
        """
        Exécute l'action demandée sur le système de fichiers.

        Args:
            action: L'action à effectuer ('read', 'write', 'search', 'list').
            file_path: Chemin du fichier cible (pour read/write).
            content: Contenu à écrire (pour write).
            pattern: Motif de recherche (pour search).
            directory: Répertoire à explorer (pour search/list).

        Returns:
            str: Le résultat de l'action.
        """
        try:
            if action == "read":
                if not file_path:
                    return "Erreur : 'file_path' est requis pour l'action 'read'."
                
                # Sécurité : empêcher la traversée de répertoires
                resolved_path = Path(file_path).resolve()
                if not str(resolved_path).startswith(str(Path.cwd())):
                    return f"Erreur : Accès refusé au fichier en dehors du répertoire de travail : {file_path}"

                if not resolved_path.exists():
                    return f"Erreur : Fichier introuvable : {file_path}"
                
                if not resolved_path.is_file():
                    return f"Erreur : {file_path} n'est pas un fichier."

                with open(resolved_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif action == "write":
                if not file_path:
                    return "Erreur : 'file_path' est requis pour l'action 'write'."
                if content is None:
                    return "Erreur : 'content' est requis pour l'action 'write'."

                resolved_path = Path(file_path).resolve()
                if not str(resolved_path).startswith(str(Path.cwd())):
                    return f"Erreur : Accès refusé au fichier en dehors du répertoire de travail : {file_path}"

                # Créer les répertoires parents si nécessaire
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(resolved_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return f"Succès : Contenu écrit dans {file_path}."

            elif action == "search":
                if not pattern:
                    return "Erreur : 'pattern' est requis pour l'action 'search'."
                if not directory:
                    directory = '.'

                resolved_dir = Path(directory).resolve()
                if not str(resolved_dir).startswith(str(Path.cwd())):
                    return f"Erreur : Accès refusé au répertoire en dehors du répertoire de travail : {directory}"

                if not resolved_dir.exists() or not resolved_dir.is_dir():
                    return f"Erreur : Répertoire introuvable ou invalide : {directory}"

                results = []
                for root, _, files in os.walk(resolved_dir):
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.md', '.yaml', '.yml', '.json')):
                            file_path = Path(root) / file
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    if re.search(pattern, f.read()):
                                        results.append(str(file_path.relative_to(Path.cwd())))
                            except Exception:
                                pass

                if results:
                    return f"Résultats de la recherche pour '{pattern}' :\n" + "\n".join(results)
                else:
                    return f"Aucun résultat trouvé pour '{pattern}'."

            elif action == "list":
                if not directory:
                    directory = '.'

                resolved_dir = Path(directory).resolve()
                if not str(resolved_dir).startswith(str(Path.cwd())):
                    return f"Erreur : Accès refusé au répertoire en dehors du répertoire de travail : {directory}"

                if not resolved_dir.exists() or not resolved_dir.is_dir():
                    return f"Erreur : Répertoire introuvable ou invalide : {directory}"

                items = []
                for item in resolved_dir.iterdir():
                    rel_path = item.relative_to(Path.cwd())
                    prefix = "📁 " if item.is_dir() else "📄 "
                    items.append(f"{prefix}{rel_path}")
                
                return "Contenu du répertoire :\n" + "\n".join(items)

            else:
                return f"Erreur : Action inconnue '{action}'. Utilisez 'read', 'write', 'search' ou 'list'."

        except Exception as e:
            return f"Erreur lors de l'exécution de l'action '{action}' : {str(e)}"
