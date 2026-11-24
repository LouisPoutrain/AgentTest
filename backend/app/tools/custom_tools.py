"""
tools/custom_tools.py — Outils personnalisés pour les agents CrewAI.

Chaque outil est décoré avec ``@tool`` de CrewAI et peut être
référencé par son nom dans les fichiers de configuration YAML.
"""

import ast
import json
import logging
import os
import re
import shutil
import shlex
import socket
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import requests

from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import pdfplumber
import wikipedia
import arxiv
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from jinja2 import Template

from app.core.path_manager import safe_resolve, safe_resolve_external

# ── Liste blanche des commandes autorisées pour run_test_command ────────────────

# Chaque entrée : (préfixe de commande, description)
ALLOWED_COMMAND_PREFIXES = (
    "npm test", "npm run", "yarn test", "yarn run",
    "pytest", "python -m pytest", "python -c",
    "node", "npx", "pip install", "pip list",
    "go test", "go build", "go vet",
    "cargo test", "cargo build", "cargo clippy",
    "gradle", "mvn test", "mvn compile",
    "bundle exec rspec", "bundle exec rake",
    "dotnet test", "dotnet build",
    "make", "make test",
    "flake8", "pylint", "mypy", "eslint",
    "prettier", "black", "ruff",
)

# Regex pour valider qu'une commande ne contient que des caractères sûrs.
# Alphanumérique, espaces (pour les arguments), tirets, underscores,
# points, virgules, slash.
# Les métacaractères shell sont strictement interdits :
# parenthèses (), pipe |, ampersand &&, point-virgule ;,
# backtick `, dollar $, guillemets, redirections <>, astérisque *,
# deux-points :, égal =, point d'interrogation ?, crochets [],
# point d'exclamation !, hash #, backslash \.
_SAFE_COMMAND_RE = re.compile(r'^[a-zA-Z0-9_\-./ ]+$')


def _is_safe_command(command: str) -> bool:
    """Vérifie qu'une commande ne contient pas de caractères dangereux."""
    if not command or len(command) > 500:
        return False
    return bool(_SAFE_COMMAND_RE.match(command))


def _build_safe_command(command: str) -> list[str]:
    """
    Convertit une chaîne de commande en liste pour subprocess sans shell.
    Utilise shlex pour un parsing correct.
    """
    return shlex.split(command)


# ── Utilitaires de validation et d'erreurs ─────────────────────────────────────

