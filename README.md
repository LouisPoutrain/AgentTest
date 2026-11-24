# Agent Zouglou

Plateforme d'orchestration d'agents IA. Un routeur LLM analyse les messages entrants et les oriente vers des équipes d'agents spécialisés (Crews) définies en YAML, avec streaming des logs en temps réel via SSE.

## Fonctionnalités

- Chat avec routeur LLM : réponse directe, appel d'outil individuel, ou dispatch vers un Crew
- Crews déclaratifs en YAML (agents, tâches, outils, modèles)
- Exécution multi-crew (séquentiel ou parallèle)
- Streaming SSE des logs agents dans l'interface
- Application desktop Electron (lance backend + frontend)
- Navigation sécurisée dans un dossier projet (sandbox de chemins)
- Historique des conversations en SQLite
- 20+ Crews préconfigurés (SWE, review, tests, sécurité, recherche web, etc.)

## Stack

| Couche | Technologies |
|--------|-------------|
| Backend | Python 3.12, FastAPI, CrewAI, LiteLLM, Pydantic, SQLite |
| Frontend | Next.js 16, React 19, Tailwind CSS v4, Zustand, shadcn/ui |
| Desktop | Electron 32 |
| LLM | Tout provider compatible LiteLLM (OpenAI, Mistral, Gemini, Ollama...) |

## Installation

Prérequis : Python 3.12+, Node.js 20+, une clé API LLM.

```bash
git clone <repository-url>
cd AgentTest

# Environnement Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Configuration
cp backend/.env.example backend/.env
# Renseigner LLM_API_KEY et LLM_BASE_URL dans backend/.env
```

## Lancement

**Desktop** (recommandé) :

```bash
cd desktop
npm install
npm start
```

**Manuel** (développement) :

```bash
# Terminal 1
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm install
npm run dev
```

Interface disponible sur http://localhost:3000.

## Configuration

Variables d'environnement dans `backend/.env` (voir [backend/.env.example](backend/.env.example)) :

| Variable | Description | Requis |
|----------|-------------|--------|
| `LLM_API_KEY` | Clé API du provider LLM | oui |
| `LLM_BASE_URL` | URL de base de l'API LLM | oui |
| `GEMINI_API_KEY` | Clé Google Gemini | non |
| `PROJECT_ROOT` | Dossier racine autorisé pour les opérations fichiers | non |
| `ALLOWED_ORIGINS` | Origines CORS autorisées | non |
| `SESSIONS_DB` | Chemin de la base SQLite | non |

## Structure

```
AgentTest/
├── backend/
│   ├── app/
│   │   ├── api/          # Routes : chat (SSE), crews, models, workspace
│   │   ├── core/         # Router, crew_runner, crew_manager, path_manager, config
│   │   ├── schemas/      # Modèles Pydantic
│   │   └── tools/        # Outils CrewAI (fichiers, terminal, web, PDF)
│   ├── config/
│   │   ├── crews/        # Définitions YAML des Crews
│   │   └── capabilities.json
│   └── tests/            # Tests pytest
├── frontend/
│   ├── app/              # Pages Next.js
│   ├── components/       # chat/, sidebar/, ui/
│   ├── e2e/              # Tests Playwright
│   └── lib/              # Client API SSE, store, types
├── desktop/              # Application Electron
└── docs/
```

## Crews

Les Crews sont des fichiers YAML dans `backend/config/crews/`. Pour en ajouter un, copiez un fichier existant et adaptez agents, tâches et settings.

Quelques exemples : `Autonomous_SWE`, `Reviewer`, `Tester`, `Project_Architect`, `Security_Adversary`, `Web_Researcher`, `InteractiveCourseCreator`, `dev_assistant`.

## API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/models` | Modèles LLM disponibles |
| POST | `/api/chat` | Chat avec streaming SSE |
| GET | `/api/crews` | Liste des Crews |
| GET | `/api/crews/{name}` | Détail d'un Crew |
| POST | `/api/crews` | Créer un Crew |
| DELETE | `/api/crews/{name}` | Supprimer un Crew |
| GET | `/api/workspace/projects` | Projets détectés |
| GET | `/api/workspace/browse` | Navigation fichiers sécurisée |

Voir [backend/README.md](backend/README.md) et [backend/docs/api.md](backend/docs/api.md).

## Tests

```bash
# Backend
PYTHONPATH=backend .venv/bin/pytest backend/tests --tb=short --maxfail=1

# Frontend
cd frontend && CI=true npm run lint
cd frontend && npm run test       # e2e Playwright
cd frontend && CI=true npm run build
```

## Build desktop

```bash
cd desktop
npm run build   # installeurs dans desktop/dist/
```

## Contribution

1. Fork, branche (`git checkout -b feature/ma-feature`)
2. Commit, push, pull request

Voir [AGENTS.md](AGENTS.md) pour les conventions du projet.

## Licence

MIT — voir [LICENSE](LICENSE).
