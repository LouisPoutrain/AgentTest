# Documentation Technique de l'API AgentTest

Ce document fournit une référence technique détaillée pour l'API **AgentTest API**. Il couvre les schémas de données, les points d'entrée, et la logique métier sous-jacente.

## 1. Point d'Entrée et Configuration Globale

- **Base URL** : `/api`
- **Format de Données** : JSON
- **Streaming** : Supporté via Server-Sent Events (SSE) uniquement sur l'endpoint `/chat`.
- **Middleware** :
  - **CORS** : Gestion des origines via `ALLOWED_ORIGINS` (défaut : `localhost:3000`).
  - **Erreur** : Retour systématique de JSON pour les erreurs 500 via `global_exception_handler`.

## 2. Schémas de Données

### 2.1 Chat (`app/schemas/chat.py`)

**ChatRequest**
Requête envoyée à l'endpoint `/api/chat`.

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :--- | :--- |
| `message` | `string` | Oui | Le message de l'utilisateur. |
| `session_id` | `string` | Non | Identifiant de session pour l'historique. |
| `crew_name` | `string` | Non | Nom spécifique du Crew à utiliser. |
| `inputs` | `dict` | Non | Paramètres dynamiques pour le Crew. |
| `llm_override` | `string` | Non | Clé pour utiliser un modèle LLM spécifique. |
| `max_rpm` | `int` | Non | Limite de requêtes par minute pour le LLM. |

### 2.2 Crews (`app/schemas/crews.py`)

**CrewCreate**
Utilisé pour créer un nouveau Crew (`POST /api/crews`).

| Champ | Type | Description |
| :--- | :--- | :--- |
| `name` | `string` | Nom unique du Crew. |
| `agents` | `list[AgentCreate]` | Liste des agents associés. |
| `tasks` | `list[TaskCreate]` | Liste des tâches associées. |
| `settings` | `dict` | Paramètres globaux (process, memory, etc.). |

**CrewResponse**
Réponse retournée lors de la récupération ou de la création d'un Crew.

| Champ | Type | Description |
| :--- | :--- | :--- |
| `name` | `string` | Nom du Crew. |
| `agents` | `list` | Détails des agents. |
| `tasks` | `list` | Détails des tâches. |
| `settings` | `dict` | Paramètres actuels. |

**AgentCreate / TaskCreate**
Schémas pour ajouter ou mettre à jour des agents/tâches individuels. Ils contiennent les définitions standard d'agent/tâche (nom, rôle, description, etc.).

**GitImportRequest**
Utilisé pour l'importation de Crews (`POST /api/crews/{name}/import`).

| Champ | Type | Description |
| :--- | :--- | :--- |
| `url` | `string` | URL GitHub du fichier YAML. |

## 3. Endpoints Détaillés

### 3.1 Santé et Modèles LLM

- **`GET /api/health`**
  - **Description** : Vérifie si le service est en ligne.
  - **Réponse Succès (200)** :
    ```json
    { "status": "ok" }
    ```

- **`GET /api/models`**
  - **Description** : Liste les modèles LLM disponibles et configurés.
  - **Réponse Succès (200)** :
    ```json
    [ "gpt-4", "gpt-3.5-turbo", "claude-2" ]
    ```

### 3.2 Chat et Orchestration

- **`POST /api/chat`**
  - **Description** : Point d'entrée principal pour l'interaction utilisateur. Le système utilise un *Meta-Routeur* (LLM) pour décider de l'action : réponse directe, demande de clarification, ou exécution d'un Crew.
  - **Réponse Succès (200)** : Flux SSE.
    - Type `log` : Messages de progression.
    - Type `result` : Réponse finale de l'agent.
    - Type `session_info` : Informations sur la session.

### 3.3 Gestion des Crews

Préfixe : `/api/crews`

#### Endpoints CRUD Principaux

| Méthode | Endpoint | Description | Payload / Réponse |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Liste les noms des Crews. | `list[str]` |
| `GET` | `/{name}` | Détails d'un Crew. | `CrewResponse` |
| `POST` | `/` | Crée un Crew. | `CrewCreate` |
| `DELETE` | `/{name}` | Supprime un Crew. | 204 No Content |
| `PUT` | `/{name}/settings` | Met à jour les paramètres. | `dict` (settings) |

#### Endpoints Agents (Sous-Crew)

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/{name}/agents` | Ajoute un agent au Crew. |
| `PUT` | `/{name}/agents/{index}` | Met à jour l'agent à l'index donné. |
| `DELETE` | `/{name}/agents/{index}` | Supprime l'agent à l'index donné. |

#### Endpoints Tâches (Sous-Crew)

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/{name}/tasks` | Ajoute une tâche au Crew. |
| `PUT` | `/{name}/tasks/{index}` | Met à jour la tâche à l'index donné. |
| `DELETE` | `/{name}/tasks/{index}` | Supprime la tâche à l'index donné. |

#### Endpoints Spécifiques

- **`GET /all/agents`** : Retourne une liste unique de tous les agents définis dans tous les Crews.
- **`GET /tools/available`** : Retourne la liste des noms d'outils (tools) disponibles dans l'environnement (`get_tool_names`).
- **`POST /{name}/import`** : Importe la configuration d'un Crew depuis une source externe (YAML GitHub). Attend `GitImportRequest`.

### 3.4 Espace de Travail (Workspace)

Préfixe : `/api/workspace`

- **`GET /projects`**
  - **Description** : Analyse le système de fichiers pour détecter les projets.
  - **Logique** : Cherche dans la racine et les sous-dossiers `frontend`/`backend` (ou frères dans `WORKSPACE_ROOT`).
  - **Détection** : Identifie les stacks (Next.js, React, Python, FastAPI, etc.).
  - **Réponse** : Liste des projets détectés avec leurs métadonnées.

- **`GET /browse`**
  - **Description** : Navigation sécurisée dans l'arborescence des fichiers.
  - **Sécurité** : Utilise `_resolve_safe_path` pour empêcher les traversées de répertoires (`../`).
  - **Réponse** :
    ```json
    {
      "path": "/current/path",
      "breadcrumbs": ["root", "subdir"],
      "items": [
        { "name": "file.txt", "type": "file" },
        { "name": "dir", "type": "directory" }
      ]
    }
    ```

## 4. Core System Internals

### 4.1 Router (`app/core/router.py`)

Fonction principale : `route_request(session_id, user_message, context_inputs)`

1. **Build System Prompt** : Appelle `build_system_prompt()` pour inclure les descriptions des Crews disponibles.
2. **LLM Call** : Interroge le modèle LLM via `get_model_for_tier(tier)` (fast, balanced, expert) pour obtenir une décision JSON.
3. **Parse & Execute** :
   - Si `direct_reply` : Génère une réponse simple.
   - Si `ask_clarification` : Demande des informations complémentaires.
   - Si `call_crew` : Délègue à `app.core.crew_runner.run_crew` pour l'exécution de la tâche multi-agent.

### 4.2 History Manager (`app/core/history_manager.py`)

- Gère la persistance des conversations.
- Associe les historiques aux `session_id`.
- Utilisé par le module Chat pour maintenir le contexte.

### 4.3 Crew Manager (`app/core/crew_manager.py`)

- CRUD simple pour les fichiers de configuration des Crews (JSON/YAML).
- Assure la cohérence des données lors des mises à jour d'agents ou de tâches.

### 4.4 Crew Runner (`app/core/crew_runner.py`)

- Exécute les instances CrewAI.
- Retourne des chunks de résultats au fur et à mesure de l'avancement, permettant le streaming SSE.
