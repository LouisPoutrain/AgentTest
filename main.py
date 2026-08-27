"""
main.py — Point d'entrée CLI de l'orchestrateur AgentTest.

Prend en argument optionnel le nom d'un fichier YAML présent
dans le dossier config/crews/ et lance l'exécution.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from crewai import Crew

from core.agent_parser import create_agents_from_yaml, create_tasks_from_yaml
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
    agents = create_agents_from_yaml(config_path, available_tools=AVAILABLE_TOOLS)
    tasks = create_tasks_from_yaml(config_path, agents)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        memory=True,
        embedder={
            "provider": "google-generativeai",
            "config": {
                "model": "models/text-embedding-004",
                "api_key": os.getenv("GEMINI_API_KEY"),
            },
        },
    )

    print("\n🚀 Lancement de l'orchestration…\n")
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("📊 RÉSULTAT FINAL")
    print("=" * 60)
    print(result)
    print()


if __name__ == "__main__":
    main()
