# CrewAI Crew Configurations

This directory contains declarative CrewAI crew definitions in YAML format. Each file defines a specialized team of AI agents that collaborate to complete a specific task.

---

## What is a Crew?

A **crew** is a team of AI agents working together to accomplish a goal. In the AgentTest platform, a crew is a reusable, declarative blueprint that defines:

- **Agents** -- AI workers with specific roles, goals, backstories, and tool access.
- **Tasks** -- Steps the agents execute in sequence, passing context from one to the next.
- **Settings** -- Global configuration controlling memory, rate limits, and execution mode.

Crews are the core building block of the platform. Users interact with crews through the chat interface or the REST API, sending a natural-language prompt and receiving structured, multi-step results streamed in real time via Server-Sent Events (SSE).

### How Crews Work

1. A user sends a message (e.g., "Review the code in `/path/to/project` for security issues").
2. The backend loads the appropriate crew YAML from this directory.
3. Agents and tasks are instantiated from the YAML using `backend/app/core/agent_parser.py`.
4. The CrewAI engine executes the tasks, streaming logs back to the frontend.
5. The user sees a live execution timeline with each agent's output.

Crews can be single-agent (one agent, one task) or multi-agent (several agents working in a pipeline). They can also delegate to other crews via the `execute_crew` tool, enabling meta-orchestration.

---

## YAML Structure

Every crew file follows this structure:

```yaml
# Optional: top-level name and description (used for display)
name: CrewName
description: >
  One-line summary of what this crew does.

# Global settings
crew_settings:
  process: "Séquentiel"       # "Séquentiel" or "Hiérarchique"
  memory: true                 # Enable CrewAI experience memory
  max_rpm: 15                  # Max LLM requests per minute (0 = unlimited)

# List of AI agents
agents:
  - name: AgentName
    role: Short role description
    goal: Actionable objective
    backstory: >
      Domain background that steers tone, expertise, and behavior.
      Can be multi-line using YAML block scalar (| or >).
    llm: openai/qwen-3.6-35b-instruct   # LiteLLM model identifier
    tools:
      - read_file
      - write_file
    verbose: true
    allow_delegation: false
    max_iter: 40                # Optional: max LLM iterations (default 40)

# List of tasks to execute
tasks:
  - description: >
      Detailed task description with {variable} interpolation.
      Variables like {message}, {project_path}, {output_dir} are
      injected at runtime by the chat endpoint.
    expected_output: >
      Exact expected output format.
    agent: AgentName            # Must match an agent name defined above
```

### Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `crew_settings.process` | string | Yes | `"Séquentiel"` (agents work in order) or `"Hiérarchique"` (manager delegates to sub-agents) |
| `crew_settings.memory` | boolean | Yes | Enable CrewAI experience memory so agents retain knowledge across tasks |
| `crew_settings.max_rpm` | integer | Yes | Rate limit for LLM requests per minute. `0` means unlimited |
| `agents[].name` | string | Yes | Unique identifier for the agent within this crew |
| `agents[].role` | string | Yes | Short title for the agent's role |
| `agents[].goal` | string | Yes | Clear, actionable objective |
| `agents[].backstory` | string | Yes | Domain background that steers tone, expertise, and behavior |
| `agents[].llm` | string | Yes | LiteLLM model ID (e.g., `openai/gpt-4o`, `anthropic/claude-3-sonnet`, `ollama/llama3`) |
| `agents[].tools` | string[] | No | Tool names from the registry (see below). Empty list `[]` means no tools |
| `agents[].verbose` | boolean | No | Enable verbose logging (default `false`) |
| `agents[].allow_delegation` | boolean | No | Whether the agent can delegate tasks to other agents in the same crew (default `false`) |
| `agents[].max_iter` | integer | No | Maximum number of LLM iterations (default `40`) |
| `tasks[].description` | string | Yes | Task description supporting `{variable}` interpolation |
| `tasks[].expected_output` | string | Yes | Description of the expected output format |
| `tasks[].agent` | string | Yes | Name of the agent that performs this task |

### Template Variables

Tasks can reference variables that are injected at runtime:

