"""
core/crew_runner.py — Exécution d'un Crew avec streaming des logs.

Ce module contient la logique d'orchestration pure (sans UI).
Il instancie les agents/tâches depuis le YAML, lance le kickoff,
et yield les logs ligne par ligne (compatible SSE).
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import queue
import re
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

import litellm

from app.core.safe_stream_writer import install_safe_streams

install_safe_streams()

# ── Wrapper Sécurisé LiteLLM (Remplace le Monkeypatch Global) ─────────────────

_orig_completion = litellm.completion
# thread_queues: thread_id -> queue, cleaned up when thread finishes
thread_queues: dict[int, "queue.Queue"] = {}
_litellm_patched = False


def _cleanup_thread_queue(thread_id: int) -> None:
    """Remove a thread's queue entry to prevent unbounded dict growth."""
    thread_queues.pop(thread_id, None)

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
            logging.debug("LITELLM KWARGS JSON: %s", json.dumps(safe_kwargs))
        except Exception as e:
            logging.debug("LITELLM KWARGS (non-json): %s", str(e))

        # 2. Nettoyage préventif des arguments
        if "tools" in kwargs and not kwargs["tools"]:
            del kwargs["tools"]
            logging.debug("Removed empty tools list from kwargs")
            
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
                    logging.warning(
                        "Temporary LLM error (%s...), retry %d/%d in %ds...",
                        err_str[:100], attempt + 2, max_retries, wait_time
                    )
                    time.sleep(wait_time)
                    continue

                logging.error(
                    "LITELLM ERROR IN SECURE WRAPPER: %s - %s\n%s",
                    type(e).__name__, e, traceback.format_exc()
                )
                if hasattr(e, "status_code"):
                    logging.error("LITELLM ERROR STATUS CODE: %s", getattr(e, "status_code"))
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
            if "LITELLM KWARGS JSON:" in msg or "LITELLM KWARGS (non-json):" in msg:
                self.log_queue.put("L'agent réfléchit (Requête envoyée au LLM)...")
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
                        log_queue.put(f"[Réflexion] {log_text}")
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

    def _execute_crew_and_stream(self, crew: Crew, log_queue: queue.Queue, inputs: dict | None = None) -> Generator[str, None, None]:
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
                    logging.error("Error reading log queue: %s", e)
                    break

        try:
            result_container = {}
            error_container = {}

            def run_kickoff():
                try:
                    result_container["result"] = crew.kickoff(inputs=inputs)
                except Exception as e:
                    error_container["error"] = e

            kickoff_thread = threading.Thread(target=run_kickoff)
            kickoff_thread.start()

            # Poll the queue while the thread is running
            while kickoff_thread.is_alive():
                try:
                    msg = log_queue.get(timeout=0.5)
                    yield self._make_chunk("log", msg)
                except queue.Empty:
                    pass

            kickoff_thread.join()

            # Clean up the kickoff thread's queue entry to prevent unbounded growth
            _cleanup_thread_queue(kickoff_thread.ident)

            # Process any remaining logs in the queue
            while not log_queue.empty():
                try:
                    msg = log_queue.get_nowait()
                    yield self._make_chunk("log", msg)
                except queue.Empty:
                    break

            if "error" in error_container:
                raise error_container["error"]

            yield self._make_chunk("result", str(result_container.get("result", "")))

        except Exception as e:
            logging.error("Crew execution error: %s", e)
            yield self._make_chunk("error", str(e))


# ── Interface Publique ──────────────────────────────────────────────────────

