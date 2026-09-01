# Plan de refonte graphique du frontend

## Objectif
Créer une interface moderne, cohérente et agréable tout en conservant la logique fonctionnelle existante. Le redesign doit :
- Utiliser **Tailwind CSS v4** avec un thème personnalisé (couleurs, typographie). 
- Exploiter les composants **Shadcn‑UI** (Button, Dialog, Select, etc.) déjà présents mais les styliser davantage.
- Introduire un **système de design** (tokens, variants) afin que chaque composant partage les mêmes règles visuelles.
- Améliorer l’**experience utilisateur** (accessibilité, dark mode, transitions fluides, responsive).
- Ne pas modifier la logique métier : les API, stores Zustand et le flow du Chat restent inchangés.

---

## 1️⃣ Analyse de l’existant
| Dossier / Fichier | Rôle | Points d’amélioration |
|-------------------|------|-----------------------|
| `components/ui/*.tsx` | Bibliothèque de composants UI de base | Les variantes de couleur et de taille sont déjà gérées via `cva`, mais les palettes sont trop génériques. |
| `components/chat/*.tsx` | UI du chat (ChatWindow, MessageBubble, ChatInput…) | Layout fonctionnel mais visuellement plat ; manque de spacings, de focus states, de contraste dark mode. |
| `components/sidebar/*.tsx` | Sidebar de navigation et configuration des crews | Couleurs très neutres, icônes peu mises en avant, pas de séparateur visuel. |
| `tailwind.config.ts` (non présent) | Configuration Tailwind | Utilise la configuration par défaut ; aucune palette personnalisée, pas de dark mode activé. |
| `next.config.ts` | Configuration Next.js | Aucun impact graphique. |

## 2️⃣ Stack technique recommandée
- **Tailwind CSS v4** (déjà en dépendance) : profiter du mode `jit` et des **design tokens**.
- **shadcn/ui** (déjà installé) : continuer à l’utiliser comme base, mais créer un **theme wrapper** (`src/theme.ts`) contenant les variables de couleur, border‑radius, etc.
- **class‑variance‑authority** : garder les variants, ajouter des **styles globaux** via `cva` afin d’éviter la duplication.
- **lucide‑react** pour les icônes : ajouter des variantes `stroke` adaptées au dark mode.
- **tailwind‑merge** pour combiner intelligemment les classes.
- **framer‑motion** (optionnel) : petites animations d’apparition/dissolution.

## 3️⃣ Modifications proposées
### 3.1 `tailwind.config.ts`
Créer ce fichier à la racine de `frontend/` :
```ts
import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';
import animate from 'tailwindcss-animate';

export default <Config>{
  darkMode: ['class'], // enable class‑based dark mode
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'hsl(var(--color-primary))',
          foreground: 'hsl(var(--color-primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--color-secondary))',
          foreground: 'hsl(var(--color-secondary-foreground))',
        },
        // … ajouter les autres tokens (accent, destructive, muted, background, border, text)
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [typography, animate],
};
``` 
Ce fichier introduit **des variables CSS** (`--color-primary`, `--radius`, …) que l’on pourra paramétrer dans `src/theme.ts`.

### 3.2 `src/theme.ts`
```ts
export const theme = {
  '--color-primary': '222 45% 55%', // hue, sat, light (hsl)
  '--color-primary-foreground': '0 0% 100%',
  '--color-secondary': '210 20% 30%',
  '--color-secondary-foreground': '0 0% 100%',
  '--color-background': '0 0% 100%',
  '--color-foreground': '222 15% 15%',
  '--color-muted': '210 10% 95%',
  '--color-muted-foreground': '210 5% 45%',
  '--color-accent': '165 70% 45%',
  '--color-accent-foreground': '0 0% 100%',
  '--radius': '0.5rem',
};
```
Ce module sera importé dans le composant racine (`app/layout.tsx`) et injecté via `<html style={theme}>`.

