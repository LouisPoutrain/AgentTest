"use client";

import { AutomationWizard } from "@/components/lab/AutomationWizard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Zap, Code2, TestTube2, BookOpen, Search } from "lucide-react";

export default function LabPage() {
  return (
    <div className="min-h-screen bg-bg-primary p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="h-12 w-12 rounded-xl bg-accent-subtle border border-accent/20 flex items-center justify-center">
            <Sparkles className="h-6 w-6 text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Laboratoire d&apos;Automatisation</h1>
            <p className="text-sm text-text-tertiary">Créez et lancez des automatisations multi-agents en quelques clics</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard icon={Code2} label="Templates" value="18" color="text-blue-500" />
          <StatCard icon={TestTube2} label="Testing" value="3" color="text-emerald-500" />
          <StatCard icon={BookOpen} label="Documentation" value="2" color="text-amber-500" />
          <StatCard icon={Search} label="Recherche" value="3" color="text-purple-500" />
        </div>

        {/* Wizard */}
        <Card className="border-border bg-bg-secondary/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="h-4 w-4 text-accent" />
              Nouveau Crew
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AutomationWizard
              onLaunch={(params) => {
                console.log("Launching:", params);
              }}
              crewName="default"
              maxRpm={15}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <Card className="border-border/60 bg-bg-secondary/50">
      <CardContent className="p-4 flex items-center gap-3">
        <Icon className={"h-5 w-5 " + color} />
        <div>
          <div className="text-lg font-bold text-text-primary">{value}</div>
          <div className="text-[10px] text-text-tertiary uppercase tracking-wider">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}
