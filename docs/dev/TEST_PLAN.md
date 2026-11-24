# Plan de Test — Agent Test

> **Périmètre** : Intégration Frontend ↔ Backend + Fonctionnement autonome du Frontend
> **Prérequis** : Backend (`uvicorn`) + Frontend (`next dev`) + (optionnel) Desktop (`electron`) lancés

---

## 1. Connexion & Santé du Backend

| # | Test | Méthode | Résultat attendu |
|---|------|---------|-----------------|
| 1.1 | **Healthcheck** | `GET http://127.0.0.1:8000/api/health` | `{ "status": "ok", "api_key_set": true }` |
| 1.2 | **Frontend détecte backend down** | Couper le backend, rafraîchir le frontend | Message d'erreur "Impossible de charger la liste des Crews" + bouton "Réessayer" |
| 1.3 | **Frontend se reconnecte** | Relancer le backend, cliquer "Réessayer" | La liste des crews se charge, le message d'erreur disparaît |

---

## 2. CRUD Crews (REST)

| # | Test | Méthode | Résultat attendu |
|---|------|---------|-----------------|
| 2.1 | **Liste des crews** | `GET /api/crews` | Tableau de noms de crews (ex: `["default", "ProjectArchitect", ...]`) |
| 2.2 | **Détail d'un crew** | `GET /api/crews/default` | Objet `CrewDetail` avec `name`, `crew_settings`, `agents[]`, `tasks[]` |
| 2.3 | **Crew inexistant** | `GET /api/crews/nonexistent` | 404 avec `{ "detail": "Crew 'nonexistent' introuvable." }` |
| 2.4 | **Créer un crew** | `POST /api/crews` `{ "name": "TestCrew", "settings": {} }` | 201 + `CrewDetail` créé sur disque (`config/crews/TestCrew.yaml`) |
| 2.5 | **Duplication** | `POST /api/crews` avec le même nom | 409 `{ "detail": "Le Crew 'TestCrew' existe déjà." }` |
| 2.6 | **Modifier settings** | `PUT /api/crews/TestCrew/settings` `{ "process": "Hiérarchique" }` | 200 + settings mis à jour dans le YAML |
| 2.7 | **Supprimer un crew** | `DELETE /api/crews/TestCrew` | 204 + fichier YAML supprimé |
| 2.8 | **Ajouter un agent** | `POST /api/crews/TestCrew/agents` `{ "name": "A1", "role": "...", "goal": "...", "backstory": "...", "llm": "gemini/gemini-2.5-flash", "tools": [] }` | 201 + agent ajouté dans le YAML |
| 2.9 | **Modifier un agent** | `PUT /api/crews/TestCrew/agents/0` | 200 + agent index 0 mis à jour |
| 2.10 | **Supprimer un agent** | `DELETE /api/crews/TestCrew/agents/0` | 200 + agent supprimé |
| 2.11 | **Ajouter une tâche** | `POST /api/crews/TestCrew/tasks` `{ "description": "...", "expected_output": "...", "agent": "A1" }` | 201 + tâche ajoutée |
| 2.12 | **Modifier une tâche** | `PUT /api/crews/TestCrew/tasks/0` | 200 + tâche mise à jour |
| 2.13 | **Supprimer une tâche** | `DELETE /api/crews/TestCrew/tasks/0` | 200 + tâche supprimée |
| 2.14 | **Liste agents globaux** | `GET /api/crews/all/agents` | Tableau d'objets agents uniques de tous les crews |
| 2.15 | **Liste outils disponibles** | `GET /api/crews/tools/available` | Tableau de strings (ex: `["read_file", "write_file", ...]`) |
| 2.16 | **Liste modèles** | `GET /api/models` | Tableau de strings de modèles (ex: `["gemini/gemini-2.5-flash", ...]`) |

---

## 3. Chat SSE (Cœur du système)

### 3a. Réponse directe (Meta-Routeur — pas de crew)

