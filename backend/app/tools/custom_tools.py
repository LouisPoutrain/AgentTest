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


def _get_project_root() -> str:
    """Retourne le chemin absolu de la racine du projet (contenant backend/ et frontend/)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _resolve_project_path(path: str) -> str:
    """Résout intelligemment un chemin (relatif ou absolu) par rapport à la racine globale du projet."""
    if not path or path == ".":
        return _get_project_root()
    if os.path.isabs(path):
        return os.path.abspath(path)
    
    root = _get_project_root()
    # Si le chemin commence par ./ ou ../ ou un nom relatif, on le résout par rapport à la racine globale
    resolved = os.path.abspath(os.path.join(root, path))
    return resolved


def _is_safe_path(path: str) -> bool:
    """Valide que le chemin ciblé reste dans l'espace de travail autorisé (/Users/.../Code/)."""
    try:
        resolved = _resolve_project_path(path)
        workspace_root = os.path.abspath(os.path.join(_get_project_root(), ".."))
        return resolved.startswith(workspace_root) and not resolved.startswith("/System") and not resolved.startswith("/etc")
    except Exception:
        return False


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
    target_path = _resolve_project_path(file_path)
    if not _is_safe_path(target_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 10000:
                return content[:10000] + "\n\n[... CONTENU TRONQUÉ POUR RAISONS DE SÉCURITÉ DE CONTEXTE ...]"
            return content
    except Exception as e:
        return f"Erreur lors de la lecture du fichier '{file_path}' : {str(e)}"


@tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """Écrit (ou écrase) un fichier avec le contenu spécifié. Retourne un message de succès."""
    target_path = _resolve_project_path(file_path)
    if not _is_safe_path(target_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
    try:
        # S'assurer que le dossier parent existe
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Le fichier '{file_path}' a été écrit avec succès."
    except Exception as e:
        return f"Erreur lors de l'écriture dans le fichier '{file_path}' : {str(e)}"


@tool("delete_path")
def delete_path(path: str) -> str:
    """Supprime un fichier ou un dossier local. Retourne un message de succès."""
    target_path = _resolve_project_path(path)
    if not _is_safe_path(target_path):
        return f"Erreur de sécurité : L'accès au chemin '{path}' est interdit en dehors du répertoire de travail."
    try:
        if not os.path.exists(target_path):
            return f"Erreur : le chemin '{path}' n'existe pas."
        
        if os.path.isfile(target_path):
            os.remove(target_path)
            return f"Le fichier '{path}' a été supprimé."
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
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
    target_dir = _resolve_project_path(dest_dir)
    if not _is_safe_path(target_dir):
        return f"Erreur de sécurité : L'accès au chemin '{dest_dir}' est interdit en dehors du répertoire de travail."
    try:
        if os.path.exists(target_dir):
            # Nettoyer l'ancien dossier pour permettre un clone propre
            shutil.rmtree(target_dir, ignore_errors=True)
            
        os.makedirs(os.path.dirname(os.path.abspath(target_dir)), exist_ok=True)
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
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
    target_path = _resolve_project_path(file_path)
    if not _is_safe_path(target_path):
        return f"Erreur de sécurité : L'accès au chemin '{file_path}' est interdit en dehors du répertoire de travail."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, 'a', encoding='utf-8') as f:
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
        target_path = _resolve_project_path(directory_path)
        if not _is_safe_path(target_path):
            return f"Erreur de sécurité : L'accès au dossier '{directory_path}' est interdit."
        if not os.path.exists(target_path):
            return f"Erreur : Le dossier '{directory_path}' n'existe pas."
        
        # Liste des dossiers "poubelles" à ignorer absolument pour ne pas perdre de temps
        IGNORE_LIST = ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.idea', '.vscode', 'dist', 'build', '.next']
        
        items = os.listdir(target_path)
        folders = []
        files = []
        
        for item in items:
            if item in IGNORE_LIST:
                continue
                
            full_path = os.path.join(target_path, item)
            if os.path.isdir(full_path):
                folders.append(f"📁 [DOSSIER] {item}/")
            else:
                files.append(f"📄 [FICHIER] {item}")
                
        # Trier pour un affichage propre
        folders.sort()
        files.sort()
        
        result = [f"Contenu de '{directory_path}' :"]
        all_items = folders + files
        if len(all_items) > 100:
            result.extend(all_items[:100])
            result.append(f"\n... (et {len(all_items) - 100} autres éléments cachés pour protéger le contexte)")
        else:
            result.extend(all_items)
        
        return "\n".join(result) if len(result) > 1 else "Le dossier est vide."
        
    except Exception as e:
        return f"Erreur lors de l'exploration de '{directory_path}' : {str(e)}"


@tool("run_test_command")
def run_test_command(project_path: str, command: str) -> str:
    """
    Exécute une commande de test, de build ou de vérification de types (ex: 'npm test', 'npx vitest run', 'pytest', 'npm run build', 'npx tsc --noEmit')
    dans le répertoire cible du projet et retourne la sortie réelle de la console (stdout, stderr, code de retour).
    """
    target_path = _resolve_project_path(project_path)
    if not _is_safe_path(target_path):
        return f"Erreur de sécurité : L'accès au chemin '{project_path}' est interdit en dehors de l'espace de travail."
    if not os.path.exists(target_path):
        return f"Erreur : Le dossier du projet '{project_path}' n'existe pas."
    
    # Sécurité basique
    cmd_lower = command.strip().lower()
    dangerous_keywords = ["rm -rf /", "mkfs", ":(){ :|:& };:", "dd if="]
    for danger in dangerous_keywords:
        if danger in cmd_lower:
            return f"Erreur de sécurité : Commande interdite '{command}'."
            
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output_parts = [
            f"=== Exécution dans '{project_path}' ===",
            f"Commande : {command}",
            f"Code de sortie : {result.returncode} ({'Succès' if result.returncode == 0 else 'Échec'})",
        ]
        
        if result.stdout:
            stdout_text = result.stdout
            if len(stdout_text) > 8000:
                stdout_text = stdout_text[:8000] + "\n\n[... SORTIE TRONQUÉE POUR RAISONS DE CONTEXTE ...]"
            output_parts.append(f"\n--- STDOUT ---\n{stdout_text}")
            
        if result.stderr:
            stderr_text = result.stderr
            if len(stderr_text) > 4000:
                stderr_text = stderr_text[:4000] + "\n\n[... ERREURS TRONQUÉES POUR RAISONS DE CONTEXTE ...]"
            output_parts.append(f"\n--- STDERR ---\n{stderr_text}")
            
        if not result.stdout and not result.stderr:
            output_parts.append("\n(Aucune sortie console)")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Erreur : La commande '{command}' a dépassé le délai autorisé de 120 secondes."
    except Exception as e:
        return f"Erreur lors de l'exécution de la commande '{command}' : {str(e)}"

@tool("generate_archify_diagram")
def generate_archify_diagram(json_spec: str, output_path: str, diagram_type: str = "architecture") -> str:
    """
    Génère un diagramme interactif HTML (Architecture, Workflow, Sequence, etc.) à l'aide du moteur Archify.
    - json_spec : La spécification du diagramme au format JSON.
    - output_path : Le nom/chemin du fichier HTML de sortie (sera résolu dans l'espace de travail).
    - diagram_type : Le type de diagramme (architecture, workflow, sequence, dataflow, lifecycle).
    """
    import tempfile
    
    target_output_path = _resolve_project_path(output_path)
    if not _is_safe_path(target_output_path):
        return f"Erreur de sécurité : L'accès au chemin '{output_path}' est interdit."
        
    # S'assurer que le dossier parent existe
    os.makedirs(os.path.dirname(os.path.abspath(target_output_path)), exist_ok=True)
        
    cache_dir = os.path.join(_get_project_root(), "backend", "app", "tools", ".cache")
    archify_dir = os.path.join(cache_dir, "archify")
    
    try:
        os.makedirs(cache_dir, exist_ok=True)
        # Cloner le dépôt si nécessaire
        if not os.path.exists(archify_dir):
            clone_cmd = ["git", "clone", "https://github.com/tt-a1i/archify.git", archify_dir]
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
        # Créer un fichier JSON temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write(json_spec)
            temp_file_path = temp_file.name
            
        # Lancer le CLI
        # node archify/bin/archify.mjs render <type> <input> <output>
        node_script = os.path.join(archify_dir, "archify", "bin", "archify.mjs")
        
        run_cmd = [
            "node", node_script, "render", diagram_type, temp_file_path, target_output_path
        ]
        
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        
        # Nettoyer
        os.remove(temp_file_path)
        
        if result.returncode == 0:
            return f"Succès : Diagramme '{diagram_type}' généré avec succès dans '{output_path}'."
        else:
            return f"Erreur lors de la génération du diagramme.\nCode: {result.returncode}\nSortie: {result.stderr or result.stdout}"
            
    except Exception as e:
        return f"Erreur critique lors de l'appel à archify : {str(e)}"

@tool("execute_crew")
def execute_crew(crew_name: str, inputs_json: str, llm_override: str = None) -> str:
    """
    Déclenche l'exécution d'un autre Crew (agent) existant et retourne le résultat final.
    Permet de déléguer des sous-tâches complexes à d'autres Crews spécialisés (ex: Reviewer, Tester, Directory_Archifier).
    - crew_name (str) : Le nom du Crew (ex: "Reviewer")
    - inputs_json (str) : Un JSON contenant les variables requises (ex: '{"project_path": "../mon_projet"}')
    - llm_override (str, optionnel) : L'ID du LLM à utiliser pour forcer le modèle du crew enfant (ex: "openai/qwen-3.6-35b-instruct").
    Retourne le rapport complet du Crew invoqué.
    """
    import json
    import requests
    import sys

    try:
        inputs_dict = json.loads(inputs_json)
    except json.JSONDecodeError as e:
        return f"Erreur: inputs_json invalide. Ce doit être un JSON valide. Détail: {str(e)}"
    
    # Appel de l'API locale /api/chat pour déclencher le crew
    url = "http://localhost:8000/api/chat"
    payload = {
        "crew_name": crew_name,
        "message": f"Délégation de la tâche au crew {crew_name}",
        "inputs": inputs_dict,
        "max_rpm": 30,
        "options": {"llm_override": llm_override} if llm_override else {}
    }
    
    final_result = ""
    try:
        print(f"\\n🚀 [Délégation] Démarrage du Crew enfant: {crew_name}...", file=sys.stdout)
        
        # On lit le SSE stream
        with requests.post(url, json=payload, stream=True, timeout=900) as response:
            if response.status_code != 200:
                return f"Erreur API: Le serveur a répondu {response.status_code}"
                
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:]
                        try:
                            data = json.loads(json_str)
                            msg_type = data.get("type")
                            content = data.get("content", "")
                            
                            if msg_type == "log":
                                print(f"[{crew_name}] {content}", file=sys.stdout)
                            elif msg_type == "result":
                                final_result = content
                                print(f"✅ [Délégation] {crew_name} a terminé.", file=sys.stdout)
                            elif msg_type == "error":
                                print(f"❌ [Délégation] {crew_name} a échoué: {content}", file=sys.stdout)
                                return f"Erreur lors de l'exécution du Crew {crew_name} : {content}"
                        except json.JSONDecodeError:
                            pass
        
        if final_result:
            return f"Rapport final de {crew_name}:\\n{final_result}"
        else:
            return f"Le Crew {crew_name} s'est terminé sans renvoyer de résultat clair."
            
    except Exception as e:
        return f"Erreur système lors du lancement du Crew {crew_name} : {str(e)}"