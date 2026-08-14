"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Circle, Clock3, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

export function CompanyJourneyPanel({ companyId }: { companyId: string }) {
  const journey = useQuery({
    queryKey: ["company-journey", companyId],
    queryFn: () => beaconApi.companyJourney(companyId),
    refetchInterval: 15_000,
  });

  if (journey.isLoading) return <Skeleton className="h-48 w-full" />;
  if (journey.isError || !journey.data) {
    return (
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle>Journey</CardTitle>
          <CardDescription>Lifecycle not available yet for this company.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const data = journey.data;
  const gapStages = data.stages.filter((s) => s.status === "pending");
  const completedAfterGap = data.stages.some(
    (s, i) =>
      s.status === "completed" &&
      data.stages.slice(0, i).some((p) => p.status === "pending"),
  );

  return (
    <div className="space-y-4">
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle>Journey</CardTitle>
          <CardDescription>
            Deterministic Signal → Won path · current stage{" "}
            <Badge variant="outline">{data.current_stage.replaceAll("_", " ")}</Badge>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {completedAfterGap ? (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
              Pipeline has gaps: {gapStages.map((s) => s.label).join(", ") || "earlier stage"} still open while later
              stages already completed. This is honest operational state — enrichment is incomplete.
            </div>
          ) : null}
          {data.stages.map((stage, index) => (
            <div key={stage.stage} className="relative pl-1">
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <StatusIcon status={stage.status} />
                  {index < data.stages.length - 1 ? <span className="mt-1 w-px flex-1 bg-border" /> : null}
                </div>
                <div className="mb-4 min-w-0 flex-1 rounded-lg border border-border/60 bg-[#0d1524]/60 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">{stage.label}</p>
                    <Badge
                      variant={
                        stage.status === "completed"
                          ? "default"
                          : stage.status === "failed"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {stage.status}
                    </Badge>
                  </div>
                  <div className="mt-2 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                    <p>Started {stage.started_at ? new Date(stage.started_at).toLocaleString() : "—"}</p>
                    <p>Completed {stage.completed_at ? new Date(stage.completed_at).toLocaleString() : "—"}</p>
                    <p>Duration {formatDuration(stage.duration_seconds)}</p>
                    <p>Connector {stage.connector || "—"}</p>
                    <p>Worker {stage.worker || "—"}</p>
                    <p>Retries {stage.retry_count}</p>
                  </div>
                  {stage.status === "skipped" ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {stage.stage === "lost"
                        ? "Alternate terminal — not lost"
                        : "Not reached yet (waiting on earlier stages)"}
                    </p>
                  ) : null}
                  {stage.status === "pending" ? (
                    <p className="mt-2 text-xs text-amber-200/90">Blocker — waiting for this stage to complete</p>
                  ) : null}
                  {stage.evidence?.length ? (
                    <p className="mt-2 text-xs text-muted-foreground">Evidence: {stage.evidence.join(" · ")}</p>
                  ) : null}
                  {stage.failures?.length ? (
                    <p className="mt-1 text-xs text-rose-300">Failures: {stage.failures.join(" · ")}</p>
                  ) : null}
                  {stage.detail ? <p className="mt-1 text-sm">{stage.detail}</p> : null}
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle>Pipeline Health</CardTitle>
          <CardDescription>Hover stages for worker · timestamp · duration · connector</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            {data.pipeline_health.map((node, index) => (
              <div key={String(node.stage)} className="flex items-center gap-2">
                <div
                  title={`worker: ${String(node.worker || "—")} | connector: ${String(node.connector || "—")} | duration: ${formatDuration(node.duration_seconds as number | null | undefined)} | at: ${String(node.timestamp || "—")}`}
                  className={cn(
                    "rounded-lg border px-3 py-2 text-sm",
                    node.status === "completed" && "border-emerald-500/40 bg-emerald-500/10",
                    node.status === "pending" && "border-amber-500/40 bg-amber-500/10",
                    node.status === "failed" && "border-rose-500/40 bg-rose-500/10",
                    node.status === "skipped" && "border-border/60 bg-muted/20 text-muted-foreground",
                  )}
                >
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{String(node.label)}</p>
                  <p className="font-medium">{String(node.mark)}</p>
                </div>
                {index < data.pipeline_health.length - 1 ? <span className="text-muted-foreground">↓</span> : null}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function formatDuration(seconds: number | null | undefined) {
  if (seconds == null) return "—";
  if (seconds <= 0) return "<1s";
  if (seconds < 60) return `${seconds}s`;
  return `${(seconds / 60).toFixed(1)}m`;
}

function StatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  if (status === "failed") return <XCircle className="h-4 w-4 text-rose-400" />;
  if (status === "pending") return <Clock3 className="h-4 w-4 text-amber-300" />;
  return <Circle className="h-4 w-4 text-muted-foreground" />;
}
