# Proposition d'Évolution Architecturale

**Date :** 2024
**Projet :** Application Next.js / React 19 / Tailwind v4

## Contexte
Ce document détaille les recommandations stratégiques pour l'évolution de l'architecture frontend actuelle. Basé sur un diagnostic technique solide (Stack moderne : Next.js, React 19, Tailwind v4, Prisma, Zustand) et les dernières best practices de l'industrie (Tendances Islands Architecture, Server Components), ce plan vise à améliorer la performance, la maintenabilité et la scalabilité.

---

## 1. Améliorations Majeures Proposées

### A. Adopts une Gestion d'État Hybride (Zustand + TanStack Query)
**Type :** Ajout de lib / Refacto logique

**Description :**
Bien que **Zustand** soit excellent pour l'état client (modals, thèmes, préférences), il n'est pas optimisé pour le cache de données serveur complexes. La tendance actuelle (Best Practice 2024-2025) recommande d'utiliser **TanStack Query (React Query)** pour la gestion des données asynchrones (fetched data, caching, invalidation).

**Justification & Références :**
*   **Séparation des préoccupations :** Comme souligné dans la *Référence 1 (Next.js Full Course - FreeCodeCamp)*, séparer l'état UI de l'état données évite la surcharge de Zustand et simplifie la logique.
*   **Performance :** TanStack Query gère nativement le déduplication des requêtes, le retry et le background refetching, ce qui est complexe à reproduire proprement avec un store global standard.
*   **Référence 3 (TanStack Query Documentation)** confirme que la combinaison Prisma + TanStack Query est le standard industriel pour éviter les données "stale".

**Migration :**
1.  Installer `@tanstack/react-query`.
2.  Créer un provider `QueryClientProvider` au niveau racine (`layout.tsx`).
3.  Migrer les appels `fetch` manuels dans les composants vers des fonctions `queryOptions` ou `useQuery`.
4.  Conserver Zustand uniquement pour l'état purement visuel (ex: `isSidebarOpen`).

---

### B. Restriction Stricte des "Client Boundaries" (Server Components First)
**Type :** Changer de design pattern (RSC Strictness)

**Description :**
Adopter une approche **"Server Components by Default"**. Aucun composant ne doit avoir `'use client'` sauf si absolument nécessaire (interactivité directe comme `onClick`, `useState` local, hooks navigateur).

**Justification & Références :**
*   **Réduction du Bundle (Zero JS) :** Les React Server Components (RSC) ne sont pas inclus dans le bundle JavaScript envoyé au client, réduisant drastiquement le temps de chargement initial.
*   **Sécurité Prisma :** La *Référence 2 (React 19 Blog / Vercel)* souligne que l'accès direct à Prisma doit se faire côté serveur. En forçant les données à venir des Server Components, on élimine le risque de fuites de données ou d'attaques API directes depuis le client.
*   **Hook `use` (React 19) :** Utiliser le nouveau hook `use` (décrit dans *Référence 2*) pour consommer les Promises dans les composants serveur, rendant le code asynchrone plus déclaratif.

**Migration :**
1.  Auditer les composants marqués `'use client'`. Supprimer l'annotation si le composant n'utilise ni hooks React ni écouteurs d'événements DOM.
2.  Déplacer la logique de fetching (Prisma) dans les composants Serveurs ou des Server Actions.
3.  Passer les données comme props aux composants fils, même s'ils sont clients.

---

### C. Migration vers la Configuration Tailwind v4 Natif
**Type :** Mise à jour configuration / Outils

**Description :**
Profiter de la refonte complète de Tailwind CSS v4 (moteur Oxide/Rust) pour supprimer le fichier `tailwind.config.js` au profit d'une configuration CSS native via la directive `@theme`.

**Justification & Références :**
*   **Performance :** Le moteur v4 est significativement plus rapide que le moteur PostCSS de la v3 (Recommandation Concrete 3).
*   **Simplicité :** Plus besoin de maintenir une configuration JS complexe pour les extensions ou les couleurs.
*   **Reference 2 (Tailwind v4 Trends) :** L'approche actuelle privilégie l'utilisation de variables CSS natives pour les tokens de design, rendant le thème dynamique (sombre/clair) plus performant.

**Migration :**
1.  Supprimer `tailwind.config.js`.
2.  Mettre à jour `src/app/globals.css` :
    ```css
    @import "tailwindcss";

    @theme {
      --color-primary: #your-hex-code;
      --font-sans: var(--font-inter);
      /* ... autres tokens ... */
    }
    ```
3.  Vérifier que `postcss.config.js` pointe vers le plugin Tailwind v4 `@tailwindcss/postcss`.

---

## 2. Plan de Migration Étapes

1.  **Phase 1 : Sécurisation & Fondations (Semaine 1)**
    *   Configurer `QueryClient` avec TanStack Query.
    *   Mettre à jour Tailwind v4 (`@theme` syntax).
    *   Vérifier que `next.config.ts` n'a pas besoin de règles de sécurité supplémentaires pour les API Routes.

2.  **Phase 2 : Migration des Données (Semaine 2-3)**
    *   Identifier les pages principales utilisant Prisma.
    *   Remplacer les `fetch` internes par des `useQuery` (coté client) ou des fetchs directs dans les Server Components (coté serveur).
    *   Supprimer l'usage de Prisma dans les composants Clients.

3.  **Phase 3 : Nettoyage et Optimisation (Semaine 4)**
    *   Analyser le bundle avec `@next/bundle-analyzer`.
    *   Supprimer les directives `'use client'` inutiles.
    *   Refactorer les petits stores Zustand non nécessaires vers des contextes ou des états locaux.

## 3. Outils Recommandés
*   **État Serveur :** `@tanstack/react-query`
*   **Styling :** `tailwindcss@4` (via `@tailwindcss/postcss`)
*   **Analyse Bundle :** `@next/bundle-analyzer`
*   **Linting :** `eslint-config-next` (mis à jour pour React 19 rules)

## Conclusion
Cette évolution positionne le projet à la pointe de la technologie web moderne. En combinant la puissance des Server Components, la robustesse de TanStack Query et la rapidité de Tailwind v4, nous obtenons une application non seulement plus performante, mais aussi mieux structurée pour évoluer à grande échelle.