| # | Test | Méthode | Résultat attendu |
|---|------|---------|-----------------|
| 3.1 | **Message simple (default)** | `POST /api/chat` `{ "crew_name": "default", "message": "Bonjour" }` | SSE stream avec chunks `session_info` → `log` → `result` |
| 3.2 | **Chunk session_info** | Parser le premier chunk SSE | `{ "type": "session_info", "content": "<uuid>", "session_id": "<uuid>" }` |
| 3.3 | **Chunk log** | Parser un chunk intermédiaire | `{ "type": "log", "content": "[Réflexion] ...", "timestamp": "..." }` |
| 3.4 | **Chunk result** | Parser le dernier chunk | `{ "type": "result", "content": "Réponse finale...", "timestamp": "..." }` |
| 3.5 | **Chunk error** | Envoyer un message qui provoque une erreur LLM | `{ "type": "error", "content": "Message d'erreur...", "timestamp": "..." }` |
| 3.6 | **Abort du stream** | Envoyer le message, puis appeler `controller.abort()` | Le stream s'arrête proprement, pas d'exception côté frontend |
| 3.7 | **Override LLM** | `POST /api/chat` avec `{ "llm_override": "gemini/gemini-2.5-flash" }` | Le crew utilise le modèle spécifié |
| 3.8 | **Override LLM invalide** | `POST /api/chat` avec `{ "llm_override": "invalid/model" }` | 400 `{ "detail": "Modèle LLM non autorisé." }` |
| 3.9 | **Session persistante** | Envoyer 2 messages avec le même `session_id` | Le 2ème message a le contexte du 1er (history_manager) |
| 3.10 | **Meta-Routeur — dispatch crew** | Envoyer "Fais un audit de sécurité de mon code" | Le routeur détecte l'intention et dispatch vers le crew approprié |
| 3.11 | **Meta-Routeur — clarification** | Envoyer une demande ambiguë | Le routeur répond avec `action: "ask_clarification"` |
| 3.12 | **Meta-Routeur — réponse directe** | Envoyer "Quel temps fait-il ?" (hors scope crew) | Le routeur répond directement sans dispatcher vers un crew |

### 3b. Exécution manuelle de crew

| # | Test | Méthode | Résultat attendu |
|---|------|---------|-----------------|
| 3.13 | **Lancer un crew nommé** | `POST /api/chat` `{ "crew_name": "ProjectArchitect", "message": "Crée un plan pour..." }` | Stream avec `[Exécution Manuelle] Lancement du crew ProjectArchitect` |
| 3.14 | **Crew avec inputs** | `POST /api/chat` `{ "crew_name": "default", "inputs": { "project_path": "./frontend" } }` | Le crew reçoit les inputs dans sa tâche |
| 3.15 | **Crew avec max_rpm** | `POST /api/chat` `{ "crew_name": "default", "max_rpm": 5 }` | Le crew respecte la limite de 5 RPM |

---

## 4. Workspace & Navigation

| # | Test | Méthode | Résultat attendu |
|---|------|---------|-----------------|
| 4.1 | **Liste des projets** | `GET /api/workspace/projects` | Tableau de `ProjectInfo` (projet courant + sous-dossiers + projets frères) |
| 4.2 | **Détection stack** | Vérifier un projet Next.js dans la réponse | `framework: "Next.js"`, `tags` incluant `"Next.js"`, `"TypeScript"`, `"Tailwind"` |
| 4.3 | **Explorer le dossier courant** | `GET /api/workspace/browse?path=.` | `BrowseResponse` avec `directories[]`, `files_count`, `breadcrumbs[]` |
| 4.4 | **Explorer un sous-dossier** | `GET /api/workspace/browse?path=./frontend` | Retourne le contenu du dossier frontend |
| 4.5 | **Breadcrumbs** | Naviguer dans `./frontend/components/chat` | Breadcrumbs: `["Code", "AgentTest", "frontend", "components", "chat"]` |
| 4.6 | **Dossier inexistant** | `GET /api/workspace/browse?path=/nonexistent` | 404 `{ "detail": "Dossier introuvable: /nonexistent" }` |
| 4.7 | **Path traversal bloquée** | `GET /api/workspace/browse?path=../../etc` | Retourne le projet courant (pas de sortie du sandbox) |
| 4.8 | **Ignorés** | Explorer un dossier avec `node_modules` | `node_modules`, `.venv`, `.git` absents de la liste |

---

## 5. Tests Frontend Autonomes (UI)

### 5a. Sidebar