def _handle_path_operation(path: str, operation_func, *args, operation_name: str = "", **kwargs):
    """
    Exécute une opération sur un fichier/répertoire avec validation de chemin et gestion d'erreurs unifiée.

    Pour les chemins absolus, utilise safe_resolve_external pour autoriser
    l'accès à des dossiers externes (ex. /Users/.../Cours/SWO).
    Pour les chemins relatifs, la validation de périmètre du projet s'applique.

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
        import os
        # Autoriser les chemins absolus (l'utilisateur les fournit explicitement)
        if os.path.isabs(path):
            target_path = safe_resolve_external(path)
        else:
            target_path = safe_resolve(path)
        return operation_func(target_path, *args, **kwargs)
    except PermissionError as e:
        logging.warning("Permission denied during %s: %s", operation_name, path)
        return f"Erreur de sécurité : {str(e)}"
    except Exception as e:
        logging.error("Error during %s for path '%s': %s", operation_name, path, str(e))
        return f"Erreur lors de l'opération '{operation_name}' sur '{path}' : {str(e)}"


# ── Outils simples ─────────────────────────────────────────────────────────────

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


# ── Opérations fichier ─────────────────────────────────────────────────────────

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


# ── Exécution de code ──────────────────────────────────────────────────────────

@tool("execute_python_code")
def execute_python_code(code: str) -> str:
    """Exécute du code Python de manière isolée via Docker. Retourne stdout/stderr."""
    # Sécurité: valider le code Python avant exécution
    if not code or len(code) > 10000:
        return "Erreur : le code est vide ou trop long (max 10000 caractères)."
    # Bloquer les imports dangereux
    dangerous_imports = ["os", "sys", "subprocess", "shutil", "socket", "urllib",
                         "requests", "http", "ftplib", "smtplib", "pickle", "marshal",
                         "builtins", "__import__", "exec", "eval"]
    for imp in dangerous_imports:
        if f"import {imp}" in code or f"from {imp}" in code:
            return f"Erreur de sécurité : l'import '{imp}' est bloqué pour des raisons de sécurité."
    # Bloquer les accès au système de fichiers
    if any(p in code for p in ["open(", "os.", "pathlib", "shutil", "tempfile"]):
        return "Erreur de sécurité : l'accès au système de fichiers est bloqué."

    container_name = f"agent-exec-{uuid.uuid4().hex[:8]}"
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--name", container_name,
                "--memory", "256m",
                "--cpus", "0.5",
                "--network", "none",
                "--security-opt", "no-new-privileges:true",
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


@tool("run_test_command")
def run_test_command(project_path: str, command: str) -> str:
    """
    Exécute une commande de test dans un répertoire projet.

    Sécurité : la commande est validée contre une liste blanche de préfixes
    et ne peut pas contenir de caractères shell dangereux.
    """
    # Validation de sécurité
    if not command or not _is_safe_command(command):
        return "Erreur de sécurité : commande non autorisée ou contenant des caractères dangereux."

    # Vérification du préfixe autorisé — vérification exacte du premier mot
    # pour éviter les faux positifs (ex: "make sure" match "make")
    first_word = command.split()[0] if command.split() else ""
    allowed_prefixes = tuple(p.split()[0] for p in ALLOWED_COMMAND_PREFIXES)
    if first_word not in allowed_prefixes:
        return (
            f"Erreur : la commande '{command}' n'est pas dans la liste blanche. "
            f"Commandes autorisées : {', '.join(ALLOWED_COMMAND_PREFIXES[:8])}..."
        )

    try:
        target = safe_resolve(project_path)
        cmd_list = _build_safe_command(command)
        process = subprocess.run(
            cmd_list,
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


# ── Clonage & dépôts ───────────────────────────────────────────────────────────

@tool("clone_github_repo")
def clone_github_repo(repo_url: str, dest_dir: str) -> str:
    """Clone un dépôt GitHub localement via la commande git clone. Retourne un message de succès."""
    from urllib.parse import urlparse

    # Parse and validate URL structure
    try:
        parsed = urlparse(repo_url)
    except Exception:
        return "Erreur de sécurité : URL GitHub invalide."

    # Must be https scheme
    if parsed.scheme not in ("https",):
        return "Erreur de sécurité : seuls les URLs https:// sont autorisés."

    # Validate hostname strictly
    hostname = parsed.hostname or ""
    if hostname not in ("github.com", "www.github.com"):
        return "Erreur de sécurité : seuls les dépôts hébergés sur github.com sont autorisés."

    # Path must start with / followed by owner/repo pattern
    path = parsed.path
    if not path.startswith("/") or len(path) < 2:
        return "Erreur de sécurité : URL GitHub invalide."

    # Extract owner and repo from path
    path_parts = path.strip("/").split("/")
    if len(path_parts) < 2:
        return "Erreur de sécurité : URL GitHub invalide (attendu /owner/repo)."

    owner, repo = path_parts[0], path_parts[1]
    if not owner or not repo:
        return "Erreur de sécurité : URL GitHub invalide (owner ou repo manquant)."

    # Additional validation: owner and repo must be alphanumeric with allowed chars
    if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$', owner):
        return "Erreur de sécurité : nom d'organisation invalide."
    if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$', repo):
        return "Erreur de sécurité : nom de dépôt invalide."

    def _clone_impl(path):
        # Sécurité: vérifier que le chemin résolu est bien un descendant du projet
        project_root = safe_resolve(".")
        try:
            path.resolve().relative_to(project_root)
        except ValueError:
            return f"Erreur de sécurité : le chemin de destination '{dest_dir}' n'est pas dans le projet."
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--no-tags", "--single-branch", repo_url, str(path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )
        return f"Le dépôt {repo_url} a été cloné avec succès dans '{dest_dir}'.\nOutput: {result.stdout}"

    try:
        target_path = safe_resolve(dest_dir)
        return _clone_impl(target_path)
    except PermissionError as e:
        return f"Erreur de sécurité : {str(e)}"
    except Exception as e:
        return f"Erreur lors du clonage de '{repo_url}' : {str(e)}"


# ── Outils de génération ───────────────────────────────────────────────────────

@tool("gen_code")
def gen_code(prompt: str, preprompts: Optional[str] = None) -> Dict[str, str]:
    """
    Génère un code logiciel basé sur une description utilisateur.
    Note : cet outil est un stub — il retourne un squelette par défaut.
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
    Note : stub — squelette basique.
    """
    try:
        main_file = None
        for filename in codebase.keys():
            if filename.endswith('.py'):
                main_file = filename
                break
        if not main_file:
            return "# Erreur : aucun fichier Python trouvé"
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
    Note : stub — amélioration basique.
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


# ── Outils système ─────────────────────────────────────────────────────────────

@tool("list_directory")
def list_directory(directory: str) -> str:
    """Liste le contenu d'un répertoire."""
    try:
        target = safe_resolve(directory)
        if target.exists():
            return str([p.name for p in target.iterdir()])
        return f"Erreur : le chemin '{directory}' n'existe pas."
    except Exception as e:
        return f"Erreur de lecture du répertoire : {str(e)}"


@tool("list_pdfs")
def list_pdfs(directory: str) -> str:
    """Recherche récursivement tous les fichiers .pdf dans un dossier.

    Retourne un JSON avec la liste des chemins absolus triés par nom.
    Utile pour inventorier tous les PDF d'un dossier de cours avant analyse.
    """
    def _find_pdfs(path):
        pdfs = sorted(str(p.resolve()) for p in path.rglob("*.pdf"))
        return json.dumps(
            {"directory": str(path), "count": len(pdfs), "pdfs": pdfs},
            ensure_ascii=False,
        )

    return _handle_path_operation(
        directory,
        _find_pdfs,
        operation_name="recherche PDF",
    )


