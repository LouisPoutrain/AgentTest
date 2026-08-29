# Code Review Report

## Résumé
Ce rapport résume les findings de l'audit de code et de sécurité. Les issues sont classées par niveau de criticité.

---

## 1. Critique (Urgent)

Ces points nécessitent une correction immédiate pour assurer la stabilité et la sécurité de l'application.

### 1.1. Fichier manquant : `app/api/router.py`
- **Fichier concerné**: `app/api/router.py`
- **Description**: Le fichier `router.py` est manquant sur le système de fichiers, bien qu'il soit probablement référencé par les imports dans `main.py` ou d'autres modules.
- **Impact**: Cela entraîne une `ImportError` ou `ModuleNotFoundError` au démarrage de l'application, empêchant son lancement.
- **Action**: Recréer le fichier `router.py` ou vérifier si les routes doivent être importées directement depuis les sous-modules (`chat.py`, `crews.py`).

### 1.2. Gestion des Secrets : `.env.example`
- **Fichier concerné**: `.env.example`
- **Description**: Le fichier contient des valeurs par défaut explicites pour les clés API (`GITHUB_TOKEN`, `HF_TOKEN`, `GEMINI_API_KEY`).
- **Risque**: 
  - Mauvaise pratique : Encourage les développeurs à copier-coller des valeurs sans les modifier.
  - Incohérence de syntaxe : `GEMINI_API_KEY=your_gemini_api_key_here` (sans guillemets) peut causer des erreurs de parsing.
- **Action**: Remplacer les valeurs par des placeholders explicites entre chevrons ou des commentaires, et standardiser la syntaxe (ex: `KEY=""`).

---

## 2. Mineur

Ces points améliorent la robustesse et la maintenabilité du code.

### 2.1. Dépendances non épinglées : `requirements.txt`
- **Fichier concerné**: `requirements.txt`
- **Description**: Les dépendances sont listées sans versions spécifiques (ex: `crewai` au lieu de `crewai==0.25.0`).
- **Risque**: Builds non reproductibles. Risque de régression si une dépendance met à jour sa version majeure/mineure.
- **Action**: Épingler les versions (`package==version`) ou utiliser `poetry.lock`/`Pipfile.lock`.

### 2.2. Configuration CORS : `app/main.py`
- **Fichier concerné**: `app/main.py`
- **Description**: Les origines autorisées (`ALLOWED_ORIGINS`) ont une valeur par défaut `http://localhost:3000`.
- **Risque**: Si la variable d'environnement n'est pas définie en production, le CORS pourrait être mal configuré ou trop permissif si une URL invalide est passée.
- **Action**: Ajouter une validation stricte des URLs dans `allowed_origins` et vérifier que `allow_credentials=True` est approprié pour les origines multiples.

---

## 3. Optimisation

Ces points concernent les bonnes pratiques architecturales et la configuration.

### 3.1. Hardcoding des LLM : `config/crews/Dev.yaml`
- **Fichier concerné**: `config/crews/Dev.yaml`
- **Description**: Les agents `Chef_Projet_Migration` et `Developpeur_React_Senior` ont leur LLM défini en dur (`openai/qwen-3.6-35b-instruct`).
- **Risque**: 
  - Dépendance fournisseur verrouillée.
  - Difficulté de maintenance si le modèle change.
- **Action**: Externaliser le paramètre `llm` via une variable d'environnement ou un fichier de config séparé.

### 3.2. Mode Verbose en Production : `config/crews/Dev.yaml`
- **Fichier concerné**: `config/crews/Dev.yaml`
- **Description**: Tous les agents ont `verbose: true`.
- **Risque**: Logs excessifs contenant potentiellement des données sensibles. Ce fichier est nommé `Dev.yaml`, ce qui suggère qu'il ne devrait pas être chargé en production.
- **Action**: S'assurer que ce fichier n'est pas chargé en environnement `PROD` ou ajouter une condition pour désactiver le verbose.

### 3.3. Gestion des Erreurs : `app/main.py`
- **Fichier concerné**: `app/main.py`
- **Description**: Absence de gestion globale des erreurs (Exception Handlers).
- **Risque**: Retour d'erreurs 500 brutes sans structure JSON cohérente pour le frontend.
- **Action**: Ajouter des handlers d'exceptions globales pour retourner des réponses JSON standardisées.
