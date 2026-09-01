"""
Outil CrewAI pour l'exécution de commandes terminal.
"""

import subprocess
from typing import Optional

from crewai.tools import BaseTool


class TerminalRunnerTool(BaseTool):
    """Outil pour exécuter des commandes shell dans le terminal."""

    name: str = "Terminal Runner"
    description: str = (
        "Un outil pour exécuter des commandes shell. "
        "Utilisez-le pour installer des dépendances, lancer des tests, compiler du code, etc. "
        "Exemple : run(command='npm install') ou run(command='python -m pytest tests/') "
        "Attention : Les commandes sont exécutées dans le répertoire de travail actuel."
    )

    def _run(self, command: str) -> str:
        """
        Exécute la commande shell demandée.

        Args:
            command: La commande shell à exécuter.

        Returns:
            str: La sortie standard et les erreurs de la commande.
        """
        # Liste des commandes interdites pour la sécurité
        forbidden_commands = ['rm -rf /', 'sudo', 'mkfs', 'dd if=/dev/zero']
        
        for forbidden in forbidden_commands:
            if forbidden in command.lower():
                return f"Erreur : Commande interdite détectée : {forbidden}"

        try:
            # Exécuter la commande
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # Timeout de 5 minutes
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode != 0:
                return f"Erreur (code {result.returncode}):\n{error}"
            
            return output if output else "Commande exécutée avec succès (aucune sortie)."

        except subprocess.TimeoutExpired:
            return "Erreur : La commande a expiré (délai de 5 minutes dépassé)."
        except Exception as e:
            return f"Erreur lors de l'exécution de la commande : {str(e)}"
