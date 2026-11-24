"use client";

import { useState, useMemo } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/lib/types";
import { ManageCrewsDialog } from "./ManageCrewsDialog";
import { transitionClasses } from "@/src/theme";
import {
  MessageSquare,
  Plus,
  Trash2,
  Sparkles,
  Library,
  Search,
  Clock,
  Calendar,
  CalendarDays,
  Zap,
  FileText,
  Code,
  Database,
  TrendingUp,
  Settings,
  Shield,
  Palette,
  Rocket,
  CheckCircle2,
  Play,
} from "lucide-react";

/**
 * Props for the NavigationSidebar component.
 */
interface NavigationSidebarProps {
  /** Array of all conversations to display in the sidebar */
  conversations: Conversation[];
  /** ID of the currently active/selected conversation */
  activeId?: string;
  /** Callback invoked when a conversation is selected by ID */
  onSelect: (id: string) => void;
  /** Callback invoked when the user clicks "New conversation" */
  onNew: () => void;
  /** List of available crew names loaded from YAML configs */
  availableCrews: string[];
  /** Callback to refresh the list of available crews */
  onRefreshCrews: () => void;
  /** Callback invoked when a conversation is deleted by ID */
  onDelete: (id: string) => void;
  /** Optional callback to launch a single crew by name */
  onLaunchCrew?: (crewName: string) => void;
  /** Currently selected crew names for multi-crew missions */
  selectedCrews?: string[];
  /** Optional callback when the selected crew list changes */
  onSelectedCrewsChange?: (crews: string[]) => void;
  /** Optional callback to launch a multi-crew mission with a specified mode */
  onLaunchMission?: (crews: string[], mode: "sequential" | "parallel") => void;
}

/**
 * The three navigation tabs available in the sidebar.
 */
type SidebarTab = "conversations" | "laboratory" | "library";

function getDateGroup(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffD = Math.floor((now.getTime() - date.getTime()) / 86400000);

  if (diffD === 0) return "Aujourd'hui";
  if (diffD === 1) return "Hier";
  if (diffD < 7) return "Cette semaine";
  if (diffD < 30) return "Ce mois-ci";
  return "Plus ancien";
}

/* ── Main Component ────────────────────────────────────────────────────── */

/**
 * Main sidebar component providing navigation across conversations,
 * the laboratory (quick actions), and the library (crew management).
 *
 * @param props - NavigationSidebarProps containing conversation data, callbacks, and crew state.
 * @returns A collapsible sidebar with tabbed navigation, conversation list, and crew launcher.
 *
 * @example
 * // Basic usage with all required props
 * <Sidebar
 *   conversations={conversations}
 *   activeId={activeConversationId}
 *   onSelect={setActiveConversation}
 *   onNew={handleNewConversation}
 *   availableCrews={crewList}
 *   onRefreshCrews={refreshCrews}
 *   onDelete={handleDeleteConversation}
 * />
 */
export function NavigationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  availableCrews,
  onRefreshCrews,
  onDelete,
  onLaunchCrew,
  selectedCrews = [],
  onSelectedCrewsChange,
  onLaunchMission,
}: NavigationSidebarProps) {
  const [activeTab, setActiveTab] = useState<SidebarTab>("conversations");

  const tabs = [
    { key: "conversations" as const, label: "Conversations", icon: MessageSquare },
    { key: "laboratory" as const, label: "Laboratoire", icon: Sparkles },
    { key: "library" as const, label: "Bibliothèque", icon: Library },
  ];

  return (
    <div className={cn(
      "w-64 h-full bg-bg-secondary border-r border-border flex flex-col shrink-0",
      transitionClasses.base
    )}>
      {/* Top: New Conversation */}
      <div className="p-3">
        <Button
          onClick={onNew}
          variant="agent-primary"
          className={cn(
            "w-full justify-start gap-2 h-9 rounded-lg text-sm font-medium shadow-sm",
            "gradient-accent text-white hover:opacity-90 transition-opacity"
          )}
        >
          <Plus size={15} />
          Nouvelle conversation
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="px-3 pb-2">
        <div className="flex gap-1 bg-bg-tertiary/50 p-0.5 rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-[10px] font-medium transition-all",
                activeTab === tab.key
                  ? "bg-bg-primary text-text-primary shadow-sm"
                  : "text-text-tertiary hover:text-text-primary"
              )}
            >
              <tab.icon size={12} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {activeTab === "conversations" && (
          <ConversationList
            conversations={conversations}
            activeId={activeId}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        )}
        {activeTab === "laboratory" && (
          <LaboratoryTab onLaunch={onLaunchCrew} />
        )}
        {activeTab === "library" && (
          <LibraryTab
            availableCrews={availableCrews}
            onRefresh={onRefreshCrews}
            selectedCrews={selectedCrews}
            onSelectedCrewsChange={onSelectedCrewsChange}
            onLaunchMission={onLaunchMission}
          />
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-border mt-auto">
        <div className="mb-3">
          <ManageCrewsDialog
            availableCrews={availableCrews}
            onRefreshCrews={onRefreshCrews}
          />
        </div>
        <div className="flex items-center justify-center gap-1.5 text-[10px] text-text-tertiary font-medium tracking-wide">
          <Zap className="h-3 w-3 text-accent" />
          <span>Agent Test v2.0</span>
        </div>
      </div>
    </div>
  );
}

