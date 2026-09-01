"use client";

import type { ChatMessage, Conversation } from "./types";

const STORAGE_KEY = "agenttest_conversations";

/* ── Helpers ── */

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/* ── LocalStorage persistence ── */

export function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveConversations(conversations: Conversation[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

/* ── Conversation management ── */

export function createConversation(crewName: string): Conversation {
  return {
    id: generateId(),
    crewName,
    messages: [],
    createdAt: new Date().toISOString(),
    title: `${crewName} — ${new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`,
  };
}

export function addMessageToConversation(
  conversation: Conversation,
  role: "user" | "assistant",
  content: string,
  type?: "log" | "result" | "error"
): Conversation {
  const message: ChatMessage = {
    id: generateId(),
    role,
    content,
    timestamp: new Date().toISOString(),
    type,
  };
  return {
    ...conversation,
    messages: [...conversation.messages, message],
  };
}

export function updateLastAssistantMessage(
  conversation: Conversation,
  content: string,
  type?: "log" | "result" | "error"
): Conversation {
  const messages = [...conversation.messages];
  const lastIdx = messages.length - 1;
  if (lastIdx >= 0 && messages[lastIdx].role === "assistant") {
    messages[lastIdx] = { ...messages[lastIdx], content, type };
  }
  return { ...conversation, messages };
}

export function updateConversationCrew(
  conversation: Conversation,
  crewName: string
): Conversation {
  return { 
    ...conversation, 
    crewName,
    title: `${crewName} — ${new Date(conversation.createdAt).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`
  };
}
