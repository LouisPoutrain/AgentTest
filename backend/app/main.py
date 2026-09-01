"""
backend/app/main.py — Point d'entrée FastAPI pour AgentTest.

Lance avec : uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys

# ── Protection contre les déconnexions de TTY [Errno 5] ───────────────────────
class SafeStreamWriter:
    """Empêche les crashs [Errno 5] Input/output error lorsque stdout/stderr perdent leur TTY."""
    def __init__(self, target):
        self.target = target

    def write(self, s):
        try:
            if self.target:
                return self.target.write(s)
        except (OSError, IOError, BrokenPipeError):
            pass

    def flush(self):
        try:
            if self.target:
                self.target.flush()
        except (OSError, IOError, BrokenPipeError):
            pass

    def isatty(self):
        try:
            return self.target.isatty()
        except Exception:
            return False

    def __getattr__(self, name):
        return getattr(self.target, name)

if not isinstance(sys.stdout, SafeStreamWriter):
    sys.stdout = SafeStreamWriter(sys.stdout)
if not isinstance(sys.stderr, SafeStreamWriter):
    sys.stderr = SafeStreamWriter(sys.stderr)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.crews import router as crews_router
from app.api.models import router as models_router
from app.api.workspace import router as workspace_router

# Charger les variables d'environnement
load_dotenv()

# ── App FastAPI ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgentTest API",
    description="API backend pour l'orchestrateur IA AgentTest (CrewAI).",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ── Gestion des Erreurs ───────────────────────────────────────────────────────

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue sur le serveur.", "error": str(exc)},
    )

# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(crews_router)
app.include_router(models_router)
app.include_router(workspace_router)


@app.get("/api/health")
async def health():
    """Healthcheck endpoint."""
    return {
        "status": "ok",
    }
