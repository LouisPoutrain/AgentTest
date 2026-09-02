"""
core/crew_runner.py — Exécution d'un Crew avec streaming des logs.

Ce module contient la logique d'orchestration pure (sans UI).
Il instancie les agents/tâches depuis le YAML, lance le kickoff,
et yield les logs ligne par ligne (compatible SSE).
"""

from __future__ import annotations

import json
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

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

# ── Wrapper Sécurisé LiteLLM (Remplace le Monkeypatch Global) ─────────────────
import litellm
import threading

_orig_completion = litellm.completion
thread_queues = {}
_litellm_patched = False

def setup_litellm_interceptor():
    """Installe le wrapper sécurisé sur litellm.completion s'il n'est pas déjà présent."""
    global _litellm_patched
    if _litellm_patched:
        return

    def _secure_completion(*args, **kwargs):
        # 1. Logging sécurisé (Sanitization des clés API)
        try:
            safe_kwargs = {k: v for k, v in kwargs.items()}
            for key in ["api_key", "headers", "Authorization"]:
                if key in safe_kwargs:
                    safe_kwargs[key] = "***REDACTED***"
            logging.error(f"🚀 LITELLM KWARGS JSON: {json.dumps(safe_kwargs)}")
        except Exception as e:
            logging.error(f"🚀 LITELLM KWARGS (non-json): {str(e)}")
            
        # 2. Nettoyage préventif des arguments
        if "tools" in kwargs and not kwargs["tools"]:
            del kwargs["tools"]
            logging.error("🧹 Removed empty tools list from kwargs")
            
        if "tools" not in kwargs and "messages" in kwargs and isinstance(kwargs["messages"], list):
            if kwargs.get("model", "").startswith("openai/"):
                for msg in reversed(kwargs["messages"]):
                    if msg.get("role") == "user":
                        msg["content"] = str(msg.get("content", "")) + "\n\nCRITICAL SYSTEM INSTRUCTION: DO NOT use native tool calls or JSON functions. You MUST output your response as plain text in the exact Thought/Action/Action Input format requested. Native tool calls will crash the system."
                        break

        if "messages" in kwargs:
            for msg in kwargs["messages"]:
                if "cache_breakpoint" in msg:
                    del msg["cache_breakpoint"]
                    
        # 3. Exécution avec Retry et Capture de Métriques
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = _orig_completion(*args, **kwargs)
                # Envoi des métriques de coût/tokens dans la file SSE du thread
                q = thread_queues.get(threading.get_ident())
                if q and hasattr(response, "usage") and response.usage:
                    tokens = getattr(response.usage, "total_tokens", 0)
                    try:
                        cost = litellm.completion_cost(completion_response=response)
                    except Exception:
                        cost = 0.0
                    q.put(json.dumps({"type": "metrics", "tokens": tokens, "cost": float(cost or 0.0)}))
                return response
            except Exception as e:
                err_str = str(e)
                is_transient = (
                    "504" in err_str or "502" in err_str or "503" in err_str
                    or "Gateway Time-out" in err_str or "timeout" in err_str.lower()
                    or "connection error" in err_str.lower() or "RateLimitError" in type(e).__name__
                )
                if is_transient and attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    logging.warning(f"⚠️ Erreur temporaire LLM ({err_str[:100]}...), nouvelle tentative {attempt + 2}/{max_retries} dans {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                import traceback
                logging.error(f"❌ LITELLM ERROR IN SECURE WRAPPER: {type(e)} - {e}\n{traceback.format_exc()}")
                if hasattr(e, "status_code"):
                    logging.error(f"❌ LITELLM ERROR STATUS CODE: {getattr(e, 'status_code')}")
                raise e

    litellm.completion = _secure_completion
    _litellm_patched = True

# Now import crewai
from crewai import Crew

from app.core.agent_parser import (
    create_agents_from_yaml,
    create_tasks_from_yaml,
    get_crew_settings_from_yaml,
)
from app.core.crew_manager import CREWS_DIR
from app.core.tool_registry import AVAILABLE_TOOLS

# ── Custom Log Handler (thread-safe queue) ───────────────────────────────────

class QueueLogHandler(logging.Handler):
    """Handler qui pousse chaque log dans une queue thread-safe."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            # Ignore harmless CrewAI JSON parsing fallbacks in memory
            if "Query analysis failed, using defaults" in msg or "Memory save analysis failed" in msg or "Consolidation analysis failed" in msg:
                return
            
            # Si le log contient le payload complet, on le simplifie pour le frontend
            if "🚀 LITELLM KWARGS JSON:" in msg or "🚀 LITELLM KWARGS (non-json):" in msg:
                self.log_queue.put("🧠 L'agent réfléchit (Requête envoyée au LLM)...")
                return
                
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)


# ── Service d'Orchestration du Crew ──────────────────────────────────────────

class CrewExecutionService:
    """
    Service responsable de l'instanciation, de la configuration et de l'exécution
    d'un Crew AI avec gestion des logs et du streaming SSE.
    """

    @staticmethod
    def _make_chunk(chunk_type: str, content: str, **extra: Any) -> str:
        """Fabrique un chunk SSE formaté en JSON."""
        data = {
            "type": chunk_type,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _resolve_config_path(crew_name: str) -> Path:
        """Résout le chemin du fichier de configuration du crew."""
        return CREWS_DIR / (
            crew_name if crew_name.endswith(".yaml") else f"{crew_name}.yaml"
        )

    @staticmethod
    def _configure_env_variables():
        """Configure les variables d'environnement pour LiteLLM."""
        if os.getenv("LLM_BASE_URL"):
            os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")
        if os.getenv("LLM_API_KEY"):
            os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")

    @staticmethod
    def _setup_logging(log_queue: queue.Queue) -> QueueLogHandler:
        """Configure le handler de logs pour capturer les logs dans la queue."""
        queue_handler = QueueLogHandler(log_queue)
        queue_handler.setFormatter(logging.Formatter("%(message)s"))
        # Note: On ne l'ajoute pas au logger racine globalement ici pour éviter
        # de polluer d'autres logs, il est géré via la queue
        return queue_handler

    def _create_agents_and_tasks(self, config_path: Path, llm_override: str | None, log_queue: queue.Queue):
        """
        Crée les agents et les tâches à partir du YAML.
        Inclut un callback pour capturer les réflexions des agents.
        """
        def agent_step_callback(agent_output):
            try:
                log_text = ""
                if hasattr(agent_output, 'log'):
                    log_text = agent_output.log.strip()
                elif isinstance(agent_output, list) and len(agent_output) > 0 and hasattr(agent_output[0], 'log'):
                    log_text = agent_output[0].log.strip()
                elif isinstance(agent_output, str):
                    log_text = agent_output.strip()
                
                if log_text:
                    q = thread_queues.get(threading.get_ident())
                    if q:
                        q.put(json.dumps({"type": "step", "status": "running", "log": log_text}))
                    else:
                        log_queue.put(f"🧠 [Réflexion] {log_text}")
            except Exception:
                pass

        agents = create_agents_from_yaml(
            config_path,
            available_tools=AVAILABLE_TOOLS,
            llm_override=llm_override,
            step_callback=agent_step_callback,
        )
        tasks = create_tasks_from_yaml(
            config_path,
            agents_list=agents,
        )
        return agents, tasks

    def _execute_crew_and_stream(self, crew: Crew, log_queue: queue.Queue) -> Generator[str, None, None]:
        """
        Lance le kickoff du crew et stream les logs depuis la queue jusqu'à la fin.
        """
        def stream_logs():
            while True:
                try:
                    msg = log_queue.get(timeout=1)
                    yield self._make_chunk("log", msg)
                except queue.Empty:
                    break
                except Exception as e:
                    logging.error(f"Error reading log queue: {e}")
                    break

        try:
            # Stream les logs existants pendant l'exécution
            for log_chunk in stream_logs():
                yield log_chunk

            # Exécution principale
            result = crew.kickoff()
            
            # Stream les logs restants après exécution
            for log_chunk in stream_logs():
                yield log_chunk

            # Yield le résultat final
            yield self._make_chunk("result", str(result))

        except Exception as e:
            logging.error(f"Crew execution error: {e}")
            yield self._make_chunk("error", str(e))


# ── Interface Publique ──────────────────────────────────────────────────────

def run_crew(
    crew_name: str,
    message: str = "",
    inputs: dict[str, Any] | None = None,
    max_rpm: int = 15,
    llm_override: str | None = None,
) -> Generator[str, None, None]:
    """
    Point d'entrée principal pour exécuter un Crew.
    
    Yields
    ------
    str
        Chunks JSON de type 'log', 'result', ou 'error'.
    """
    service = CrewExecutionService()
    config_path = service._resolve_config_path(crew_name)

    if not config_path.exists():
        yield service._make_chunk("error", f"Crew '{crew_name}' introuvable.")
        return

    # Configuration initiale
    service._configure_env_variables()
    setup_litellm_interceptor()
    
    yield service._make_chunk("log", f"Chargement du Crew : {crew_name}...")

    try:
        # Chargement de la configuration
        crew_settings = get_crew_settings_from_yaml(config_path)
        effective_rpm = max_rpm or crew_settings.get("max_rpm", 15)

        yield service._make_chunk("log", f"Paramètres : process={crew_settings['process']}, memory={crew_settings['memory']}, max_rpm={effective_rpm}")

        # Setup Logging
        log_queue: queue.Queue[str] = queue.Queue()
        service._setup_logging(log_queue)

        # Instanciation
        agents, tasks = service._create_agents_and_tasks(
            config_path, 
            llm_override, 
            log_queue
        )

        # Création du Crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=crew_settings.get("process", "sequential"),
            memory=crew_settings.get("memory", False),
            cache=crew_settings.get("cache", True),
            max_rpm=effective_rpm,
            verbose=True,
        )

        # Exécution et Streaming
        yield from service._execute_crew_and_stream(crew, log_queue)

    except Exception as e:
        logging.error(f"Failed to run crew '{crew_name}': {e}", exc_info=True)
        yield service._make_chunk("error", f"Erreur critique lors de l'exécution du Crew : {str(e)}")
