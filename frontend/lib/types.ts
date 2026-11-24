/* ── TypeScript types for AgentTest frontend ──
 *
 * Data contracts shared between the Next.js frontend and the FastAPI backend.
 * These interfaces mirror the Pydantic schemas in backend/app/schemas/ and
 * the SSE chunk format produced by backend/app/api/chat.py.
 *
 * Key contracts:
 * - ChatMessage / Conversation: persisted in localStorage (key: "agenttest_conversations")
 * - SSEChunk: matches the JSON payload from the SSE stream (type field determines rendering)
 * - CrewDetail / AgentConfig / TaskConfig: loaded from YAML via /api/crews endpoints
 * - ProjectInfo / BrowseResponse: returned by /api/workspace endpoints
 */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  type?: "log" | "result" | "error";
}

export interface Conversation {
  id: string;
  crewName: string;
  crewNames?: string[];
  executionMode?: "sequential" | "parallel";
  messages: ChatMessage[];
  createdAt: string;
  title: string;
  folderContext?: string;
}

export interface CrewSettings {
  process: "Séquentiel" | "Hiérarchique";
  memory: boolean;
  max_rpm: number;
}

export interface CrewDetail {
  name: string;
  crew_settings: CrewSettings;
  agents: AgentConfig[];
  tasks: TaskConfig[];
}

export interface AgentConfig {
  name: string;
  role: string;
  goal: string;
  backstory: string;
  llm: string;
  tools: string[];
  verbose: boolean;
  allow_delegation: boolean;
}

export interface TaskConfig {
  description: string;
  expected_output: string;
  agent: string;
}

export interface SSEChunk {
  type: "log" | "result" | "error" | "step" | "metrics" | "session_info";
  content: string;
  timestamp: string;
  code?: number;
  available_models?: string[];
  stepStatus?: string;
  stepKey?: string;
  status?: string;
  tokens?: number;
  cost?: number;
  crewName?: string;
  log?: string;
}

export interface StreamChatOptions {
  message?: string;
  inputs?: Record<string, unknown>;
  max_rpm?: number;
  llm_override?: string | null;
}

export interface CrewPipelineStep {
  crewName: string;
  status: "pending" | "running" | "completed" | "error";
  tokens?: number;
  cost?: number;
}

export interface CrewLaunchField {
  key: string;
  label: string;
  placeholder?: string;
  defaultValue?: string;
  type: "text" | "textarea" | "path" | "select";
  options?: string[];
  description?: string;
  required?: boolean;
}

export interface ProjectInfo {
  name: string;
  path: string;
  absolute_path: string;
  is_current: boolean;
  framework: string;
  tags: string[];
  has_git: boolean;
  has_tests: boolean;
  has_package_json: boolean;
  last_modified: number;
}

export interface DirectoryItem {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number | null;
  has_subdirs: boolean;
}

export interface BrowseResponse {
  current_path: string;
  absolute_path: string;
  parent_path: string | null;
  breadcrumbs: { name: string; path: string }[];
  directories: DirectoryItem[];
  files_count: number;
}