| Variable | Source | Example |
|---|---|---|
| `{message}` | User's chat message | `"{message}"` |
| `{project_path}` | Selected project folder | `"{project_path}/src/main.py"` |
| `{output_dir}` | Auto-generated output directory | `"{output_dir}/report.json"` |
| `{pdf_path}` | Path to an uploaded PDF | `"{pdf_path}"` |
| `{pdf_alternatives}` | Alternative PDF paths | `"{pdf_alternatives}"` |
| `{feature_request}` | Feature description | `"{feature_request}"` |
| `{available_crews_context}` | Catalog of all crews | Used by meta-orchestrators |
| `{available_llms_context}` | Available LLM models | Used by meta-orchestrators |

Any other `{variable}` found in the YAML that is not a known input variable is auto-injected with the string `"valeur_non_fournie"` to prevent CrewAI from crashing.

---

## Process Modes

### Séquentiel (Sequential)

Agents execute tasks one after another. Each task receives the result of the previous task as context. This is the default and most common mode.

```yaml
crew_settings:
  process: "Séquentiel"
```

Use sequential mode when tasks have a natural order: explore -> analyze -> write -> review.

### Hiérarchique (Hierarchical)

A manager agent delegates tasks to sub-agents. The manager has control over the workflow and can assign work based on intermediate results.

```yaml
crew_settings:
  process: "Hiérarchique"
```

Use hierarchical mode when you need a central coordinator that makes decisions about task assignment and workflow direction.

---

## Available Tools

Tools are registered in `backend/app/core/tool_registry.py`. An agent can only use tools explicitly listed in its `tools` array.

| Tool | Description |
|---|---|
| `read_file` | Read file contents safely (path-sanitized) |
| `write_file` | Write file contents safely (path-sanitized) |
| `append_to_file` | Append content to an existing file |
| `file_editor` | Advanced file editing with diff-based changes |
| `terminal_runner` | Execute commands in a sandboxed terminal |
| `list_directory` | List directory contents |
| `run_test_command` | Execute test commands (pytest, vitest, etc.) |
| `execute_python_code` | Run Python code in a sandbox |
| `execute_crew` | Invoke another crew from within a task |
| `web_search` | Perform web searches |
| `read_pdf` | Extract text from PDF files |
| `http_request` | Make HTTP requests |
| `wikipedia_search` | Search Wikipedia |
| `arxiv_search` | Search arXiv for research papers |
| `web_scrape` | Scrape web pages |
| `youtube_transcript` | Extract YouTube video transcripts |
| `search_scholar` | Search Google Scholar |
| `clone_github_repo` | Clone a GitHub repository |
| `gen_code` | Generate code snippets |
| `gen_entrypoint` / `execute_entrypoint` | Generate and run entrypoint scripts |
| `improve_fn` | Improve existing functions |
| `calculate_text_length` | Count characters in text |
| `delete_path` | Delete a file or directory |
| `research_state_of_the_art` | Research state-of-the-art on a topic |
| `download_resources` | Download external resources |
| `generate_state_of_the_art_report` | Generate SoTA report |
| `generate_state_of_the_art_html` | Generate HTML SoTA report |
| `research_educational_resources` | Research educational content |
| `generate_educational_html` | Generate educational HTML |
| `generate_educational_markdown` | Generate educational Markdown |
| `generate_archify_diagram` | Generate architecture diagrams |
| `generate_html_report` | Generate HTML reports |

**Security note:** All file operations go through `PathManager.resolve()` to prevent directory traversal. Shell commands are sandboxed. Tools that execute code (`execute_python_code`, `terminal_runner`) run in isolated environments.

---

## How to Add a New Crew

### Step 1: Create the YAML File

Create a new file in this directory: `backend/config/crews/MyCrew.yaml`

The filename (without `.yaml`) becomes the crew identifier used in the API.

### Step 2: Define the Crew Settings

```yaml
crew_settings:
  process: "Séquentiel"
  memory: true
  max_rpm: 15
```

Choose the process mode based on your workflow:
- **Sequential** for linear pipelines (explore -> analyze -> produce).
- **Hierarchical** when a manager needs to coordinate sub-agents dynamically.

### Step 3: Define the Agents

