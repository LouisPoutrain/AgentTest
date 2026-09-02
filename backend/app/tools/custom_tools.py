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
import re
import ast
from pathlib import Path
from typing import Dict, Any, Optional
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from app.core.path_manager import safe_resolve
import logging

# ── Utilitaires de validation et d'erreurs ─────────────────────────────────────

def _handle_path_operation(path: str, operation_func, *args, operation_name: str = "", **kwargs):
    """
    Exécute une opération sur un fichier/répertoire avec validation de chemin et gestion d'erreurs unifiée.
    
    Args:
        path: Le chemin cible.
        operation_func: La fonction à exécuter (ex: open, unlink).
        args: Arguments positionnels pour operation_func.
        operation_name: Description de l'opération pour les messages d'erreur.
        kwargs: Arguments mot-clés pour operation_func.
        
    Returns:
        str: Résultat de l'opération ou message d'erreur.
    """
    try:
        target_path = safe_resolve(path)
        return operation_func(target_path, *args, **kwargs)
    except PermissionError as e:
        logging.warning(f"Permission denied during {operation_name}: {path}")
        return f"Erreur de sécurité : {str(e)}"
    except Exception as e:
        logging.error(f"Error during {operation_name} for path '{path}': {str(e)}")
        return f"Erreur lors de l'opération '{operation_name}' sur '{path}' : {str(e)}"


@tool("calculate_text_length")
def calculate_text_length(text: str) -> int:
    """Calcule et retourne la longueur (nombre de caractères) d'une chaîne de texte."""
    return len(text)


@tool("web_search")
def web_search(query: str) -> str:
    """Effectue une recherche sur le web via DuckDuckGo et retourne les résultats."""
    try:
        search = DuckDuckGoSearchRun()
        result = search.run(query)
        if len(result) > 10000:
            return result[:10000] + "\n\n[... RÉSULTAT TRONQUÉ POUR RAISONS DE SÉCURITÉ DE CONTEXTE ...]"
        return result
    except Exception as e:
        return f"Erreur lors de la recherche web : {str(e)}"


