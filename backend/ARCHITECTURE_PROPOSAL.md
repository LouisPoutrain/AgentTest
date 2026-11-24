# Plan d'Architecture & Implémentation : Archify

## Dossier cible
`../archify/`

## 1. Stack Technique

Pour garantir performance, maintainabilité et évolutivité (SaaS), voici la stack recommandée :

*   **Framework Principal (Fullstack SaaS) :** **Next.js 14+ (App Router)**
    *   Permet de gérer le Frontend (React), l'API Backend (Serverless Functions), et l'authentification.
    *   SSR/SSG pour les pages publiques, CSR pour le dashboard interactif.
*   **Langage :** **TypeScript** (Strict mode) pour la sécurité des types, crucial pour le parsing YAML/JSON complexe.
*   **Styling :** **Tailwind CSS** v3.4+ pour le style rapide et cohérent.
*   **Base de Données :** **PostgreSQL** (via Neon ou Supabase) stockée avec **Prisma ORM**.
    *   Table `User`, `Diagram`, `Version`.
*   **Moteur de Rendu (Core Library) :** **Node.js Library** (bundled as ES Module)
    *   Utilisera `js-yaml` pour le parsing.
    *   Utilisera `dagre` pour le calcul de layout (positionnement automatique des nœuds).
    *   Utilisera `svg2pdf` ou manipulation directe du DOM SVG pour la génération du fichier HTML standalone auto-contenu.
*   **Gestion de Projet :** **Turborepo** (Monorepo) pour séparer la logique métier (Core) de l'interface utilisateur (App).

---

## 2. Arborescence des fichiers

Voici la structure exacte à créer dans `../archify/` :

```
archify/
├── .gitignore
├── package.json              # Root workspace
├── turbo.json                # Turborepo config
├── README.md
│
├── apps/
│   └── web/                  # Next.js Application
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx          # Landing page
│       │   │   ├── dashboard/        # Protected Dashboard
│       │   │   │   ├── page.tsx
│       │   │   │   └── new/          # Create diagram flow
│       │   │   │       └── page.tsx
│       │   │   ├── api/
│       │   │   │   └── diagrams/
│       │   │   │       ├── route.ts      # CRUD API
│       │   │   │       └── generate/
│       │   │   │           └── route.ts  # Triggers rendering
│       │   │   └── components/
│       │   │       ├── editor/
│       │   │       │   ├── CodeEditor.tsx
│       │   │       │   └── VisualPreview.tsx
│       │   │       ├── ui/               # Shadcn/UI components
│       │   │       └── layout/           # Header, Sidebar
│       │   ├── lib/
│       │   │   ├── auth.ts             # Auth helpers (Clerk/Auth.js)
│       │   │   └── db.ts               # Prisma Client singleton
│       │   └── styles/                 # Global CSS
│       └── public/
│           ├── fonts/
│           └── images/
│
├── packages/
│   └── core-engine/        # Core Logic Library (Rendering & Parsing)
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           ├── index.ts                # Exports
│           ├── parser/                 # YAML/JSON Parsers
│           │   ├── yamlParser.ts
│           │   ├── jsonParser.ts
│           │   └── types.ts            # Shared Types (Node, Edge, Diagram)
│           ├── renderer/               # SVG/HTML Generation
│           │   ├── svgGenerator.ts
│           │   ├── layoutCalculator.ts # Dagre integration
│           │   └── htmlSandbox.ts      # Wraps SVG in standalone HTML
│           └── styles/                 # Default CSS templates for diagrams
│               ├── dark.css
│               └── light.css
```

---

## 3. Spécification détaillée fichier par fichier

### A. Packages Core (`packages/core-engine/`)

1.  **`src/parser/types.ts`**
    *   Définition des interfaces TypeScript strictes : `Node`, `Edge`, `Diagram`, `Metadata`.
    *   C'est la source de vérité pour la structure de données.
2.  **`src/parser/yamlParser.ts`**
    *   Fonction `parseYaml(content: string): Diagram`.
    *   Utilise `js-yaml`.
    *   Mapping des champs YAML bruts vers le modèle `Diagram` standardisé.
    *   Validation basique (ex: vérifier que les IDs de source/cible existent).
3.  **`src/parser/jsonParser.ts`**
    *   Fonction `parseJson(content: string): Diagram`.
    *   Utilise `JSON.parse` + validation schéma (Zod recommandé).
4.  **`src/renderer/layoutCalculator.ts`**
    *   Fonction `calculateLayout(nodes: Node[], edges: Edge[])`.
    *   Utilise `dagre` pour déterminer les coordonnées X/Y optimales sans croisement excessif.