@tool("performance_profiler")
def performance_profiler(command: str) -> str:
    """
    Exécute une commande et retourne son profil de performance (Temps, Mémoire, CPU).
    """
    # Sécurité: valider la commande avec les mêmes règles que run_test_command
    if not command or not _is_safe_command(command):
        return "Erreur de sécurité : commande non autorisée ou contenant des caractères dangereux."
    first_word = command.split()[0] if command.split() else ""
    allowed_prefixes = tuple(p.split()[0] for p in ALLOWED_COMMAND_PREFIXES)
    if first_word not in allowed_prefixes:
        return f"Erreur : la commande '{command}' n'est pas dans la liste blanche."
    try:
        # Exécuter directement sans passer par sh -c pour éviter l'injection de commandes
        cmd_list = _build_safe_command(command)
        full_cmd = ["/usr/bin/time", "-v"] + cmd_list
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

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


# ── Outils SOTA / Éducatifs (implémentations fonctionnelles) ───────────────────

@tool("research_state_of_the_art")
def research_state_of_the_art(topic: str) -> str:
    """
    Recherche l'état de l'art sur un sujet donné via recherche web.
    Retourne un résumé structuré des ressources trouvées.
    """
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(f"{topic} state of the art 2024 2025 survey")
        return (
            f"Recherche SOTA pour : {topic}\n\n"
            f"Résultats de recherche web :\n{results}\n\n"
            f"[Pour un rapport complet, utilisez generate_state_of_the_art_report avec ce contenu]"
        )
    except Exception as e:
        return f"Erreur lors de la recherche SOTA : {str(e)}"


