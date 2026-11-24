# Plan de Refonte : Laboratoire d'Automatisation (Automation Lab)

> **Vision** : Transformer l'application en un laboratoire d'automatisation IA de niveau Premium, où la création, la configuration et le lancement d'agents sont d'une simplicité enfantine, même pour un utilisateur non technique. L'interface doit être ultra-peaufinée, fluide, avec des micro-interactions soignées et des retours visuels parfaits.

---

## Phase 1 — Refonte de l'Expérience Utilisateur (Frontend & Design)

### 1.1. Système de Navigation & Structure

**Problème actuel** : L'interface actuelle est un chat unique avec un panneau latéral droit complexe. La navigation est linéaire et ne reflète pas la nature "laboratoire" de l'application.

**Proposition** :

| Élément | Avant | Après |
|---------|-------|-------|
| **Navigation principale** | Sidebar gauche statique | Sidebar gauche avec 3 onglets : `Lots` (conversations), `Laboratoire` (automatisations), `Bibliothèque` (crews/templates) |
| **Zone centrale** | Chat unique | Dashboard par défaut → Chat quand une conversation est active |
| **Panneau droit** | CrewLaunchPad monolithique (925 lignes) | Panneau contextuel dynamique : propriétés de l'automatisation, logs en temps réel, paramètres avancés |

**Principe UX** : *Progressive Disclosure* — l'utilisateur voit d'abord l'essentiel, les détails n'apparaissent que quand il les demande.

### 1.2. Wizard de Création d'Automatisation (Le Cœur du Système)

**Problème actuel** : `CrewLaunchPad.tsx` est un monolithe de 925 lignes avec ~400 lignes de matching hardcoded par type de crew. L'expérience est confuse : formulaires techniques, presets inline, pas de feedback visuel clair.

**Proposition** : Un **Wizard en 3 étapes** avec barre de progression visuelle :

```
┌─────────────────────────────────────────────────┐
│  Étape 1/3  ───────●──────────○────────○        │
│                                                  │
│      Que souhaitez-vous automatiser ?            │
│                                                  │
│  [  Code Review  ]  [  Architecture  ]           │
│  [  Testing      ]  [  Documentation           ] │
│  [  Déploiement  ]  [  Recherche  ]              │
│                                                  │
│  ←  Précédent                    Suivant →       │
└─────────────────────────────────────────────────┘
```

**Étape 1 — Choix du Template** :
- Grille de cartes visuelles avec icônes, descriptions et tags
- Chaque carte représente un "pattern" d'automatisation (pas un crew technique)
- Catégories : Développement, Testing, Documentation, Recherche, Architecture
- Carte "Personnalisé" pour les cas non couverts
- **Recherche en temps réel** dans les templates

