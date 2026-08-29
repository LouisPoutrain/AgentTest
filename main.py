"""
main.py — Point d'entrée CLI de l'orchestrateur AgentTest.

Prend en argument optionnel le nom d'un fichier YAML présent
dans le dossier config/crews/ et lance l'exécution.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import re
from pathlib import Path

from dotenv import load_dotenv
from crewai import Crew

from core.agent_parser import (
    create_agents_from_yaml,
    create_tasks_from_yaml,
    get_crew_settings_from_yaml
)
from tools.custom_tools import (
    calculate_text_length,
    web_search,
    read_file,
    write_file,
    delete_path,
    execute_python_code,
    clone_github_repo
)

AVAILABLE_TOOLS = {
    "calculate_text_length": calculate_text_length,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "delete_path": delete_path,
    "execute_python_code": execute_python_code,
    "clone_github_repo": clone_github_repo,
}

def main() -> None:
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Variable GEMINI_API_KEY manquante.")
        sys.exit(1)

    crews_dir = Path(__file__).resolve().parent / "config" / "crews"
    crews_dir.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Lance un CrewIA configuré via YAML.")
    parser.add_argument(
        "crew_yaml", 
        nargs="?", 
        help="Le nom du fichier YAML à exécuter (ex: default_crew.yaml)"
    )
    args = parser.parse_args()

    if not args.crew_yaml:
        available_crews = list(crews_dir.glob("*.yaml"))
        if not available_crews:
            print(f"❌ Aucun fichier YAML trouvé dans {crews_dir}.")
        else:
            print("ℹ️ Veuillez spécifier un Crew. Options disponibles :")
            for crew_file in available_crews:
                print(f"  - {crew_file.name}")
        sys.exit(1)

    config_path = crews_dir / args.crew_yaml
    if not config_path.exists():
        print(f"❌ Le fichier de configuration {config_path} n'existe pas.")
        sys.exit(1)

    print(f"\n📄 Chargement du Crew : {config_path.name}")
    crew_settings = get_crew_settings_from_yaml(config_path)
    agents = create_agents_from_yaml(config_path, available_tools=AVAILABLE_TOOLS)
    tasks = create_tasks_from_yaml(config_path, agents)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=crew_settings["process"],
        verbose=True,
        memory=crew_settings["memory"],
        max_rpm=crew_settings["max_rpm"],
        embedder={
            "provider": "sentence-transformer",
            "config": {
                "model": "all-MiniLM-L6-v2"
            }
        },
    )

    print("\n🚀 Lancement de l'orchestration…\n")
    
    max_retries = 3
    retries = 0
    result = None

    while retries <= max_retries:
        try:
            result = crew.kickoff()
            break
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota exceeded" in error_str or "Rate Limit" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                retries += 1
                if retries > max_retries:
                    print("\n❌ Nombre maximal de tentatives atteint (429). Arrêt du script.")
                    sys.exit(1)
                
                # Extraction automatique du délai de pause depuis le message d'erreur
                delay = 60
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str)
                if match:
                    delay = int(float(match.group(1))) + 2
                
                print(f"\n⚠️ Limite d'API atteinte (429). Pause automatique de {delay} secondes avant tentative {retries}/{max_retries}...")
                time.sleep(delay)
            else:
                raise e

    print("\n" + "=" * 60)
    print("📊 RÉSULTAT FINAL")
    print("=" * 60)
    print(result)
    print()


if __name__ == "__main__":
    main()
