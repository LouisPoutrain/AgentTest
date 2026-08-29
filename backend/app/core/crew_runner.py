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
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

# ── Monkeypatch LiteLLM BEFORE crewai imports it ─────────────────────────────
import litellm

_orig_completion = litellm.completion

def _patched_completion(*args, **kwargs):
    # Try to log as JSON
    try:
        safe_kwargs = {k: v for k, v in kwargs.items()}
        # Remove sensitive keys
        for key in ["api_key", "headers", "Authorization"]:
            if key in safe_kwargs:
                safe_kwargs[key] = "***REDACTED***"
        logging.error(f"🚀 LITELLM KWARGS JSON: {json.dumps(safe_kwargs)}")
    except Exception as e:
        logging.error(f"🚀 LITELLM KWARGS (non-json): {str(e)}")
        
    if "tools" in kwargs and not kwargs["tools"]:
        del kwargs["tools"]
        logging.error("🧹 Removed empty tools list from kwargs")
        
    # Prevent hallucinated native tool calls when tools are removed
    if "tools" not in kwargs and "messages" in kwargs and isinstance(kwargs["messages"], list):
        if kwargs.get("model", "").startswith("openai/"):
            # Ajouter l'instruction de sécurité à la fin du dernier message utilisateur
            for msg in reversed(kwargs["messages"]):
                if msg.get("role") == "user":
                    msg["content"] = str(msg.get("content", "")) + "\n\nCRITICAL SYSTEM INSTRUCTION: DO NOT use native tool calls or JSON functions. You MUST output your response as plain text in the exact Thought/Action/Action Input format requested. Native tool calls will crash the system."
                    break

    # Remove cache_breakpoint from messages, vLLM proxies reject it with 422
    if "messages" in kwargs:
        for msg in kwargs["messages"]:
            if "cache_breakpoint" in msg:
                del msg["cache_breakpoint"]
                
    try:
        return _orig_completion(*args, **kwargs)
    except Exception as e:
        import traceback
        logging.error(f"❌ LITELLM ERROR IN PATCH: {type(e)} - {e}\n{traceback.format_exc()}")
        if hasattr(e, "status_code"):
            logging.error(f"❌ LITELLM ERROR STATUS CODE: {getattr(e, 'status_code')}")
        if hasattr(e, "message"):
            logging.error(f"❌ LITELLM ERROR MESSAGE: {getattr(e, 'message')}")
        if hasattr(e, "response"):
            logging.error(f"❌ LITELLM RESPONSE DUMP: {getattr(e, 'response')}")
        raise e

litellm.completion = _patched_completion

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
                # On ne transmet qu'un petit message sympa à l'UI
                self.log_queue.put("🧠 L'agent réfléchit (Requête envoyée au LLM)...")
                return
                
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)


# ── Exécution principale ─────────────────────────────────────────────────────


