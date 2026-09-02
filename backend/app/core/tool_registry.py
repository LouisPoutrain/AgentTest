"""
core/tool_registry.py — Registre unique des outils disponibles pour les agents CrewAI.

Point d'entrée unique pour résoudre les outils par leur nom.
Élimine la duplication entre app.py et main.py.
"""

from __future__ import annotations

from app.core.tools.file_editor import FileEditorTool
from app.core.tools.terminal_runner import TerminalRunnerTool
from app.tools.custom_tools import (
    calculate_text_length,
    web_search,
    read_file,
    write_file,
    delete_path,
    execute_python_code,
    clone_github_repo,
    append_to_file,
    gen_code,
    gen_entrypoint,
    execute_entrypoint,
    improve_fn,
    list_directory,
    run_test_command,
    generate_archify_diagram,
    execute_crew,
    research_state_of_the_art,
    download_resources,
    generate_state_of_the_art_report,
    generate_state_of_the_art_html,
    # NOUVEAUX OUTILS POUR EducationalContentCreator
    research_educational_resources,
    generate_educational_html,
    generate_educational_markdown,
)

# Instancier les nouveaux outils
file_editor = FileEditorTool()
terminal_runner = TerminalRunnerTool()

AVAILABLE_TOOLS: dict[str, object] = {
    "calculate_text_length": calculate_text_length,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "delete_path": delete_path,
    "execute_python_code": execute_python_code,
    "clone_github_repo": clone_github_repo,
    "append_to_file": append_to_file,
    "gen_code": gen_code,
    "gen_entrypoint": gen_entrypoint,
    "execute_entrypoint": execute_entrypoint,
    "improve_fn": improve_fn,
    "list_directory": list_directory,
    "run_test_command": run_test_command,
    "generate_archify_diagram": generate_archify_diagram,
    "execute_crew": execute_crew,
    # Outils existants
    "file_editor": file_editor,
    "terminal_runner": terminal_runner,
    "research_state_of_the_art": research_state_of_the_art,
    "download_resources": download_resources,
    "generate_state_of_the_art_report": generate_state_of_the_art_report,
    "generate_state_of_the_art_html": generate_state_of_the_art_html,
    # NOUVEAUX OUTILS
    "research_educational_resources": research_educational_resources,
    "generate_educational_html": generate_educational_html,
    "generate_educational_markdown": generate_educational_markdown,
}

def get_tool_names() -> list[str]:
    """Retourne la liste des noms d'outils disponibles."""
    return list(AVAILABLE_TOOLS.keys())