# AgentTest API

Bienvenue dans la documentation de **AgentTest API**. Cette application est une API RESTful construite avec **FastAPI**, conçue pour orchestrer des agents IA (Crews) et gérer des interactions complexes via un routeur intelligent.

## 📋 Table des Matières

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
  - [Santé & Modèles](#santé--modèles)
  - [Chat & Orchestration](#chat--orchestration)
  - [Gestion des Crews](#gestion-des-crews)
  - [Espace de Travail](#espace-de-travail)
- [Sécurité](#sécurité)

## 🏗️ Architecture

L'API repose sur plusieurs modules clés :

1. **Orchestration IA (`app/core/router.py`)** : Un meta-routeur basé sur LLM qui analyse les messages utilisateurs pour décider de l'action appropriée (réponse directe, clarification ou exécution d'un Crew).
2. **Gestion des Crews (`app/api/crews.py`)** : Permet de créer, modifier et supprimer des équipes d'agents IA (Crews) et leurs tâches associées.
3. **Espace de Travail (`app/api/workspace.py`)** : Fournit des outils pour naviguer dans le système de fichiers et détecter automatiquement les projets (Next.js, React, Python, etc.).
4. **Historique (`app/core/history_manager.py`)** : Gère la persistance des conversations par session.

## 🚀 Installation

1. Clonez le dépôt :
   ```bash
   git clone <repository-url>
   cd agent-test-api
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurez les variables d'environnement (voir ci-dessous).

4. Lancez le serveur :
   ```bash
   uvicorn app.main:app --reload
   ```

## ⚙️ Configuration

L'application nécessite les variables d'environnement suivantes pour fonctionner correctement :

| Variable | Description | Défaut |
| :--- | :--- | :--- |
| `LLM_API_KEY` | Clé API pour le modèle LLM principal | - |
| `LLM_BASE_URL` | URL de base de l'API LLM | - |
| `ALLOWED_ORIGINS` | Origines CORS autorisées | `localhost:3000` |

## 🌐 API Endpoints

L'API expose plusieurs points d'entrée sous le préfixe `/api`.

### Santé & Modèles

- **`GET /api/health`** : Vérifie l'état de santé de l'application.
  - *Réponse* : `{ "status": "ok" }`

- **`GET /api/models`** : Liste les modèles LLM disponibles.
  - *Réponse* : Liste de chaînes de caractères (`list[str]`).

### Chat & Orchestration

- **`POST /api/chat`** : Point d'entrée principal pour interagir avec l'agent IA.
  - *Méthode* : POST
  - *Streaming* : Supporte le streaming Server-Sent Events (SSE).
  - *Payload* : `ChatRequest` (message, session_id, crew_name, inputs, llm_override, max_rpm).
  - *Réponse* : Chunks SSE de type `log`, `result`, ou `session_info`.

### Gestion des Crews

Gère les équipes d'agents IA via le préfixe `/api/crews`.

#### Endpoints Principaux
- **`GET /`** : Liste les noms de tous les Crews.
- **`GET /{name}`** : Récupère les détails d'un Crew spécifique.
- **`POST /`** : Crée un nouveau Crew.
- **`DELETE /{name}`** : Supprime un Crew existant.
- **`PUT /{name}/settings`** : Met à jour les paramètres globaux (process, memory, max_rpm).

#### Sous-Endpoints (Agents & Tâches)
- **Agents** :
  - `POST /{name}/agents` : Ajouter un agent.
  - `PUT /{name}/agents/{index}` : Mettre à jour un agent.
  - `DELETE /{name}/agents/{index}` : Supprimer un agent.
- **Tâches** :
  - `POST /{name}/tasks` : Ajouter une tâche.
  - `PUT /{name}/tasks/{index}` : Mettre à jour une tâche.
  - `DELETE /{name}/tasks/{index}` : Supprimer une tâche.

#### Autres
- **`GET /all/agents`** : Liste tous les agents uniques de tous les Crews.
- **`POST /{name}/import`** : Importe un Crew depuis un fichier YAML GitHub.
- **`GET /tools/available`** : Liste les outils disponibles.

### Espace de Travail

Préfixe : `/api/workspace`

- **`GET /projects`** : Détecte et liste les projets dans l'espace de travail. Identifie automatiquement les stacks techniques (Next.js, React, Python, FastAPI, etc.).
- **`GET /browse`** : Navigation sécurisée dans le système de fichiers. Retourne les répertoires, fichiers et le fil d'Ariane (breadcrumbs).

## 🔒 Sécurité

- **CORS** : Configurée dynamiquement via `ALLOWED_ORIGINS`.
- **Gestion des Erreurs** : Un gestionnaire global retourne des réponses JSON en cas d'erreur 500.
- **Sécurité des Chemins** : L'endpoint `/api/workspace/browse` utilise une résolution de chemin sécurisée (`_resolve_safe_path`) pour prévenir les attaques par traversal de répertoires.
- **BrokenPipeError** : Protection contre les interruptions de connexion stdout/stderr.

---

*Pour plus de détails techniques sur les schémas de données et l'implémentation, consultez `docs/api.md`.*
