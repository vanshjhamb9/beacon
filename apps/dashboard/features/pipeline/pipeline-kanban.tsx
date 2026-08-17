"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { GripVertical } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn, formatScore } from "@/lib/utils";

type Stage = "new" | "contacted" | "replied" | "meeting" | "won" | "lost";

const STAGES: { id: Stage; label: string; color: string; bgColor: string }[] = [
  { id: "new", label: "New", color: "text-blue-500", bgColor: "bg-blue-500/10" },
  { id: "contacted", label: "Contacted", color: "text-orange-500", bgColor: "bg-orange-500/10" },
  { id: "replied", label: "Replied", color: "text-green-500", bgColor: "bg-green-500/10" },
  { id: "meeting", label: "Meeting", color: "text-purple-500", bgColor: "bg-purple-500/10" },
  { id: "won", label: "Won", color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
  { id: "lost", label: "Lost", color: "text-red-500", bgColor: "bg-red-500/10" },
];

function getStatusStage(status: string): Stage {
  const s = status.toLowerCase();
  if (s === "contacted") return "contacted";
  if (s === "replied") return "replied";
  if (s === "meeting" || s === "proposal" || s === "negotiation") return "meeting";
  if (s === "won") return "won";
  if (s === "lost" || s === "garbage" || s === "archived") return "lost";
  return "new";
}

export function PipelineKanban() {
  const queryClient = useQueryClient();
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [deptFilter, setDeptFilter] = useState<"all" | "comai" | "inowix" | "cyber">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "new" | "not_contacted" | "contacted" | "with_data">(
    "all",
  );

  const workspace = useQuery({
    queryKey: ["workspace-leads"],
    queryFn: () => beaconApi.workspaceLeads({ limit: 300 }),
    refetchInterval: 20_000,
  });

  const transition = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      beaconApi.workspaceSetStage(id, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-analytics"] });
    },
  });

  const allItems = useMemo(
    () => ((workspace.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>,
    [workspace.data]
  );

  const items = useMemo(() => {
    let next = allItems;
    if (deptFilter === "comai") {
      next = next.filter((item) => String(item.department || item.service_match || item.lane || "").startsWith("COMAI"));
    } else if (deptFilter === "cyber") {
      next = next.filter((item) =>
        String(item.department || item.lane || item.source || "").toLowerCase().includes("cyber"),
      );
    } else if (deptFilter === "inowix") {
      next = next.filter((item) => String(item.department || item.service_match || "").startsWith("Inowix"));
    }
    if (statusFilter === "new" || statusFilter === "not_contacted") {
      next = next.filter((item) => String(item.stage || "new") === "new");
    } else if (statusFilter === "contacted") {
      next = next.filter((item) => ["contacted", "replied", "meeting", "won"].includes(String(item.stage || "")));
    } else if (statusFilter === "with_data") {
      next = next.filter((item) => Boolean(item.has_contact_data));
    }
    return next;
  }, [allItems, deptFilter, statusFilter]);

  const comaiCount = allItems.filter((i) => String(i.department || i.service_match || "").startsWith("COMAI")).length;
  const cyberCount = allItems.filter((i) => String(i.department || i.lane || i.source || "").toLowerCase().includes("cyber")).length;
  const inowixCount = allItems.filter((i) => String(i.department || i.service_match || "").startsWith("Inowix")).length;

  const leadsByStage: Record<Stage, Array<Record<string, unknown>>> = {
    new: [],
    contacted: [],
    replied: [],
    meeting: [],
    won: [],
    lost: [],
  };

  items.forEach((lead) => {
    const stage = getStatusStage(String(lead.stage || lead.status || ""));
    leadsByStage[stage].push(lead);
  });

  const handleDragStart = (leadId: string) => setDraggedId(leadId);
  const handleDragOver = (e: React.DragEvent) => e.preventDefault();
  const handleDrop = (e: React.DragEvent, targetStage: Stage) => {
    e.preventDefault();
    if (draggedId) {
      transition.mutate({ id: draggedId, status: targetStage });
      setDraggedId(null);
    }
  };

  if (workspace.isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Qualified Leads</h1>
          <p className="text-sm text-muted-foreground">
            {items.length} Lead Engine leads across {STAGES.length} stages
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
        <div className="flex flex-wrap gap-1 rounded-lg border border-border/60 bg-muted/20 p-1">
          {(
            [
              ["all", "All"],
              ["new", "New"],
              ["not_contacted", "Not contacted"],
              ["contacted", "Contacted"],
              ["with_data", "With data"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setStatusFilter(id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                statusFilter === id ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg border border-border/60 bg-muted/20 p-1">
          <button
            onClick={() => setDeptFilter("all")}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              deptFilter === "all" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            All ({allItems.length})
          </button>
          <button
            onClick={() => setDeptFilter("comai")}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              deptFilter === "comai" ? "bg-purple-500/20 text-purple-400 shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            COMAI ({comaiCount})
          </button>
          <button
            onClick={() => setDeptFilter("inowix")}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              deptFilter === "inowix" ? "bg-blue-500/20 text-blue-400 shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            Inowix ({inowixCount})
          </button>
          <button
            onClick={() => setDeptFilter("cyber")}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              deptFilter === "cyber" ? "bg-emerald-500/20 text-emerald-400 shadow-sm" : "text-muted-foreground hover:text-foreground"
            )}
          >
            Cyber ({cyberCount})
          </button>
        </div>
      </div>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
        {STAGES.map((stage) => (
          <div
            key={stage.id}
            className="flex w-[280px] shrink-0 flex-col"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, stage.id)}
          >
            <div className={cn("mb-3 flex items-center justify-between rounded-t-xl px-4 py-3", stage.bgColor)}>
              <div className="flex items-center gap-2">
                <span className={cn("font-medium", stage.color)}>{stage.label}</span>
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
                leadsByStage[stage.id]?.map((lead, idx) => {
                  const leadId = String(lead.id || idx);
                  const score = Number(lead.intent_score || lead.score || 0);
                  return (
                    <motion.div
                      key={leadId}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.02 * idx }}
                      draggable
                      onDragStart={() => handleDragStart(leadId)}
                      className={cn(
                        "cursor-grab rounded-lg border border-border/60 bg-card p-3 transition-colors hover:border-primary/50 active:cursor-grabbing",
                        draggedId === leadId && "opacity-50"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <Link href={`/leads/${leadId}`} className="font-medium hover:text-primary">
                          {String(lead.company_name || lead.company || "Unknown")}
                        </Link>
                        <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground/50" />
                      </div>

                      {score > 0 && (
                        <div className="mt-1">
                          <span
                            className={cn(
                              "rounded-full px-2 py-0.5 text-xs font-medium",
                              score >= 80
                                ? "bg-green-500/10 text-green-500"
                                : score >= 60
                                  ? "bg-yellow-500/10 text-yellow-500"
                                  : "bg-muted text-muted-foreground"
                            )}
                          >
                            {formatScore(score, 0)}
                          </span>
                        </div>
                      )}

                      <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                        {String(lead.why_now || lead.description || "")}
                      </p>

                      <div className="mt-2 flex flex-wrap gap-1">
                        {!!lead.department && (
                          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                            {String(lead.department)}
                          </span>
                        )}
                        {!!lead.grade && (
                          <span className="rounded bg-orange-500/10 px-1.5 py-0.5 text-[10px] text-orange-400">
                            {String(lead.grade)}
                          </span>
                        )}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