@tool("download_resources")
def download_resources(resources: str) -> str:
    """
    Télécharge des ressources spécifiques via wget/curl dans le dossier de travail.
    """
    try:
        # Sécurité : ne télécharger que depuis des URLs validées
        url = resources.strip()
        if not (url.startswith("https://") or url.startswith("http://")):
            return "Erreur : URL invalide. Seules les URLs http/https sont autorisées."

        target = safe_resolve(".")
        dest = target / (url.split("/")[-1] or "download")

        result = subprocess.run(
            ["curl", "-f", "-L", "-o", str(dest), url],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return f"Ressource téléchargée avec succès dans '{dest}'."
        return f"Erreur de téléchargement : {result.stderr or result.stdout}"
    except Exception as e:
        return f"Erreur lors du téléchargement : {str(e)}"


@tool("generate_state_of_the_art_report")
def generate_state_of_the_art_report(topic: str, content: str) -> str:
    """
    Génère un rapport structuré sur l'état de l'art à partir de contenu brut.
    """
    try:
        # Structure un rapport lisible à partir du contenu brut
        report = (
            f"# Rapport SOTA : {topic}\n\n"
            f"## Résumé\n"
            f"{content[:5000]}\n\n"
            f"## Analyse\n"
            f"Ce rapport synthétise les informations collectées sur '{topic}'.\n"
            f"Pour une analyse approfondie, croisez avec plusieurs sources de recherche."
        )
        return report
    except Exception as e:
        return f"Erreur lors de la génération du rapport : {str(e)}"


@tool("generate_state_of_the_art_html")
def generate_state_of_the_art_html(topic: str, content: str) -> str:
    """
    Génère une page HTML sur l'état de l'art.
    """
    try:
        safe_topic = topic.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_content = content[:5000].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>SOTA : {safe_topic}</title>
<style>body{{font-family:system-ui;max-width:800px;margin:2rem auto;padding:0 1rem}}
h1{{color:#1a1a2e}}pre{{background:#f5f5f5;padding:1rem;overflow:auto}}</style></head>
<body><h1>Rapport SOTA : {safe_topic}</h1>
<pre>{safe_content}</pre></body></html>"""
        return html
    except Exception as e:
        return f"Erreur lors de la génération HTML : {str(e)}"


@tool("research_educational_resources")
def research_educational_resources(topic: str) -> str:
    """
    Recherche des ressources éducatives sur un sujet donné.
    """
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(f"{topic} tutorial course learning guide")
        return (
            f"Ressources éducatives pour : {topic}\n\n"
            f"{results}\n\n"
            f"[Utilisez generate_educational_html ou generate_educational_markdown pour formater]"
        )
    except Exception as e:
        return f"Erreur lors de la recherche éducative : {str(e)}"


@tool("generate_educational_html")
def generate_educational_html(html_content: str, output_dir: str) -> str:
    """Génère une page HTML éducative et la sauvegarde."""
    try:
        path = safe_resolve(output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"HTML éducatif écrit dans {path}"
    except Exception as e:
        return f"Erreur : {str(e)}"


@tool("generate_educational_markdown")
def generate_educational_markdown(markdown_content: str, output_dir: str) -> str:
    """Génère un document Markdown éducatif et le sauvegarde."""
    try:
        path = safe_resolve(output_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        return f"Markdown éducatif écrit dans {path}"
    except Exception as e:
        return f"Erreur : {str(e)}"


# ── Outils avancés ─────────────────────────────────────────────────────────────

@tool("generate_archify_diagram")
def generate_archify_diagram(json_spec: str, output_path: str, diagram_type: str = "architecture") -> str:
    """Génère un diagramme d'architecture interactif en utilisant Archify."""

    archify_dir = Path(__file__).resolve().parent / ".cache" / "archify"
    archify_bin = archify_dir / "archify" / "bin" / "archify.mjs"

    if not archify_bin.exists():
        return f"Erreur: Le binaire Archify est introuvable à {archify_bin}"

    try:
        out_path = safe_resolve(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_json:
            temp_json.write(json_spec)
            temp_json_path = temp_json.name

        try:
            cmd = [
                "node", str(archify_bin),
                "deliver", diagram_type, temp_json_path, str(out_path),
                "--quality", "showcase", "--json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(archify_dir)
            )

            if result.returncode == 0:
                return f"Succès: Diagramme '{diagram_type}' généré avec succès dans {out_path}."
            else:
                return f"Erreur lors de la génération du diagramme:\nCode: {result.returncode}\nSortie: {result.stdout}\nErreurs: {result.stderr}"
        finally:
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)

    except Exception as e:
        return f"Erreur inattendue: {str(e)}"


@tool("update_tool_registry")
def update_tool_registry(tool_name: str, tool_code: str) -> str:
    """
    Met à jour ou ajoute un outil dans le registre custom_tools.py.
    - tool_name : Le nom exact utilisé dans le décorateur @tool("nom").
    - tool_code : Le code source complet de la fonction (incluant le décorateur).

    Sécurité : le code est validé contre des patterns dangereux avant écriture.
    """
    # Validation de sécurité: empêcher l'exécution de code arbitraire
    dangerous_patterns = [
        # Module imports — system / filesystem / network
        "import os", "import sys", "import subprocess", "import shutil",
        "import pathlib", "import socket", "import urllib", "import requests",
        "import http", "import ftplib", "import smtplib", "import pickle",
        "import marshal", "import compile", "import importlib",
        "import ctypes", "import cdll", "import dl",
        # Built-in execution
        "eval(", "exec(", "compile(", "__import__",
        # os / subprocess execution
        "os.system", "os.popen", "os.exec", "os.spawn", "os.fork",
        "subprocess.",
        # Filesystem writes
        "shutil.rmtree", "shutil.copy", "shutil.move", "shutil.copytree",
        "Path.unlink", "Path.write_text", "Path.read_text", "Path.mkdir",
        "Path.rmdir",
        # Builtins / introspection
        "import builtins", "__builtins__", "globals()", "locals()",
        # eval / exec variants
        "eval(", "exec(", "compile(", "eval(",
        # importlib / dynamic loading
        "importlib", "importlib.", "pkgutil", "runpy",
        # ctypes / low-level
        "ctypes", "ctypes.", "cdll", "cdll.", "dll",
        # Other dangerous stdlib
        "telnetlib", "distutils", "site.", "sys.", "threading",
        "multiprocessing", "signal.", "curses", "pty",
    ]
    code_lower = tool_code.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in code_lower:
            return (
                f"Erreur de sécurité : le code de l'outil contient des opérations "
                f"interdites ('{pattern}'). Les outils ne doivent pas accéder au système de fichiers, "
                f"au réseau ou exécuter du code arbitraire."
            )

    # Validation syntaxique du code seul
    try:
        ast.parse(tool_code)
    except SyntaxError as e:
        return f"Erreur de syntaxe dans le code de l'outil : {str(e)}. L'outil n'a pas été enregistré."

    registry_path = Path(__file__).resolve()
    try:
        content = registry_path.read_text(encoding='utf-8')

        lines = content.splitlines()
        start_line = -1
        end_line = -1

        for i, line in enumerate(lines):
            if f'@tool("{tool_name}")' in line:
                start_line = i
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
            new_lines = lines[:start_line] + [tool_code.strip()] + lines[end_line+1:]
            new_content = "\n".join(new_lines)
        else:
            new_content = content.strip() + "\n\n" + tool_code.strip()

        # Validation syntaxique du fichier complet
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return f"Erreur de syntaxe dans le registre après mise à jour : {str(e)}. L'outil n'a pas été enregistré."

        # Atomic write: write to temp file then rename to prevent corruption
        temp_fd, temp_path = tempfile.mkstemp(
            dir=str(registry_path.parent),
            prefix=".tmp_tool_registry_",
            suffix=".py",
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as tmp_f:
                tmp_f.write(new_content)
            os.replace(temp_path, str(registry_path))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
        return f"L'outil '{tool_name}' a été mis à jour avec succès dans le registre."

    except Exception as e:
        return f"Erreur lors de la mise à jour du registre : {str(e)}"


# ── Outils de lecture PDF ──────────────────────────────────────────────────────

@tool("read_pdf")
def read_pdf(file_path: str, max_pages: int = 0) -> str:
    """
    Lit un fichier PDF et en extrait le texte complet avec structure.
    Utilise pdfplumber pour une extraction précise (meilleur que PyPDF2).

    Args:
        file_path: Chemin vers le fichier PDF.
        max_pages: Nombre maximal de pages à lire (0 = tout lire).

    Returns:
        Texte structuré avec numéros de pages et titres détectés.
    """
    def _read_pdf_content(path, max_p):
        try:
            with pdfplumber.open(path) as pdf:
                pages = pdf.pages
                if max_p > 0:
                    pages = pages[:max_p]

                sections = []
                for i, page in enumerate(pages, 1):
                    text = page.extract_text() or ""
                    # Extraire les titres (lignes en majuscules ou très courtes en début de page)
                    lines = text.split('\n')
                    for line in lines[:3]:
                        stripped = line.strip()
                        if stripped and len(stripped) < 80 and stripped.isupper():
                            sections.append(f"[Page {i}] ## {stripped}")
                    sections.append(f"[Page {i}] {text}")

                full_text = "\n\n".join(sections)
                if len(full_text) > 50000:
                    full_text = full_text[:50000] + "\n\n[... CONTENU TRONQUÉ (max 50 Ko) ...]"
                return full_text
        except Exception as e:
            return f"Erreur lors de la lecture du PDF : {str(e)}"

    return _handle_path_operation(
        file_path,
        _read_pdf_content,
        max_p=max_pages,
        operation_name="lecture PDF"
    )


# ── Outils de recherche académique ─────────────────────────────────────────────

@tool("search_scholar")
def search_scholar(query: str, limit: int = 10) -> str:
    """
    Recherche des articles académiques via l'API Semantic Scholar (gratuite).
    Retourne le titre, les auteurs, l'année, le nombre de citations,
    l'abstract, l'URL et le lien PDF (si accès ouvert).
    """
    if not query or not query.strip():
        return "Erreur : la requête de recherche ne peut pas être vide."

    if limit < 1 or limit > 100:
        return "Erreur : le limit doit être entre 1 et 100."

    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query.strip(),
            "limit": min(limit, 100),
            "fields": "title,authors,year,citationCount,url,openAccessPdf,venue,journal,publicationTypes,tldr",
        }
        response = requests.get(url, params=params, timeout=15)
        try:
            if response.status_code == 429:
                return "Erreur : limite de taux atteinte pour l'API Semantic Scholar. Réessayez plus tard."
            if response.status_code != 200:
                return f"Erreur API Semantic Scholar (HTTP {response.status_code}) : {response.text[:500]}"

            data = response.json()
            papers = data.get("data", [])
            total = data.get("total", 0)

            if not papers:
                return f"Aucun résultat trouvé pour '{query}' ({total} résultats au total)."

            results = []
            for i, paper in enumerate(papers, 1):
                title = paper.get("title", "N/A")
                authors = paper.get("authors", [])
                author_names = ", ".join(a.get("name", "") for a in authors) if authors else "N/A"
                year = paper.get("year", "N/A")
                citations = paper.get("citationCount", 0)
                url = paper.get("url", "N/A")
                abstract = paper.get("tldr", {}).get("text", paper.get("abstract", "N/A"))
                pdf_url = paper.get("openAccessPdf", {}).get("url", "N/A") if paper.get("openAccessPdf") else "N/A"
                venue = paper.get("venue", paper.get("journal", {}).get("name", "N/A")) if paper.get("venue") else "N/A"

                entry = (
                    f"{i}. **{title}**\n"
                    f"   Auteurs : {author_names}\n"
                    f"   Année : {year} | Revue : {venue}\n"
                    f"   Citations : {citations}\n"
                    f"   URL : {url}\n"
                )
                if abstract and abstract != "N/A":
                    entry += f"   Abstract : {abstract[:500]}{'...' if len(abstract) > 500 else ''}\n"
                if pdf_url and pdf_url != "N/A":
                    entry += f"   PDF (accès ouvert) : {pdf_url}\n"
                results.append(entry)

            return (
                f"Recherche académique : '{query}' ({total} résultats, {len(papers)} affichés)\n\n"
                + "\n".join(results)
            )
        finally:
            response.close()

    except requests.Timeout:
        return "Erreur : le délai d'attente de l'API Semantic Scholar a été dépassé (15s)."
    except requests.ConnectionError:
        return "Erreur : impossible de se connecter à l'API Semantic Scholar. Vérifiez votre connexion réseau."
    except Exception as e:
        return f"Erreur lors de la recherche académique : {str(e)}"


# ── Outil HTTP générique ────────────────────────────────────────────────────────

# Regex pour valider les schémas autorisés
_SAFE_URL_RE = re.compile(r'^https?://')

# Liste d'adresses IP privées/réservées à bloquer (sécurité)
_BLOCKED_HOSTS = (
    "localhost", "127.0.0.1", "0.0.0.0",
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.",
    "192.168.",
    "169.254.",
    "::1",
    "0:0:0:0:0:0:0:1",
)


def _is_safe_url(url: str) -> tuple[bool, str]:
    """Vérifie qu'une URL est sûre (schéma + pas d'hôte privé)."""
    if not _SAFE_URL_RE.match(url):
        return False, "Erreur de sécurité : seuls les schémas http:// et https:// sont autorisés."

    # Vérifier que l'hôte n'est pas une adresse privée
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ""

        for blocked in _BLOCKED_HOSTS:
            if host == blocked or host.startswith(blocked):
                return False, f"Erreur de sécurité : l'accès à l'hôte privé '{host}' est bloqué."

        # Vérifier la résolution DNS
        try:
            socket.getaddrinfo(host, None)
        except socket.gaierror:
            pass  # L'erreur de connexion sera capturée plus bas
    except Exception:
        pass

    return True, ""


@tool("http_request")
def http_request(
    url: str,
    method: str = "GET",
    headers: str = "{}",
    body: str = "{}",
) -> str:
    """
    Exécute une requête HTTP vers n'importe quelle API externe.

    Args:
        url : URL cible (http/https uniquement, pas d'hôtes privés).
        method : Méthode HTTP (GET, POST, PUT, DELETE).
        headers : Chaîne JSON de headers (ex: '{"Authorization": "Bearer xxx"}').
        body : Chaîne JSON du body (pour POST/PUT).

    Returns:
        Réponse structurée (status_code, headers, body).
    """
    # Validation URL
    safe, error = _is_safe_url(url)
    if not safe:
        return error

    # Validation méthode
    method = method.upper()
    allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    if method not in allowed_methods:
        return f"Erreur : méthode HTTP '{method}' non autorisée. Méthodes autorisées : {', '.join(sorted(allowed_methods))}"

    # Parser headers et body
    try:
        parsed_headers = json.loads(headers) if headers else {}
    except json.JSONDecodeError as e:
        return f"Erreur : headers JSON invalide : {str(e)}"

    # Bloquer les headers sensibles
    SENSITIVE_HEADERS = {
        "authorization", "proxy-authorization",
        "cookie", "set-cookie",
        "proxy-authorization",
    }
    for header_name in parsed_headers:
        if header_name.lower() in SENSITIVE_HEADERS:
            return (
                f"Erreur de sécurité : le header '{header_name}' est bloqué "
                "pour des raisons de sécurité."
            )

    try:
        parsed_body = json.loads(body) if body else None
    except json.JSONDecodeError as e:
        return f"Erreur : body JSON invalide : {str(e)}"

    # Exécuter la requête
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=parsed_headers,
            json=parsed_body if method in ("POST", "PUT", "PATCH") else None,
            data=parsed_body if method in ("POST", "PUT", "PATCH") and not isinstance(parsed_body, dict) else None,
            timeout=10,
            allow_redirects=False,
        )
        try:
            # Limiter la taille de la réponse
            response_text = response.text[:50000]
            if len(response.text) > 50000:
                response_text += "\n\n[... RÉPONSE TRONQUÉE (max 50 Ko) ...]"

            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_text,
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
        finally:
            response.close()

    except requests.Timeout:
        return json.dumps({
            "status_code": 0,
            "error": "Délai d'attente dépassé (10s).",
        }, indent=2, ensure_ascii=False)
    except requests.ConnectionError as e:
        return json.dumps({
            "status_code": 0,
            "error": f"Erreur de connexion : {str(e)}",
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status_code": 0,
            "error": f"Erreur inattendue : {str(e)}",
        }, indent=2, ensure_ascii=False)


# ── Outils de recherche généraliste ─────────────────────────────────────────────

@tool("wikipedia_search")
def wikipedia_search(query: str, sentences: int = 5, auto_suggest: bool = True) -> str:
    """
    Recherche sur Wikipédia et retourne un résumé en français ou anglais.
    Retourne le résumé, les sections principales et les liens internes.

    Args:
        query: Terme de recherche.
        sentences: Nombre de phrases à inclure dans le résumé (par défaut 5).
        auto_suggest: Si True, suggère automatiquement des pages similaires.
    """
    try:
        # Essayer d'abord en français
        wikipedia.set_lang("fr")
        search_results = wikipedia.search(query, results=3)

        if not search_results:
            # Essayer en anglais
            wikipedia.set_lang("en")
            search_results = wikipedia.search(query, results=3)
            if not search_results:
                return f"Aucun résultat Wikipédia trouvé pour '{query}'."

        # Chercher la meilleure correspondance
        best_page = None
        best_score = 0
        for title in search_results[:3]:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                # Score basé sur la similarité du titre
                title_lower = title.lower()
                query_lower = query.lower()
                score = sum(1 for w in query_lower.split() if w in title_lower)
                if score > best_score:
                    best_score = score
                    best_page = page
            except wikipedia.exceptions.DisambiguationError:
                continue
            except wikipedia.exceptions.PageError:
                continue

        if best_page is None:
            # Prendre le premier résultat
            try:
                best_page = wikipedia.page(search_results[0], auto_suggest=False)
            except Exception:
                return f"Impossible de charger la page pour '{query}'."

        # Construire la réponse
        result = (
            f"# {best_page.title}\n\n"
            f"{best_page.summary[:4000]}\n\n"
            f"## Sections principales\n"
        )
        for i, section in enumerate(best_page.sections[:15], 1):
            result += f"{i}. {section['title']}\n"

        result += f"\n## Liens internes notables\n"
        for link in best_page.links[:20]:
            result += f"- {link}\n"

        result += f"\n[Lire l'article complet]({best_page.url})"
        return result

    except wikipedia.exceptions.DisambiguationError as e:
        options = "\n".join(f"- {opt}" for opt in e.options[:10])
        return (
            f"Page ambiguë : '{query}' correspond à plusieurs pages.\n"
            f"Options possibles :\n{options}\n\n"
            f"Précisez votre recherche pour l'une de ces pages."
        )
    except Exception as e:
        return f"Erreur lors de la recherche Wikipédia : {str(e)}"


@tool("arxiv_search")
def arxiv_search(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> str:
    """
    Recherche des articles académiques sur arXiv.
    Retourne le titre, les auteurs, l'abstract, les citations et le lien PDF.

    Args:
        query: Requête de recherche (ex: 'transformer attention deep learning').
        max_results: Nombre maximal de résultats (1-100).
        sort_by: 'relevance' ou 'lastUpdatedDate'.

    Returns:
        Liste structurée d'articles avec résumés.
    """
    try:
        if max_results < 1 or max_results > 100:
            return "Erreur : max_results doit être entre 1 et 100."

        sort_criteria = arxiv.SortCriterion.RELEVANCE if sort_by == "relevance" else arxiv.SortCriterion.LAST_UPDATED_DATE

        search = arxiv.Search(
            query=query,
            max_results=min(max_results, 100),
            sort_by=sort_criteria,
            sort_order="descending",
        )

        results = list(search.results())
        if not results:
            return f"Aucun article arXiv trouvé pour '{query}'."

        output = [f"Recherche arXiv : '{query}' ({len(results)} résultats)\n"]
        for i, paper in enumerate(results, 1):
            entry = (
                f"{i}. **{paper.title}**\n"
                f"   Auteurs : {', '.join(a.name for a in paper.authors[:5])}"
                f"{' et +' if len(paper.authors) > 5 else ''}\n"
                f"   Publié : {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}\n"
                f"   Citations : {paper.citation_count or 0} | PDF : {paper.pdf_url}\n"
                f"   Abstract : {paper.summary[:1500]}"
            )
            output.append(entry)

        return "\n\n".join(output)

    except Exception as e:
        return f"Erreur lors de la recherche arXiv : {str(e)}"


@tool("web_scrape")
def web_scrape(url: str, max_length: int = 10000) -> str:
    """
    Récupère et extrait le contenu textuel d'une page web.
    Utilise BeautifulSoup pour un nettoyage propre du HTML.

    Args:
        url : URL de la page à scraper (http/https uniquement).
        max_length : Longueur maximale du texte extrait.

    Returns:
        Contenu textuel nettoyé de la page.
    """
    # Sécurité : whitelist schémas + pas d'hôtes privés
    if not _SAFE_URL_RE.match(url):
        return "Erreur de sécurité : seuls les schémas http:// et https:// sont autorisés."

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ""
        for blocked in _BLOCKED_HOSTS:
            if host == blocked or host.startswith(blocked):
                return f"Erreur de sécurité : l'accès à l'hôte privé '{host}' est bloqué."
    except Exception:
        pass

    try:
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AgentTest/1.0)"
        })
        try:
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Supprimer les éléments inutiles
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()

            # Extraire le texte
            text = soup.get_text(separator="\n", strip=True)

            # Nettoyer les espaces multiples
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)

            if len(text) > max_length:
                text = text[:max_length] + "\n\n[... CONTENU TRONQUÉ ...]"

            # Extraire le titre
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else "Pas de titre"

            return f"## {title_text}\n\n{text}"
        finally:
            response.close()

    except requests.Timeout:
        return "Erreur : délai d'attente dépassé (15s)."
    except requests.ConnectionError:
        return "Erreur : impossible de se connecter à l'URL."
    except requests.HTTPError as e:
        return f"Erreur HTTP : {e.response.status_code} - {e.response.reason}"
    except Exception as e:
        return f"Erreur lors du scraping : {str(e)}"