```yaml
agents:
  - name: Analyst
    role: Senior Data Analyst
    goal: Analyze the data and identify key patterns.
    backstory: >
      You are an expert data analyst with 10 years of experience.
      You excel at finding patterns in complex datasets.
    llm: openai/qwen-3.6-35b-instruct
    tools:
      - read_file
      - list_directory
    verbose: true
    allow_delegation: false
```

**Best practices for agent design:**
- Give each agent a clear, specific role.
- Write backstories that steer tone and expertise (the LLM reads these as system prompts).
- Only grant the tools the agent actually needs.
- Set `allow_delegation: true` only if the agent needs to delegate to peers.
- Use `max_iter` to limit how many LLM calls an agent can make (prevents infinite loops).

### Step 4: Define the Tasks

```yaml
tasks:
  - description: >
      Analyze the data in "{project_path}" and identify key patterns.

      1. List the files in the project directory.
      2. Read the relevant data files.
      3. Identify patterns and anomalies.
    expected_output: >
      A structured report of findings with specific data points.
    agent: Analyst
```

**Best practices for task design:**
- Use numbered steps for clarity.
- Reference `{message}` for the user's input, `{project_path}` for the project folder, and `{output_dir}` for writing results.
- Be specific about the expected output format.
- Each task should have a clear, verifiable deliverable.

### Step 5: Test the Crew

Send a request to the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze the project at /path/to/project",
    "crew_name": "MyCrew"
  }'
```

Or use the frontend chat interface to select your crew and send a message.

### Step 6 (Optional): Register in Capabilities

If you want your crew to appear in the UI with a custom description and keywords, add it to `backend/config/capabilities.json`:

```json
{
  "crews": {
    "MyCrew": {
      "description": "Analyzes data and identifies patterns.",
      "keywords": ["analyse", "données", "patterns", "data"]
    }
  }
}
```

---

## How to Modify Existing Crews

### Direct YAML Editing

Changes to YAML files take effect immediately on the next API request -- no server restart is needed. Simply edit the file and send a new message.

### Runtime Modification via API

The endpoints in `backend/app/api/crews.py` provide full CRUD operations:

| Operation | Endpoint | Description |
|---|---|---|
| List all crews | `GET /api/crews` | Returns all crew names |
| Get crew details | `GET /api/crews/{name}` | Returns full crew config |
| Create crew | `POST /api/crews` | Creates a new crew YAML |
| Delete crew | `DELETE /api/crews/{name}` | Removes a crew YAML |
| Add agent | `POST /api/crews/{name}/agents` | Adds an agent to an existing crew |
| Update agent | `PUT /api/crews/{name}/agents/{index}` | Replaces an agent by index |
| Delete agent | `DELETE /api/crews/{name}/agents/{index}` | Removes an agent by index |
| Add task | `POST /api/crews/{name}/tasks` | Adds a task to an existing crew |
| Update task | `PUT /api/crews/{name}/tasks/{index}` | Replaces a task by index |
| Delete task | `DELETE /api/crews/{name}/tasks/{index}` | Removes a task by index |
| Update settings | `PUT /api/crews/{name}/settings` | Updates crew_settings |
| Import from GitHub | `POST /api/crews/import` | Imports a crew YAML from a GitHub raw URL |

### Modifying an Existing Crew

1. Edit the YAML file directly in your editor.
2. Or use the API endpoints above to modify agents, tasks, or settings programmatically.
3. Test by sending a message through the chat interface.

**Important:** When modifying agents, the `name` field must remain unique within the crew. When modifying tasks, the `agent` reference must match an existing agent name.

---

## Crew Architecture Patterns

### Pattern 1: Single-Agent Pipeline

One agent, one task. Simplest form, good for focused operations.

```yaml
# Example: Web_Researcher
agents:
  - name: Web_Researcher
    role: Senior Web Research Analyst
    goal: Research the web and produce comprehensive reports.
    backstory: >
      Expert in web research and information synthesis.
    llm: openai/qwen-3.6-35b-instruct
    tools: [web_search]
    verbose: true

tasks:
  - description: >
      Research the following topic: "{message}"
      1. Search the web for relevant information.
      2. Synthesize findings into a structured report.
    expected_output: A structured Markdown report with references.
    agent: Web_Researcher
