"use client";

import type { ChatMessage, Conversation } from "./types";

const STORAGE_KEY = "agenttest_conversations";

/* ── Helpers ── */

/**
 * Generates a short unique identifier using timestamp + random bytes.
 *
 * @returns A 10-character alphanumeric string (e.g. ``"1ab2cd3e4f"``).
 */
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/* ── LocalStorage persistence ── */

/**
 * Loads all conversations from ``localStorage``.
 *
 * Returns an empty array on parse errors or when running server-side.
 *
 * @returns Array of ``Conversation`` objects, or ``[]``.
 */
export function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/**
 * Persists the full conversation list to ``localStorage``.
 *
 * No-op when running server-side (``window`` undefined).
 *
 * @param conversations - The full array of conversations to serialize.
 */
export function saveConversations(conversations: Conversation[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

/* ── Conversation management ──
 *
 * All functions in this section follow an immutable update pattern:
 * they return a new ``Conversation`` object with spread copies,
 * never mutating the input. This is compatible with React's
 * strict rendering model and Zustand's immutable state updates.
 */

/**
 * Creates a new conversation with an empty message list.
 *
 * For multi-crew launches, the title includes the crew count.
 *
 * @param crewName - Primary crew name (shown in title).
 * @param options - Optional multi-crew configuration.
 * @returns A new ``Conversation`` object.
 */
export function createConversation(
  crewName: string,
  options?: { crewNames?: string[]; executionMode?: "sequential" | "parallel" }
): Conversation {
  return {
    id: generateId(),
    crewName,
    crewNames: options?.crewNames,
    executionMode: options?.executionMode,
    messages: [],
    createdAt: new Date().toISOString(),
    title: options?.crewNames
      ? `${options.crewNames.length} crew(s) — ${new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`
      : `${crewName} — ${new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`,
  };
}

/**
 * Appends a new message to a conversation (immutable).
 *
 * @param conversation - The conversation to update.
 * @param role - ``"user"`` or ``"assistant"``.
 * @param content - Message text.
 * @param type - Optional SSE chunk type (``"log" | "result" | "error"``).
 * @returns A new ``Conversation`` with the appended message.
 */
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

/**
 * Updates the last assistant message in a conversation (immutable).
 *
 * If the last message is not from the assistant, the conversation is
 * returned unchanged. This is used to merge streaming log chunks into
 * a single assistant message instead of creating many small messages.
 *
 * @param conversation - The conversation to update.
 * @param content - New content for the last assistant message.
 * @param type - Optional SSE chunk type.
 * @returns A new ``Conversation`` with the updated last message, or the
 *          original if the last message is not from the assistant.
 */
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

/**
 * Updates the crew name and title of a conversation (immutable).
 *
 * Used when a conversation is created without a crew and later assigned one.
 *
 * @param conversation - The conversation to update.
 * @param crewName - New crew name.
 * @returns A new ``Conversation`` with updated crew and title.
 */
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

/**
 * Updates the folder context of a conversation (immutable).
 *
 * The folder context determines which workspace directory is used as
 * the default for file operations and crew inputs.
 *
 * @param conversation - The conversation to update.
 * @param folderContext - Absolute or relative folder path.
 * @returns A new ``Conversation`` with the updated folder context.
 */
export function updateConversationFolder(
  conversation: Conversation,
  folderContext: string
): Conversation {
  return {
    ...conversation,
    folderContext
  };
}
