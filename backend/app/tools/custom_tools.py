"""
tools/custom_tools.py — Outils personnalisés pour les agents CrewAI.

Chaque outil est décoré avec ``@tool`` de CrewAI et peut être
référencé par son nom dans les fichiers de configuration YAML.
"""

import os
import shutil
import subprocess
import sys
import json
import tempfile
import uuid
from typing import Dict, Any, Optional
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun


@tool("calculate_text_length")
def calculate_text_length(text: str) -> int:
    """Calcule et retourne la longueur (nombre de caractères) d'une chaîne de texte."""
    return len(text)


def _is_safe_path(path: str) -> bool:
    """Valide que le chemin ciblé reste dans le répertoire du projet pour la sécurité."""
    try:
        abs_path = os.path.abspath(path)
        project_root = os.path.abspath("/Users/poutrainlouis/Code/AgentTest")
        return abs_path.startswith(project_root)
    except Exception:
        return False


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
    if not _is_safe_path(file_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erreur lors de la lecture du fichier '{file_path}' : {str(e)}"


@tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """Écrit (ou écrase) un fichier avec le contenu spécifié. Retourne un message de succès."""
    if not _is_safe_path(file_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
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
    if not _is_safe_path(path):
        return f"Erreur de sécurité : L'accès au chemin '{path}' est interdit en dehors du répertoire de travail."
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
    import uuid
    container_name = f"agent-exec-{uuid.uuid4().hex[:8]}"
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--name", container_name,
                "--memory", "256m",
                "--cpus", "0.5",
                "--network", "none",
                "python:3.10-slim",
                "python", "-c", code
            ],
            capture_output=True,
            text=True,
            timeout=30  # Sécurité : 30 secondes max
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErreurs :\n{result.stderr}"
        return output if output else "Le code s'est exécuté sans erreur mais n'a rien affiché."
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        except:
            pass
        return "Erreur : L'exécution du code a dépassé le délai autorisé de 30 secondes."
    except Exception as e:
        return f"Erreur lors de l'exécution du code : {str(e)}"


@tool("clone_github_repo")
def clone_github_repo(repo_url: str, dest_dir: str) -> str:
    """Clone un dépôt GitHub localement via la commande git clone. Retourne un message de succès."""
    if not repo_url.startswith("https://github.com/"):
        return "Erreur de sécurité : Seules les URL https://github.com/ sont autorisées."
    if not _is_safe_path(dest_dir):
        return f"Erreur de sécurité : L'accès au chemin '{dest_dir}' est interdit en dehors du répertoire de travail."
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


@tool("append_to_file")
def append_to_file(file_path: str, content: str) -> str:
    """Ajoute du texte à la fin d'un fichier. Crée le fichier s'il n'existe pas."""
    if not _is_safe_path(file_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'a', encoding='utf-8') as f:
            if not content.startswith('\n'):
                f.write('\n')
            f.write(content)
        return f"Le texte a été ajouté avec succès à la fin du fichier '{file_path}'."
    except Exception as e:
        return f"Erreur lors de l'ajout au fichier '{file_path}' : {str(e)}"


# Constantes pour le conteneur Docker
DOCKER_IMAGE = "python:3.10-slim"  # Image de base légère et standard

@tool("gen_code")
def gen_code(prompt: str, preprompts: Optional[str] = None) -> Dict[str, str]:
    """
    Génère un code logiciel basé sur une description utilisateur.
    Cette fonction simule l'étape de génération de code.
    """
    try:
        generated_files = {
            "main.py": "print('Hello from generated code')",
            "requirements.txt": "requests==2.31.0\npandas==2.0.0"
        }
        return generated_files
    except Exception as e:
        return {"error": f"Échec de la génération du code: {str(e)}"}

@tool("gen_entrypoint")
def gen_entrypoint(prompt: str, codebase: Dict[str, str]) -> str:
    """
    Génère un script d'entrée (entrée) pour exécuter la base de code générée.
    """
    try:
        main_file = None
        for filename in codebase.keys():
            if filename.endswith('.py'):
                main_file = filename
                break
        
        if not main_file:
            return "# Error: No Python file found to create an entrypoint."

        install_cmd = "pip install -r requirements.txt --quiet" if "requirements.txt" in codebase else "true"
        run_cmd = f"python {main_file}"
        
        entrypoint_content = f"#!/bin/bash\nset -e\n{install_cmd}\n{run_cmd}\n"
        return entrypoint_content
    except Exception as e:
        return f"Erreur lors de la génération de l'entrée: {str(e)}"

@tool("execute_entrypoint")
def execute_entrypoint(entrypoint_script: str, execution_env: str = "docker") -> Dict[str, Any]:
    """
    Exécute le script d'entrée généré dans un conteneur Docker éphémère pour isoler l'hôte.
    C'est la fonction critique pour la sécurité : elle ne permet JAMAIS l'exécution native locale.
    """
    if not entrypoint_script:
        return {"stdout": "", "stderr": "Le script d'entrée est vide.", "exit_code": 1}

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="agent_exec_")
        
        script_path = os.path.join(temp_dir, "run.sh")
        with open(script_path, "w") as f:
            f.write(entrypoint_script)
        os.chmod(script_path, 0o755)

        full_docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{temp_dir}:/mnt/workspace",
            DOCKER_IMAGE,
            "bash", "/mnt/workspace/run.sh"
        ]
        
        process = subprocess.run(
            full_docker_cmd,
            capture_output=True,
            text=True,
            timeout=60  # Timeout de sécurité
        )
        
        return {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode
        }

    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Le script a dépassé le temps d'exécution (60s).", "exit_code": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "Docker n'est pas installé ou n'est pas dans le PATH.", "exit_code": 1}
    except Exception as e:
        return {"stdout": "", "stderr": f"Erreur d'exécution Docker: {str(e)}", "exit_code": 1}
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

