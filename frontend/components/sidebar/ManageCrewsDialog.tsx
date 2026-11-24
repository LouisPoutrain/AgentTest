"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings, PlusCircle, Trash2, Zap } from "lucide-react";
import { createCrew, deleteCrew } from "@/lib/api";
import { toast } from "sonner";

/**
 * Props for the ManageCrewsDialog component.
 */
interface ManageCrewsDialogProps {
  /** List of available crew names loaded from the backend configuration. */
  availableCrews: string[];
  /** Callback invoked after a crew is created or deleted to refresh the list. */
  onRefreshCrews: () => void;
}

/**
 * A dialog that lets users manage CrewAI crew configurations:
 * list existing crews, create new ones with process/memory/RPM settings,
 * and delete crews that are no longer needed.
 *
 * @example
 * // Basic usage inside a sidebar or page component:
 * <ManageCrewsDialog
 *   availableCrews={crewList}
 *   onRefreshCrews={fetchCrews}
 * />
 */
export function ManageCrewsDialog({ availableCrews, onRefreshCrews }: ManageCrewsDialogProps) {
  const [open, setOpen] = useState(false);

  // Create crew form
  const [crewName, setCrewName] = useState("");
  const [crewProcess, setCrewProcess] = useState("Séquentiel");
  const [crewMemory, setCrewMemory] = useState(true);
  const [crewMaxRpm, setCrewMaxRpm] = useState(15);

  const handleCreateCrew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!crewName) return;
    try {
      await createCrew(crewName, {
        process: crewProcess,
        memory: crewMemory,
        max_rpm: crewMaxRpm,
      });
      setCrewName("");
      onRefreshCrews();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur inconnue";
      toast.error("Erreur", { description: message });
    }
  };

  const handleDeleteCrew = async (name: string) => {
    if (!confirm(`Supprimer définitivement le Crew "${name}" et toute sa configuration ?`)) return;
    try {
      await deleteCrew(name);
      onRefreshCrews();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur inconnue";
      toast.error("Erreur", { description: message });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={<Button variant="outline" size="sm" className="w-full justify-start gap-2 bg-transparent border-border/60 hover:bg-bg-tertiary text-xs" />}
      >
        <Settings size={14} /> Gérer les Crews
      </DialogTrigger>
      <DialogContent className="max-w-lg bg-bg-primary border-border text-text-primary">
        <DialogHeader>
          <DialogTitle className="text-base">Gestion des Crews</DialogTitle>
        </DialogHeader>

        {/* Existing Crews */}
        <div className="space-y-2 mt-2">
          <Label className="text-[10px] text-text-tertiary uppercase tracking-widest">Crews existants</Label>
          {availableCrews.length === 0 ? (
            <div className="text-xs text-text-tertiary text-center py-4">Aucun crew configuré</div>
          ) : (
            <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
              {availableCrews.map(name => (
                <div key={name} className="group flex items-center justify-between bg-bg-secondary/60 p-2.5 rounded-lg border border-border/60">
                  <div className="flex items-center gap-2 text-xs">
                    <Zap className="h-3 w-3 text-accent fill-current" />
                    <span className="font-medium">{name}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteCrew(name)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-text-tertiary hover:text-red-500 hover:bg-bg-tertiary rounded transition-all"
                    title="Supprimer"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create new crew */}
        <div className="border-t border-border/60 pt-4 mt-4">
          <Label className="text-[10px] text-text-tertiary uppercase tracking-widest">Créer un nouveau crew</Label>
          <form onSubmit={handleCreateCrew} className="space-y-3 mt-2">
            <Input
              value={crewName}
              onChange={e => setCrewName(e.target.value)}
              placeholder="Nom du crew (ex: equipe_dev)"
              className="bg-bg-secondary/60 border-border/60 text-xs"
              required
            />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Processus</Label>
                <Select value={crewProcess} onValueChange={(val) => val && setCrewProcess(val)}>
                  <SelectTrigger className="h-8 text-sm bg-bg-secondary/60 border-border/60"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Séquentiel">Séquentiel</SelectItem>
                    <SelectItem value="Hiérarchique">Hiérarchique</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Limite RPM</Label>
                <Input type="number" value={crewMaxRpm} onChange={e => setCrewMaxRpm(parseInt(e.target.value))} min={1} max={100} className="h-8 text-sm bg-bg-secondary/60 border-border/60" />
              </div>
            </div>

            <label className="flex items-center gap-2 text-xs">
              <Switch checked={crewMemory} onCheckedChange={setCrewMemory} /> Mémoire activée (local)
            </label>

            <Button type="submit" className="w-full bg-accent hover:bg-accent-hover text-white text-sm">
              <PlusCircle size={14} className="mr-1.5" /> Créer le Crew
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
