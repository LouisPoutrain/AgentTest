# Proposition d'Évolution Architecturale : Projet Backend "AgentTest"

## 1. Résumé Exécutif
Ce document propose une feuille de route pour transformer le backend actuel (monolithique, sans persistance SQL ni sécurité robuste) en une architecture de production robuste, scalable et sécurisée, adaptée à l'orchestration d'agents IA autonomes.

---

## 2. Trois Améliorations Majeures Proposées

### A. Découplage Asynchrone via File d'Attente (Event-Driven Architecture)
**Le Changement :** Séparer strictement la couche API (FastAPI) de la couche de calcul (CrewAI).
*   **Actuel :** FastAPI exécute les agents directement dans le thread de requête (bloquant).
*   **Proposé :** FastAPI accepte la requête, génère un `task_id`, et publie une tâche dans une file d'attente (Redis). Des workers (Celery ou Arq) consomment cette tâche et exécutent l'agent.
*   **Avantage :** L'API reste réactive (< 100ms de latence). Les agents, qui peuvent mettre plusieurs minutes à "réfléchir", ne bloquent pas les connexions utilisateurs. Permet la scalabilité horizontale des workers.

### B. Persistance Hybride : PostgreSQL + Vector Store
**Le Changement :** Introduire une base de données relationnelle pour les données métier et structurées.
*   **Actuel :** Stockage éphémère ou local via ChromaDB uniquement.
*   **Proposé :** Utilisation de **PostgreSQL** pour les utilisateurs, les métadonnées des crews, et les historiques de chat. Conservation de ChromaDB (ou migration vers PGVector) pour la mémoire sémantique (RAG).
*   **Avantage :** Garantit la cohérence des données (transactions ACID), permet l'interrogation SQL complexe et assure la persistance à long terme des données critiques.

### C. Sécurisation "Zero Trust" avec Authentification Standardisée
**Le Changement :** Implémenter une couche d'authentification robuste avant l'accès à la logique métier.
*   **Actuel :** Pas de middleware d'authentification visible (risque majeur).
*   **Proposé :** Intégration de **FastAPI Users** ou d'un middleware JWT/OAuth2. Validation des tokens par `Depends(get_current_user)` sur les endpoints sensibles.
*   **Avantage :** Protège l'API contre les accès non autorisés, permet le traçabilité des actions par utilisateur, et sécurise les appels LLM coûteux ou sensibles.

---

## 3. Justification par Références Web et État de l'Art

Les choix ci-dessus sont validés par les meilleures pratiques actuelles (2024-2025) observées dans l'industrie IA :

1.  **Architecture Asynchrone :**
    *   *Source :* Les architectures modernes (HuggingFace, LangChain Inc.) déconseillent l'exécution synchrone des agents dans les threads HTTP.
    *   *Justification :* La documentation FastAPI et les retours d'expérience sur la scalabilité des LLM confirment que le découplage via des files d'attente (Redis/Celery) est indispensable pour gérer la latence variable des modèles IA [FastAPI Best Practices].

2.  **Persistance Hybride :**
    *   *Source :* Guides de déploiement LangChain/CrewAI et exemples Microsoft Semantic Kernel.
    *   *Justification :* L'utilisation exclusive de bases vectorielles locales est risquée pour la production. PostgreSQL offre la robustesse nécessaire pour les données relationnelles, tandis que ChromaDB/PGVector reste idéal pour la RAG [LangChain Docs - State Management].

3.  **Sécurité :**
    *   *Source :* Documentation FastAPI sur l'Injection de Dépendances et les Bonnes Pratiques de Sécurité.
    *   *Justification :* Les APIs exposant des agents IA sont des cibles prioritaires pour les injections de prompts. L'authentification par JWT/OAuth2 est la norme industrielle pour restreindre l'accès et auditer les requêtes [FastAPI Documentation - Dependency Injection].

---

## 4. Plan de Migration et Étapes d'Implémentation

### Phase 1 : Sécurisation et Structure (Semaines 1-2)
1.  Installer `fastapi-users` ou `PyJWT`.
2.  Créer un middleware d'authentification global dans `main.py`.
3.  Protéger les endpoints `/chat` et `/crews` par défaut.
4.  Ajouter la validation stricte des entrées via Pydantic pour prévenir les injections.

### Phase 2 : Asynchronisation (Semaines 3-4)
1.  Installer `celery` et `redis` (ou `arq` pour une solution plus légère).
2.  Refactorer `app/core/agent_execution.py` pour qu'il ne soit qu'un worker consommant des tâches.
3.  Modifier les routeurs FastAPI pour qu'ils envoient des tâches en file d'attente et retournent un `task_id` immédiatement.
4.  Implémenter un endpoint `/status/{task_id}` pour vérifier l'avancement.

### Phase 3 : Persistance des Données (Semaines 5-6)
1.  Installer `SQLAlchemy 2.0` et `PostgreSQL`.
2.  Modéliser les tables `User`, `ChatSession`, `Message`.
3.  Adapter les schémas Pydantic pour inclure les références DB.
4.  Migrer la logique de sauvegarde des historiques de chat vers PostgreSQL.

### Phase 4 : Observabilité et Monitoring (Semaine 7+)
1.  Intégrer `OpenTelemetry` pour tracer les appels LLM.
2.  Configurer `Prometheus` pour exposer les métriques (latence, erreurs, coûts).
3.  Mettre en place des dashboards Grafana pour surveiller la santé des agents.

---

## 5. Outils Recommandés

| Domaine | Outil Recommandé | Raison |
| :--- | :--- | :--- |
| **File d'Attente** | **Celery** + **Redis** | Standard de l'industrie, robuste, gestion des retries. |
| **Base de Données** | **PostgreSQL** + **SQLAlchemy** | Fiabilité, ACID, écosystème Python riche. |
| **Authentification** | **FastAPI Users** | Intègre JWT, OAuth2, gestion des utilisateurs, bcrypt. |
| **Observabilité** | **OpenTelemetry** | Standard ouvert pour le tracing distribué. |

---

*Document généré par Architecte Cloud & Logiciel Visionnaire.*
*Basé sur le diagnostic technique initial et les recherches web sur les stacks FastAPI/CrewAI/LangChain.*
