# AGENTS.md — Agent Zouglou (AgentTest)

AI Orchestration Platform powered by **FastAPI + CrewAI** (Backend), **Next.js 16 + React 19 + Tailwind v4** (Frontend), and **Electron 32** (Desktop).

---

## ⚡ Essential Commands

### Development Servers
- **Backend**: `cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000` (or from root: `PYTHONPATH=backend .venv/bin/uvicorn app.main:app --reload --port 8000`)
- **Frontend**: `cd frontend && npm run dev` (runs on `http://localhost:3000`)
- **Desktop**: `cd desktop && npm start` (spawns both backend & frontend, waits for `/api/health`)

### Verification & Testing (Mandatory after changes)
- **Backend Tests (Concise & Context-Safe)**: `PYTHONPATH=backend .venv/bin/pytest backend/tests --tb=short --maxfail=1`
- **Single Backend Test**: `PYTHONPATH=backend .venv/bin/pytest backend/tests/test_router.py -v --tb=short`
- **Frontend Linting (Non-interactive CI mode)**: `cd frontend && CI=true npm run lint`
- **Frontend Typecheck / Build (CI mode)**: `cd frontend && CI=true npm run build`
- **Desktop Packaging**: `cd desktop && npm run build`

---

## 🧭 Cognitive Protocol: Error Prevention & Quality

Follow this 4-step execution loop for every task to avoid hallucinations and regressions:

1. **Reconnaissance First (Read before Write)**:
   - Always read existing files and type definitions before writing new code.
   - Never assume function signatures, schemas, or library versions.
   - Inspect `frontend/lib/types.ts` for frontend data contracts and `backend/app/schemas/` for backend models.

2. **Surgical & Minimal Diffs**:
   - Make precise edits targeted strictly at the requested change.
   - Never rewrite an entire file when changing a function.
   - Preserve existing comments, docstrings, and formatting.
   - Do not install new dependencies without checking existing ones in `requirements.txt` or `package.json`.

3. **Mandatory Verification Loop**:
   - After modifying Python code: immediately run `PYTHONPATH=backend .venv/bin/pytest <targeted_test> --tb=short`.
   - After modifying TypeScript/React code: immediately run `cd frontend && CI=true npm run lint`.
   - Do not consider a task complete until verification passes.

4. **Fail Loud & Root-Cause Diagnosis**:
   - If a test or command fails, do not write quick workarounds (e.g. `try: ... except: pass`).
   - Identify and fix the actual root cause. If requirements are ambiguous, ask rather than guess.

---

## 🛑 Hard Guardrails & Known Pitfalls (The "Never Do" List)

### 1. Python & Environment
- **NEVER** use system `python` or system `pytest`. Always use `.venv/bin/python` and `.venv/bin/pytest` (located at repository root).
- **ALWAYS** export or prefix `PYTHONPATH=backend` before running Python tests/scripts, or `ModuleNotFoundError: No module named 'app'` will occur.
- **ALWAYS** add `--tb=short` (or `--maxfail=1`) to pytest to prevent giant stack traces from exhausting the context window.
- The project uses a **single unified venv** at the root (`.venv/`). There is no longer a `backend/.venv/`.
- **NEVER** remove `install_safe_streams()` in `backend/app/main.py` — it prevents `BrokenPipeError` during SSE streaming.

### 2. Path & Command Security
- **NEVER** use raw path concatenation or arbitrary file writes. All file operations MUST go through `PathManager.resolve()` or `safe_resolve()` in `app/core/path_manager.py` to prevent directory traversal outside `PROJECT_ROOT`.
- **NEVER** execute shell commands directly inside custom tools without passing through the security whitelist in `app/tools/custom_tools.py` (`_SAFE_COMMAND_PREFIXES`).

### 3. React 19 & Next.js 16 (App Router)
- **ALWAYS** use absolute import aliases (`@/components/...`, `@/lib/...`, `@/app/...`) defined in `tsconfig.json`. **NEVER** use fragile deep relative imports (e.g. `../../../../components/ui/button`).
- **ALWAYS** run frontend scripts with `CI=true` (e.g. `CI=true npm run lint`) to prevent interactive prompts or warnings from blocking the agent.
- **NEVER** read or write `ref.current` during component rendering (e.g. `if (ref.current !== val)` in component body). In React 19, this triggers strict compiler errors and breaks hydration. Use `useEffect` or functional state instead.
- **NEVER** downgrade Tailwind syntax — frontend uses **Tailwind CSS v4** (`@tailwindcss/postcss`).
- Keep components split cleanly: `components/chat/`, `components/sidebar/`, `components/ui/`.

### 4. SSE Streaming Contract (`/api/chat`)
- The Server-Sent Events stream relies on strict JSON chunks with `type: "session_info" | "log" | "result" | "error"`.
- Any modification to SSE payload schema must be coordinated synchronously between `backend/app/api/chat.py` and `frontend/lib/api.ts`.