5.  **`src/renderer/svgGenerator.ts`**
    *   Fonction `generateSVG(diagram: DiagramWithLayout): string`.
    *   Génère le code SVG brut.
    *   Applique les styles CSS dynamiquement basés sur le thème (Dark/Light).
    *   Gère les formes (carrés pour services, cylindres pour DB, etc.).
6.  **`src/renderer/htmlSandbox.ts`**
    *   Fonction `generateStandaloneHTML(diagramWithLayout): string`.
    *   Prend le SVG et les styles CSS.
    *   Les injecte dans un squelette HTML5 complet (`<!DOCTYPE html>...`).
    *   Ajoute des scripts JS minimes pour le zoom/pan (si nécessaire) ou utilise CSS scroll-snap.
    *   Retourne la chaîne de caractères prête au téléchargement.

### B. Application Web (`apps/web/`)

1.  **`src/app/api/diagrams/route.ts`**
    *   `POST`: Crée un nouveau diagramme dans la BDD (Prisma). Récupère le YAML du body, appelle le `core-engine` pour valider, mais ne rend pas encore.
    *   `GET`: Liste les diagrammes de l'utilisateur.
2.  **`src/app/api/diagrams/generate/route.ts`**
    *   `POST`: Reçoit un `diagramId`.
    *   Récupère le diagramme de la BDD.
    *   Appelle `core-engine` pour le rendu final (Layout + HTML).
    *   Retourne le HTML généré au client ou sauvegarde la version finale.
3.  **`src/app/dashboard/new/page.tsx`**
    *   Interface split-screen : Éditeur de code (gauche) et Prévisualisation (droite).
    *   Utilise une bibliothèque comme `monaco-editor` (VS Code style) pour l'édition YAML.
    *   Bouton "Générer le Fichier HTML" qui appelle l'API generate.

---

## 4. Étapes de développement pour le CrewManager

### Phase 1 : Configuration & Fondations
1.  Initialiser le repository Git et le structure Monorepo (Turborepo).
2.  Configurer TypeScript et ESLint partagés.
3.  Créer le package `core-engine` et définir les interfaces `types.ts` (Node, Edge, Diagram).

### Phase 2 : Le Moteur de Rendu (Core)
4.  Implémenter `yamlParser.ts` pour lire le fichier `Directory_Archifier.yaml` fictif et le mapper vers le JSON interne.
5.  Intégrer `dagre` pour calculer les positions X/Y des nœuds.
6.  Implémenter `svgGenerator.ts` pour dessiner les nœuds et les arêtes dans un SVG.
7.  Implémenter `htmlSandbox.ts` pour envelopper le tout dans un fichier HTML autonome.
8.  *Unit Tests :* Tester avec des YAML complexes (cycles, grands graphes, nœuds orphelins).

### Phase 3 : Interface & API
9.  Configurer Next.js App Router et Tailwind CSS.
10. Mettre en place l'authentification (ex: Clerk ou NextAuth) pour gérer les utilisateurs.
11. Créer le schéma Prisma (`User`, `Diagram`).
12. Développer les API Routes (`/api/diagrams`).
13. Développer le composant `VisualPreview` qui fait un rendu live du SVG (sans passer par le fichier HTML final pour la prévisualisation, pour la performance).

### Phase 4 : UX & Finalisation
14. Implémenter les thèmes Dark/Light dans le CSS généré.
15. Ajouter l'exportation du fichier `.html`.
16. Ajustements UI (Zones de drop, Toasts de succès/erreur).
17. Documentation et déploiement (Vercel).

---

## 5. Notes Techniques

*   **Performance du Rendu :** Pour les très grands diagrammes (>50 nœuds), le calcul de layout peut être coûteux. Il est recommandé de l'exécuter côté serveur (Worker) ou en mode async dans l'API si la complexité augmente.
*   **Sécurité :** Le HTML généré par l'utilisateur peut contenir du script (XSS). Cependant, comme c'est un fichier téléchargé et ouvert localement, le risque est limité à l'environnement local. Si une fonctionnalité de "Lien Public" est ajoutée plus tard (V2), l'iframe contenant le SVG doit avoir `sandbox` attributs stricts.
*   **Gestion des Styles :** Les styles SVG doivent être injectés dans une balise `<style>` dans le `<head>` du HTML final, et non via des classes externes, pour garantir l'autonomie du fichier.

## Prochaine étape
Valider cette architecture avec l'équipe de développement avant de lancer l'initialisation du projet.