| # | Test | Composant | Résultat attendu |
|---|------|-----------|-----------------|
| 5.1 | **Affichage des crews** | `Sidebar` | Liste des crews chargés depuis `/api/crews` |
| 5.2 | **Nouvelle conversation** | Bouton "Nouvelle conversation" | Crée une conversation avec `crewName: "default"`, la sélectionne |
| 5.3 | **Changement de crew** | Dropdown de sélection de crew dans la sidebar | Met à jour `crewName` de la conversation active |
| 5.4 | **Suppression conversation** | Bouton supprimer sur une conversation | Conversation retirée de la liste, aucune autre affectée |
| 5.5 | **Sélection conversation** | Clic sur une conversation dans la sidebar | Devient active, le ChatWindow affiche ses messages |
| 5.6 | **Persistance localStorage** | Créer 2 conversations, recharger la page | Les 2 conversations réapparaissent au reload |
| 5.7 | **Contexte dossier** | Sélecteur de dossier dans la sidebar | Le `folderContext` est sauvegardé dans la conversation |

### 5b. ChatWindow

| # | Test | Composant | Résultat attendu |
|---|------|-----------|-----------------|
| 5.8 | **Affichage messages** | `ChatWindow` | Les messages utilisateur (`role: "user"`) et assistant (`role: "assistant"`) s'affichent |
| 5.9 | **Message utilisateur** | Taper un message + Enter | Le message apparaît immédiatement dans le chat |
| 5.10 | **Streaming en temps réel** | Envoyer un message | Les chunks SSE apparaissent progressivement (pas d'attente de fin) |
| 5.11 | **Type log** | Chunk `{ "type": "log", "content": "[Routeur]..." }` | Affiché avec un style de log (couleur/icone différente) |
| 5.12 | **Type result** | Chunk `{ "type": "result", "content": "..." }` | Affiché comme le contenu principal de la réponse |
| 5.13 | **Type error** | Chunk `{ "type": "error", "content": "..." }` | Préfixé de "**Erreur:**" et stylisé en rouge |
| 5.14 | **Scroll auto** | Pendant le streaming | Le chat scroll automatiquement vers le bas |
| 5.15 | **Bouton stop** | Clic sur "Stop" pendant le streaming | Le stream s'arrête, le message d'erreur AbortError n'est pas affiché |
| 5.16 | **CrewLaunchPad** | Sélectionner un crew non-default | Le panneau de configuration du crew s'affiche dans le header |
| 5.17 | **CrewConfig — modification settings** | Modifier `process` dans CrewConfig | L'UI reflète le changement, le crew est mis à jour via API |
| 5.18 | **CrewConfig — ajout agent** | Formulaire d'ajout d'agent dans CrewConfig | L'agent apparaît dans la liste, le crew est mis à jour |
| 5.19 | **CrewConfig — ajout tâche** | Formulaire d'ajout de tâche dans CrewConfig | La tâche apparaît dans la liste, le crew est mis à jour |
| 5.20 | **CrewSelector** | Ouvrir le sélecteur de crew | Liste filtrable des crews disponibles |
| 5.21 | **ModelPicker** | Ouvrir le sélecteur de modèle | Liste des modèles depuis `/api/models` |
| 5.22 | **FolderPickerModal** | Ouvrir le sélecteur de dossier | Navigation arborescente via `/api/workspace/browse` |

### 5c. ExecutionTimeline

| # | Test | Composant | Résultat attendu |
|---|------|-----------|-----------------|
| 5.23 | **Affichage des étapes** | Pendant l'exécution d'un crew | Les étapes du crew s'affichent en temps réel |
| 5.24 | **Statut pending** | Chunk `{ "stepStatus": "pending", "stepKey": "agent-0" }` | Cercle/icône grise |
| 5.25 | **Statut running** | Chunk `{ "stepStatus": "running", "stepKey": "agent-0" }` | Cercle/icône animée/bleue |
| 5.26 | **Statut completed** | Chunk `{ "stepStatus": "completed", "stepKey": "agent-0" }` | Cercle/icône verte |
| 5.27 | **Statut error** | Chunk `{ "stepStatus": "error", "stepKey": "agent-0" }` | Cercle/icône rouge |
| 5.28 | **Coût & tokens** | Chunk `{ "tokens": 1234, "cost": 0.005 }` | Affiché à côté de l'étape |

### 5d. Thème & UI

| # | Test | Composant | Résultat attendu |
|---|------|-----------|-----------------|
| 5.29 | **Toggle dark/light** | Bouton `ThemeToggle` | Le thème change immédiatement, persiste au reload |
| 5.30 | **Icône adaptative** | `ThemeToggle` | Soleil en mode dark, lune en mode light |
| 5.31 | **Responsive layout** | Redimensionner la fenêtre | Sidebar + ChatWindow s'adaptent (flex layout) |
| 5.32 | **Header** | `Header` | Titre "Agent Test" + bouton theme + boutons crew/model |

---

## 6. End-to-End (Scénarios complets)

| # | Scénario | Étapes | Résultat attendu |
|---|----------|--------|-----------------|
| 6.1 | **Conversation complète** | 1. Nouvelle conversation → 2. Sélectionner "ProjectArchitect" → 3. Envoyer "Crée un plan MVP pour une app de gestion de tâches" → 4. Le crew s'exécute → 5. Le résultat apparaît | Stream complet, crew exécuté, résultat affiché |
| 6.2 | **Multi-tours** | 1. Envoyer un message → 2. Attendre la réponse → 3. Envoyer un 2ème message dans la même conversation | Le 2ème message a le contexte du 1er (session persistante) |
| 6.3 | **Changement de crew en cours** | 1. Conversation avec "default" → 2. Changer vers "SecurityReviewer" → 3. Envoyer un message | Le message est envoyé au bon crew |
| 6.4 | **Rechargement page** | 1. Créer 2 conversations avec des messages → 2. Recharger la page → 3. Vérifier | Tout est restauré (conversations, messages, crew sélectionné) |
| 6.5 | **Workflow workspace** | 1. Ouvrir FolderPicker → 2. Naviguer dans l'arborescence → 3. Sélectionner un dossier → 4. Envoyer un message | Le `folderContext` est passé au crew comme input |
| 6.6 | **Meta-Routeur complet** | 1. Conversation "default" → 2. Envoyer "Fais un audit de sécurité de mon code frontend" → 3. Le routeur dispatch → 4. Le crew SecurityReviewer s'exécute | Le routeur détecte l'intention, dispatch, et le crew s'exécute |

---

## 7. Tests d'Erreur & Edge Cases

| # | Test | Description | Résultat attendu |
|---|------|-------------|-----------------|
| 7.1 | **API non disponible** | Backend coupé, frontend lancé | Message d'erreur clair, pas de crash |
| 7.2 | **Réponse SSE malformée** | Mock du backend renvoyant du JSON brut au lieu de SSE | Le frontend ignore le chunk malformed (try/catch existant) |
| 7.3 | **Crew YAML corrompu** | Écrire du texte brut dans un fichier `.yaml` de crew | Le frontend affiche une erreur, ne plante pas |
| 7.4 | **Conversations vides** | localStorage vidé, page rechargée | Page affiche "Sélectionnez ou créez une conversation" |
| 7.5 | **Conversations corrompues** | localStorage contient du JSON invalide | `loadConversations()` retourne `[]` (try/catch existant) |
| 7.6 | **Session ID null** | `POST /api/chat` sans `session_id` | Le backend crée une nouvelle session automatiquement |
| 7.7 | **Message vide** | Envoyer un message vide | Le frontend bloque (champ requis) ou le backend ignore |
| 7.8 | **Stream très long** | Crew avec 10+ étapes | Le buffer SSE ne déborde pas, tous les chunks sont reçus |

---

## 8. Tests Desktop (Electron)

| # | Test | Description | Résultat attendu |
|---|------|-------------|-----------------|
| 8.1 | **Lancement** | `cd desktop && npm start` | Backend + Frontend lancés, Electron ouvert sur l'UI |
| 8.2 | **Healthcheck Electron** | Pendant le boot | L'UI attend que `/api/health` soit ready avant d'afficher |
| 8.3 | **Fermeture propre** | Fermer la fenêtre Electron | Backend + Frontend killés (tree-kill), ports 8000/3000 libérés |
| 8.4 | **Icone dock** | macOS dock | L'icône ronde "Agent Test" affichée |

---

## Résumé des priorités

| Priorité | Catégorie | # Tests |
|----------|-----------|---------|
| **P0** | Chat SSE (cœur du produit) | 3.1–3.15 |
| **P0** | Connexion Backend ↔ Frontend | 1.1–1.3 |
| **P1** | CRUD Crews complet | 2.1–2.16 |
| **P1** | End-to-End scénarios | 6.1–6.6 |
| **P2** | UI components | 5.1–5.32 |
| **P2** | Workspace & navigation | 4.1–4.8 |
| **P3** | Edge cases & erreurs | 7.1–7.8 |
| **P3** | Desktop Electron | 8.1–8.4 |

**Total : 73 tests** répartis en 8 catégories.
