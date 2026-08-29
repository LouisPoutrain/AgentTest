"""
core/git_importer.py — Importateur de configurations YAML depuis GitHub.

Télécharge un fichier YAML brut depuis une URL GitHub (raw)
et le sauvegarde dans le dossier ``config/crews/`` du projet.
"""

from __future__ import annotations

from pathlib import Path
import requests

def download_yaml_from_github(
    raw_url: str,
    crews_dir: str | Path,
    crew_name: str,
    timeout: int = 15,
) -> Path:
    """Télécharge un fichier YAML depuis GitHub et le sauvegarde localement.

    Parameters
    ----------
    raw_url:
        URL brute du fichier YAML sur GitHub.
    crews_dir:
        Chemin local du dossier `config/crews/`.
    crew_name:
        Nom sous lequel sauvegarder le fichier (sans l'extension .yaml).
    timeout:
        Délai maximal en secondes pour la requête HTTP.

    Returns
    -------
    Path
        Chemin absolu du fichier sauvegardé.
    """
    if not raw_url.endswith((".yaml", ".yml")):
        raise ValueError(f"L'URL ne semble pas pointer vers un fichier YAML : {raw_url}")

    if not crew_name.strip():
        raise ValueError("Le nom du Crew ne peut pas être vide.")

    # S'assurer que le nom finit par .yaml
    filename = crew_name if crew_name.endswith((".yaml", ".yml")) else f"{crew_name}.yaml"
    
    response = requests.get(raw_url, timeout=timeout)
    response.raise_for_status()

    dest = Path(crews_dir) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(response.text, encoding="utf-8")

    return dest.resolve()
