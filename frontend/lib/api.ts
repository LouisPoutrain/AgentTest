/* ── API Client for AgentTest backend ──
 *
 * Typed wrappers around the FastAPI REST endpoints and the SSE chat stream.
 * All functions throw on HTTP errors; the SSE client parses `data: {...}`
 * lines and invokes the caller-supplied `onChunk` callback for each chunk.
 */

import type { CrewDetail, SSEChunk, AgentConfig, CrewSettings, ProjectInfo, BrowseResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/* ── Health ── */

/**
 * Pings the backend health endpoint.
 *
 * @returns `{ status: "ok", api_key_set: boolean }`
 * @throws Error if the backend is unreachable.
 */
export async function checkHealth(): Promise<{ status: string; api_key_set: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

/* ── Crews CRUD ── */

/**
 * Lists all crew names defined in ``config/crews/``.
 *
 * @returns Array of crew name strings.
 */
export async function listCrews(): Promise<string[]> {
  console.log("Fetching crews from:", `${API_BASE}/api/crews`);
  try {
    const res = await fetch(`${API_BASE}/api/crews`, { cache: "no-store" });
    console.log("Crews response status:", res.status);
    if (!res.ok) throw new Error("Failed to list crews: " + res.statusText);
    const data = await res.json();
    console.log("Fetched crews:", data.length);
    return data;
  } catch (err) {
    console.error("Error in listCrews:", err);
    throw err;
  }
}

/**
 * Fetches the full configuration of a single crew.
 *
 * @param name - Crew name (matches the YAML filename without ``.yaml``).
 * @returns Crew detail including settings, agents, and tasks.
 * @throws Error if the crew does not exist.
 */
export async function getCrew(name: string): Promise<CrewDetail> {
  const res = await fetch(`${API_BASE}/api/crews/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`Crew '${name}' not found`);
  return res.json();
}

/**
 * Creates a new crew with the given settings.
 *
 * @param name - Unique crew name.
 * @param settings - Optional process, memory, and max_rpm configuration.
 * @returns The created crew detail.
 * @throws Error if a crew with this name already exists.
 */
export async function createCrew(
  name: string,
  settings?: { process?: string; memory?: boolean; max_rpm?: number }
): Promise<CrewDetail> {
  const res = await fetch(`${API_BASE}/api/crews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, settings: settings || {} }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create crew");
  }
  return res.json();
}

/**
 * Deletes a crew and all its agents and tasks.
 *
 * @param name - Crew name to delete.
 * @throws Error if the crew does not exist.
 */
export async function deleteCrew(name: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/crews/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete crew");
}

/**
 * Updates the global settings of an existing crew.
 *
 * Only provided fields are updated; omitted fields remain unchanged.
 *
 * @param crewName - Crew name.
 * @param settings - Partial ``CrewSettings`` to merge.
 * @returns Updated crew detail.
 * @throws Error on invalid settings or if the crew does not exist.
 */
export async function updateCrewSettings(
  crewName: string,
  settings: Partial<CrewSettings>
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/settings`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update crew settings");
  }
  return res.json();
}

/* ── Agents CRUD ── */

/**
 * Adds a new agent to an existing crew.
 *
 * @param crewName - Crew name.
 * @param agent - Agent definition (name, role, goal, backstory, llm, tools).
 * @returns Updated crew detail.
 * @throws Error if the crew does not exist or the agent name conflicts.
 */
export async function addAgent(
  crewName: string,
  agent: {
    name: string;
    role: string;
    goal: string;
    backstory: string;
    llm: string;
    tools: string[];
    verbose?: boolean;
    allow_delegation?: boolean;
  }
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/agents`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(agent),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to add agent");
  }
  return res.json();
}

/**
 * Updates an existing agent within a crew by zero-based index.
 *
 * @param crewName - Crew name.
 * @param index - Zero-based index of the agent to update.
 * @param agent - Updated agent definition.
 * @returns Updated crew detail.
 * @throws Error if the crew or agent index does not exist.
 */
export async function updateAgent(
  crewName: string,
  index: number,
  agent: {
    name: string;
    role: string;
    goal: string;
    backstory: string;
    llm: string;
    tools: string[];
    verbose?: boolean;
    allow_delegation?: boolean;
  }
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/agents/${index}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(agent),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update agent");
  }
  return res.json();
}

/**
 * Removes an agent from a crew by zero-based index.
 *
 * @param crewName - Crew name.
 * @param index - Zero-based index of the agent to remove.
 * @returns Updated crew detail.
 * @throws Error if the crew or agent index does not exist.
 */
export async function deleteAgent(
  crewName: string,
  index: number
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/agents/${index}`,
    {
      method: "DELETE",
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete agent");
  }
  return res.json();
}

/**
 * Returns all unique agent definitions across all crews.
 *
 * @returns Array of agent configuration objects.
 */
export async function listAllAgents(): Promise<AgentConfig[]> {
  const res = await fetch(`${API_BASE}/api/crews/all/agents`);
  if (!res.ok) return [];
  return res.json();
}

/* ── Tasks CRUD ── */

/**
 * Adds a new task to an existing crew, assigned to a specific agent.
 *
 * @param crewName - Crew name.
 * @param task - Task definition (description, expected_output, agent).
 * @returns Updated crew detail.
 * @throws Error if the crew does not exist.
 */
export async function addTask(
  crewName: string,
  task: { description: string; expected_output: string; agent: string }
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/tasks`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(task),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to add task");
  }
  return res.json();
}

