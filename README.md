# Agent Zouglou

**AI Orchestration Platform** — Chattez avec un meta-routeur intelligent qui dispatche automatiquement vos demandes vers des équipes d'agents spécialisés (Crews), avec streaming SSE en temps réel.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────────┐
│   Frontend   │────▶│  Meta-Router  │────▶│  Crew 1  ──▶  Crew 2   │
│  Next.js 16  │◀────│   (FastAPI)   │◀────│  (CrewAI agents + tools)│
│  React 19    │ SSE │               │     └─────────────────────────┘
└─────────────┘     └──────────────┘
       ▲
       └──── Electron 32 (Desktop app macOS / Windows / Linux)
```

---

## ✨ Features

- **💬 Chat intelligent** — Un routeur LLM analyse chaque message et décide : réponse directe, clarification, outil individuel, ou dispatch vers un Crew
- **👥 Crews déclaratifs** — Définissez des équipes d'agents en YAML (rôles, goals, backstories, outils, modèles LLM)
- **🔄 Multi-crew** — Exécutez plusieurs Crews séquentiellement ou en parallèle sur la même demande
- **📡 Streaming SSE** — Logs en temps réel des agents (pensées, appels d'outils, résultats) directement dans l'UI
- **🖥️ Desktop app** — Application Electron native qui lance backend + frontend automatiquement
- **📁 Workspace browsing** — Sélectionnez un dossier projet, l'agent y lit/écrit en toute sécurité (path sandboxing)
- **🗂️ Historique** — Conversations persistées en SQLite, rechargeables à tout moment
- **🧩 20+ Crews préconfigurés** — SWE autonome, review, tests, sécurité, recherche web, création de cours, analyse JSON, Git, et plus

---

## 🛠️ Stack Technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Python 3.12 · FastAPI · CrewAI · LiteLLM · Pydantic · SQLite |
| **Frontend** | Next.js 16 · React 19 · Tailwind CSS v4 · Zustand · Framer Motion · shadcn/ui |
| **Desktop** | Electron 32 · Node.js |
| **LLM** | Compatible LiteLLM (OpenAI, Gemini, Mistral, Ollama, etc.) |

---

## 🚀 Quick Start

### Prérequis

- Python 3.12+
- Node.js 20+
- Une clé API LLM (OpenAI, Gemini, Mistral, ou autre provider LiteLLM)

### 1. Cloner le projet

```bash
git clone <repository-url>
cd AgentTest
```

### 2. Configurer le backend

```bash
# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Installer les dépendances
pip install -r backend/requirements.txt

# Configurer les variables d'environnement
cp backend/.env.example backend/.env
# Éditez backend/.env avec votre clé API LLM
```

### 3. Lancer l'application

**Option A — Desktop (recommandé)** :
```bash
cd desktop
npm install
npm start
```
L'app Electron démarre automatiquement le backend (port 8000) et le frontend (port 3000).

**Option B — Manuel (dev)** :
```bash
# Terminal 1 — Backend
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```
Puis ouvrez [http://localhost:3000](http://localhost:3000).

---

## ⚙️ Configuration

Créez `backend/.env` à partir de `backend/.env.example` :

| Variable | Description | Requis |
|----------|-------------|--------|
| `LLM_API_KEY` | Clé API de votre provider LLM | ✅ |
| `LLM_BASE_URL` | URL de base de l'API LLM (ex: `https://api.openai.com/v1`) | ✅ |
| `GEMINI_API_KEY` | Clé API Google Gemini (optionnel) | ❌ |
| `PROJECT_ROOT` | Dossier racine autorisé pour les opérations fichiers | ❌ (défaut: repo) |
| `ALLOWED_ORIGINS` | Origines CORS autorisées | ❌ (défaut: localhost:3000) |
| `SESSIONS_DB` | Chemin de la base SQLite | ❌ (défaut: `sessions.db`) |

Voir [backend/.env.example](backend/.env.example) pour le template complet.

---

## 📁 Structure du projet