### 5. Electron Process Lifecycle
- In `desktop/main.js`, both `backendProcess` and `frontendProcess` must always be killed using `tree-kill(pid)` on `before-quit`. Never leave orphan background processes holding ports 8000 or 3000.

---

## 🏗️ Architecture & Component Map

```
AgentTest/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py       # POST /api/chat (SSE streaming orchestrator)
│   │   │   ├── crews.py      # CRUD endpoints for Crews, Agents, and Tasks
│   │   │   ├── models.py     # GET /api/models (lists available LLM models)
│   │   │   └── workspace.py  # GET /api/workspace/projects & /browse (path-safe)
│   │   ├── core/
│   │   │   ├── router.py     # LLM Meta-Router (direct answer, clarify, or crew dispatch)
│   │   │   ├── crew_runner.py# CrewAI runner executing agents & streaming logs
│   │   │   ├── crew_manager.py # Crew YAML loader, validator, and serializer
│   │   │   ├── path_manager.py # PathManager sandbox preventing path traversal
│   │   │   └── history_manager.py # SQLite session persistence (sessions.db)
│   │   └── tools/
│   │       └── custom_tools.py # Sandboxed CrewAI tools (file read/write, search, tests)
│   ├── config/
│   │   ├── capabilities.json # Metadata and model tier assignments (fast, balanced, expert)
│   │   └── crews/*.yaml      # Declarative CrewAI configurations
│   └── tests/                # Comprehensive pytest suite
│
├── frontend/
│   ├── app/                  # Next.js App Router (layout.tsx, page.tsx)
│   ├── components/
│   │   ├── chat/             # ChatWindow, CrewLaunchPad, LogViewer, MessageList
│   │   ├── sidebar/          # Sidebar, CrewConfig, FolderSelector
│   │   └── ui/               # Radix UI, Base UI, Shadcn primitives
│   └── lib/
│       ├── api.ts            # Typed SSE client & REST fetchers
│       ├── store.ts          # Zustand state (conversations, folder context)
│       └── types.ts          # TypeScript interfaces (ChatMessage, CrewDetail, etc.)
│
├── desktop/
│   └── main.js               # Electron entrypoint, subprocess supervisor, healthcheck
│
└── sessions.db               # SQLite database for persistent conversation history
```

---

## 🛠️ Adding or Modifying a Crew

Crews are declaratively defined in `backend/config/crews/<Crew_Name>.yaml`:

```yaml
name: ExampleCrew
description: Clear, single-sentence summary of the crew's specialization
crew_settings:
  process: Séquentiel      # Options: Séquentiel | Hiérarchique
  memory: true
  max_rpm: 15
agents:
  - name: ExpertAgent
    role: Specialist Role
    goal: Clear, actionable objective
    backstory: Domain background that steers tone and expertise
    llm: openai/qwen-3.6-35b-instruct
    tools: [read_file, write_file, search_code, run_test_command]
    verbose: true
    allow_delegation: false
tasks:
  - description: Detailed task description with {input_variables}
    expected_output: Exact expected output format
    agent: ExpertAgent
```

When creating a new crew, register it in `backend/config/capabilities.json` if custom model tiers or UI categories are needed.

---

## 🔐 Environment Configuration

Stored in `backend/.env` (never commit secret values):
- `LLM_API_KEY`: API key for LLM provider (LiteLLM / OpenAI / local proxy).
- `LLM_BASE_URL`: Base URL for LLM endpoint.
- `GEMINI_API_KEY`: Google Gemini API key (optional).
- `ALLOWED_ORIGINS`: Allowed CORS origins (`http://localhost:3000,http://127.0.0.1:3000`).
- `PROJECT_ROOT`: Root workspace directory (defaults to repository root).
- `SESSIONS_DB`: Path to SQLite database (`sessions.db`).

## 🎨 UI/UX & Design Sourcing Protocol

L'objectif est d'avoir une UI de niveau "Premium SaaS". Ne génère JAMAIS de design Tailwind basique de ton propre chef.

1. **Design Inspiration via GitHub MCP :**
   - Lorsque je te demande de créer un nouveau composant (ex: un beau tableau de bord, une landing page, une sidebar animée), tu DOIS utiliser l'outil GitHub pour chercher l'implémentation dans des dépôts de référence publics.
   - **Dépôts cibles recommandés :** `shadcn-ui/ui`, `aceternity/ui`, `magicuidesign/magicui`, ou `tremorlabs/tremor`.

2. **Extraction et Adaptation :**
   - Cherche les fichiers `.tsx` pertinents dans ces dépôts via `search_repositories` ou `search_code`.
   - Lis le code source de leur composant.
   - Adapte strictement leur code pour qu'il soit compatible avec **React 19** (pas de `ref.current` dans le render) et **Tailwind v4** (utilise la nouvelle syntaxe `@tailwindcss/postcss`).
   - Intègre ce design de pointe dans `frontend/components/ui/`.