/* ── Laboratory Tab ────────────────────────────────────────────────────── */

/**
 * Laboratory tab component displaying quick-action buttons for common crew tasks.
 * Each button launches a predefined crew without creating a new conversation.
 *
 * @param props - Component props.
 * @param props.onLaunch - Optional callback to launch a crew by name.
 * @returns A scrollable list of quick-action cards for common automation tasks.
 */
function LaboratoryTab({ onLaunch }: { onLaunch?: (crewName: string) => void }) {
  const quickActions = [
    { icon: Code, label: "Analyse de code", desc: "Audit et suggestions", color: "text-blue-500", crew: "Reviewer" },
    { icon: Database, label: "Requête données", desc: "SQL & transformations", color: "text-emerald-500", crew: "Json_Analyzer" },
    { icon: TrendingUp, label: "Rapport analytique", desc: "Stats & visualisations", color: "text-purple-500", crew: "StateOfTheArtCrew" },
    { icon: Settings, label: "Configuration", desc: "Paramètres système", color: "text-orange-500", crew: "Project_Architect" },
    { icon: Shield, label: "Audit sécurité", desc: "Vulnérabilités & fixes", color: "text-red-500", crew: "Security_Adversary" },
    { icon: Palette, label: "Design review", desc: "UI/UX & accessibilité", color: "text-pink-500", crew: "Refactorer" },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="h-4 w-4 text-accent" />
          <h3 className="text-xs font-semibold text-text-primary">Actions rapides</h3>
        </div>
        <p className="text-[10px] text-text-tertiary">Lancez une automatisation sans créer de conversation</p>
      </div>

      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1.5 pb-4">
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => onLaunch?.(action.crew)}
              className={cn(
                "w-full text-left p-2.5 rounded-lg border border-transparent transition-all duration-150 group/action",
                "hover:bg-bg-tertiary/60 hover:border-border/60"
              )}
            >
              <div className="flex items-center gap-2.5">
                <div className={cn("h-8 w-8 rounded-lg bg-bg-tertiary border border-border/60 flex items-center justify-center shrink-0 group-hover/action:scale-105 transition-transform duration-200")}>
                  <action.icon className={cn("h-4 w-4", action.color)} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-text-primary truncate">{action.label}</div>
                  <div className="text-[10px] text-text-tertiary">{action.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

/* ── Library Tab ───────────────────────────────────────────────────────── */

/**
 * Library tab component for browsing, selecting, and launching crews.
 * Supports single-crew selection and multi-crew mission launching
 * in either sequential or parallel execution mode.
 *
 * @param props - Component props.
 * @param props.availableCrews - List of all crew names available from YAML configs.
 * @param props.onRefresh - Callback to refresh the crew list.
 * @param props.selectedCrews - Array of currently selected crew names for missions.
 * @param props.onSelectedCrewsChange - Optional callback when the selection changes.
 * @param props.onLaunchMission - Optional callback to launch a multi-crew mission.
 * @returns A scrollable crew list with selection checkboxes and a mission launch bar.
 */
function LibraryTab({
  availableCrews,
  onRefresh,
  selectedCrews,
  onSelectedCrewsChange,
  onLaunchMission,
}: {
  availableCrews: string[];
  onRefresh: () => void;
  selectedCrews: string[];
  onSelectedCrewsChange?: (crews: string[]) => void;
  onLaunchMission?: (crews: string[], mode: "sequential" | "parallel") => void;
}) {
  const toggleCrew = (crew: string) => {
    const next = selectedCrews.includes(crew)
      ? selectedCrews.filter((c) => c !== crew)
      : [...selectedCrews, crew];
    onSelectedCrewsChange?.(next);
  };

  return (
    <div className="flex flex-col min-h-0">
      <div className="px-4 py-3 shrink-0">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Library className="h-4 w-4 text-accent" />
            <h3 className="text-xs font-semibold text-text-primary">Bibliothèque</h3>
          </div>
          <button
            onClick={onRefresh}
            className="text-[10px] text-text-tertiary hover:text-text-primary transition-colors"
            title="Rafraîchir"
          >
            <Clock className="h-3 w-3" />
          </button>
        </div>
        <p className="text-[10px] text-text-tertiary">{availableCrews.length} crew{availableCrews.length !== 1 ? '(s)' : ''} disponible{availableCrews.length !== 1 ? 's' : ''}</p>
      </div>

      <ScrollArea className="flex-1 min-h-0 px-2">
        <div className="space-y-1.5 pb-4">
          {availableCrews.length === 0 ? (
            <div className="px-3 py-6 text-center">
              <Library className="h-8 w-8 text-text-tertiary/40 mx-auto mb-2" />
              <p className="text-xs text-text-tertiary">Aucun crew disponible</p>
            </div>
          ) : (
            availableCrews.map((crew) => {
              const isSelected = selectedCrews.includes(crew);
              return (
                <button
                  key={crew}
                  type="button"
                  onClick={() => toggleCrew(crew)}
                  className={cn(
                    "w-full text-left p-2.5 rounded-lg border transition-all duration-150 group/crew",
                    isSelected
                      ? "bg-accent/10 border-accent/30"
                      : "border-transparent hover:bg-bg-tertiary/60 hover:border-border/60"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <div className={cn(
                      "h-8 w-8 rounded-lg border flex items-center justify-center shrink-0 transition-all duration-200",
                      isSelected
                        ? "bg-accent border-accent/40"
                        : "bg-bg-tertiary border-border/60 group-hover/crew:scale-105"
                    )}>
                      {isSelected ? (
                        <CheckCircle2 className="h-4 w-4 text-accent" />
                      ) : (
                        <Zap className={cn("h-4 w-4", isSelected ? "text-accent" : "text-text-tertiary")} />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className={cn(
                        "text-xs font-medium truncate",
                        isSelected ? "text-text-primary" : "text-text-primary"
                      )}>{crew}</div>
                      <div className="text-[10px] text-text-tertiary flex items-center gap-1">
                        <FileText className="h-2.5 w-2.5" />
                        <span>CrewAI</span>
                      </div>
                    </div>
                    {isSelected && (
                      <div className="h-1.5 w-1.5 rounded-full bg-accent shrink-0" />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </ScrollArea>

      {/* Mission Launch Bar */}
      {selectedCrews.length > 0 && (
        <div className="p-3 border-t border-border shrink-0">
          <div className="flex items-center gap-1.5 mb-2">
            <Rocket className="h-3.5 w-3.5 text-accent" />
            <span className="text-[10px] font-semibold text-text-primary uppercase tracking-wider">
              Mission — {selectedCrews.length} crew{selectedCrews.length > 1 ? 's' : ''} sélectionné{selectedCrews.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => onLaunchMission?.(selectedCrews, "sequential")}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 h-8 rounded-lg text-[10px] font-medium transition-all",
                "bg-accent text-white hover:opacity-90 shadow-sm"
              )}
            >
              <Play className="h-3 w-3" />
              Séquentiel
            </button>
            <button
              type="button"
              onClick={() => onLaunchMission?.(selectedCrews, "parallel")}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 h-8 rounded-lg text-[10px] font-medium transition-all",
                "bg-bg-tertiary text-text-primary border border-border hover:bg-bg-primary transition-all"
              )}
            >
              <Zap className="h-3 w-3" />
              Parallèle
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Conversation List with Search & Date Groups ───────────────────────── */

/**
 * Conversation list component with real-time search filtering and
 * automatic date-based grouping (Today, Yesterday, This week, etc.).
 *
 * @param props - Component props.
 * @param props.conversations - Full list of conversations to display and filter.
 * @param props.activeId - ID of the currently active conversation for highlighting.
 * @param props.onSelect - Callback invoked when a conversation is clicked.
 * @param props.onDelete - Callback invoked when the delete button is clicked.
 * @returns A scrollable, searchable conversation list grouped by date sections.
 */
function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
}: {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = useMemo(() =>
    conversations.filter((c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.crewName.toLowerCase().includes(searchQuery.toLowerCase())
    ), [conversations, searchQuery]);

  // Group by date
  const grouped = useMemo(() => {
    const groups: Record<string, Conversation[]> = {};
    const order: string[] = [];
    filtered.forEach((c) => {
      const group = getDateGroup(c.createdAt);
      if (!groups[group]) {
        groups[group] = [];
        order.push(group);
      }
      groups[group].push(c);
    });
    return { groups, order };
  }, [filtered]);

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-4 py-8 text-center">
        <MessageSquare className="h-10 w-10 text-text-tertiary/30 mx-auto mb-3" />
        <p className="text-xs text-text-tertiary font-medium">Aucune conversation</p>
        <p className="text-[10px] text-text-tertiary/60 mt-1">Créez-en une pour commencer</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="px-2 py-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary pointer-events-none" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={cn(
              "w-full h-7 pl-7 pr-2 text-[11px] bg-bg-tertiary/50 border border-border/40 rounded-md",
              "placeholder:text-text-tertiary/60",
              "focus:outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent/30",
              "transition-all duration-150"
            )}
          />
        </div>
      </div>

      {/* List */}
      <ScrollArea className="flex-1 px-2">
        <div className="pb-4 space-y-3">
          {filtered.length === 0 ? (
            <div className="px-3 py-8 text-center">
              <Search className="h-6 w-6 text-text-tertiary/40 mx-auto mb-2" />
              <p className="text-xs text-text-tertiary">Aucun résultat</p>
            </div>
          ) : (
            grouped.order.map((groupLabel) => (
              <div key={groupLabel}>
                {/* Section Label */}
                <div className="px-3 py-1.5 flex items-center gap-1.5">
                  {groupLabel === "Aujourd'hui" && <Calendar className="h-2.5 w-2.5 text-text-tertiary" />}
                  {groupLabel === "Hier" && <Calendar className="h-2.5 w-2.5 text-text-tertiary" />}
                  {groupLabel === "Cette semaine" && <CalendarDays className="h-2.5 w-2.5 text-text-tertiary" />}
                  {groupLabel === "Ce mois-ci" && <Clock className="h-2.5 w-2.5 text-text-tertiary" />}
                  <span className="text-[9px] font-semibold text-text-tertiary uppercase tracking-widest">
                    {groupLabel}
                  </span>
                </div>

                {/* Items */}
                <div className="space-y-0.5">
                  {grouped.groups[groupLabel].map((conv) => (
                    <ConversationItem
                      key={conv.id}
                      conversation={conv}
                      isActive={activeId === conv.id}
                      onSelect={() => onSelect(conv.id)}
                      onDelete={() => onDelete(conv.id)}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

/* ── Single Conversation Item ──────────────────────────────────────────── */

/**
 * Single conversation row rendered within the ConversationList.
 * Displays the conversation title with an icon, highlights the active item,
 * and shows a delete button on hover.
 *
 * @param props - Component props.
 * @param props.conversation - The conversation object to render.
 * @param props.isActive - Whether this conversation is currently selected.
 * @param props.onSelect - Callback invoked when the row is clicked.
 * @param props.onDelete - Callback invoked when the delete button is clicked.
 * @returns A clickable row with conversation title, icon, and hover delete action.
 */
function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={cn(
        "group/item flex items-center w-full px-2.5 py-2 rounded-lg transition-all duration-150",
        isActive
          ? "bg-bg-tertiary text-text-primary shadow-sm border border-border/40"
          : "text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary border border-transparent"
      )}
    >
      <button
        onClick={onSelect}
        className="flex-1 text-left text-xs truncate flex items-center gap-2 overflow-hidden"
      >
        <MessageSquare size={13} className={cn(
          "shrink-0 transition-colors duration-150",
          isActive ? "text-accent" : "opacity-50 group-hover/item:opacity-80"
        )} />
        <span className="truncate font-medium">{conversation.title || "Sans titre"}</span>
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className={cn(
          "opacity-0 group-hover/item:opacity-100 p-1 text-text-tertiary hover:text-red-500 hover:bg-bg-primary rounded transition-all duration-150 shrink-0 ml-0.5",
          "focus:opacity-100"
        )}
        title="Supprimer la conversation"
      >
        <Trash2 size={11} />
      </button>
    </div>
  );
}
