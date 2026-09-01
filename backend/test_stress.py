import requests
import json
import time

url = "http://localhost:8000/api/chat"

queries = [
    {
        "title": "Requête 1 : Refactorisation d'architecture et synchronisation Fullstack",
        "feature_request": (
            "Nous devons enrichir le flux SSE actuel. Dans le backend, modifie crew_runner.py et chat.py "
            "pour inclure des métriques en temps réel (tokens utilisés, coût estimé, statut d'étape). "
            "Côté frontend, mets à jour frontend/lib/types.ts avec ces nouvelles interfaces, et modifie "
            "ExecutionTimeline.tsx et ChatWindow.tsx pour afficher ces métriques en direct. Assure-toi de "
            "gérer la reconnexion automatique du flux en cas de coupure."
        )
    },
    {
        "title": "Requête 2 : Sécurité, Sandboxing et exécution de code dynamique",
        "feature_request": (
            "Dans backend/app/tools/custom_tools.py, nous avons l'outil execute_python_code qui tourne sous Docker. "
            "Ajoute une couche de sécurité supplémentaire en Python pur : implémente un validateur AST statique (module ast) "
            "qui analyse le code avant exécution et bloque l'utilisation d'imports dangereux (os, sys, subprocess). "
            "Ensuite, ajoute un composant CodeTesterModal.tsx dans le frontend pour tester cet outil interactivement avec des "
            "variables mockées et afficher une stack trace propre en cas de violation de sécurité."
        )
    },
    {
        "title": "Requête 3 : Optimisation UI et gestion d'état complexe",
        "feature_request": (
            "L'interface ChatWindow.tsx risque de ralentir si les agents génèrent des milliers de logs. "
            "1) Implémente une virtualisation de la liste des messages (ex: react-window). "
            "2) Remplace la gestion d'état React locale par un store Zustand avec sélecteurs granulaires pour éviter le "
            "re-render total de la page à chaque nouveau log. "
            "3) Ajoute un historique Undo/Redo pour les configurations de Crews avec les raccourcis Cmd+Z."
        )
    },
    {
        "title": "Requête 4 : Test Suite complète et Edge Cases",
        "feature_request": (
            "Sécurise le projet : 1) Configure pytest pour le backend et vitest pour le frontend. "
            "2) Écris des tests unitaires complets pour agent_parser.py afin de valider la robustesse face à des fichiers YAML malformés. "
            "3) Crée un test d'intégration simulant le crash complet d'un sous-crew, et vérifie qu'une ErrorBoundary côté React "
            "(ChatWindow.tsx) capture l'erreur et affiche un message sans faire planter l'application entière."
        )
    }
]

print("======================================================")
print(" DÉMARRAGE DU STRESS-TEST DE L'AUTONOMOUS SWE AGENT")
print("======================================================\n")

for i, query in enumerate(queries, 1):
    print(f"🚀 LANCEMENT DE LA REQUÊTE {i}/4 : {query['title']}")
    print("-" * 50)
    
    payload = {
        "crew_name": "Autonomous_SWE",
        "message": f"Stress-test requête {i}",
        "inputs": {
            "project_path": "/Users/poutrainlouis/Code/AgentTest",
            "feature_request": query['feature_request']
        },
        "max_rpm": 60
    }
    
    try:
        with requests.post(url, json=payload, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data = json.loads(decoded_line[6:])
                        msg_type = data.get('type')
                        content = data.get('content')
                        print(f"[{msg_type}] {content}")
    except Exception as e:
        print(f"Erreur fatale sur la requête {i} : {e}")
        
    print(f"\n✅ FIN DE LA REQUÊTE {i}\n")
    print("=" * 50)
    time.sleep(5)  # Pause entre chaque requête pour refroidir le LLM
    
print("🎉 TOUTES LES REQUÊTES DU STRESS-TEST ONT ÉTÉ TRAITÉES.")
