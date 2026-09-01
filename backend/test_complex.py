import requests
import json

url = "http://localhost:8000/api/chat"
payload = {
    "crew_name": "Autonomous_SWE",
    "message": "Fais un test de tes capacités d'auto-expansion.",
    "inputs": {
        "project_path": "/Users/poutrainlouis/Code/AgentTest",
        "feature_request": (
            "1. Crée un fichier 'experimental_playground/mock_users.json' contenant un tableau JSON de 5 faux utilisateurs (nom, age, profession).\n"
            "2. Crée un NOUVEAU crew appelé 'Json_Analyzer' (en écrivant un fichier Json_Analyzer.yaml dans backend/config/crews/). "
            "Son but doit être de lire un fichier JSON et d'extraire la moyenne d'âge et les professions.\n"
            "3. Utilise execute_crew pour déléguer l'analyse du fichier 'experimental_playground/mock_users.json' à ton nouveau crew 'Json_Analyzer' (utilise le LLM openai/gpt-oss-120b pour lui).\n"
            "4. Affiche le rapport final."
        )
    },
    "max_rpm": 30
}

print("Lancement du test complexe...")
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
