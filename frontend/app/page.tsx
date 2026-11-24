"use client";

import { useEffect, useState } from "react";
import { NavigationSidebar } from "@/components/sidebar/NavigationSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { CrewConfig } from "@/components/sidebar/CrewConfig";
import {
  loadConversations,
  saveConversations,
  createConversation,
  addMessageToConversation,
  updateLastAssistantMessage,
  updateConversationCrew,
  updateConversationFolder
} from "@/lib/store";
import { listCrews, streamChat, getCrew, listModels } from "@/lib/api";
import type { Conversation, SSEChunk, CrewDetail } from "@/lib/types";
import { useLotStore } from "@/src/stores/useLotStore";

/**
 * Internal state for an active streaming session.
 *
 * Tracks whether a stream is in progress and holds the ``AbortController``
 * so the user can cancel it via the stop button.
 */
interface StreamingEntry {
  isStreaming: boolean;
  controller: AbortController;
}

/**
 * Home page — the main chat application.
 *
 * Manages the full conversation lifecycle:
 * 1. Loads persisted conversations from ``localStorage`` on mount.
 * 2. Lists available crews and LLM models from the backend.
 * 3. Streams SSE chunks from ``/api/chat`` and merges them into
 *    conversation messages (streaming log chunks are merged into a
 *    single assistant message to avoid UI flicker).
 * 4. Persists conversations back to ``localStorage`` on every change.
 *
 * @example
 * // The page is the root layout for the chat application.
 * // It composes the sidebar, chat window, and crew configuration.
 * export default function Home() { ... }
 */
