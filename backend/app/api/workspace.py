"""API routes pour l'exploration dynamique et la découverte des projets et dossiers de l'espace de travail."""

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

# Déterminer la racine de travail (dossier parent contenant les projets)
CURRENT_PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[4]))


class ProjectInfo(BaseModel):
    name: str
    path: str
    absolute_path: str
    is_current: bool = False
    framework: str
    tags: list[str]
    has_git: bool = False
    has_tests: bool = False
    has_package_json: bool = False
    last_modified: float


class DirectoryItem(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    has_subdirs: bool = False


class BrowseResponse(BaseModel):
    current_path: str
    absolute_path: str
    parent_path: Optional[str] = None
    breadcrumbs: list[dict[str, str]]
    directories: list[DirectoryItem]
    files_count: int


def _detect_stack(dir_path: Path) -> tuple[str, list[str]]:
    """Détecte intelligemment les frameworks, langages et bibliothèques d'un dossier."""
    tags: list[str] = []
    framework = "Projet"

    # Vérification Node / JavaScript / TypeScript
    pkg_file = dir_path / "package.json"
    if pkg_file.exists() and pkg_file.is_file():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "next" in deps:
                    framework = "Next.js"
                    tags.append("Next.js")
                elif "react" in deps:
                    framework = "React"
                    tags.append("React")
                elif "vue" in deps:
                    framework = "Vue"
                    tags.append("Vue")
                elif "svelte" in deps or "@sveltejs/kit" in deps:
                    framework = "Svelte"
                    tags.append("Svelte")
                elif "express" in deps or "fastify" in deps:
                    framework = "Node.js API"
                    tags.append("Node.js")
                else:
                    framework = "Node.js"
                    tags.append("Node.js")

                if "typescript" in deps or (dir_path / "tsconfig.json").exists():
                    tags.append("TypeScript")
                if "prisma" in deps or "@prisma/client" in deps or (dir_path / "prisma").exists():
                    tags.append("Prisma")
                if "tailwindcss" in deps:
                    tags.append("Tailwind")
                if "vitest" in deps:
                    tags.append("Vitest")
                elif "jest" in deps:
                    tags.append("Jest")
        except Exception:
            tags.append("Node.js")

    # Vérification Python
    has_py = any(dir_path.glob("*.py")) or (dir_path / "requirements.txt").exists() or (dir_path / "pyproject.toml").exists()
    if has_py:
        if not tags or framework == "Projet":
            framework = "Python"
        tags.append("Python")
        
        req_file = dir_path / "requirements.txt"
        pyproject = dir_path / "pyproject.toml"
        content = ""
        if req_file.exists():
            try:
                content += req_file.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                pass
        if pyproject.exists():
            try:
                content += pyproject.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                pass

        if "fastapi" in content or (dir_path / "app").exists():
            tags.append("FastAPI")
            if framework == "Python":
                framework = "FastAPI"
        if "crewai" in content:
            tags.append("CrewAI")
        if "pytest" in content:
            tags.append("Pytest")
        if "django" in content:
            tags.append("Django")
            framework = "Django"

    if (dir_path / ".git").exists():
        tags.append("Git")

    if not tags:
        tags.append("Dossier")

    return framework, list(dict.fromkeys(tags))


def _resolve_safe_path(input_path: str) -> Path:
    """Résout un chemin de manière sécurisée par rapport au dossier racine ou du projet."""
    clean = input_path.strip()
    if not clean or clean == ".":
        target = CURRENT_PROJECT_ROOT
    elif clean.startswith("/"):
        target = Path(clean).resolve()
    else:
        target = (CURRENT_PROJECT_ROOT / clean).resolve()

    # Vérifier que le chemin reste dans WORKSPACE_ROOT ou est un descendant valide
    try:
        # Autoriser les chemins situés dans WORKSPACE_ROOT (/Users/.../Code)
        if WORKSPACE_ROOT.resolve() in target.parents or target == WORKSPACE_ROOT.resolve() or target == CURRENT_PROJECT_ROOT.resolve():
            return target
    except Exception:
        pass

    return CURRENT_PROJECT_ROOT


@router.get("/projects", response_model=list[ProjectInfo])
async def list_projects():
    """Détecte et liste dynamiquement tous les projets disponibles dans l'espace de travail parent."""
    projects: list[ProjectInfo] = []

    # 1. Ajouter d'abord les sous-dossiers locaux du projet courant
    try:
        cur_fw, cur_tags = _detect_stack(CURRENT_PROJECT_ROOT)
        projects.append(
            ProjectInfo(
                name=f"{CURRENT_PROJECT_ROOT.name} (Projet courant)",
                path=".",
                absolute_path=str(CURRENT_PROJECT_ROOT),
                is_current=True,
                framework=cur_fw,
                tags=cur_tags,
                has_git=(CURRENT_PROJECT_ROOT / ".git").exists(),
                has_tests=(CURRENT_PROJECT_ROOT / "tests").exists() or (CURRENT_PROJECT_ROOT / "test").exists(),
                has_package_json=(CURRENT_PROJECT_ROOT / "package.json").exists(),
                last_modified=os.path.getmtime(CURRENT_PROJECT_ROOT),
            )
        )

        for sub_name in ["frontend", "backend"]:
            sub_path = CURRENT_PROJECT_ROOT / sub_name
            if sub_path.exists() and sub_path.is_dir():
                sub_fw, sub_tags = _detect_stack(sub_path)
                projects.append(
                    ProjectInfo(
                        name=f"{CURRENT_PROJECT_ROOT.name} / {sub_name}",
                        path=f"./{sub_name}",
                        absolute_path=str(sub_path),
                        is_current=False,
                        framework=sub_fw,
                        tags=sub_tags,
                        has_git=False,
                        has_tests=(sub_path / "tests").exists() or (sub_path / "test").exists(),
                        has_package_json=(sub_path / "package.json").exists(),
                        last_modified=os.path.getmtime(sub_path),
                    )
                )
    except Exception as e:
        pass

    # 2. Scanner les projets frères dans WORKSPACE_ROOT
    try:
        if WORKSPACE_ROOT.exists() and WORKSPACE_ROOT.is_dir():
            for item in sorted(WORKSPACE_ROOT.iterdir(), key=lambda p: p.name.lower()):
                if item.is_dir() and not item.name.startswith(".") and item != CURRENT_PROJECT_ROOT:
                    # Calculer le chemin relatif par rapport à CURRENT_PROJECT_ROOT
                    rel_path = f"../{item.name}"
                    fw, tags = _detect_stack(item)
                    has_tests = (item / "tests").exists() or (item / "test").exists() or (item / "__tests__").exists()
                    
                    projects.append(
                        ProjectInfo(
                            name=item.name,
                            path=rel_path,
                            absolute_path=str(item),
                            is_current=False,
                            framework=fw,
                            tags=tags,
                            has_git=(item / ".git").exists(),
                            has_tests=has_tests,
                            has_package_json=(item / "package.json").exists(),
                            last_modified=os.path.getmtime(item),
                        )
                    )
    except Exception:
        pass

    return projects


@router.get("/browse", response_model=BrowseResponse)
async def browse_directory(path: str = Query(default=".")):
    """Explore le contenu d'un dossier pour permettre une navigation interactive dans l'UI."""
    target_dir = _resolve_safe_path(path)

    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Dossier introuvable: {path}")

    # Calculer le chemin relatif affichable
    try:
        rel_from_cur = os.path.relpath(target_dir, CURRENT_PROJECT_ROOT)
        if rel_from_cur == ".":
            display_path = "."
        elif not rel_from_cur.startswith("."):
            display_path = f"./{rel_from_cur}"
        else:
            display_path = rel_from_cur
    except Exception:
        display_path = str(target_dir)

    # Calculer le parent
    parent_path = None
    if target_dir != WORKSPACE_ROOT.resolve():
        p = target_dir.parent
        try:
            rel_p = os.path.relpath(p, CURRENT_PROJECT_ROOT)
            parent_path = "." if rel_p == "." else (f"./{rel_p}" if not rel_p.startswith(".") else rel_p)
        except Exception:
            parent_path = str(p)

    # Construire les breadcrumbs
    breadcrumbs: list[dict[str, str]] = []
    try:
        # Décomposer depuis WORKSPACE_ROOT
        rel_to_ws = target_dir.relative_to(WORKSPACE_ROOT)
        parts = list(rel_to_ws.parts)
        
        breadcrumbs.append({"name": "Code", "path": ".."})
        accumulated = WORKSPACE_ROOT
        for part in parts:
            accumulated = accumulated / part
            try:
                part_rel = os.path.relpath(accumulated, CURRENT_PROJECT_ROOT)
                part_display = "." if part_rel == "." else (f"./{part_rel}" if not part_rel.startswith(".") else part_rel)
            except Exception:
                part_display = str(accumulated)
            breadcrumbs.append({"name": part, "path": part_display})
    except Exception:
        breadcrumbs.append({"name": target_dir.name or str(target_dir), "path": display_path})

    directories: list[DirectoryItem] = []
    files_count = 0

    ignored_dirs = {".git", "node_modules", ".next", ".venv", "__pycache__", "dist", "build", ".turbo"}

    try:
        for entry in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if entry.name in ignored_dirs or entry.name.startswith("."):
                continue

            try:
                rel_entry = os.path.relpath(entry, CURRENT_PROJECT_ROOT)
                entry_display = f"./{rel_entry}" if not rel_entry.startswith(".") else rel_entry
            except Exception:
                entry_display = str(entry)

            if entry.is_dir():
                has_subdirs = False
                try:
                    has_subdirs = any(p.is_dir() and not p.name.startswith(".") for p in entry.iterdir())
                except Exception:
                    pass

                directories.append(
                    DirectoryItem(
                        name=entry.name,
                        path=entry_display,
                        is_dir=True,
                        has_subdirs=has_subdirs,
                    )
                )
            else:
                files_count += 1
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission refusée pour lire ce dossier.")

    return BrowseResponse(
        current_path=display_path,
        absolute_path=str(target_dir),
        parent_path=parent_path,
        breadcrumbs=breadcrumbs,
        directories=directories,
        files_count=files_count,
    )
