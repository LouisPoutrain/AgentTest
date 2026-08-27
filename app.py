"""
app.py — Interface Streamlit pour l'orchestrateur AgentTest (Multi-Crews).

Cinq onglets :
- 📊 Dashboard & Gestion : Gérer les Crews (Visualiser, Supprimer).
- 🏗️ Nouveau Crew      : Créer un fichier Crew vide.
- 🤖 Ajouter Agent     : Ajouter un agent à un Crew existant.
- 📋 Ajouter Tâche     : Ajouter une tâche à un Crew existant.
- 🚀 Espace d'Exécution : Lancer l'orchestration d'un Crew.
"""

from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from crewai import Crew

from core.agent_parser import create_agents_from_yaml, create_tasks_from_yaml
from core.git_importer import download_yaml_from_github
from tools.custom_tools import (
    calculate_text_length,
    web_search,
    read_file,
    write_file,
    delete_path,
    execute_python_code,
    clone_github_repo
)

# ── Configuration ────────────────────────────────────────────────────────────

load_dotenv()

CREWS_DIR = Path(__file__).resolve().parent / "config" / "crews"
CREWS_DIR.mkdir(parents=True, exist_ok=True)

AVAILABLE_TOOLS = {
    "calculate_text_length": calculate_text_length,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "delete_path": delete_path,
    "execute_python_code": execute_python_code,
    "clone_github_repo": clone_github_repo,
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_all_crews() -> list[str]:
    """Retourne la liste des noms de fichiers YAML dans le dossier config/crews/."""
    return [f.name for f in CREWS_DIR.glob("*.yaml")]

def load_config(crew_filename: str) -> dict:
    """Charge le fichier YAML d'un Crew et retourne son contenu brut."""
    path = CREWS_DIR / crew_filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_config(crew_filename: str, config: dict) -> None:
    """Sauvegarde le dictionnaire dans le fichier YAML d'un Crew."""
    path = CREWS_DIR / crew_filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            config,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

# ── Page Streamlit ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AgentTest — Orchestrateur IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AgentTest — Dashboard Multi-Crews")
st.caption("Gérez vos équipes d'agents IA, configurez leurs tâches et lancez des orchestrations autonomes.")

# Liste globale des crews
all_crews = get_all_crews()

# Message de bienvenue si aucun crew
if not all_crews:
    st.info("👋 Bienvenue ! Vous n'avez pas encore de Crew configuré. Utilisez l'onglet « 🏗️ Nouveau Crew » ou « 🌐 Import Git » (dans le sidebar ou ci-dessous) pour démarrer.")

# ── Onglets ──────────────────────────────────────────────────────────────────

tab_dash, tab_new, tab_agent, tab_task, tab_run = st.tabs([
    "📊 Dashboard & Gestion",
    "🏗️ Nouveau Crew",
    "🤖 Ajouter Agent",
    "📋 Ajouter Tâche",
    "🚀 Espace d'Exécution",
])

# ==============================================================================
# Onglet 1 : Dashboard & Gestion
# ==============================================================================
with tab_dash:
    st.header("Gestion des Crews")
    
    if not all_crews:
        st.warning("Aucun Crew disponible.")
    else:
        selected_crew_dash = st.selectbox("Sélectionner un Crew à inspecter", all_crews, key="dash_crew_select")
        
        if selected_crew_dash:
            config = load_config(selected_crew_dash)
            agents_cfg = config.get("agents", [])
            tasks_cfg = config.get("tasks", [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"👥 Agents ({len(agents_cfg)})")
                for agent_cfg in agents_cfg:
                    with st.expander(f"🤖 {agent_cfg.get('role', 'Sans rôle')} — `{agent_cfg.get('name', '?')}`"):
                        st.markdown(f"**But :** {agent_cfg.get('goal', '—')}")
                        st.markdown(f"**Backstory :** {agent_cfg.get('backstory', '—')}")
                        st.markdown(f"**LLM :** `{agent_cfg.get('llm', '—')}`")
                        tools = agent_cfg.get("tools", [])
                        st.markdown(f"**Outils :** {', '.join(f'`{t}`' for t in tools) if tools else 'Aucun'}")
                        
            with col2:
                st.subheader(f"📋 Tâches ({len(tasks_cfg)})")
                for i, task_cfg in enumerate(tasks_cfg, 1):
                    with st.expander(f"Tâche {i} — Agent : `{task_cfg.get('agent', '?')}`"):
                        st.markdown(f"**Description :** {task_cfg.get('description', '—')}")
                        st.markdown(f"**Sortie attendue :** {task_cfg.get('expected_output', '—')}")
            
            st.divider()
            st.markdown("### Danger Zone")
            if st.button("🗑️ Supprimer ce Crew", type="primary", use_container_width=True):
                (CREWS_DIR / selected_crew_dash).unlink()
                st.toast(f"Crew {selected_crew_dash} supprimé.")
                st.rerun()

# ==============================================================================
# Onglet 2 : Nouveau Crew
# ==============================================================================
with tab_new:
    st.header("Créer un nouveau Crew")
    col_new_manual, col_new_git = st.columns(2)
    
    with col_new_manual:
        st.subheader("📝 Création Manuelle")
        new_crew_name = st.text_input("Nom du Crew (sans .yaml)", placeholder="ex: dev_team")
        if st.button("🏗️ Créer le Crew vide", use_container_width=True):
            if not new_crew_name.strip():
                st.error("Le nom ne peut pas être vide.")
            else:
                filename = f"{new_crew_name.strip()}.yaml"
                if filename in all_crews:
                    st.error("Ce Crew existe déjà.")
                else:
                    save_config(filename, {"agents": [], "tasks": []})
                    st.toast(f"Crew {filename} créé avec succès !")
                    st.rerun()

    with col_new_git:
        st.subheader("🌐 Import Git")
        git_url = st.text_input(
            "URL brute du fichier YAML sur GitHub",
            placeholder="https://raw.githubusercontent.com/.../crew.yaml",
            key="git_url",
        )
        git_crew_name = st.text_input("Nom sous lequel sauvegarder le Crew", placeholder="ex: imported_crew", key="git_crew_name")
        
        if st.button("📥 Importer depuis GitHub", use_container_width=True, key="btn_git"):
            if not git_url or not git_crew_name:
                st.error("❌ Veuillez saisir une URL et un nom de Crew.")
            else:
                try:
                    saved_path = download_yaml_from_github(git_url, CREWS_DIR, git_crew_name)
                    st.toast(f"✅ Configuration importée dans `{saved_path.name}` !")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'import : {e}")

# ==============================================================================
# Onglet 3 : Ajouter Agent
# ==============================================================================
with tab_agent:
    st.header("Ajouter un agent à un Crew")
    if not all_crews:
        st.warning("Aucun Crew disponible. Veuillez d'abord en créer un.")
    else:
        target_crew_agent = st.selectbox("Sélectionnez le Crew", all_crews, key="select_crew_agent")
        
        with st.form("agent_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                agent_name = st.text_input("Nom (identifiant unique)", placeholder="ex: coder")
                agent_role = st.text_input("Rôle", placeholder="ex: Développeur Senior")
                agent_llm = st.selectbox("Modèle LLM", options=["gemini/gemini-3.6-flash", "gemini/gemini-2.5-pro"])
            with col2:
                agent_goal = st.text_area("But (Goal)", height=100)
                agent_backstory = st.text_area("Background (Backstory)", height=100)

            st.markdown("**Outils disponibles :**")
            tool_cols = st.columns(3)
            selected_tools = []
            for i, tool_name in enumerate(AVAILABLE_TOOLS):
                with tool_cols[i % 3]:
                    if st.checkbox(f"`{tool_name}`", key=f"tool_{tool_name}"):
                        selected_tools.append(tool_name)

            agent_verbose = st.checkbox("Mode verbose", value=True)
            submitted_agent = st.form_submit_button("➕ Ajouter l'agent", use_container_width=True)

        if submitted_agent:
            if not agent_name or not agent_role or not agent_goal or not agent_backstory:
                st.error("❌ Tous les champs textes sont obligatoires.")
            else:
                config = load_config(target_crew_agent)
                if "agents" not in config:
                    config["agents"] = []
                
                existing_names = [a.get("name") for a in config["agents"]]
                if agent_name in existing_names:
                    st.error(f"❌ L'agent « {agent_name} » existe déjà dans {target_crew_agent}.")
                else:
                    new_agent = {
                        "name": agent_name,
                        "role": agent_role,
                        "goal": agent_goal,
                        "backstory": agent_backstory,
                        "verbose": agent_verbose,
                        "allow_delegation": False,
                        "llm": agent_llm,
                        "tools": selected_tools,
                    }
                    config["agents"].append(new_agent)
                    save_config(target_crew_agent, config)
                    st.toast(f"✅ Agent « {agent_role} » ajouté à {target_crew_agent} !")
                    st.rerun()

# ==============================================================================
# Onglet 4 : Ajouter Tâche
# ==============================================================================
with tab_task:
    st.header("Ajouter une tâche à un Crew")
    if not all_crews:
        st.warning("Aucun Crew disponible.")
    else:
        target_crew_task = st.selectbox("Sélectionnez le Crew", all_crews, key="select_crew_task")
        
        config_for_tasks = load_config(target_crew_task)
        agent_names = [a.get("name", "?") for a in config_for_tasks.get("agents", [])]
        
        if not agent_names:
            st.warning(f"⚠️ Aucun agent dans {target_crew_task}. Ajoutez un agent d'abord.")
        else:
            with st.form("task_form", clear_on_submit=True):
                task_description = st.text_area("Description de la tâche", height=120)
                task_expected_output = st.text_input("Sortie attendue")
                task_agent = st.selectbox("Agent assigné", options=agent_names)
                
                submitted_task = st.form_submit_button("➕ Ajouter la tâche", use_container_width=True)

            if submitted_task:
                if not task_description or not task_expected_output:
                    st.error("❌ Description et sortie attendue sont obligatoires.")
                else:
                    if "tasks" not in config_for_tasks:
                        config_for_tasks["tasks"] = []
                    new_task = {
                        "description": task_description,
                        "expected_output": task_expected_output,
                        "agent": task_agent,
                    }
                    config_for_tasks["tasks"].append(new_task)
                    save_config(target_crew_task, config_for_tasks)
                    st.toast(f"✅ Tâche ajoutée à {target_crew_task} !")
                    st.rerun()

# ==============================================================================
# Onglet 5 : Espace d'Exécution
# ==============================================================================
with tab_run:
    st.header("🚀 Lancer l'exécution d'un Crew")
    
    if not os.getenv("GEMINI_API_KEY"):
        st.error("❌ Variable `GEMINI_API_KEY` manquante. Ajoutez-la dans votre `.env`.")
        st.stop()

    if not all_crews:
        st.warning("Aucun Crew disponible à exécuter.")
    else:
        selected_crew_run = st.selectbox("Sélectionnez le Crew à exécuter", all_crews, key="select_crew_run")
        config_run = load_config(selected_crew_run)
        
        if not config_run.get("tasks"):
            st.warning(f"⚠️ Impossible de lancer : aucune tâche définie dans {selected_crew_run}.")
        else:
            if st.button("🔥 Lancer le Kickoff", use_container_width=True, type="primary"):
                with st.spinner(f"Exécution de {selected_crew_run} en cours... (Cela peut prendre plusieurs minutes)"):
                    try:
                        old_stdout = sys.stdout
                        captured = StringIO()
                        sys.stdout = captured

                        config_path = CREWS_DIR / selected_crew_run
                        agents = create_agents_from_yaml(config_path, available_tools=AVAILABLE_TOOLS)
                        tasks = create_tasks_from_yaml(config_path, agents)

                        crew = Crew(
                            agents=agents,
                            tasks=tasks,
                            verbose=True,
                            memory=True,
                            embedder={
                                "provider": "google-generativeai",
                                "config": {
                                    "model": "models/text-embedding-004",
                                    "api_key": os.getenv("GEMINI_API_KEY"),
                                },
                            },
                        )

                        result = crew.kickoff()
                        
                        sys.stdout = old_stdout
                        
                        st.success("🎉 Résultat final :")
                        st.markdown(f"> {result}")

                        with st.expander("📜 Logs d'exécution détaillés"):
                            st.code(captured.getvalue(), language="text")

                    except Exception as e:
                        sys.stdout = old_stdout
                        st.error(f"❌ Erreur lors de l'exécution : {e}")