/**
 * Updates an existing task within a crew by zero-based index.
 *
 * @param crewName - Crew name.
 * @param index - Zero-based index of the task to update.
 * @param task - Updated task definition.
 * @returns Updated crew detail.
 * @throws Error if the crew or task index does not exist.
 */
export async function updateTask(
  crewName: string,
  index: number,
  task: { description: string; expected_output: string; agent: string }
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/tasks/${index}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(task),
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update task");
  }
  return res.json();
}

/**
 * Removes a task from a crew by zero-based index.
 *
 * @param crewName - Crew name.
 * @param index - Zero-based index of the task to remove.
 * @returns Updated crew detail.
 * @throws Error if the crew or task index does not exist.
 */
export async function deleteTask(
  crewName: string,
  index: number
): Promise<CrewDetail> {
  const res = await fetch(
    `${API_BASE}/api/crews/${encodeURIComponent(crewName)}/tasks/${index}`,
    {
      method: "DELETE",
    }
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to delete task");
  }
  return res.json();
}

/* ── Models ── */

/**
 * Lists all available LLM model identifiers.
 *
 * Models are loaded from the LiteLLM configuration and include both
 * local (Ollama) and remote (OpenAI, Anthropic) model identifiers.
 *
 * @returns Array of model strings (e.g. ``"openai/gpt-4o"``).
 */
export async function listModels(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/models`, { cache: "no-store" });
  if (!res.ok) return ["openai/qwen-3.6-35b-instruct"];
  return res.json();
}

/* ── Tools ── */

/**
 * Returns the list of all tools available for use by agents in crews.
 *
 * Tools are registered in the tool registry and include file operations,
 * search, and custom CrewAI tools.
 *
 * @returns Array of tool name strings.
 */
export async function listTools(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/crews/tools/available`);
  if (!res.ok) return [];
  return res.json();
}

/* ── Chat (SSE Streaming) ── */

/**
 * Opens an SSE connection to ``/api/chat`` and streams JSON chunks.
 *
 * The SSE stream follows a strict lifecycle:
 * 1. ``session_info`` chunk — sent first, contains the ``session_id``.
 * 2. ``log`` chunks — streaming log messages from crew execution or meta-router.
 * 3. ``result`` chunk — final result text, sent when execution completes.
 * 4. Connection closes after the final chunk.
 *
 * On error, an ``error`` chunk is sent instead of ``result``.
 *
 * The client must pass an ``onChunk`` callback to process each parsed
 * ``SSEChunk``. The ``AbortSignal`` can be used to cancel the stream.
 *
 * @param crewName - Crew name (ignored if ``crew_names`` is provided).
 * @param options - Message, inputs, model override, RPM limit, and crew list.
 * @param onChunk - Callback invoked for every parsed SSE chunk.
 * @param signal - Optional ``AbortSignal`` to cancel the stream.
 * @throws Error if the HTTP response is not OK or no readable stream is returned.
 */
export async function streamChat(
  crewName: string,
  options: { message?: string; inputs?: Record<string, unknown>; max_rpm?: number; llm_override?: string | null; session_id?: string; crew_names?: string[]; execution_mode?: "sequential" | "parallel" },
  onChunk: (chunk: SSEChunk) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      crew_name: crewName,
      crew_names: options.crew_names || null,
      execution_mode: options.execution_mode || "sequential",
      message: options.message || "",
      inputs: options.inputs || null,
      max_rpm: options.max_rpm || 15,
      llm_override: options.llm_override || null,
      session_id: options.session_id,
    }),
    signal,
  });

  if (!res.ok) {
    throw new Error("Failed to start chat stream");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No readable stream");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const chunk: SSEChunk = JSON.parse(line.slice(6));
          onChunk(chunk);
        } catch {
          // Skip malformed chunks
        }
      }
    }
  }
}

/* ── Workspace & Projects Discovery ── */

/**
 * Lists all projects discovered in the workspace root.
 *
 * Each project includes a name, path, and detected stack type.
 *
 * @returns Array of ``ProjectInfo`` objects.
 * @throws Error if the workspace endpoint fails.
 */
export async function getWorkspaceProjects(): Promise<ProjectInfo[]> {
  const res = await fetch(`${API_BASE}/api/workspace/projects`);
  if (!res.ok) throw new Error("Failed to fetch workspace projects");
  return res.json();
}

/**
 * Browses a directory within the workspace and returns its contents.
 *
 * Each entry includes the file name, type (file/directory), and path.
 * A ``breadcrumbs`` array and parent path are included for navigation.
 *
 * @param path - Directory path relative to the workspace root (default ``"."``).
 * @returns ``BrowseResponse`` with entries, breadcrumbs, and parent path.
 * @throws Error if the directory cannot be browsed.
 */
export async function browseWorkspaceDirectory(path: string = "."): Promise<BrowseResponse> {
  const res = await fetch(`${API_BASE}/api/workspace/browse?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to browse directory");
  }
  return res.json();
}

