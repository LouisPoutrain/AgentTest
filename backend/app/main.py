"""
backend/app/main.py — Point d'entrée FastAPI pour AgentTest.

Lance avec : uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.crews import router as crews_router
from app.api.models import router as models_router

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

# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(crews_router)
app.include_router(models_router)


@app.get("/api/health")
async def health():
    """Healthcheck endpoint."""
    return {
        "status": "ok",
    }
