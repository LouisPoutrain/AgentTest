"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings, PlusCircle, Trash2 } from "lucide-react";
import { createCrew, deleteCrew, getCrew } from "@/lib/api";
import type { CrewDetail } from "@/lib/types";

interface ManageCrewsDialogProps {
  availableCrews: string[];
  onRefreshCrews: () => void;
}

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
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  const handleDeleteCrew = async (name: string) => {
    if (!confirm(`Supprimer définitivement le Crew "${name}" et toute sa configuration ?`)) return;
    try {
      await deleteCrew(name);
      onRefreshCrews();
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={<Button variant="outline" size="sm" className="w-full justify-start gap-2 bg-transparent border-border hover:bg-bg-tertiary" />}
      >
        <Settings size={16} /> Gérer les Crews
      </DialogTrigger>
      <DialogContent className="max-w-lg bg-bg-secondary border-border text-text-primary">
        <DialogHeader>
          <DialogTitle>Gestion des Crews</DialogTitle>
        </DialogHeader>

        {/* Existing Crews */}
        <div className="space-y-2 mt-2">
          <Label className="text-xs text-text-secondary uppercase tracking-wider">Crews existants</Label>
          {availableCrews.length === 0 ? (
            <div className="text-sm text-text-secondary text-center py-4">Aucun crew configuré</div>
          ) : (
            <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
              {availableCrews.map(name => (
                <div key={name} className="group flex items-center justify-between bg-bg-tertiary p-3 rounded-lg border border-border">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-accent">⚡</span>
                    <span className="font-medium">{name}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteCrew(name)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-text-secondary hover:text-red-500 hover:bg-bg-primary rounded transition-all"
                    title="Supprimer"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create new crew */}
        <div className="border-t border-border pt-4 mt-4">
          <Label className="text-xs text-text-secondary uppercase tracking-wider">Créer un nouveau crew</Label>
          <form onSubmit={handleCreateCrew} className="space-y-3 mt-2">
            <Input
              value={crewName}
              onChange={e => setCrewName(e.target.value)}
              placeholder="Nom du crew (ex: equipe_dev)"
              className="bg-bg-tertiary border-border"
              required
            />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Processus</Label>
                <Select value={crewProcess} onValueChange={setCrewProcess}>
                  <SelectTrigger className="h-8 text-sm bg-bg-tertiary border-border"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Séquentiel">Séquentiel</SelectItem>
                    <SelectItem value="Hiérarchique">Hiérarchique</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Limite RPM</Label>
                <Input type="number" value={crewMaxRpm} onChange={e => setCrewMaxRpm(parseInt(e.target.value))} min={1} max={100} className="h-8 text-sm bg-bg-tertiary border-border" />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <Switch checked={crewMemory} onCheckedChange={setCrewMemory} /> Mémoire activée (local)
            </label>

            <Button type="submit" className="w-full bg-accent hover:bg-accent-hover text-white">
              <PlusCircle size={16} className="mr-2" /> Créer le Crew
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