### 3.3 Refactorisation des composants UI
| Composant | Action | Exemple de changement |
|-----------|--------|-----------------------|
| `Button` | Utiliser les nouvelles **tokens** (`bg-primary`, `text-primary-foreground`). Ajouter `transition-colors`. | `className={cn('transition-colors', buttonVariants({variant, size, className}))}` |
| `MessageBubble` | Ajouter un **bordure légère** et un **fond** qui dépend du rôle (assistant vs user). Utiliser `rounded-xl` et `shadow-sm`. | `className={cn('bg-muted/50 dark:bg-muted/30', role === 'assistant' && 'border-l-4 border-primary')}` |
| `ChatWindow` | Introduire un **header** avec un gradient de fond, rendre le **scroll** plus fluide (`scroll-smooth`). | `className="flex flex-col h-full overflow-y-auto scroll-smooth"` |
| `Sidebar` | Séparer les sections avec `divide-y` et ajouter des **hover effects** sur les items. | `className="hover:bg-muted/30 transition-colors"` |
| `CrewSelector` | Remplacer le `Select` par le composant `shadcn/ui` déjà stylisé, mais ajouter un **placeholder** plus descriptif. |
| `Dialog` (ex: `CrewLaunchPad`) | Appliquer `animate-in`/`animate-out` de `tailwind‑animate` pour le fade‑in/fade‑out. |

### 3.4 Ajout de nouveaux composants décoratifs
- **`Header.tsx`** : barre supérieure fixe avec le logo, le sélecteur de thème (light / dark) et le statut du crew.
- **`Footer.tsx`** : lien vers la documentation, copyright, petit texte d’attribution.
- **`ThemeToggle.tsx`** : bouton qui bascule la classe `dark` sur `<html>`.

### 3.5 Gestion du **dark mode**
Dans `app/layout.tsx` :
```tsx
import { theme } from '@/theme';
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full" style={theme}>
      <body className="bg-background text-foreground antialiased h-full">
        {children}
      </body>
    </html>
  );
}
```
Le `ThemeToggle` modifiera `document.documentElement.classList.toggle('dark')`.

### 3.6 Tests de régression visuelle (manuel)
1. Lancer `npm run dev`.
2. Vérifier que toutes les pages (chat, sidebar, configuration) s’affichent correctement en **light** et **dark**.
3. S’assurer que le flux **Chat → API → UI** fonctionne comme avant (aucune modification du store ou des appels).  
4. Utiliser le navigateur pour tester la **responsivité** (mobile, tablette, desktop).

## 4️⃣ Plan d’action détaillé (chronologique)
| Étape | Description | Fichiers impactés | Durée estimée |
|------|-------------|-------------------|--------------|
| 1️⃣ Créer `tailwind.config.ts` & `src/theme.ts` | Mise en place du design‑system. | `tailwind.config.ts`, `src/theme.ts` | 0.5 j |
| 2️⃣ Adapter le layout global | Injection du thème et du dark mode. | `app/layout.tsx` | 0.5 j |
| 3️⃣ Refactoriser les composants UI | Mise à jour des variantes, ajout de transitions. | `components/ui/*.tsx`, `components/chat/*.tsx`, `components/sidebar/*.tsx` | 1 j |
| 4️⃣ Ajouter les nouveaux composants décoratifs | Header, Footer, ThemeToggle. | `components/Header.tsx`, `components/Footer.tsx`, `components/ThemeToggle.tsx` | 0.5 j |
| 5️⃣ Mettre à jour les imports & routes | Exporter les nouveaux composants depuis `components/index.ts` et les utiliser dans les pages. | `app/page.tsx`, `components/**/index.ts` | 0.5 j |
| 6️⃣ Tests manuels & ajustements | Vérifier l’apparence et le bon fonctionnement. | – | 0.5 j |
| **Total** | – | – | **≈ 4 jours** |

## 5️⃣ Risques & mitigations
- **Risque :** rupture du CSS existant → **Mitigation** : les changements sont purement **additionnels** (extensions de `cva`), aucune classe CSS n’est retirée.
- **Risque :** incompatibilité avec le serveur Next.js (SSR) → **Mitigation** : le thème utilise uniquement le **style inline** côté client, le rendu SSR reste identique.
- **Risque :** régression fonctionnelle du Chat → **Mitigation** : aucun fichier de logique (`lib/store.ts`, `lib/api.ts`) n’est touché.

## 6️⃣ Livraison
Le fichier présent **`FRONTEND_REDESIGN_PLAN.md`** résume ce plan. Une fois le plan approuvé, les développeurs pourront appliquer les modifications pas à pas en suivant le tableau ci‑dessus.

---

*Ce document a été généré par le Méta‑Orchestrateur IA afin de guider la refonte graphique du projet Frontend sans impacter la logique métier.*
