"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
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

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | undefined>();
  const [availableCrews, setAvailableCrews] = useState<string[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [activeCrewDetail, setActiveCrewDetail] = useState<CrewDetail | null>(null);
  const [streamingState, setStreamingState] = useState<Record<string, { isStreaming: boolean; controller: AbortController }>>({});
  const [isLoaded, setIsLoaded] = useState(false);

  // Load initial data
  useEffect(() => {
    const loaded = loadConversations();
    setConversations(loaded);
    if (loaded.length > 0) {
      setActiveId(loaded[0].id);
    }
    setIsLoaded(true);
    
    listCrews().then(setAvailableCrews).catch(console.error);
    listModels().then(setAvailableModels).catch(console.error);
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
    inputs: Record<string, any>;
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
          max_rpm: options?.max_rpm || 15,
          llm_override: options?.llm_override || null,
          session_id: convId,
        },
        (chunk: SSEChunk) => {
          // Update lot store if it's a step
          if (chunk.type === "log" && chunk.stepStatus) {
            useLotStore.getState().setStep(convId, chunk.stepKey || "unknown", {
              status: chunk.stepStatus as any,
              tokens: chunk.tokens,
              cost: chunk.cost,
            });
          }

          setConversations(prev => {
            const current = prev.find(c => c.id === updatedConv.id);
            if (!current) return prev;
            
            // Format log nicely
            let displayContent = chunk.content;
            if (chunk.type === "log") {
               displayContent = `_⚙️ Orchestration en cours... Consultez le **[Tableau des Lots](/lots)** pour suivre la réflexion des agents en temps réel._`;
            } else if (chunk.type === "error") {
               displayContent = `**Erreur:** ${chunk.content}`;
            }
            
            const updated = updateLastAssistantMessage(current, displayContent, chunk.type);
            return prev.map(c => c.id === updated.id ? updated : c);
          });
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setConversations(prev => {
          const current = prev.find(c => c.id === updatedConv.id);
          if (!current) return prev;
          const updated = updateLastAssistantMessage(current, `**Erreur:** ${err.message}`, "error");
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

  return (
    <div className="flex h-screen w-full bg-bg-primary text-text-primary overflow-hidden font-sans">
      <Sidebar 
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNewConversation}
        availableCrews={availableCrews}
        onRefreshCrews={() => {
          listCrews().then(setAvailableCrews).catch(console.error);
        }}
        onDelete={handleDeleteConversation}
      />
      <main className="flex-1 min-w-0 h-full flex flex-col relative">
        {activeConversation ? (
          <ChatWindow 
            messages={activeConversation.messages}
            activeId={activeConversation.id}
            isStreaming={!!streamingState[activeConversation.id]?.isStreaming}
            crewName={activeConversation.crewName}
            crewDetail={activeCrewDetail}
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
            Sélectionnez ou créez une conversation
          </div>
        )}
      </main>
    </div>
  );
}
