# InteractiveCourseCreator — Crew de Création de Cours Interactifs Multi-PDF

## Présentation

Le **InteractiveCourseCreator** transforme un **dossier contenant un ou plusieurs PDF** en un **cours interactif complet** : un site web HTML/CSS/JS autonome avec leçons, exercices, quiz, dark mode et suivi de progression.

### Ce que ce crew fait :
- **Inventorie** tous les PDF du dossier (recherche récursive, y compris sous-dossiers)
- **Analyse chaque PDF en profondeur** (en boucle, résumable — un PDF par itération)
- **Vérifie** que tous les PDF ont bien été analysés (agent dédié)
- **Enrichit** le contenu avec des recherches web (Wikipedia, arXiv, web)
- **Structure** le cours selon la Taxonomie de Bloom
- **Rédige** les leçons, **conçoit** les exercices (QCM, QCU, vrai/faux, études de cas, projet de synthèse)
- **Génère** un site web moderne (dark mode, responsive, quiz interactifs, progression en localStorage)
- **Valide** la qualité (5 axes) et **corrige** automatiquement les problèmes détectés

---

## Pipeline (11 agents séquentiels)

```
1. PDFInventory      → 00_pdf_manifest.json          (liste exhaustive des PDF)
2. PDFAnalyst        → 01_analysis_<slug>.json ×N    (analyse par PDF, boucle résumable)
                      → 01_analysis.json             (fusion de toutes les analyses)
3. AnalysisVerifier  → 02_analysis_verification.json (vérif. complétude X/Y PDF)
4. ContentEnricher   → 03_enriched_content.json      (recherches web, analogies, exemples)
5. PedagogyArchitect → 04_course_structure.json      (modules, Bloom, prérequis)
6. ContentWriter     → 05_lesson_content.md          (leçons complètes en Markdown)
7. ExerciseDesigner  → 06_exercises.json             (QCM, QCU, V/F, pratiques, cas, synthèse)
8. WebDesigner       → 07_website_design.json        (design system complet)
9. HTMLGenerator     → index.html, modules/, exercises/, assets/
10. QualityReviewer  → 08_review_report.json         (rapport d'action, scores 0-100)
11. QualityFixer     → 09_fixes_applied.json         (corrections appliquées si besoin)
```

### Boucle d'analyse résumable
L'étape 2 (PDFAnalyst) traite les PDF **un par un** et sauvegarde chaque analyse dans
`01_analysis_<slug>.json`. Si l'agent atteint sa limite d'itérations, **relancer le crew
reprend là où il s'est arrêté** : les PDF déjà analysés sont détectés et sautés.

### Vérification de qualité
- **AnalysisVerifier** (étape 3) : garantit qu'aucun PDF n'a été oublié avant de continuer.
- **QualityReviewer** (étape 10) : audit final sur 5 axes (complétude, précision, cohérence
  pédagogique, qualité technique, UX) avec score 0-100 et statut
  `APPROVED` / `APPROVED_WITH_CORRECTIONS` / `REJECTED`.
- **QualityFixer** (étape 11) : applique les corrections du rapport (priorité
  critical → major → minor) et documente ce qui a été fait dans `09_fixes_applied.json`.

---

## Comment déclencher le pipeline

### Option 1 — Via l'application (chat)
Donner simplement le chemin du dossier contenant les PDF :

```
Crée un cours interactif à partir du dossier /Users/poutrainlouis/Code/Cours/SWO
```

Le routeur détecte la demande, passe `project_path` au crew, et `chat.py` injecte
automatiquement `output_dir` (`<dossier>/cours_interactif`) et la liste des PDF.

### Option 2 — Via l'API
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crée un cours interactif à partir de ce dossier",
    "crew_name": "InteractiveCourseCreator",
    "inputs": { "project_path": "/chemin/vers/le/dossier" }
  }'
```

### Option 3 — Via Python
```python
from app.core.crew_runner import run_crew

for chunk in run_crew(
    crew_name="InteractiveCourseCreator",
    message="Crée un cours interactif à partir de ce dossier",
    inputs={"project_path": "/chemin/vers/le/dossier"},
):
    print(chunk)
```

### Variables d'entrée
| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `project_path` | Requis | Chemin du dossier contenant les PDF (recherche récursive) |
| `output_dir` | Optionnel | Dossier de sortie (défaut : `<project_path>/cours_interactif`) |
| `pdf_path` | Optionnel | PDF principal (optionnel — le crew détecte tout seul) |
| `pdf_alternatives` | Optionnel | Autres PDF (optionnel — le crew détecte tout seul) |

---

## Structure de sortie

```
<dossier>/cours_interactif/
├── 00_pdf_manifest.json            # Inventaire des PDF (id, chemin, slug)
├── 01_analysis_<slug>.json         # Analyse individuelle par PDF
├── 01_analysis.json                # Analyse fusionnée (concepts, formules, structure)
├── 02_analysis_verification.json   # Vérification de complétude (X/Y PDF)
├── 03_enriched_content.json        # Contenu enrichi (web, analogies, glossaire)
├── 04_course_structure.json        # Structure pédagogique (modules, Bloom)
├── 05_lesson_content.md            # Leçons complètes (Markdown)
├── 06_exercises.json               # Exercices (QCM, QCU, V/F, pratiques, cas)
├── 07_website_design.json          # Spécification de design
├── 08_review_report.json           # Rapport qualité (scores, corrections)
├── 09_fixes_applied.json           # Corrections appliquées par le QualityFixer
├── index.html                      # Page d'accueil du cours
├── modules/
│   └── module-NN-nom.html          # Une page par module
├── exercises/
│   ├── exercises-QCM.html
│   ├── exercises-QCU.html
│   ├── exercises-vf.html
│   ├── exercises-pratique.html
│   ├── exercises-cas.html
│   └── exercises-synthese.html
└── assets/
    ├── style.css                   # Design system complet (light + dark)
    └── interactive.js              # Quiz, navigation, progression (localStorage)
```

**Ouvrir le cours** : `open <dossier>/cours_interactif/index.html`

---

## Configuration

- **Fichier du crew** : `backend/config/crews/InteractiveCourseCreator.yaml`
- **Modèles** : chaque agent a `llm: "openai/"` (préfixe LiteLLM) — le modèle effectif
  est injecté via `llm_override` (défaut : `openai/qwen-3.6-35b-instruct`).
- **Sécurité** : les outils fichier passent par `PathManager` — les dossiers accessibles
  sont ceux sous `PROJECT_ROOT` (voir `backend/.env`, actuellement `/Users/poutrainlouis/Code`).
- **Outil dédié** : `list_pdfs` (recherche récursive des PDF) dans
  `backend/app/tools/custom_tools.py`, enregistré dans `tool_registry.py`.

## Temps d'exécution estimé

| Phase | Durée estimée |
|-------|---------------|
| Inventaire + analyse (par PDF) | 2-5 min / PDF |
| Vérification | 1-2 min |
| Enrichissement web | 3-8 min |
| Structure + rédaction | 5-15 min |
| Exercices + design | 5-10 min |
| Génération HTML | 5-15 min |
| Revue + corrections | 5-10 min |
| **Total (3-5 PDF)** | **~30-70 min** |

## Tests

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests/test_agent_parser.py --tb=short
```