@tool("youtube_transcript")
def youtube_transcript(video_id: str, languages: list[str] = None) -> str:
    """
    Extrait la transcription textuelle d'une vidéo YouTube.

    Args:
        video_id : ID de la vidéo YouTube (ex: 'dQw4w9WgXcQ' ou l'URL complète).
        languages : Liste de langues prioritaires (ex: ['fr', 'en']). Par défaut: ['fr', 'en', 'auto'].

    Returns:
        Transcription complète de la vidéo avec timestamps.
    """
    try:
        # Extraire l'ID de la vidéo depuis l'URL
        import re
        if "youtube.com" in video_id or "youtu.be" in video_id:
            match = re.search(r'(?:v=|youtu\.be/|video/)([a-zA-Z0-9_-]{11})', video_id)
            if match:
                video_id = match.group(1)
            else:
                return "Erreur : ID YouTube invalide dans l'URL fournie."
        elif len(video_id) != 11:
            return "Erreur : l'ID YouTube doit faire exactement 11 caractères."

        langs = languages or ["fr", "en", "auto"]

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception:
            return f"Erreur : vidéo '{video_id}' introuvable ou privée."

        # Chercher d'abord en français, puis anglais, puis auto-détecté
        transcript = None
        detected_lang = None
        for lang in langs:
            try:
                if lang == "auto":
                    transcript = transcript_list.find_transcript(langues=[])
                else:
                    transcript = transcript_list.find_transcript(langues=[lang])
                detected_lang = transcript.language
                break
            except Exception:
                continue

        if transcript is None:
            # Essayer toutes les langues disponibles
            try:
                transcript = transcript_list.find_transcript(langues=[])
                detected_lang = transcript.language
            except Exception:
                return f"Aucune transcription disponible pour la vidéo '{video_id}'."

        # Construire la transcription
        segments = transcript.fetch()
        full_text = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                start = segment.start
                minutes = int(start // 60)
                seconds = int(start % 60)
                full_text.append(f"[{minutes:02d}:{seconds:02d}] {text}")

        result = (
            f"## Transcription YouTube\n"
            f"Langue détectée : {detected_lang}\n"
            f"Nombre de segments : {len(full_text)}\n\n"
            + "\n".join(full_text[:5000])  # Limiter pour éviter les dépassements
        )

        if len(full_text) > 5000:
            result += "\n\n[... TRANSCRIPTION TRONQUÉE (5000 segments max) ...]"

        return result

    except Exception as e:
        return f"Erreur lors de l'extraction de la transcription : {str(e)}"


@tool("generate_html_report")
def generate_html_report(
    title: str,
    content: str,
    output_path: str = "report.html",
    template: str = "default",
) -> str:
    """
    Génère un rapport HTML professionnel et lisible à partir de contenu textuel.
    Supporte plusieurs templates : 'default', 'minimal', 'academic'.

    Args:
        title: Titre du rapport.
        content: Contenu textuel (Markdown ou texte brut).
        output_path: Chemin de sortie du fichier HTML.
        template: Template à utiliser ('default', 'minimal', 'academic').

    Returns:
        Chemin du fichier généré et résumé.
    """
    try:
        out_path = safe_resolve(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Convertir Markdown basique en HTML
        html_content = _markdown_to_html(content)

        templates = {
            "default": _html_template_default,
            "minimal": _html_template_minimal,
            "academic": _html_template_academic,
        }

        template_func = templates.get(template, _html_template_default)
        html = template_func(title, html_content)

        out_path.write_text(html, encoding="utf-8")
        return f"Rapport HTML généré avec succès : {out_path}\n\n" \
               f"Titre : {title}\n" \
               f"Template : {template}\n" \
               f"Taille : {len(html)} caractères"

    except Exception as e:
        return f"Erreur lors de la génération du rapport HTML : {str(e)}"


def _markdown_to_html(text: str) -> str:
    """Convertit un Markdown basique en HTML."""
    html = text

    # Titres
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\2</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Gras et italique
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Listes non-ordonnées
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)\n', r'<ul>\1</ul>\n', html, flags=re.DOTALL)

    # Liens
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

    # Code inline
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Paragraphes
    html = re.sub(r'\n\n', r'</p><p>', html)
    html = f'<p>{html}</p>'

    return html


def _html_template_default(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --bg: #fafafa; --text: #1a1a2e; --accent: #6366f1;
    --card: #ffffff; --border: #e2e8f0;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0f172a; --text: #e2e8f0; --accent: #818cf8;
      --card: #1e293b; --border: #334155;
    }}
  }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
    max-width: 800px; margin: 0 auto; padding: 2rem 1rem;
    line-height: 1.7;
  }}
  h1 {{ color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }}
  h2 {{ color: var(--accent); margin-top: 2rem; }}
  h3 {{ color: var(--text); }}
  code {{ background: var(--border); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.9em; }}
  pre {{ background: var(--border); padding: 1rem; border-radius: 8px; overflow-x: auto; }}
  ul, ol {{ padding-left: 1.5rem; }}
  li {{ margin: 0.25rem 0; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 2rem; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">Généré par Agent Test</div>
{content}
</body>
</html>"""


def _html_template_minimal(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 680px; margin: 3rem auto; padding: 0 1rem; line-height: 1.8; color: #333; }}
  h1 {{ font-size: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.5rem; }}
  code {{ background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 3px; }}
</style>
</head>
<body>
<h1>{title}</h1>
{content}
</body>
</html>"""


def _html_template_academic(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Times New Roman', serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; line-height: 1.9; color: #222; }}
  h1 {{ text-align: center; font-size: 1.6rem; margin-bottom: 0.5rem; }}
  .meta {{ text-align: center; color: #666; margin-bottom: 2rem; font-size: 0.9rem; }}
  h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 0.3rem; margin-top: 2rem; }}
  h3 {{ margin-top: 1.5rem; }}
  code {{ background: #f8f8f8; padding: 0.1rem 0.3rem; }}
  ul {{ margin-left: 2rem; }}
  li {{ margin: 0.3rem 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">Rapport académique — Généré par Agent Test</div>
{content}
</body>
</html>"""


# ── Outil d'exécution de crew (interne) ────────────────────────────────────────

@tool("execute_crew")
def execute_crew(crew_name: str, inputs_json: str = "{}", llm_override: str = None) -> str:
    """
    Exécute un crew CrewAI de manière synchrone.
    Note : cet outil est destiné à l'exécution imbriquée de crews.
    """
    try:
        inputs = json.loads(inputs_json) if isinstance(inputs_json, str) else inputs_json
    except json.JSONDecodeError:
        inputs = {}

    from app.core.crew_runner import run_crew
    results = list(run_crew(
        crew_name=crew_name,
        message=inputs.get("message", ""),
        inputs=inputs,
        llm_override=llm_override,
    ))
    return "\n".join(r for r in results if '"type": "result"' in r or '"type":"result"' in r) or "Exécution terminée (aucun résultat textuel)."
