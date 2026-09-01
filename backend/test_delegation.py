import requests
import json
import sys

url = "http://localhost:8000/api/chat"
payload = {
    "crew_name": "Autonomous_SWE",
    "message": "Fais un test de délégation.",
    "inputs": {
        "project_path": "/Users/poutrainlouis/Code/AgentTest",
        "feature_request": "Délègue l'analyse approfondie (review) du fichier 'backend/app/main.py' au crew 'Reviewer'. Assure-toi d'utiliser ton outil execute_crew et de choisir stratégiquement le modèle LLM. Fais-moi ensuite un résumé des problèmes trouvés."
    },
    "max_rpm": 30
}

print("Lancement du test de délégation...")
try:
    with requests.post(url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data = json.loads(decoded_line[6:])
                    print(f"[{data.get('type')}] {data.get('content')}")
except Exception as e:
    print("Erreur:", e)