@tool("improve_fn")
def improve_fn(prompt: str, codebase: Dict[str, str]) -> Dict[str, str]:
    """
    Améliore le code existant en fonction d'un prompt ou d'une rétroaction.
    """
    try:
        if not codebase:
            return {"error": "Aucune base de code fournie à améliorer."}
            
        improved_codebase = codebase.copy()
        
        if "main.py" in improved_codebase:
            current_code = improved_codebase["main.py"]
            if "try:" not in current_code and "except" not in current_code:
                improved_codebase["main.py"] = current_code.replace("print(", "# Improved: \n    try:\n        print(")
            
        return improved_codebase

    except Exception as e:
        return {"error": f"Échec de l'amélioration du code: {str(e)}"}

@tool("list_directory")
def list_directory(directory_path: str) -> str:
    """
    Liste les fichiers et sous-dossiers situés DIRECTEMENT dans le chemin spécifié (niveau 1 uniquement).
    Utilise cet outil pour naviguer dans l'arborescence dossier par dossier.
    """
    try:
        if not os.path.exists(directory_path):
            return f"Erreur : Le dossier '{directory_path}' n'existe pas."
        
        # Liste des dossiers "poubelles" à ignorer absolument pour ne pas perdre de temps
        IGNORE_LIST = ['.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode', 'dist', 'build']
        
        items = os.listdir(directory_path)
        folders = []
        files = []
        
        for item in items:
            if item in IGNORE_LIST:
                continue
                
            full_path = os.path.join(directory_path, item)
            if os.path.isdir(full_path):
                folders.append(f"📁 [DOSSIER] {item}/")
            else:
                files.append(f"📄 [FICHIER] {item}")
                
        # Trier pour un affichage propre
        folders.sort()
        files.sort()
        
        result = [f"Contenu de '{directory_path}' :"]
        result.extend(folders)
        result.extend(files)
        
        return "\n".join(result) if len(result) > 1 else "Le dossier est vide."
        
    except Exception as e:
        return f"Erreur lors de l'exploration de '{directory_path}' : {str(e)}"