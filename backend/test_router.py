import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.core.router import route_request

# On teste la fonction route_request avec un faux session_id
res = route_request("test_session", "Affiche le contenu du fichier pip_freeze.txt", {"project_path": "./backend"})
print("ROUTE_REQUEST RESULT:", res)