```

### Pattern 2: Multi-Agent Sequential Pipeline

Multiple agents working in sequence, each building on the previous output.

```yaml
# Example: Reviewer (3-phase audit)
agents:
  - name: Explorateur_Projet    # Phase 1: maps the codebase
  - name: Auditeur_Code         # Phase 2: reads and analyzes files
  - name: Lead_Tech_Redacteur   # Phase 3: compiles the report

tasks:
  - description: "Explore the project structure..."  # agent: Explorateur_Projet
  - description: "Analyze each identified file..."   # agent: Auditeur_Code
  - description: "Generate the final report..."      # agent: Lead_Tech_Redacteur
```

In sequential mode, each task automatically receives the result of the previous task as context.

### Pattern 3: Hierarchical Delegation

A manager agent coordinates sub-agents, making dynamic decisions about task assignment.

```yaml
crew_settings:
  process: "Hiérarchique"

agents:
  - name: Manager
    role: Project Manager
    goal: Coordinate the team and ensure quality.
    allow_delegation: true
  - name: Developer
    role: Senior Developer
    goal: Implement the requested features.
    allow_delegation: false
```

### Pattern 4: Meta-Orchestration (Crew-to-Crew)

A crew that delegates to other crews via the `execute_crew` tool. This enables recursive, self-directed workflows.

```yaml
# Example: Autonomous_SWE
agents:
  - name: Autonomous_SWE
    role: Meta-Orchestrator
    goal: Orchestrate all other crews to complete complex tasks.
    tools:
      - read_file
      - write_file
      - file_editor
      - execute_crew    # <-- Key tool for meta-orchestration
```

The meta-orchestrator receives `{available_crews_context}` and `{available_llms_context}` variables that list all available crews and models, enabling it to make informed delegation decisions.

### Pattern 5: Self-Healing Loop

A crew that detects failures and retries automatically, potentially invoking other crews to fix issues.

```yaml
# Example: Tester
tasks:
  - description: "Map the project structure..."
    agent: Cartographe_QA
  - description: "Generate test files..."
    agent: Ingenieur_Tests_Automatises
  - description: |
      Execute tests and self-heal:
      1. Run tests via 'run_test_command'.
      2. If tests fail, invoke the 'Fixer' crew via 'execute_crew'.
      3. Re-run tests after fixes.
      4. Repeat up to 3 times.
    agent: Ingenieur_Tests_Automatises
```

---

## Common Crew Configurations

### Minimal Crew (1 agent, 1 task)

```yaml
crew_settings:
  process: "Séquentiel"
  memory: false
  max_rpm: 10

agents:
  - name: SimpleAgent
    role: Simple Role
    goal: Do one thing well.
    backstory: You are good at one thing.
    llm: openai/qwen-3.6-35b-instruct
    tools: [read_file]
    verbose: false

tasks:
  - description: "Read the file at {project_path} and summarize it."
    expected_output: A brief summary of the file contents.
    agent: SimpleAgent
```

### Full-Stack Development Crew (2 agents, 2 tasks)

```yaml
crew_settings:
  process: "Séquentiel"
  memory: true
  max_rpm: 20

agents:
  - name: Architect
    role: Software Architect
    goal: Design the solution and plan the implementation.
    backstory: Expert architect who plans before coding.
    llm: openai/qwen-3.6-35b-instruct
    tools: [read_file, list_directory, write_file]
    verbose: true
    max_iter: 30

  - name: Developer
    role: Senior Developer
    goal: Implement the architecture plan.
    backstory: Expert developer who writes clean, tested code.
    llm: openai/qwen-3.6-35b-instruct
    tools: [read_file, write_file, file_editor, run_test_command]
    verbose: true
    max_iter: 70

tasks:
  - description: "Analyze {project_path} and design an implementation plan."
    expected_output: A detailed implementation plan.
    agent: Architect

  - description: "Implement the plan in {project_path} and run tests."
    expected_output: Updated code files and test results.
    agent: Developer
```

### Crew with Memory and Rate Limiting

```yaml
crew_settings:
  process: "Séquentiel"
  memory: true        # Agents remember across tasks
  max_rpm: 10         # Conservative rate limit for deep analysis
