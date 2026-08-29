/* ── TypeScript types for AgentTest frontend ── */

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
  messages: ChatMessage[];
  createdAt: string;
  title: string;
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
  type: "log" | "result" | "error";
  content: string;
  timestamp: string;
  code?: number;
  available_models?: string[];
}