def run_crew(
    crew_name: str,
    message: str = "",
    inputs: dict[str, Any] | None = None,
    max_rpm: int = 15,
    llm_override: str | None = None,
    use_yaml_llm: bool = False,
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

    # Fallback par défaut quand aucun modèle n'est spécifié.
    # Si use_yaml_llm est True, on n'applique AUCUN override : chaque agent
    # utilise le modèle défini dans son YAML (per-agent LLM).
    if use_yaml_llm:
        effective_llm_override = None
    else:
        effective_llm_override = llm_override or "openai/qwen-3.6-35b-instruct"

    inputs = inputs or {}
    if message and "message" not in inputs:
        inputs["message"] = message

    if not config_path.exists():
        yield service._make_chunk("error", f"Crew '{crew_name}' introuvable.")
        return

    # Auto-inject missing template variables to prevent CrewAI from crashing.
    # We deliberately skip variables that are expected to be provided by the
    # caller (output_dir, project_path, pdf_path, message) so that the
    # chat.py injection logic takes full control over them.
    KNOWN_INPUT_VARS = {"output_dir", "project_path", "pdf_path", "pdf_alternatives", "message"}
    try:
        content = config_path.read_text(encoding="utf-8")
        # Find all {variables} in the YAML, ignoring doubled braces {{ or }}
        variables = set(re.findall(r'(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})', content))
        for var in variables:
            if var not in inputs and var not in KNOWN_INPUT_VARS:
                inputs[var] = "valeur_non_fournie"
    except Exception as e:
        logging.warning("Failed to auto-inject template variables: %s", e)

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
            effective_llm_override,
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
        yield from service._execute_crew_and_stream(crew, log_queue, inputs=inputs)

    except Exception as e:
        logging.error("Failed to run crew '%s': %s", crew_name, e, exc_info=True)
        yield service._make_chunk("error", f"Erreur critique lors de l'exécution du Crew : {str(e)}")


def run_multi_crew(
    crew_names: list[str],
    message: str,
    execution_mode: str = "sequential",
    inputs: dict[str, Any] | None = None,
    max_rpm: int = 15,
    llm_override: str | None = None,
) -> Generator[str, None, None]:
    """
    Exécute plusieurs Crews en mode séquentiel ou parallèle.

    Séquentiel : chaque crew reçoit le résultat du précédent comme contexte.
    Parallèle : tous les crews s'exécutent simultanément, résultats agrégés.

    Yields
    ------
    str
        Chunks JSON tagués avec 'crewName' pour l'attribution frontend.
    """
    service = CrewExecutionService()
    inputs = inputs or {}
    accumulated_context = ""

    # Ensure llm_override has a fallback so crews without explicit llm in YAML don't crash
    effective_llm_override = llm_override or "openai/qwen-3.6-35b-instruct"

    # Auto-inject output_dir for InteractiveCourseCreator in multi-crew mode
    if "InteractiveCourseCreator" in crew_names:
        project_path = inputs.get("project_path", ".")
        resolved_project = str(Path(project_path).resolve())
        inputs["project_path"] = resolved_project
        inputs["output_dir"] = str(Path(resolved_project) / "cours_interactif")
        # pdf_path and pdf_alternatives are injected by the caller (chat.py)
        # but we ensure they exist as template vars if missing
        if "pdf_path" not in inputs:
            inputs["pdf_path"] = ""
        if "pdf_alternatives" not in inputs:
            inputs["pdf_alternatives"] = []

    if execution_mode == "sequential":
        for idx, crew_name in enumerate(crew_names):
            # Build the message with accumulated context for crews after the first
            crew_inputs = dict(inputs)
            if accumulated_context:
                # Prepend context to the message so the crew can use it
                crew_inputs["message"] = (
                    f"[Contexte du crew précédent]\n{accumulated_context}\n\n---\n\n"
                    f"[Ta mission]\n{message}"
                )
            else:
                crew_inputs["message"] = message

            yield service._make_chunk(
                "log",
                f"[Étape {idx + 1}/{len(crew_names)}] Exécution du crew {crew_name}...",
                crewName=crew_name,
            )

            final_result = ""
            for chunk in run_crew(
                crew_name=crew_name,
                message=crew_inputs.get("message", message),
                inputs=crew_inputs,
                max_rpm=max_rpm,
                llm_override=effective_llm_override,
            ):
                # Tag every chunk with the current crew name
                try:
                    data = json.loads(chunk)
                    data["crewName"] = crew_name
                    yield json.dumps(data, ensure_ascii=False)
                except Exception:
                    # If chunk is already tagged or malformed, just yield as-is
                    yield chunk

                try:
                    data = json.loads(chunk)
                    if data.get("type") == "result":
                        final_result = data.get("content", "")
                except Exception:
                    pass

            # Accumulate result for next crew
            if final_result:
                accumulated_context = (
                    (accumulated_context + "\n\n---\n\n") if accumulated_context else ""
                ) + final_result
                # Truncate to avoid context overflow
                if len(accumulated_context) > 8000:
                    accumulated_context = accumulated_context[-8000:]

            yield service._make_chunk(
                "log",
                f"[Étape {idx + 1}/{len(crew_names)}] Crew {crew_name} terminé.",
                crewName=crew_name,
            )

    else:
        # Parallel mode
        for crew_name in crew_names:
            yield service._make_chunk(
                "log",
                f"[Parallèle] Préparation du crew {crew_name}...",
                crewName=crew_name,
            )

        results: dict[str, str] = {}
        errors: dict[str, str] = {}
        all_chunks: dict[str, list[str]] = {name: [] for name in crew_names}

        def _run_single_crew(crew_name: str) -> tuple[str, list[str], str | None]:
            chunks: list[str] = []
            final_result = ""
            try:
                for chunk in run_crew(
                    crew_name=crew_name,
                    message=message,
                    inputs=dict(inputs),
                    max_rpm=max_rpm,
                    llm_override=effective_llm_override,
                ):
                    try:
                        data = json.loads(chunk)
                        data["crewName"] = crew_name
                        tagged = json.dumps(data, ensure_ascii=False)
                    except Exception:
                        tagged = chunk
                    chunks.append(tagged)
                    try:
                        data = json.loads(chunk)
                        if data.get("type") == "result":
                            final_result = data.get("content", "")
                    except Exception:
                        pass
                return crew_name, chunks, final_result
            except Exception as e:
                errors[crew_name] = str(e)
                return crew_name, chunks, None

        # Run all crews concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(crew_names), 5)) as executor:
            futures = {executor.submit(_run_single_crew, name): name for name in crew_names}
            for future in concurrent.futures.as_completed(futures):
                crew_name, chunks, _ = future.result()
                all_chunks[crew_name] = chunks

        # Yield all chunks interleaved (round-robin to simulate real-time)
        queues: dict[str, queue.Queue[str]] = {
            name: queue.Queue() for name in crew_names
        }

        def _fill_queues():
            for name, chunks in all_chunks.items():
                for chunk in chunks:
                    queues[name].put(chunk)

        fill_thread = threading.Thread(target=_fill_queues)
        fill_thread.start()

        try:
            # Interleave: yield one chunk from each non-empty queue in round-robin
            active_queues = set(crew_names)
            while active_queues:
                yielded_any = False
                for name in list(active_queues):
                    try:
                        chunk = queues[name].get_nowait()
                        yield chunk
                        yielded_any = True
                    except queue.Empty:
                        pass
                if not yielded_any:
                    # Check if all queues are done
                    all_done = all(queues[name].empty() for name in active_queues)
                    if all_done:
                        break
                    time.sleep(0.05)
        finally:
            fill_thread.join()

        # Yield aggregated result
        aggregated = "\n\n=== Résultat Agrégé ===\n\n"
        for name in crew_names:
            if name in errors:
                aggregated += f"[Erreur] **{name}** : {errors[name]}\n\n"
            else:
                aggregated += f"**{name}**\n---\n"
                # Extract result from last chunk
                for chunk in reversed(all_chunks[name]):
                    try:
                        data = json.loads(chunk)
                        if data.get("type") == "result":
                            aggregated += data.get("content", "")
                            break
                    except Exception:
                        pass
                aggregated += "\n\n"

        yield service._make_chunk("result", aggregated.strip())