```

Use `memory: true` when agents need to retain context across multiple interactions. Use a lower `max_rpm` for crews that perform deep analysis (code review, security audit) to avoid overwhelming the LLM provider.

### Crew with Custom LLM per Agent

```yaml
agents:
  - name: FastAnalyst
    role: Quick Analyst
    goal: Fast analysis.
    backstory: Quick and efficient.
    llm: openai/llama-3.1-8b       # Fast, cheap model for simple tasks
    tools: [read_file]

  - name: DeepThinker
    role: Deep Analyst
    goal: Deep, thorough analysis.
    backstory: Takes time to think carefully.
    llm: openai/gpt-oss-120b        # Powerful model for complex reasoning
    tools: [read_file, list_directory]
```

Different agents can use different models. Use fast models for simple tasks and expert models for complex reasoning. The `capabilities.json` file defines the default model tiers:

| Tier | Model | Use Case |
|---|---|---|
| `fast` | `openai/llama-3.1-8b` | Simple, quick tasks |
| `balanced` | `openai/qwen-3.6-35b-instruct` | General-purpose work |
| `expert` | `openai/gpt-oss-120b` | Complex reasoning, architecture |

---

## Relationship with the AgentTest Platform

### Data Flow

```
User Message (UI)
    |
    v
POST /api/chat  (chat.py)
    |
    v
crew_runner.run_crew()
    |
    v
agent_parser.create_agents_from_yaml()   -- loads YAML
agent_parser.create_tasks_from_yaml()    -- builds task graph
    |
    v
CrewAI kickoff() with SSE streaming
    |
    v
Frontend: ExecutionTimeline + AgentLog components
```

### Integration Points

1. **`backend/app/api/chat.py`** -- The chat endpoint that dispatches to crews. Accepts `crew_name` in the request body.

2. **`backend/app/core/crew_manager.py`** -- CRUD operations for crews. Lists, loads, creates, deletes, and modifies crew YAML files.

3. **`backend/app/core/crew_runner.py`** -- Executes crews with SSE streaming. Handles LLM interception, retry logic, and log queue management.

4. **`backend/app/core/agent_parser.py`** -- Parses YAML into CrewAI `Agent` and `Task` objects. Validates required fields and resolves tool references.

5. **`backend/app/core/tool_registry.py`** -- Single source of truth for available tools. Agents can only use tools listed here.

6. **`backend/config/capabilities.json`** -- Maps crew names to UI descriptions and search keywords. Controls which crews appear in the UI crew selector.

7. **Frontend (`frontend/lib/api.ts`, `frontend/lib/types.ts`)** -- SSE client that receives and renders crew execution logs. The `CrewSelector` component reads from `capabilities.json` to display available crews.

### Runtime Behavior

- Crew YAML files are read on every request (no caching). Changes take effect immediately.
- The `name` field in the YAML must match the filename (without `.yaml`).
- If a crew file is missing or malformed, the API returns an error chunk: `{"type": "error", "content": "..."}`.
- Crews execute in a background thread; logs are streamed via SSE to the frontend in real time.
- The `run_multi_crew()` function supports executing multiple crews sequentially or in parallel, with accumulated context passed between crews.

---

## Troubleshooting

### Crew Not Found

```
{"type": "error", "content": "Crew 'MyCrew' introuvable."}
```

- Verify the YAML filename matches the crew name exactly (case-sensitive).
- Check that the file is in `backend/config/crews/`.
- Ensure the file is valid YAML (no trailing spaces, proper indentation).

### Agent Not Found in Task

```
ValueError: Tache reference l'agent « Unknown » mais aucun agent avec ce nom n'existe.
```

- The `agent` field in a task must exactly match an `agents[].name` in the same file.
- Check for typos and whitespace issues.

### Tool Not Found

```
ValueError: Outil « unknown_tool » referenced but absent from available_tools.
```

- The tool must be registered in `backend/app/core/tool_registry.py`.
- Check the tool name spelling in the agent's `tools` array.

### LLM Error

- Verify the `llm` field uses a valid LiteLLM model ID.
- Check that `LLM_API_KEY` and `LLM_BASE_URL` are set in `backend/.env`.
- Check that the model is available from your LLM provider.

### Infinite Loop

- Set `max_iter` on agents that might loop (e.g., self-healing crews).
- Use `memory: false` if memory is causing unexpected behavior.
- Review the agent's backstory for instructions that might cause loops.
