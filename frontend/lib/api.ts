/* ── API Client for AgentTest backend ── */

import type { CrewDetail, SSEChunk, AgentConfig, TaskConfig, CrewSettings } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/* ── Health ── */

export async function checkHealth(): Promise<{ status: string; api_key_set: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

/* ── Crews CRUD ── */

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

export async function getCrew(name: string): Promise<CrewDetail> {
  const res = await fetch(`${API_BASE}/api/crews/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`Crew '${name}' not found`);
  return res.json();
}

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

export async function deleteCrew(name: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/crews/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete crew");
}

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

export async function listAllAgents(): Promise<AgentConfig[]> {
  const res = await fetch(`${API_BASE}/api/crews/all/agents`);
  if (!res.ok) return [];
  return res.json();
}

/* ── Tasks CRUD ── */

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

export async function listModels(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/models`, { cache: "no-store" });
  if (!res.ok) return ["gemini/gemini-2.5-flash", "gemini/gemini-1.5-pro"];
  return res.json();
}

/* ── Tools ── */

export async function listTools(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/crews/tools/available`);
  if (!res.ok) return [];
  return res.json();
}

/* ── Chat (SSE Streaming) ── */

export async function streamChat(
  crewName: string,
  options: { message?: string; inputs?: Record<string, any>; max_rpm?: number; llm_override?: string | null; session_id?: string },
  onChunk: (chunk: SSEChunk) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      crew_name: crewName,
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

export async function getWorkspaceProjects(): Promise<import("./types").ProjectInfo[]> {
  const res = await fetch(`${API_BASE}/api/workspace/projects`);
  if (!res.ok) throw new Error("Failed to fetch workspace projects");
  return res.json();
}

export async function browseWorkspaceDirectory(path: string = "."): Promise<import("./types").BrowseResponse> {
  const res = await fetch(`${API_BASE}/api/workspace/browse?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to browse directory");
  }
  return res.json();
}

