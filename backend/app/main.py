"""
backend/app/main.py — Point d'entrée FastAPI pour AgentTest.

Lance avec : uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os

from app.core.config import validate_env
from app.core.safe_stream_writer import install_safe_streams

install_safe_streams()

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.api.chat import router as chat_router
from app.api.crews import router as crews_router
from app.api.models import router as models_router
from app.api.registry import router as registry_router
from app.api.workspace import router as workspace_router

# Charger les variables d'environnement
load_dotenv()

env_errors = validate_env()
if env_errors:
    for err in env_errors:
        logging.warning("Missing required env var: %s", err)

# ── App FastAPI ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgentTest API",
    description="API backend pour l'orchestrateur IA AgentTest (CrewAI).",
    version="1.0.0",
)

# ── Rate Limiting ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

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

app.add_middleware(SlowAPIMiddleware)

# ── Gestion des Erreurs ───────────────────────────────────────────────────────

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error("Global Error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue sur le serveur.", "error": str(exc)},
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Trop de requêtes. Veuillez réessayer plus tard."},
    )

# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(crews_router)
app.include_router(models_router)
app.include_router(registry_router)
app.include_router(workspace_router)


@app.get("/api/health")
async def health():
    """Healthcheck endpoint."""
    return {
        "status": "ok",
    }