def _make_chunk(chunk_type: str, content: str, **extra: Any) -> str:
    """Fabrique un chunk SSE formaté en JSON."""
    data = {
        "type": chunk_type,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    return json.dumps(data, ensure_ascii=False)


def run_crew(
    crew_name: str,
    message: str = "",
    max_rpm: int = 15,
    llm_override: str | None = None,
) -> Generator[str, None, None]:
    """Lance l'exécution d'un Crew et yield des chunks SSE.

    Yields
    ------
    str
        Chunks JSON de type 'log', 'result', ou 'error'.
    """
    config_path = CREWS_DIR / (
        crew_name if crew_name.endswith(".yaml") else f"{crew_name}.yaml"
    )

    if not config_path.exists():
        yield _make_chunk("error", f"Crew '{crew_name}' introuvable.")
        return

    # Mappage des variables d'environnement pour LiteLLM (Custom OpenAI endpoints)
    if os.getenv("LLM_BASE_URL"):
        os.environ["OPENAI_API_BASE"] = os.getenv("LLM_BASE_URL")
    if os.getenv("LLM_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")

    # Yield un log initial
    yield _make_chunk("log", f"Chargement du Crew : {crew_name}...")

    try:
        # Charger les settings
        crew_settings = get_crew_settings_from_yaml(config_path)
        effective_rpm = max_rpm or crew_settings.get("max_rpm", 15)

        yield _make_chunk("log", f"Paramètres : process={crew_settings['process']}, memory={crew_settings['memory']}, max_rpm={effective_rpm}")

        # Instancier agents et tâches
        agents = create_agents_from_yaml(
            config_path,
            available_tools=AVAILABLE_TOOLS,
            llm_override=llm_override,
        )
        yield _make_chunk("log", f"{len(agents)} agent(s) chargé(s).")

        tasks = create_tasks_from_yaml(config_path, agents)
        yield _make_chunk("log", f"{len(tasks)} tâche(s) chargée(s).")

        # Configurer la capture de logs via queue
        log_queue: queue.Queue[str] = queue.Queue()
        queue_handler = QueueLogHandler(log_queue)
        queue_handler.setFormatter(logging.Formatter("%(message)s"))
        
        # Configurer la capture de logs par crew (Fichier)
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        crew_log_file = logs_dir / f"{crew_name}_{timestamp_str}.log"
        file_handler = logging.FileHandler(crew_log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        # Attacher le handler aux loggers CrewAI
        crewai_logger = logging.getLogger("crewai")
        crewai_logger.addHandler(queue_handler)
        crewai_logger.addHandler(file_handler)
        crewai_logger.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        root_logger.addHandler(file_handler)

        # Construire le Crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=crew_settings["process"],
            verbose=True,
            memory=crew_settings["memory"],
            max_rpm=effective_rpm,
            embedder={
                "provider": "sentence-transformer",
                "config": {
                    "model": "all-MiniLM-L6-v2"
                }
            },
        )

        yield _make_chunk("log", "🚀 Lancement de l'orchestration...")

        # Lancer le kickoff dans un thread séparé pour pouvoir streamer les logs
        result_container: dict[str, Any] = {}

        def _kickoff():
            import time
            import re
            
            max_retries = 3
            retries = 0
            
            # Use various keys in inputs so users can use {message}, {user_request} or {topic} in their prompts
            inputs = {
                "message": message,
                "user_request": message,
                "topic": message,
                "user_prompt": message
            }
            
            while retries <= max_retries:
                try:
                    result_container["result"] = crew.kickoff(inputs=inputs)
                    if "error" in result_container:
                        del result_container["error"]
                    break
                except Exception as exc:
                    error_str = str(exc)
                    if "429" in error_str or "Quota exceeded" in error_str or "Rate Limit" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        retries += 1
                        if retries > max_retries:
                            result_container["error"] = Exception(f"Nombre maximal de tentatives atteint (429). {error_str}")
                            break
                        
                        delay = 60
                        match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str)
                        if match:
                            delay = int(float(match.group(1))) + 2
                            
                        # Log pour affichage dans l'interface UI (SSE)
                        crewai_logger.info(f"⚠️ Limite d'API atteinte (429). Pause automatique de {delay} secondes avant tentative {retries}/{max_retries}...")
                        time.sleep(delay)
                    else:
                        result_container["error"] = exc
                        break

        thread = threading.Thread(target=_kickoff, daemon=True)
        thread.start()

        # Streamer les logs pendant que le thread tourne
        while thread.is_alive():
            while not log_queue.empty():
                try:
                    msg = log_queue.get_nowait()
                    if msg.strip():
                        yield _make_chunk("log", msg)
                except queue.Empty:
                    break
            time.sleep(0.1)

        # Vider la queue restante
        while not log_queue.empty():
            try:
                msg = log_queue.get_nowait()
                if msg.strip():
                    yield _make_chunk("log", msg)
            except queue.Empty:
                break

        # Nettoyer les handlers
        crewai_logger.removeHandler(queue_handler)
        crewai_logger.removeHandler(file_handler)
        root_logger.removeHandler(queue_handler)
        root_logger.removeHandler(file_handler)
        file_handler.close()

        # Vérifier le résultat
        if "error" in result_container:
            error = result_container["error"]
            error_str = str(error)

            if "429" in error_str or "Rate Limit" in error_str or "Quota exceeded" in error_str:
                from app.core.crew_manager import get_available_models
                yield _make_chunk(
                    "error",
                    "Quota de l'API atteint (Rate Limit 429). Choisissez un autre modèle.",
                    code=429,
                    available_models=get_available_models(),
                )
            else:
                yield _make_chunk("error", f"Erreur lors de l'exécution : {error_str}")
        else:
            result = result_container.get("result", "")
            yield _make_chunk("result", str(result))

    except Exception as e:
        yield _make_chunk("error", f"Erreur fatale : {str(e)}")