```
AgentTest/
├── backend/                  # API FastAPI + orchestration CrewAI
│   ├── app/
│   │   ├── api/              # Routes: chat (SSE), crews CRUD, models, workspace
│   │   ├── core/             # Router, crew_runner, crew_manager, path_manager, config
│   │   ├── schemas/          # Modèles Pydantic
│   │   └── tools/            # Outils CrewAI sandboxés (fichiers, terminal, web, PDF...)
│   ├── config/
│   │   ├── crews/*.yaml      # 20+ définitions de Crews
│   │   └── capabilities.json # Routing par mots-clés + model tiers
│   ├── tests/                # Suite pytest (9 modules)
│   └── requirements.txt
├── frontend/                 # Next.js 16 + React 19
│   ├── app/                  # Pages (chat, lots, lab)
│   ├── components/
│   │   ├── chat/             # ChatWindow, CrewLaunchPad, MessageBubble, etc.
│   │   ├── sidebar/          # NavigationSidebar, CrewConfig
│   │   └── ui/               # Composants shadcn/ui
│   ├── e2e/                  # Tests Playwright
│   └── lib/                  # api.ts (SSE client), store.ts, types.ts
├── desktop/                  # Electron 32 (main.js lance backend + frontend)
├── docs/                     # Documentation développeur
│   └── dev/                  # Notes internes (plans, migrations)
└── sessions.db               # Historique des conversations (SQLite)
```

---

## 🤖 Crews disponibles

Les Crews sont définis en YAML dans `backend/config/crews/`. Exemples :

| Crew | Spécialisation |
|------|---------------|
| `Autonomous_SWE` | Développement logiciel de bout en bout |
| `Reviewer` | Audit de code et sécurité |
| `Tester` | Tests automatisés et détection de régressions |
| `Project_Architect` | Conception d'architecture et choix de stack |
| `Refactorer` | Clean code et réduction de dette technique |
| `Documentaliste` | Documentation technique |
| `Security_Adversary` | Pentesting et simulation d'attaques |
| `Web_Researcher` | Recherche web et synthèse |
| `InteractiveCourseCreator` | Création de cours interactifs depuis des PDF |
| `dev_assistant` | Assistant développeur généraliste |

Pour créer votre propre Crew, copiez un YAML existant et modifiez-le — aucune code requis.

---

## 🌐 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/models` | Liste des modèles LLM disponibles |
| `POST` | `/api/chat` | Chat avec streaming SSE (multi-crew supporté) |
| `GET` | `/api/crews` | Liste des Crews |
| `GET` | `/api/crews/{name}` | Détails d'un Crew (agents, tâches, settings) |
| `POST` | `/api/crews` | Créer un Crew |
| `DELETE` | `/api/crews/{name}` | Supprimer un Crew |
| `GET` | `/api/workspace/projects` | Lister les projets détectés |
| `GET` | `/api/workspace/browse` | Navigation sécurisée dans les fichiers |

Documentation détaillée : [backend/README.md](backend/README.md) · [backend/docs/api.md](backend/docs/api.md)

---

## 🧪 Tests

```bash
# Backend (pytest)
PYTHONPATH=backend .venv/bin/pytest backend/tests --tb=short --maxfail=1

# Frontend (lint)
cd frontend && CI=true npm run lint

# Frontend (e2e Playwright)
cd frontend && npm run test

# Frontend (build)
cd frontend && CI=true npm run build
```

---

## 🖥️ Build Desktop

```bash
cd desktop
npm install
npm run build   # Génère les installeurs dans desktop/dist/
```

---

## 🤝 Contribuer

1. Fork le projet
2. Créez une branche (`git checkout -b feature/ma-feature`)
3. Commitez vos changements (`git commit -m 'feat: ma feature'`)
4. Push (`git push origin feature/ma-feature`)
5. Ouvrez une Pull Request

Consultez [AGENTS.md](AGENTS.md) pour les conventions de code et le protocole de qualité.

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE)

---

*Développé avec ❤️ et beaucoup de ☕*
