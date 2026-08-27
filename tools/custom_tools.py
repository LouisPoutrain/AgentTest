"""
tools/custom_tools.py — Outils personnalisés pour les agents CrewAI.

Chaque outil est décoré avec ``@tool`` de CrewAI et peut être
référencé par son nom dans les fichiers de configuration YAML.
"""

import os
import shutil
import subprocess
import sys
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun


@tool("calculate_text_length")
def calculate_text_length(text: str) -> int:
    """Calcule et retourne la longueur (nombre de caractères) d'une chaîne de texte."""
    return len(text)


@tool("web_search")
def web_search(query: str) -> str:
    """Effectue une recherche sur le web via DuckDuckGo et retourne les résultats."""
    try:
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        return f"Erreur lors de la recherche web : {str(e)}"


@tool("read_file")
def read_file(file_path: str) -> str:
    """Lit et retourne le contenu d'un fichier local."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erreur lors de la lecture du fichier '{file_path}' : {str(e)}"


@tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """Écrit (ou écrase) un fichier avec le contenu spécifié. Retourne un message de succès."""
    try:
        # S'assurer que le dossier parent existe
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Le fichier '{file_path}' a été écrit avec succès."
    except Exception as e:
        return f"Erreur lors de l'écriture dans le fichier '{file_path}' : {str(e)}"


@tool("delete_path")
def delete_path(path: str) -> str:
    """Supprime un fichier ou un dossier local. Retourne un message de succès."""
    try:
        if not os.path.exists(path):
            return f"Erreur : le chemin '{path}' n'existe pas."
        
        if os.path.isfile(path):
            os.remove(path)
            return f"Le fichier '{path}' a été supprimé."
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Le dossier '{path}' a été supprimé."
        else:
            return f"Erreur : le type de chemin pour '{path}' n'est pas géré."
    except Exception as e:
        return f"Erreur lors de la suppression de '{path}' : {str(e)}"


@tool("execute_python_code")
def execute_python_code(code: str) -> str:
    """Exécute du code Python localement de manière isolée et retourne la sortie standard (stdout/stderr)."""
    try:
        result = subprocess.run(
            [sys.executable or "python", "-c", code],
            capture_output=True,
            text=True,
            timeout=30  # Sécurité : 30 secondes max
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErreurs :\n{result.stderr}"
        return output if output else "Le code s'est exécuté sans erreur mais n'a rien affiché."
    except subprocess.TimeoutExpired:
        return "Erreur : L'exécution du code a dépassé le délai autorisé de 30 secondes."
    except Exception as e:
        return f"Erreur lors de l'exécution du code : {str(e)}"


@tool("clone_github_repo")
def clone_github_repo(repo_url: str, dest_dir: str) -> str:
    """Clone un dépôt GitHub localement via la commande git clone. Retourne un message de succès."""
    try:
        if os.path.exists(dest_dir):
            return f"Erreur : Le dossier de destination '{dest_dir}' existe déjà."
            
        result = subprocess.run(
            ["git", "clone", repo_url, dest_dir],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Le dépôt {repo_url} a été cloné avec succès dans '{dest_dir}'.\nOutput: {result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Erreur Git lors du clonage de '{repo_url}' : {e.stderr}"
    except Exception as e:
        return f"Erreur lors du clonage de '{repo_url}' : {str(e)}"
