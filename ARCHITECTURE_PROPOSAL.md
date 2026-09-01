# Plan d'Architecture & Implémentation : LLM Pulse

- **Dossier cible :** `../llm_pulse/`
- **Tagline :** "Diagnostiquez la santé de vos modèles LLM en quelques secondes."

## 1. Stack Technique

Pour un outil CLI léger, performant et maintenable, nous utilisons la stack suivante :

- **Langage :** Python 3.11+ (Type hints, typing utilities).
- **CLI Framework :** `Typer` (Moderne, basé sur Click, excellent pour les interfaces en ligne de commande).
- **Client HTTP :** `httpx` (Support natif d'Asyncio, plus performant que `requests` pour les tests parallèles).
- **Gestion de Config :** `PyYAML` pour le fichier `config.yaml` et `Pydantic` pour la validation stricte des paramètres.
- **Traitement Asynchrone :** `asyncio` et `aiohttp` (via httpx) pour gérer les requêtes concurrentes et le rate limiting dynamique sans bloquer le thread principal.
- **Génération de Rapport :** Module Python natif pour générer du Markdown propre et structuré.
- **Tests :** `pytest` pour les tests unitaires et d'intégration.
- **Linter/Formatteur :** `ruff` ou `black` + `mypy` pour la qualité du code.

## 2. Arborescence des fichiers

Voici l'arborescence exacte à créer dans `../llm_pulse/` :

```text
llm_pulse/
├── .gitignore
├── pyproject.toml          # Configuration du projet (hatch/uv/poetry)
├── README.md               # Documentation d'installation et d'usage
├── ARCHITECTURE_PROPOSAL.md # Ce fichier
├── LICENSE
├── llm_pulse/
│   ├── __init__.py
│   ├── __main__.py         # Point d'entrée CLI
│   ├── cli.py              # Définition des commandes Typer
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py       # Cœur du moteur de test (orchestration)
│   │   ├── tests.py        # Définition des types de tests (perf, safety, etc.)
│   │   └── reporter.py     # Génération du rapport Markdown
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base.py         # Client HTTP abstrait
│   │   └── llm_client.py   # Implémentation spécifique LLM (OpenAI, Anthropic, Ollama)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config.py       # Modèles Pydantic pour config.yaml
│   │   └── results.py      # Modèles Pydantic pour les résultats (TestRun, TestResult)
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py # Gestionnaire intelligent de rate limiting (backoff)
│       └── helpers.py      # Fonctions utilitaires (hashing prompts, etc.)
├── tests/
│   ├── __init__.py
│   ├── test_engine.py
│   ├── test_client.py
│   └── test_reporter.py
├── config.example.yaml     # Exemple de fichier de configuration
└── requirements-dev.txt    # Dépendances de développement
```

## 3. Spécification détaillée fichier par fichier

### Configuration & Entry Points

- **`pyproject.toml`**:
  - Définit les dépendances : `typer`, `httpx`, `pyyaml`, `pydantic`, `pytest`, `asyncio` (stdlib).
  - Configure l'entry point pour la commande CLI `llm-pulse`.

- **`llm_pulse/__main__.py`**:
  - Simple script qui importe et lance `cli.py`.

- **`llm_pulse/cli.py`**:
  - Utilise `typer.Typer()`.
  - Définit la commande `run` avec les options : `--config`, `--output`, `--dry-run`, `--endpoint`, `--api-key`, `--model`.
  - Gère la création du client LLM et l'appel au moteur principal.

### Modèles de Données

- **`llm_pulse/models/config.py`**:
  - Classe `TestConfig` (Pydantic) : `max_requests`, `delay_between_requests_sec`, `rate_limit_retry_max`.
  - Classes pour les sous-tests : `SafetyTest`, `FormatTest`.
  - Validation automatique des chemins de fichiers et formats YAML.

- **`llm_pulse/models/results.py`**:
  - `TestResult` : `test_type`, `prompt_hash`, `input_tokens`, `output_tokens`, `latency_ms`, `status_code`, `is_success`, `error_message`, `safety_flag`, `json_valid`.
  - `TestRun` : `id`, `timestamp`, `endpoint`, `model_name`, `results` (list[TestResult]).
  - Propriétés calculées : `avg_latency_ms`, `avg_tokens_per_second`, `safety_score`, `format_compliance_score`.

### Cœur du Moteur (Core)

- **`llm_pulse/clients/llm_client.py`**:
  - Hérite d'une interface abstraite (si étendable) ou contient la logique `httpx.AsyncClient`.
  - Méthode `async send_request(prompt, model, api_key)`.
  - Intègre la logique de retry base sur `httpx` et les codes d'erreur 429.

- **`llm_pulse/utils/rate_limiter.py`**:
  - Classe `RateLimiter` utilisant `asyncio.Semaphore` et des calculs de backoff exponentiel.
  - Gère les pauses dynamiques si l'API retourne 429.

- **`llm_pulse/core/engine.py`**:
  - Classe `LLMPulseEngine`.
  - Méthode `async run_test_suite()` :
    - Initialise les données.
    - Boucle sur les itérations (Performance, Robustesse, Sécurité).
    - Utilise `asyncio.gather` pour lancer les requêtes par lots (batching) pour le benchmark de performance.
    - Exécute les tests de sécurité un par un ou en petits groupes pour assurer l'ordre.
    - Appelle le `reporter` à la fin.

- **`llm_pulse/core/reporter.py`**:
  - Fonction `generate_markdown_report(run_data: TestRun) -> str`.
  - Génère un Markdown structuré avec :
    - Résumé des métriques (Latence, Throughput, Score de sécurité).
    - Tableau des résultats détaillés.
    - Section "Anomalies Critiques" si erreurs détectées.
  - Sauvegarde le fichier si un chemin de sortie est fourni.

### Tests

- **`tests/`** :
  - Mock `httpx` pour simuler des réponses LLM sans coût réel.
  - Vérifie le calcul des scores.
  - Vérifie la génération du rapport Markdown.
  - Teste le comportement du rate limiter (mock `time.sleep` ou async equivalent).

## 4. Étapes de Développement pour le CrewManager

### Phase 1 : Infrastructure et Config (Jours 1-2)
1.  Initialiser le repo git et le fichier `pyproject.toml`.
2.  Créer la structure de dossiers.
3.  Implémenter `models/config.py` pour parser `config.yaml`.
4.  Implémenter `models/results.py` pour structurer les données de sortie.
5.  Créer le fichier `config.example.yaml`.

### Phase 2 : Client HTTP et Rate Limiting (Jours 3-4)
1.  Implémenter `clients/llm_client.py` pour envoyer des requêtes simples à une API ouverte (ex: huggingface inference API ou mock).
2.  Intégrer `utils/rate_limiter.py` pour gérer les 429.
3.  Écrire les tests unitaires pour le client et le rate limiter.

### Phase 3 : Moteur de Tests (Jours 5-7)
1.  Implémenter `core/tests.py` pour définir les templates de prompts (Performance, Jailbreak, JSON, Long Context).
2.  Implémenter `core/engine.py` pour orchestrer les appels.
    - Priorité : Test de Performance (async batch).
    - Deuxième : Tests de Robustesse/Sécurité.
3.  Ajouter la logique de hachage des prompts pour éviter les doublons inutiles si nécessaire.

### Phase 4 : CLI et Rapport (Jours 8-9)
1.  Implémenter `cli.py` avec Typer pour exposer les commandes.
2.  Implémenter `core/reporter.py` pour générer le Markdown.
3.  Connecter le CLI au moteur via `__main__.py`.
4.  Tester en mode `--dry-run` pour valider la structure sans appels API.

### Phase 5 : Finalisation et Documentation (Jour 10)
1.  Ajouter `README.md` avec exemples d'utilisation.
2.  Nettoyer le code (linter/formatteur).
3.  Créer le package PyPI (`python -m build`).
4.  Vérification finale des acceptance criteria (gestion d'erreurs, format rapport, dry-run).

## 5. Critères d'Acceptation Techniques

- [x] Le script utilise Python 3.11+ et Typer.
- [x] La configuration est validée par Pydantic.
- [x] Les requêtes HTTP sont asynchrones pour maximiser le débit.
- [x] Les erreurs 429 sont gérées via un backoff exponentiel.
- [x] Le rapport Markdown est généré localement sans dépendances lourdes.
- [x] Un mode `--dry-run` est disponible.
