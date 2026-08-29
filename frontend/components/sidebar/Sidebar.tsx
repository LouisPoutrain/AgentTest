"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { MessageSquare, Plus, FolderKanban, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/lib/types";
import { ManageCrewsDialog } from "./ManageCrewsDialog";

interface SidebarProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  availableCrews: string[];
  onRefreshCrews: () => void;
  onDelete: (id: string) => void;
}

export function Sidebar({ conversations, activeId, onSelect, onNew, availableCrews, onRefreshCrews, onDelete }: SidebarProps) {
  return (
    <div className="w-64 h-full bg-bg-secondary border-r border-border flex flex-col shrink-0">
      <div className="p-4">
        <Button 
          onClick={onNew}
          className="w-full justify-start gap-2 bg-transparent border border-border hover:bg-bg-tertiary text-text-primary"
        >
          <Plus size={16} />
          Nouvelle conversation
        </Button>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="px-4 py-2 text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Conversations
        </div>
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1 pb-4">
            {conversations.length === 0 ? (
              <div className="px-2 py-4 text-sm text-text-secondary text-center">
                Aucun historique
              </div>
            ) : (
              conversations.map((conv) => (
                <div 
                  key={conv.id} 
                  className={cn(
                    "group flex items-center w-full px-2 py-1.5 rounded-md transition-colors",
                    activeId === conv.id
                      ? "bg-bg-tertiary text-text-primary"
                      : "text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary"
                  )}
                >
                  <button
                    onClick={() => onSelect(conv.id)}
                    className="flex-1 text-left text-sm truncate flex items-center gap-2 overflow-hidden"
                  >
                    <MessageSquare size={14} className="shrink-0" />
                    <span className="truncate">{conv.title}</span>
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }} 
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-text-secondary hover:text-red-500 hover:bg-bg-primary rounded transition-all shrink-0 ml-1"
                    title="Supprimer la conversation"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Footer / Quick info */}
      <div className="p-4 border-t border-border mt-auto">
        <div className="mb-4">
          <ManageCrewsDialog availableCrews={availableCrews} onRefreshCrews={onRefreshCrews} />
        </div>
        <div className="text-xs text-text-secondary/50">
          AgentTest v2.0
        </div>
      </div>
    </div>
  );
}
