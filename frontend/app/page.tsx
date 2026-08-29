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
  updateConversationCrew
} from "@/lib/store";
import { listCrews, streamChat, getCrew } from "@/lib/api";
import type { Conversation, SSEChunk, CrewDetail } from "@/lib/types";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | undefined>();
  const [availableCrews, setAvailableCrews] = useState<string[]>([]);
  const [activeCrewDetail, setActiveCrewDetail] = useState<CrewDetail | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
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
  }, []);

  // Save on change
  useEffect(() => {
    if (isLoaded) {
      saveConversations(conversations);
    }
  }, [conversations, isLoaded]);

  const activeConversation = conversations.find(c => c.id === activeId);

  useEffect(() => {
    if (activeConversation) {
      getCrew(activeConversation.crewName).then(setActiveCrewDetail).catch(console.error);
    }
  }, [activeConversation?.crewName]);

  const handleNewConversation = () => {
    // For simplicity, just pick the first available crew if any
    const defaultCrew = availableCrews[0] || "default_crew.yaml";
    const newConv = createConversation(defaultCrew);
    setConversations([newConv, ...conversations]);
    setActiveId(newConv.id);
  };

  const handleSendMessage = async (message: string) => {
    if (!activeConversation) return;

    // 1. Add user message
    let updatedConv = addMessageToConversation(activeConversation, "user", message);
    
    // 2. Add empty assistant message placeholder
    updatedConv = addMessageToConversation(updatedConv, "assistant", "");
    
    setConversations(prev => prev.map(c => c.id === updatedConv.id ? updatedConv : c));
    setIsStreaming(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      await streamChat(
        activeConversation.crewName,
        { message, max_rpm: 15 },
        (chunk: SSEChunk) => {
          setConversations(prev => {
            const current = prev.find(c => c.id === updatedConv.id);
            if (!current) return prev;
            
            // Format log nicely
            let displayContent = chunk.content;
            if (chunk.type === "log") {
               displayContent = `_${chunk.content}_`;
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
      setIsStreaming(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setIsStreaming(false);
      setAbortController(null);
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
          <>
            <ChatWindow 
              messages={activeConversation.messages}
              isStreaming={isStreaming}
              crewName={activeConversation.crewName}
              availableCrews={availableCrews}
              onCrewChange={(newName) => {
                setConversations(prev => 
                  prev.map(c => c.id === activeConversation.id ? updateConversationCrew(c, newName) : c)
                );
              }}
              headerAction={activeCrewDetail ? <CrewConfig crewDetail={activeCrewDetail} onUpdate={setActiveCrewDetail} /> : undefined}
              onSendMessage={handleSendMessage}
              onStop={handleStop}
            />
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-text-secondary">
            Sélectionnez ou créez une conversation
          </div>
        )}
      </main>
    </div>
  );
}
