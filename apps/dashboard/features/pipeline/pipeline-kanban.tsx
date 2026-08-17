"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { GripVertical, Phone, Mail, User, Zap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatScore } from "@/lib/utils";

type Stage = "new" | "contacted" | "replied" | "meeting" | "won" | "lost";

const STAGES: { id: Stage; label: string; color: string; bgColor: string }[] = [
  { id: "new", label: "New / Hot", color: "text-blue-500", bgColor: "bg-blue-500/10" },
  { id: "contacted", label: "Warm", color: "text-orange-500", bgColor: "bg-orange-500/10" },
  { id: "replied", label: "Contacted", color: "text-green-500", bgColor: "bg-green-500/10" },
  { id: "meeting", label: "Meeting", color: "text-purple-500", bgColor: "bg-purple-500/10" },
  { id: "won", label: "Won", color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
  { id: "lost", label: "Low / Archive", color: "text-red-500", bgColor: "bg-red-500/10" },
];

type Lead = {
  id: string;
  company_name: string;
  founder_name: string;
  decision_maker_role: string;
  email: string;
  phone: string;
  website: string;
  category: string;
  city: string;
  lead_priority: string;
  intent_score: number;
  sales_reason: string;
  source: string;
  stage: string;
};

function getStageFromPriority(priority: string, score: number): Stage {
  if (priority === "HOT" || score >= 80) return "new";
  if (priority === "WARM" || score >= 65) return "contacted";
  if (priority === "LOW" && score >= 50) return "replied";
  if (score < 50) return "lost";
  return "new";
}

function priorityColor(priority: string) {
  switch (priority) {
    case "HOT":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "WARM":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function PipelineKanban() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [draggedId, setDraggedId] = useState<string | null>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/unified-leads/pipeline");
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads);
      }
    } catch (e) {
      console.error("Failed to fetch pipeline leads", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchLeads();
    const interval = setInterval(fetchLeads, 30000);
    return () => clearInterval(interval);
  }, [fetchLeads]);

  const leadsByStage: Record<Stage, Lead[]> = useMemo(() => {
    const result: Record<Stage, Lead[]> = {
      new: [],
      contacted: [],
      replied: [],
      meeting: [],
      won: [],
      lost: [],
    };

    leads.forEach((lead) => {
      const stage =
        (lead.stage as Stage) ||
        getStageFromPriority(lead.lead_priority, lead.intent_score);
      result[stage].push(lead);
    });

    return result;
  }, [leads]);

  const handleDragStart = (leadId: string) => setDraggedId(leadId);
  const handleDragOver = (e: React.DragEvent) => e.preventDefault();
  const handleDrop = (e: React.DragEvent, targetStage: Stage) => {
    e.preventDefault();
    if (draggedId) {
      setLeads((prev) =>
        prev.map((l) =>
          l.id === draggedId ? { ...l, stage: targetStage } : l
        )
      );
      setDraggedId(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-2xl font-semibold">
            Qualified Leads Pipeline
          </h1>
          <p className="text-muted-foreground">Loading pipeline...</p>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => (
            <div key={stage.id} className="w-[280px] shrink-0">
              <div
                className={cn(
                  "mb-3 flex items-center justify-between rounded-t-xl px-4 py-3",
                  stage.bgColor
                )}
              >
                <span className={cn("font-medium", stage.color)}>
                  {stage.label}
                </span>
              </div>
              <div className="flex flex-1 flex-col gap-2 rounded-b-xl border border-t-0 border-border/60 bg-muted/10 p-2 min-h-[200px]">
                <div className="h-20 rounded-lg bg-muted/30 animate-pulse" />
                <div className="h-20 rounded-lg bg-muted/30 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">
            Qualified Leads Pipeline
          </h1>
          <p className="text-sm text-muted-foreground">
            {leads.length} leads across {STAGES.length} stages — drag to move
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/leads"
            className="rounded-lg border border-border/60 px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted/40"
          >
            View All Leads
          </Link>
        </div>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
        {STAGES.map((stage) => (
          <div
            key={stage.id}
            className="flex w-[300px] shrink-0 flex-col"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, stage.id)}
          >
            <div
              className={cn(
                "mb-3 flex items-center justify-between rounded-t-xl px-4 py-3",
                stage.bgColor
              )}
            >
              <div className="flex items-center gap-2">
                <span className={cn("font-medium", stage.color)}>
                  {stage.label}
                </span>
                <span className="rounded-full bg-background/50 px-2 py-0.5 text-xs font-medium">
                  {leadsByStage[stage.id]?.length || 0}
                </span>
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-2 rounded-b-xl border border-t-0 border-border/60 bg-muted/10 p-2">
              {leadsByStage[stage.id]?.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border/50 p-4 text-center text-sm text-muted-foreground">
                  No leads
                </div>
              ) : (
                leadsByStage[stage.id]?.map((lead, idx) => (
                  <motion.div
                    key={lead.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.02 * idx }}
                    draggable
                    onDragStart={() => handleDragStart(lead.id)}
                    className={cn(
                      "cursor-grab rounded-lg border border-border/60 bg-card p-3 transition-colors hover:border-primary/50 active:cursor-grabbing",
                      draggedId === lead.id && "opacity-50"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="font-medium hover:text-primary"
                      >
                        {lead.company_name}
                      </Link>
                      <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground/50" />
                    </div>

                    <div className="mt-1.5 flex items-center gap-2">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          lead.intent_score >= 80
                            ? "bg-green-500/10 text-green-500"
                            : lead.intent_score >= 60
                              ? "bg-yellow-500/10 text-yellow-500"
                              : "bg-muted text-muted-foreground"
                        )}
                      >
                        {formatScore(lead.intent_score, 0)}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${priorityColor(lead.lead_priority)}`}
                      >
                        {lead.lead_priority}
                      </Badge>
                    </div>

                    {lead.founder_name && (
                      <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <User className="h-3 w-3" />
                        {lead.founder_name}
                        {lead.decision_maker_role && (
                          <span className="text-[10px]">
                            ({lead.decision_maker_role})
                          </span>
                        )}
                      </div>
                    )}

                    {lead.email && (
                      <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Mail className="h-3 w-3 text-blue-400" />
                        <span className="truncate font-mono">
                          {lead.email}
                        </span>
                      </div>
                    )}

                    {lead.phone && (
                      <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Phone className="h-3 w-3 text-emerald-400" />
                        <span className="font-mono">{lead.phone}</span>
                      </div>
                    )}

                    <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                      {lead.sales_reason}
                    </p>

                    <div className="mt-2 flex flex-wrap gap-1">
                      {lead.category && (
                        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                          {lead.category}
                        </span>
                      )}
                      {lead.city && (
                        <span className="rounded bg-orange-500/10 px-1.5 py-0.5 text-[10px] text-orange-400">
                          {lead.city}
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
