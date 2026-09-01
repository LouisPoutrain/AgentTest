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
    """Installe le wrapper sécurisé sur litellm.completion s'il n'est pas déjà présent.
    Cela évite le monkeypatching global sauvage à l'import du fichier.
    """
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
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = _orig_completion(*args, **kwargs)
                # Envoi des métriques de coût/tokens dans la file SSE du thread
                queue = thread_queues.get(threading.get_ident())
                if queue and hasattr(response, "usage") and response.usage:
                    tokens = getattr(response.usage, "total_tokens", 0)
                    try:
                        cost = litellm.completion_cost(completion_response=response)
                    except Exception:
                        cost = 0.0
                    queue.put(json.dumps({"type": "metrics", "tokens": tokens, "cost": float(cost or 0.0)}))
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
    inputs: dict[str, Any] | None = None,
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

    # Installer le wrapper sécurisé litellm avant de lancer
    setup_litellm_interceptor()

    # Yield un log initial
    yield _make_chunk("log", f"Chargement du Crew : {crew_name}...")

    try:
        # Charger les settings
        crew_settings = get_crew_settings_from_yaml(config_path)
        effective_rpm = max_rpm or crew_settings.get("max_rpm", 15)

        yield _make_chunk("log", f"Paramètres : process={crew_settings['process']}, memory={crew_settings['memory']}, max_rpm={effective_rpm}")

        # Configurer la capture de logs via queue
        log_queue: queue.Queue[str] = queue.Queue()
        queue_handler = QueueLogHandler(log_queue)
        queue_handler.setFormatter(logging.Formatter("%(message)s"))
        
        def agent_step_callback(agent_output):
            try:
                log_text = ""
                # agent_output peut être un AgentAction ou une liste
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

        # Instancier agents et tâches
        agents = create_agents_from_yaml(
            config_path,
            available_tools=AVAILABLE_TOOLS,
            llm_override=llm_override,
            step_callback=agent_step_callback,
        )
        yield _make_chunk("log", f"{len(agents)} agent(s) chargé(s).")

        tasks = create_tasks_from_yaml(config_path, agents)
        yield _make_chunk("log", f"{len(tasks)} tâche(s) chargée(s).")


        
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
            
            thread_queues[threading.get_ident()] = log_queue
            try:
                # Prepare inputs dictionary
                effective_inputs: dict[str, Any] = {}
                if inputs and isinstance(inputs, dict):
                    effective_inputs.update(inputs)
                    if "message" not in effective_inputs and message:
                        effective_inputs["message"] = message
                else:
                    effective_inputs = {
                        "message": message,
                        "user_request": message,
                        "topic": message,
                        "user_prompt": message
                    }
                    
                if "project_path" not in effective_inputs:
                    try:
                        from app.tools.custom_tools import _get_project_root
                        effective_inputs["project_path"] = _get_project_root()
                    except Exception:
                        pass
                
                # --- INJECTION AUTO DU CONTEXTE DES CREWS ---
                try:
                    from app.core.crew_manager import get_all_crews, get_crew, get_available_models
                    crews_summary = []
                    for c_name in get_all_crews():
                        c_data = get_crew(c_name)
                        desc = c_data.get("description", "Aucune description fournie.")
                        
                        tasks_info = []
                        for t in c_data.get("tasks", []):
                            t_desc = t.get("description", "").replace("\n", " ")
                            t_out = t.get("expected_output", "").replace("\n", " ")
                            tasks_info.append(f"  - But: {t_desc}\n    Output: {t_out}")
                        
                        tasks_str = "\n".join(tasks_info)
                        crews_summary.append(f"### Crew: {c_name}\nDescription: {desc}\nTâches:\n{tasks_str}")
                    
                    effective_inputs["available_crews_context"] = "\n\n".join(crews_summary)

                    # Injection du contexte des LLMs (seulement ceux de l'API custom ILAAS)
                    llms = [m for m in get_available_models() if m.startswith("openai/")]
                    effective_inputs["available_llms_context"] = ", ".join(llms) if llms else "Aucun modèle trouvé."
                except Exception as e:
                    crewai_logger.error(f"Erreur lors de l'injection du contexte des crews/LLMs: {e}")
                # --------------------------------------------
                
                while retries <= max_retries:
                    try:
                        result_container["result"] = crew.kickoff(inputs=effective_inputs)
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
            finally:
                thread_queues.pop(threading.get_ident(), None)

        thread = threading.Thread(target=_kickoff, daemon=True)
        thread.start()

        # Streamer les logs pendant que le thread tourne
        def _process_queue():
            while not log_queue.empty():
                try:
                    msg = log_queue.get_nowait()
                    if not msg.strip(): continue
                    try:
                        data = json.loads(msg)
                        if isinstance(data, dict) and "type" in data:
                            if data["type"] == "step":
                                yield _make_chunk("log", f"🧠 [Réflexion] {data.get('log', '')}", stepStatus=data.get("status"), stepKey="agent_step")
                            elif data["type"] == "metrics":
                                yield _make_chunk("log", f"📊 [Metrics] Tokens: {data.get('tokens')} | Cost: ${data.get('cost')}", stepStatus="running", tokens=data.get("tokens"), cost=data.get("cost"), stepKey="agent_step")
                        else:
                            yield _make_chunk("log", msg)
                    except json.JSONDecodeError:
                        yield _make_chunk("log", msg)
                except queue.Empty:
                    break

        while thread.is_alive():
            yield from _process_queue()
            time.sleep(0.1)

        # Vider la queue restante
        yield from _process_queue()

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