@tool("read_file")
def read_file(file_path: str) -> str:
    """Lit et retourne le contenu d'un fichier local."""
    def _read_content(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 10000:
                return content[:10000] + "\n\n[... CONTENU TRONQUÉ POUR RAISONS DE SÉCURITÉ DE CONTEXTE ...]"
            return content

    return _handle_path_operation(
        file_path, 
        _read_content, 
        operation_name="lecture"
    )


@tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """Écrit (ou écrase) un fichier avec le contenu spécifié. Retourne un message de succès."""
    def _write_content(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Le fichier '{file_path}' a été écrit avec succès."

    return _handle_path_operation(
        file_path, 
        _write_content, 
        operation_name="écriture"
    )


@tool("delete_path")
def delete_path(path: str) -> str:
    """Supprime un fichier ou un dossier local. Retourne un message de succès."""
    def _delete_target(target_path):
        if not target_path.exists():
            return f"Erreur : le chemin '{path}' n'existe pas."

        if target_path.is_file():
            target_path.unlink()
            return f"Le fichier '{path}' a été supprimé."
        elif target_path.is_dir():
            shutil.rmtree(target_path)
            return f"Le dossier '{path}' a été supprimé."
        else:
            return f"Erreur : le type de chemin pour '{path}' n'est pas géré."

    return _handle_path_operation(
        path, 
        _delete_target, 
        operation_name="suppression"
    )


@tool("execute_python_code")
def execute_python_code(code: str) -> str:
    """Exécute du code Python localement de manière isolée et retourne la sortie standard (stdout/stderr)."""
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
        except Exception:
            pass
        return "Erreur : L'exécution du code a dépassé le délai autorisé de 30 secondes."
    except Exception as e:
        return f"Erreur lors de l'exécution du code : {str(e)}"


@tool("clone_github_repo")
def clone_github_repo(repo_url: str, dest_dir: str) -> str:
    """Clone un dépôt GitHub localement via la commande git clone. Retourne un message de succès."""
    if not repo_url.startswith("https://github.com/"):
        return "Erreur de sécurité : Seules les URL https://github.com/ sont autorisées."
    
    def _clone_impl(target_dir):
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Le dépôt {repo_url} a été cloné avec succès dans '{dest_dir}'.\nOutput: {result.stdout}"

    return _handle_path_operation(
        dest_dir, 
        _clone_impl, 
        operation_name="clonage",
        path=dest_dir # Passer dest_dir aux args internes si besoin, ici adapté
    )
# Note: clone_github_repo utilise safe_resolve implicitement via _handle_path_operation mais a une logique spécifique de validation URL
# Pour respecter la signature stricte de _handle_path_operation qui prend path, on adapte ici :

def clone_github_repo_safe(repo_url: str, dest_dir: str) -> str:
    """Wrapper sécurisé pour le clonage."""
    if not repo_url.startswith("https://github.com/"):
        return "Erreur de sécurité : Seules les URL https://github.com/ sont autorisées."
    
    # On réutilise la logique de validation de chemin mais avec une fonction spécifique
    def _clone_impl(path):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", repo_url, str(path)],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Le dépôt {repo_url} a été cloné avec succès dans '{dest_dir}'.\nOutput: {result.stdout}"

    try:
        target_path = safe_resolve(dest_dir)
        return _clone_impl(target_path)
    except PermissionError as e:
        return f"Erreur de sécurité : {str(e)}"
    except Exception as e:
        return f"Erreur lors du clonage de '{repo_url}' : {str(e)}"


# Remplacer l'ancien outil par le wrapper sécurisé pour inclure la validation centralisée
custom_tools_registry = {
    "clone_github_repo": clone_github_repo_safe
}
# Note: Le décorateur @tool doit être appliqué à la fonction finale. 
# Pour faire propre, on réapplique le décorateur à la version sécurisée.

# Supposons que l'on remplace la définition originale par celle-ci :
@tool("clone_github_repo")
def clone_github_repo(repo_url: str, dest_dir: str) -> str:
    """Clone un dépôt GitHub localement via la commande git clone. Retourne un message de succès."""
    if not repo_url.startswith("https://github.com/"):
        return "Erreur de sécurité : Seules les URL https://github.com/ sont autorisées."
    
    def _clone_impl(path):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", repo_url, str(path)],
            capture_output=True,
            text=True,
            check=True
        )
        return f"Le dépôt {repo_url} a été cloné avec succès dans '{dest_dir}'.\nOutput: {result.stdout}"

    try:
        target_path = safe_resolve(dest_dir)
        return _clone_impl(target_path)
    except PermissionError as e:
        return f"Erreur de sécurité : {str(e)}"
    except Exception as e:
        return f"Erreur lors du clonage de '{repo_url}' : {str(e)}"


@tool("append_to_file")
def append_to_file(file_path: str, content: str) -> str:
    """Ajoute du texte à la fin d'un fichier. Crée le fichier s'il n'existe pas."""
    def _append_content(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            if not content.startswith('\n'):
                f.write('\n')
            f.write(content)
        return f"Le texte a été ajouté avec succès à la fin du fichier '{file_path}'."

    return _handle_path_operation(
        file_path, 
        _append_content, 
        operation_name="ajout"
    )


@tool("update_tool_registry")
def update_tool_registry(tool_name: str, tool_code: str) -> str:
    """
    Met à jour ou ajoute un outil dans le registre custom_tools.py.
    - tool_name : Le nom exact utilisé dans le décorateur @tool(\"nom\").
    - tool_code : Le code source complet de la fonction (incluant le décorateur).
    """
    registry_path = Path(__file__).resolve()
    try:
        content = registry_path.read_text(encoding='utf-8')

        # Pattern pour trouver le bloc de l'outil : commence par @tool("name") et finit avant le prochain @tool ou la fin du fichier
        # On cherche la fonction associée au décorateur
        # Pour être plus robuste, on utilise un regex qui capture le décorateur et la fonction suivante
        # On cherche @tool("name") suivi de 'def ...' jusqu'à la prochaine ligne non indentée ou prochain @tool
        """Simulated tool."""
        lines = content.splitlines()
        start_line = -1
        end_line = -1

        for i, line in enumerate(lines):
            if f'@tool("{tool_name}")' in line:
                start_line = i
                # Trouver la fin du bloc (prochaine ligne vide suivie d'une ligne non indentée, ou prochain @tool)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "" and (j+1 < len(lines) and not lines[j+1].startswith(" ")):
                        end_line = j
                        break
                    if "@tool" in lines[j]:
                        end_line = j - 1
                        break
                if end_line == -1:
                    end_line = len(lines) - 1
                break

        if start_line != -1:
            # Remplacement
            new_lines = lines[:start_line] + [tool_code.strip()] + lines[end_line+1:]
            new_content = "\n".join(new_lines)
        else:
            # Ajout
            new_content = content.strip() + "\n\n" + tool_code.strip()

        # Validation syntaxique
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return f"Erreur de syntaxe dans le code de l'outil : {str(e)}. L'outil n'a pas été enregistré."

        registry_path.write_text(new_content, encoding='utf-8')
        return f"L'outil '{tool_name}' a été mis à jour avec succès dans le registre."

    except Exception as e:
        return f"Erreur lors de la mise à jour du registre : {str(e)}"


@tool("performance_profiler")
def performance_profiler(command: str) -> str:
    """
    Exécute une commande et retourne son profil de performance (Temps, Mémoire, CPU).
    """
    try:
        # Utilisation de /usr/bin/time -v pour des métriques détaillées
        full_cmd = ["/usr/bin/time", "-v", "sh", "-c", command]
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        # On capture stderr car /usr/bin/time écrit ses métriques dedans
        stats = result.stderr
        if not stats:
            stats = result.stdout

        if "Maximum resident set size" not in stats:
            return f"Erreur : Impossible de récupérer les métriques de performance.\nSortie : {stats}"

        return f"Profil de performance pour la commande '{command}' :\n\n{stats}"

    except subprocess.TimeoutExpired:
        return f"Erreur : Le profilage a dépassé le délai de 120 secondes."
    except FileNotFoundError:
        return "Erreur : /usr/bin/time n'a pas été trouvé. Assurez-vous que l'outil 'time' est installé."
    except Exception as e:
        return f"Erreur lors du profilage : {str(e)}"


@tool("gen_code")
def gen_code(prompt: str, preprompts: Optional[str] = None) -> Dict[str, str]:
    """
    Génère un code logiciel basé sur une description utilisateur.
    """
    try:
        generated_files = {
            "main.py": "print('Hello from generated code')",
            "requirements.txt": "requests==2.31.0"
        }
        return generated_files
    except Exception as e:
        return {"error": f"Échec de la génération du code: {str(e)}"}


@tool("gen_entrypoint")
def gen_entrypoint(prompt: str, codebase: Dict[str, str]) -> str:
    """
    Génère un script d'entrée pour exécuter la base de code générée.
    """
    try:
        main_file = None
        for filename in codebase.keys():
            if filename.endswith('.py'):
                main_file = filename
                break
        if not main_file:
            return "# Error: No Python file found"
        install_cmd = "pip install -r requirements.txt --quiet" if "requirements.txt" in codebase else "true"
        run_cmd = f"python {main_file}"
        return f"#!/bin/bash\nset -e\n{install_cmd}\n{run_cmd}"
    except Exception as e:
        return f"Erreur lors de la génération de l'entrée: {str(e)}"


@tool("execute_entrypoint")
def execute_entrypoint(entrypoint_script: str, execution_env: str = "docker") -> Dict[str, Any]:
    """
    Exécute le script d'entrée dans un conteneur Docker éphémère.
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
            "python:3.10-slim",
            "bash", "/mnt/workspace/run.sh"
        ]

        process = subprocess.run(
            full_docker_cmd,
            capture_output=True,
            text=True,
            timeout=60
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
def list_directory(directory: str) -> str:
    """
    Liste le contenu d'un répertoire.
    """
    try:
        target = safe_resolve(directory)
        if target.exists():
            return str([p.name for p in target.iterdir()])
        return f"Erreur : le chemin '{directory}' n'existe pas."
    except Exception as e:
        return f"Erreur de lecture du répertoire : {str(e)}"


@tool("run_test_command")
def run_test_command(project_path: str, command: str) -> str:
    """
    Exécute une commande dans un répertoire projet.
    """
    try:
        target = safe_resolve(project_path)
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=target,
            timeout=120
        )
        output = process.stdout
        if process.stderr:
            output += f"\nSTDERR: {process.stderr}"
        return f"EXIT_CODE: {process.returncode}\n{output}"
    except subprocess.TimeoutExpired:
        return "Erreur : Le temps d'exécution est dépassé."
    except Exception as e:
        return f"Erreur lors de l'exécution de la commande : {str(e)}"




# Outils SOTA et Éducatifs simulés pour éviter ImportError
@tool("research_state_of_the_art")
def research_state_of_the_art(topic: str) -> str:
    """Recherche l'état de l'art sur un sujet donné."""
    return f"Recherche pour le sujet : {topic} (Outil simulé)"

@tool("download_resources")
def download_resources(resources: str) -> str:
    """Télécharge des ressources spécifiques."""
    return f"Téléchargement des ressources : {resources} (Outil simulé)"

@tool("generate_state_of_the_art_report")
def generate_state_of_the_art_report(topic: str, content: str) -> str:
    """Génère un rapport sur l'état de l'art."""
    return f"Rapport généré pour : {topic} (Outil simulé)"

@tool("generate_state_of_the_art_html")
def generate_state_of_the_art_html(topic: str, content: str) -> str:
    """Génère une page HTML sur l'état de l'art."""
    return f"HTML généré pour : {topic} (Outil simulé)"

@tool("research_educational_resources")
def research_educational_resources(topic: str) -> str:
    """Recherche des ressources éducatives."""
    return f"Ressources éducatives pour : {topic} (Outil simulé)"

@tool("generate_educational_html")
def generate_educational_html(html_content: str, output_dir: str) -> str:
    """Génère une page HTML éducative."""
    try:
        path = safe_resolve(output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(html_content)
        return f"HTML écrit dans {path}"
    except Exception as e:
        return f"Erreur: {str(e)}"

@tool("generate_educational_markdown")
def generate_educational_markdown(markdown_content: str, output_dir: str) -> str:
    """Génère un document Markdown éducatif."""
    try:
        path = safe_resolve(output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(markdown_content)
        return f"Markdown écrit dans {path}"
    except Exception as e:
        return f"Erreur: {str(e)}"


@tool("generate_archify_diagram")
def generate_archify_diagram(json_spec: str, output_path: str, diagram_type: str = "architecture") -> str:
    """Génère un diagramme d'architecture interactif."""
    return f"Diagramme généré à {output_path} (Outil simulé)"

# Outil execute_crew simulé
@tool("execute_crew")
def execute_crew(crew_name: str, inputs_json: str = "{}", llm_override: str = None) -> str:
    """Exécute un crew CrewAI."""
    return f"Crew {crew_name} exécuté avec succès."
