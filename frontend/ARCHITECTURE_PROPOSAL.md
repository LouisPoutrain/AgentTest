# Proposition d'Évolution Architecturale - Projet Frontend Next.js

## 1. Contexte et Diagnostic
Le projet actuel utilise une stack moderne et performante : **Next.js 16.3.3**, **React 19.2.8**, **Tailwind CSS 4** et **Shadcn UI**. L'architecture est basée sur l'**App Router** avec une séparation Client/Serveur. Cependant, pour passer d'un prototype à une application d'entreprise robuste, des optimisations architecturales sont nécessaires.

## 2. Améliorations Majeures Proposées

### A. Optimisation du Rendu avec Streaming et Suspense Boundaries
**Problème actuel** : L'application utilise les Server Components par défaut, mais il est crucial de garantir que le chargement initial ne soit pas bloqué par des requêtes asynchrones longues.

**Proposition** :
*   Implémenter des frontières de `Suspense` autour des composants qui dépendent de données externes ou de calculs lourds.
*   Utiliser le streaming natif de Next.js pour afficher le contenu progressivement (Skeletons UI).
*   **Avantage** : Amélioration significative du **TTFB** (Time to First Byte) et du **LCP** (Largest Contentful Paint), améliorant le SEO et l'expérience utilisateur.

**Référence** : 
*   [Next.js Documentation: App Router & Data Fetching](https://nextjs.org/docs/app) - Section sur le Streaming et le Suspense.

### B. Adoption du React Compiler et Simplification de la Mémoïsation
**Problème actuel** : Le code React traditionnel nécessite une mémoïsation manuelle (`useMemo`, `useCallback`) pour éviter les re-rendus inutiles, ce qui complexifie le code.

**Proposition** :
*   Migrer vers les bonnes pratiques du **React Compiler** (intégré à React 19). Ce compilateur automatise la mémoïsation, permettant d'écrire du code plus lisible et plus performant sans annotations manuelles.
*   Réviser les composants pour éviter les closures défectueuses et les dépendances de tableaux.
*   **Avantage** : Code plus maintenable, moins de bugs liés aux dépendances de hooks, et performances optimisées automatiquement.

**Référence** : 
*   [React 19 Blog Post](https://react.dev/blog/2024/12/05/react-19) - Introduction au React Compiler.

### C. Centralisation des Mutations avec Server Actions
**Problème actuel** : L'application semble avoir une séparation frontend/backend. Les mutations (création, mise à jour) pourraient passer par des appels API REST/GraphQL externes.

**Proposition** :
*   Remplacer les appels API directs pour les mutations par des **Next.js Server Actions**. Cela permet d'exécuter du code côté serveur directement depuis les composants clients ou serveurs.
*   Utiliser `useFormStatus` pour gérer les états de chargement des formulaires.
*   **Avantage** : Sécurité accrue (pas d'exposition de routes API publiques pour les mutations), typage fort via TypeScript, et intégration native avec le cache de Next.js.

**Référence** : 
*   [Next.js Documentation: Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)

## 3. Outils et Bibliothèques Recommandés

1.  **`next-themes`** : Déjà utilisé, continuer pour la gestion du thème sombre/clair.
2.  **`class-variance-authority` (CVA)** : Déjà utilisé, continuer pour la gestion des variantes de composants Shadcn.
3.  **`tailwind-merge`** : Déjà utilisé, essentiel pour la composition des classes.
4.  **`react-markdown` + `rehype-highlight`** : Déjà utilisé pour le rendu de contenu riche, maintenir cette stack pour la visualisation de réponses d'agents IA.

## 4. Étapes de Migration

1.  **Audit des Composants** : Identifier les composants qui peuvent être transformés en Server Components ou qui nécessitent des `Suspense` boundaries.
2.  **Refactoring des Hooks** : Remplacer les `useMemo` et `useCallback` manuels par du code standard pour profiter du React Compiler.
3.  **Implémentation des Server Actions** : Migrer les mutations de données (ex: envoi de messages, sauvegarde de préférences) vers des Server Actions.
4.  **Tests E2E** : Mettre en place **Playwright** pour tester les flux critiques (Login, Envoi de message, Affichage du rendu Markdown).

## 5. Conclusion
En suivant cette proposition, le projet bénéficiera d'une architecture plus performante, plus sécurisée et plus facile à maintenir, alignée avec les dernières innovations de l'écosystème React et Next.js.