**Étape 2 — Configuration Visuelle** :
- Formulaire épuré avec champs progressifs (n'apparaissent que si nécessaires)
- **Visualisation du flux** : un mini-graphique montrant les agents en enchaînement (drag-and-drop pour réordonner)
- Prévisualisation en temps réel du prompt système généré
- Tooltips contextuels sur chaque champ (icône `?` avec explication)

**Étape 3 — Confirmation & Lancement** :
- Résumé visuel de l'automatisation configurée
- Bouton "Lancer" avec animation de confirmation
- Option "Sauvegarder comme template"

### 1.3. Composants Clés à Recréer

#### 1.3.1. `TemplateGallery` (nouveau)
- Grille responsive de templates d'automatisation
- Filtres par catégorie, complexité, temps estimé
- Drag & drop pour créer une automatisation depuis la galerie
- Favoris personnels (stockés en localStorage)

#### 1.3.2. `AutomationWizard` (remplace `CrewLaunchPad`)
- Wizard en 3 étapes avec barre de progression
- Navigation avant/arrière fluide (framer-motion transitions)
- Validation en temps réel avec feedback visuel
- Sauvegarde automatique du brouillon (localStorage)
- **Zéro hardcoded** : les champs sont définis par un registry de schemas déclaratifs

#### 1.3.3. `AgentFlowBuilder` (nouveau)
- Visualisation des agents en flux (flow diagram)
- Drag-and-drop pour réordonner les agents
- Connexion visuelle entre les tâches (flèches)
- Click sur un agent pour voir/éditer ses détails
- Inspiré de n8n.io ou Make.com

#### 1.3.4. `Toast` System (nouveau)
- Remplacer tous les `alert()` par un système de toasts
- Types : `success`, `error`, `warning`, `info`
- Position : bottom-right, auto-dismiss
- Bibliothèque recommandée : `sonner` (shadcn par défaut) ou `react-hot-toast`

#### 1.3.5. `ConversationSidebar` (refonte)
- Recherche en temps réel dans les conversations
- Grouping par date (Aujourd'hui, Hier, Cette semaine, Plus ancien)
- Renommage inline (double-click)
- Drag & drop pour réorganiser
- Swipe-to-delete sur mobile

### 1.4. Design System & Polish

#### 1.4.1. Micro-interactions (framer-motion)
- **Hover** : élévation subtile + changement de couleur d'accent
- **Click** : effet de ripple sur les boutons
- **Transitions de page** : fade-in/out lors du changement de vue
- **Loading** : skeleton screens au lieu de spinners simples
- **Feedback d'erreur** : shake animation + toast rouge
- **Succès** : checkmark animé + toast vert

#### 1.4.2. Typographie & Espacement
- Hiérarchie claire : titres 24px/700, sous-titres 16px/500, corps 14px/400
- Espacement basé sur une grille 4px (4, 8, 12, 16, 24, 32, 48, 64)
- Line-height : 1.5 pour le corps, 1.3 pour les titres

#### 1.4.3. Accessibilité
- Contraste AA minimum (4.5:1 pour le texte)
- Navigation clavier complète (Tab, Enter, Escape)
- ARIA labels sur tous les éléments interactifs
- Support du mode sombre avec transition fluide

#### 1.4.4. Responsive Design
- Mobile-first : l'interface doit fonctionner sur mobile
- Sidebar rétractable sur mobile (drawer)
- Grille de templates adaptative (1 colonne mobile → 2 tablette → 3 desktop)

### 1.5. Architecture Technique Frontend

```
frontend/
├── app/
│   ├── page.tsx              → Dashboard (redirige vers /lab)
│   └── lab/
│       └── page.tsx          → Nouvelle vue principale du laboratoire
├── components/
│   ├── lab/                  → NOUVEAU
│   │   ├── TemplateGallery.tsx
│   │   ├── AutomationWizard.tsx
│   │   ├── AgentFlowBuilder.tsx
│   │   └── AutomationCard.tsx
│   ├── chat/
│   │   ├── ChatWindow.tsx    → Réduit à ~150 lignes (orchestration uniquement)
│   │   ├── ChatInput.tsx     → Gardé tel quel
│   │   └── ...               → Composants existants conservés
│   ├── sidebar/
│   │   ├── NavigationSidebar.tsx  → Nouvelle sidebar unifiée
│   │   ├── ConversationList.tsx   → Refonte avec recherche/grouping
│   │   └── ...
│   └── ui/
│       ├── toast.tsx         → NOUVEAU (wrapper sonner)
│       ├── skeleton.tsx      → NOUVEAU
│       └── ...               → Existants conservés
├── lib/
│   ├── registry/             → NOUVEAU
│   │   ├── templates.ts      → Registry déclaratif des templates
│   │   ├── fields.ts         → Registry des champs de formulaire
│   │   └── descriptions.ts   → Descriptions UI (plus de matching hardcoded)
│   └── ...
```

---

## Phase 2 — Restructuration du Moteur (Backend CrewAI)

### 2.1. Registry Déclaratif des Crews

**Problème actuel** : La logique de matching par type de crew est dupliquée entre `utils.ts` (frontend) et `CrewLaunchPad.tsx` (frontend). Le backend lit les YAMLs à chaque appel du meta-router.

**Proposition** : Créer un registry centralisé côté backend qui alimente le frontend :

```python
# backend/app/core/crew_registry.py (nouveau)
class CrewRegistry:
    """Registry centralisé des crews avec cache et validation."""
    
    def get_all_crews(self) -> list[CrewMetadata]:
        """Retourne les metadata de tous les crews (sans charger le YAML complet)."""
        
    def get_crew_schema(self, name: str) -> CrewSchema:
        """Retourne le schéma de configuration d'un crew (champs requis, options)."""
        
    def get_available_templates(self) -> list[Template]:
        """Retourne les templates prêts à l'emploi avec descriptions UI."""
```

**API ajoutée** :
- `GET /api/registry/templates` → Liste des templates avec metadata UI (nom, description, icône, catégorie, champs requis)
- `GET /api/registry/schema/{name}` → Schéma de configuration d'un crew
- `GET /api/registry/agents` → Liste des agents disponibles avec metadata

### 2.2. Amélioration du Meta-Router

**Problèmes actuels** :
- Le prompt système est reconstruit à chaque appel (O(n) lectures YAML)
- L'extraction JSON est fragile (brace-matching)
- Pas de fallback si le modèle "fast" est indisponible
- `context_inputs` avec `\\n\\n` au lieu de vrais sauts de ligne

**Proposition** :

| Amélioration | Détail |
|--------------|--------|
| **Cache du prompt** | Le prompt système est construit une fois et mis en cache. Invalidé quand un crew est modifié. |
| **JSON parsing robuste** | Utiliser `json_repair` ou un parser plus tolérant que le brace-matching |
| **Fallback modèle** | Si le modèle "fast" est indisponible, fallback sur "balanced" avec un avertissement |
| **Validation de réponse** | Le JSON retourné est validé contre un schéma Pydantic avant d'être utilisé |
| **Vrais sauts de ligne** | Corriger le bug `\\n\\n` → `\n\n` dans `build_system_prompt()` |

### 2.3. Gestion du Cycle de Vie des Crews

**Problèmes actuels** :
- Pas de mécanisme d'annulation (un crew tourne jusqu'au bout)
- Pas de validation des YAMLs (typos ignorées silencieusement)
- Deux formats YAML (`crew_settings` vs `settings`)
- `execute_crew` bufferise toute la sortie (défait le streaming)

**Proposition** :

| Fonctionnalité | Détail |
|----------------|--------|
| **Annulation** | Ajouter un endpoint `POST /api/chat/{session_id}/cancel` qui signale au runner d'arrêter proprement |
| **Validation YAML** | Schéma Pydantic pour valider les crews avant écriture. Erreur claire si le YAML est invalide. |
| **Unification YAML** | Migrer tous les crews vers `crew_settings`. Déprécier `settings` avec un warning. |
| **Streaming pour execute_crew** | Convertir `execute_crew` en async generator qui forward les chunks SSE |
| **Rate limiting par session** | Empêcher qu'une session ne submerge le système avec des requêtes trop fréquentes |

### 2.4. Sécurité Renforcée

| Problème | Solution |
|----------|----------|
| `shell=True` dans `terminal_runner` | Remplacer par `subprocess.run()` avec liste d'arguments, pas de shell |
| `update_tool_registry` modifie le code source | Supprimer ou restreindre à un mode admin uniquement |
| Import GitHub sans validation Content-Type | Ajouter validation MIME + taille max (1MB) |
| `execute_python_code` bypassable via `__import__` | Ajouter des checks supplémentaires dans le sandbox Docker |

### 2.5. API Contract Evolution

**Nouveaux endpoints** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/registry/templates` | GET | Liste des templates avec metadata UI |
| `/api/registry/schema/{name}` | GET | Schéma de configuration d'un crew |
| `/api/automations` | GET/POST | CRUD des automatisations sauvegardées (plus que des crews YAML) |
| `/api/automations/{id}/run` | POST | Lancer une automatisation sauvegardée |
| `/api/automations/{id}/cancel` | POST | Annuler une automatisation en cours |
| `/api/chat/{session_id}/cancel` | POST | Annuler un chat en cours |
| `/api/templates/favorite/{id}` | POST | Ajouter/retirer un template des favoris |

**Endpoints dépréciés** (conservés pour compatibilité) :
- `POST /api/crews` → toujours supporté mais les nouvelles créations passent par `/api/automations`

---

## Phase 3 — Plan d'Action & Découpage

### Ticket 1 : Système de Toast & Gestion d'Erreurs UX
**Priorité** : P0 — Fondamentale
**Impact** : Remplace tous les `alert()` par un système professionnel

**Tâches** :
1. Installer `sonner` (`npm install sonner`)
2. Créer `frontend/components/ui/toast.tsx` (wrapper autour de sonner)
3. Créer un hook `useToast()` pour un usage centralisé
4. Remplacer tous les `alert()` dans `CrewConfig.tsx` et `ManageCrewsDialog.tsx`
5. Ajouter des toasts de feedback sur les actions CRUD (création, suppression, mise à jour)
6. Ajouter des toasts d'erreur sur les échecs API (network errors, 4xx, 5xx)

**Vérification** : `cd frontend && CI=true npm run lint` + `cd frontend && CI=true npm run build`

---

### Ticket 2 : Registry Déclaratif des Templates & Champs
**Priorité** : P0 — Fondamentale pour le wizard
**Impact** : Élimine toute la logique hardcoded de matching de crews

**Tâches** :
1. Créer `frontend/lib/registry/templates.ts` — Registry déclaratif des templates
   - Chaque template : `{ id, name, description, icon, category, fields[], crewName?, isCustom }`
   - Les templates "préfaits" pointent vers des crews existants
   - Le template "Personnalisé" permet de créer sans crew
2. Créer `frontend/lib/registry/fields.ts` — Registry des champs de formulaire
   - Chaque champ : `{ key, type, label, placeholder, validation, dependsOn }`
   - Types : `text`, `textarea`, `select`, `multiselect`, `folder`, `toggle`
3. Déplacer `getCrewDescription()` de `utils.ts` vers ce registry
4. Créer `backend/app/api/registry.py` — Endpoint pour servir les metadata
5. Supprimer le matching hardcoded de `CrewLaunchPad.tsx` (préparer le terrain pour le wizard)

**Vérification** : Backend tests + frontend lint

---

### Ticket 3 : Wizard de Création d'Automatisation (MVP)
**Priorité** : P1 — Cœur de la nouvelle UX
**Impact** : Remplace `CrewLaunchPad.tsx` par une expérience guidée

**Tâches** :
1. Créer `frontend/components/lab/AutomationWizard.tsx`
   - Barre de progression en haut (3 étapes)
   - Navigation fluide avec framer-motion (fade/slide entre les étapes)
   - Étape 1 : Grille de templates (cartes visuelles)
   - Étape 2 : Formulaire de configuration (champs du registry)
   - Étape 3 : Résumé + bouton de lancement
2. Créer `frontend/components/lab/TemplateCard.tsx` — Carte visuelle pour un template
3. Créer `frontend/components/lab/FieldRenderer.tsx` — Rendu dynamique des champs selon le registry
4. Intégrer le wizard dans `ChatWindow.tsx` (remplacer le panneau CrewLaunchPad)
5. Gérer la navigation avant/arrière avec conservation de l'état
6. Sauvegarde automatique du brouillon en localStorage

**Vérification** : Lint + build frontend

---

### Ticket 4 : Refonte de la Sidebar & Organisation des Conversations
**Priorité** : P1 — Navigation du laboratoire
**Impact** : La sidebar devient un vrai outil de navigation, pas juste une liste

**Tâches** :
1. Créer `frontend/components/sidebar/NavigationSidebar.tsx`
   - 3 onglets : `Lots` (conversations), `Laboratoire` (templates favoris), `Bibliothèque` (crews)
   - Icônes pour chaque section
2. Créer `frontend/components/sidebar/ConversationList.tsx`
   - Recherche en temps réel (filtre par titre, contenu, crew)
   - Grouping par date (Aujourd'hui, Hier, Cette semaine, Plus ancien)
   - Renommage inline (double-click sur le titre)
   - Swipe-to-delete (mobile) / bouton supprimer (desktop)
3. Créer `frontend/components/sidebar/FavoriteTemplates.tsx`
   - Liste des templates favoris avec un-star/unfavorite
4. Réduire `Sidebar.tsx` à un simple wrapper
5. Mettre à jour `app/page.tsx` pour utiliser la nouvelle sidebar

**Vérification** : Lint + build frontend

---

### Ticket 5 : Backend — Registry API + Validation YAML + Meta-Router Cache
**Priorité** : P1 — Fondations backend
**Impact** : Le backend devient fiable, rapide et sert les metadata au frontend

**Tâches** :
1. Créer `backend/app/core/crew_registry.py`
   - `CrewRegistry` class avec cache en mémoire
   - `get_all_crews()` → liste des metadata (nom, description, catégorie, champs requis)
   - `get_crew_schema()` → schéma de configuration d'un crew
   - `get_available_templates()` → templates prêts à l'emploi
2. Créer `backend/app/api/registry.py`
   - `GET /api/registry/templates`
   - `GET /api/registry/schema/{name}`
   - `GET /api/registry/agents`
3. Ajouter validation YAML avec Pydantic
   - Schéma `CrewYamlSchema` pour valider les crews avant écriture
   - Erreurs claires en cas de YAML invalide
4. Corriger le bug `\\n\\n` → `\n\n` dans `router.py`
5. Implémenter le cache du prompt système (TTL 5 min, invalidation sur modification de crew)
6. Ajouter fallback modèle dans le meta-router
7. Unifier les formats YAML (migrer `settings` → `crew_settings`)

**Vérification** : `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests --tb=short --maxfail=1`

---

## Résumé Visif du Plan

```
┌──────────────────────────────────────────────────────────────┐
│                    AUTOMATION LAB — ROADMAP                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1 — FRONTEND & DESIGN                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│  P0  [████████████████]  Toast System & Error Handling      │
│  P0  [████████████████]  Registry Déclaratif (Templates)    │
│  P1  [████████████░░]    Wizard de Création (3 étapes)      │
│  P1  [████████████░░]    Refonte Sidebar & Navigation       │
│                                                              │
│  PHASE 2 — BACKEND ENGINE                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│  P1  [████████████████]  Registry API + Validation YAML     │
│  P1  [████████████░░]    Meta-Router Cache + Fallback       │
│  P2  [██████████░░░░]    Annulation de Crews                │
│  P2  [██████████░░░░]    Sécurité (shell, imports, sandbox) │
│                                                              │
│  PHASE 3 — POLISH & AVANCÉ                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│  P3  [████████░░░░░]    AgentFlowBuilder (drag & drop)      │
│  P3  [████████░░░░░]    Micro-interactions & Animations     │
│  P3  [████████░░░░░]    Responsive Mobile                   │
│  P3  [████████░░░░░]    Internationalisation                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  5 Tickets Techniques → Voir Phase 3                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Principes Directeurs

1. **Simplicité d'abord** : Chaque écran doit être compréhensible en moins de 3 secondes. Si un champ technique est nécessaire, l'expliquer avec un tooltip.

2. **Progressive Disclosure** : L'utilisateur voit d'abord les templates prédéfinis. La configuration avancée n'apparaît que quand il clique sur "Personnalisé" ou "Paramètres avancés".

3. **Feedback immédiat** : Chaque action a un retour visuel (toast, animation, changement d'état). L'utilisateur ne se demande jamais "ça a marché ?".

4. **Zéro surprise** : Les erreurs sont anticipées et expliquées clairement. Pas de `alert()` brute, pas de crash silencieux.

5. **Consistance** : Tous les composants partagent le même design system (couleurs, espacements, typographie, animations). Rien ne semble "importé".

6. **Performance perçue** : Les skeleton screens, les optimistic updates et les transitions fluides donnent l'impression que l'application est instantanée.