export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | undefined>();
  const [availableCrews, setAvailableCrews] = useState<string[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [activeCrewDetail, setActiveCrewDetail] = useState<CrewDetail | null>(null);
  const [streamingState, setStreamingState] = useState<Record<string, StreamingEntry>>({});
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCrews, setSelectedCrews] = useState<string[]>([]);

  // Load initial data
  useEffect(() => {
    const loaded = loadConversations();
    setConversations(loaded);
    if (loaded.length > 0) {
      setActiveId(loaded[0].id);
    }
    setIsLoaded(true);
    
    listCrews().then(setAvailableCrews).catch((err) => {
      console.error("Failed to load crews:", err);
      setError("Impossible de charger la liste des Crews.");
    });
    listModels().then(setAvailableModels).catch((err) => {
      console.error("Failed to load models:", err);
    });
  }, []);

  // Save on change
  useEffect(() => {
    if (isLoaded) {
      saveConversations(conversations);
    }
  }, [conversations, isLoaded]);

  const activeConversation = conversations.find(c => c.id === activeId);

  useEffect(() => {
    if (activeConversation?.crewName && activeConversation.crewName !== "default") {
      getCrew(activeConversation.crewName).then(setActiveCrewDetail).catch(console.error);
    } else {
      setActiveCrewDetail(null);
    }
  }, [activeConversation?.crewName]);

  const handleNewConversation = () => {
    const defaultCrew = "default";
    const newConv = createConversation(defaultCrew);
    setConversations([newConv, ...conversations]);
    setActiveId(newConv.id);
  };

  const handleLaunchCrew = async ({
    message,
    inputs,
    options,
  }: {
    message: string;
    inputs: Record<string, unknown>;
    options?: { llm_override?: string; max_rpm?: number };
  }) => {
    if (!activeConversation) return;

    // 1. Add user message
    let updatedConv = addMessageToConversation(activeConversation, "user", message);
    
    // 2. Add empty assistant message placeholder
    updatedConv = addMessageToConversation(updatedConv, "assistant", "");
    
    setConversations(prev => prev.map(c => c.id === updatedConv.id ? updatedConv : c));
    
    const convId = updatedConv.id;
    const controller = new AbortController();
    
    setStreamingState(prev => ({
      ...prev,
      [convId]: { isStreaming: true, controller }
    }));

    try {
      await streamChat(
        activeConversation.crewName,
        {
          message,
          inputs,
          max_rpm: options?.max_rpm ?? 15,
          llm_override: options?.llm_override || null,
          session_id: convId,
          crew_names: activeConversation.crewNames,
          execution_mode: activeConversation.executionMode,
        },
        (chunk: SSEChunk) => {
          // Update lot store for step events (crew execution progress)
          // Backend sends {"type": "step", "status": "running", "log": "..."}
          const stepStatus = chunk.stepStatus || chunk.status;
          if (stepStatus) {
            const stepKey = chunk.crewName ? `${chunk.crewName}/${chunk.stepKey || "unknown"}` : (chunk.stepKey || "unknown");
            useLotStore.getState().setStep(convId, stepKey, {
              status: stepStatus as "pending" | "running" | "completed" | "error",
              tokens: chunk.tokens,
              cost: chunk.cost,
            });
          }

          // Skip non-message chunks (step, metrics, session_info)
          if (!["log", "result", "error"].includes(chunk.type)) return;

          setConversations(prev => {
            const current = prev.find(c => c.id === updatedConv.id);
            if (!current) return prev;

            let displayContent = chunk.content;
            if (chunk.type === "error") {
               displayContent = `**Erreur:** ${chunk.content}`;
            }

            const lastMsg = current.messages[current.messages.length - 1];
            let updated;

            // If the last message is an empty placeholder, update it.
            // If it's already filled with a previous log/result, add a new message.
            if (lastMsg && lastMsg.role === "assistant" && lastMsg.content === "") {
              updated = updateLastAssistantMessage(current, displayContent, chunk.type as "log" | "result" | "error");
            } else {
              updated = addMessageToConversation(current, "assistant", displayContent, chunk.type as "log" | "result" | "error");
            }

            return prev.map(c => c.id === updated.id ? updated : c);
          });
        },
        controller.signal
      );
    } catch (err: unknown) {
      const isAbort = err instanceof DOMException && err.name === "AbortError";
      if (!isAbort) {
        setConversations(prev => {
          const current = prev.find(c => c.id === updatedConv.id);
          if (!current) return prev;
          const msg = err instanceof Error ? err.message : String(err);
          const updated = updateLastAssistantMessage(current, `**Erreur:** ${msg}`, "error");
          return prev.map(c => c.id === updated.id ? updated : c);
        });
      }
    } finally {
      setStreamingState(prev => {
        const next = { ...prev };
        delete next[convId];
        return next;
      });
    }
  };

  const handleSendMessage = (message: string) => {
    handleLaunchCrew({
      message,
      inputs: { 
        message, 
        project_path: activeConversation?.folderContext || "." 
      },
    });
  };

  const handleStop = () => {
    if (!activeId) return;
    const state = streamingState[activeId];
    if (state?.controller) {
      state.controller.abort();
      setStreamingState(prev => {
        const next = { ...prev };
        delete next[activeId];
        return next;
      });
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeId === id) {
      setActiveId(undefined);
    }
  };

  const handleLaunchCrewFromSidebar = (crewName: string) => {
    const newConv = createConversation(crewName);
    setConversations([newConv, ...conversations]);
    setActiveId(newConv.id);
  };

  const handleLaunchMission = (crewNames: string[], mode: "sequential" | "parallel") => {
    const newConv = createConversation("default", { crewNames, executionMode: mode });
    setConversations([newConv, ...conversations]);
    setActiveId(newConv.id);
    setSelectedCrews([]);
  };

  return (
    <div className="flex h-screen w-full bg-bg-primary text-text-primary overflow-hidden font-sans">
      <NavigationSidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNewConversation}
        availableCrews={availableCrews}
        onRefreshCrews={() => {
          listCrews().then(setAvailableCrews).catch(console.error);
        }}
        onDelete={handleDeleteConversation}
        onLaunchCrew={handleLaunchCrewFromSidebar}
        selectedCrews={selectedCrews}
        onSelectedCrewsChange={setSelectedCrews}
        onLaunchMission={handleLaunchMission}
      />
      <main className="flex-1 min-w-0 h-full flex flex-col relative">
        {activeConversation ? (
          <ChatWindow
            messages={activeConversation.messages}
            activeId={activeConversation.id}
            isStreaming={!!streamingState[activeConversation.id]?.isStreaming}
            crewName={activeConversation.crewName}
            crewDetail={activeCrewDetail}
            crewNames={activeConversation.crewNames}
            executionMode={activeConversation.executionMode}
            availableCrews={availableCrews}
            availableModels={availableModels}
            onCrewChange={(newName) => {
              setConversations(prev => 
                prev.map(c => c.id === activeConversation.id ? updateConversationCrew(c, newName) : c)
              );
            }}
            headerAction={activeCrewDetail ? <CrewConfig crewDetail={activeCrewDetail} onUpdate={setActiveCrewDetail} /> : undefined}
            folderContext={activeConversation.folderContext}
            onFolderChange={(folder) => {
              setConversations(prev => 
                prev.map(c => c.id === activeConversation.id ? updateConversationFolder(c, folder) : c)
              );
            }}
            onSendMessage={handleSendMessage}
            onLaunchCrew={handleLaunchCrew}
            onStop={handleStop}
            onResetLaunchPad={handleNewConversation}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-text-secondary">
            {error ? (
              <div className="text-center">
                <p className="text-red-400 mb-2">{error}</p>
                <button
                  type="button"
                  onClick={() => {
                    listCrews().then(setAvailableCrews).catch(console.error);
                    setError(null);
                  }}
                  className="text-accent hover:underline text-sm"
                >
                  Réessayer
                </button>
              </div>
            ) : (
              <p>Sélectionnez ou créez une conversation</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
