"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatRelativeTime, formatScore } from "@/lib/utils";

export function DiagnosticsWorkspace() {
  const diagnostics = useQuery({
    queryKey: ["diagnostics"],
    queryFn: beaconApi.diagnostics,
    refetchInterval: 15_000,
  });

  if (diagnostics.isError) {
    return (
      <ErrorState
        description="Diagnostics API unavailable. Confirm the API is running."
        onRetry={() => void diagnostics.refetch()}
      />
    );
  }

  const data = diagnostics.data;

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Pipeline Reliability</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Diagnostics</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Live collector, queue, worker, and database health — refreshes every 15 seconds.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void diagnostics.refetch()} disabled={diagnostics.isFetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${diagnostics.isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </header>

      {diagnostics.isLoading || !data ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric label="Worker" value={data.worker.worker_status} hint={`Celery queue ${data.worker.celery_queue_length}`} />
            <Metric label="Scheduler" value={data.worker.scheduler_status} hint={data.worker.detail || "Beat inferred from collector runs"} />
            <Metric
              label="Last collection"
              value={data.last_successful_collection ? formatRelativeTime(data.last_successful_collection) : "—"}
            />
            <Metric
              label="Last opportunity"
              value={data.last_processed_opportunity ? formatRelativeTime(data.last_processed_opportunity) : "—"}
            />
            <Metric label="Raw events (24h)" value={String(data.database.raw_events_24h)} hint={`${data.database.raw_events_1h} last hour`} />
            <Metric label="Signals" value={String(data.database.classified_signals)} hint={`${data.database.companies} companies`} />
            <Metric label="Opportunities" value={String(data.database.opportunities)} hint={`${data.database.solution_matches} revenue matches`} />
            <Metric
              label="Quality avg ms"
              value={data.average_quality_processing_ms != null ? formatScore(data.average_quality_processing_ms, 1) : "—"}
            />
          </section>

          {(data.top_failing_connectors.length > 0 || data.last_error || data.missing_env.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle>Attention</CardTitle>
                <CardDescription>Failures, missing keys, and degraded connectors</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {data.last_error ? <p className="text-rose-300">Last error: {data.last_error}</p> : null}
                {data.top_failing_connectors.length ? (
                  <p className="text-muted-foreground">
                    Top failing connectors: {data.top_failing_connectors.join(", ")}
                  </p>
                ) : null}
                {data.missing_env.length ? (
                  <p className="text-muted-foreground">Missing optional env: {data.missing_env.join(", ")}</p>
                ) : null}
              </CardContent>
            </Card>
          )}

          <section className="grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
            <Card>
              <CardHeader>
                <CardTitle>Collectors</CardTitle>
                <CardDescription>Status, last run, emissions, and errors</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="pb-2 pr-3 font-medium">Source</th>
                      <th className="pb-2 pr-3 font-medium">Health</th>
                      <th className="pb-2 pr-3 font-medium">24h</th>
                      <th className="pb-2 pr-3 font-medium">Last run</th>
                      <th className="pb-2 pr-3 font-medium">Emitted</th>
                      <th className="pb-2 font-medium">Last error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.collectors.map((collector) => (
                      <tr key={collector.source} className="border-t border-border/50">
                        <td className="py-2.5 pr-3 font-medium">{collector.source}</td>
                        <td className="py-2.5 pr-3">
                          <Badge className={healthTone(collector.health_status)}>{collector.health_status}</Badge>
                        </td>
                        <td className="py-2.5 pr-3 tabular-nums">{collector.signals_24h}</td>
                        <td className="py-2.5 pr-3 text-muted-foreground">
                          {collector.last_run_at ? formatRelativeTime(collector.last_run_at) : "never"}
                        </td>
                        <td className="py-2.5 pr-3 tabular-nums">
                          {collector.last_emitted ?? "—"}/{collector.last_collected ?? "—"}
                        </td>
                        <td className="max-w-[280px] truncate py-2.5 text-muted-foreground" title={collector.last_error || undefined}>
                          {collector.last_error || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Queues</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {data.queues.map((queue) => (
                    <div key={queue.name} className="flex items-center justify-between gap-3 text-sm">
                      <div>
                        <p className="font-medium">{queue.name}</p>
                        <p className="text-xs text-muted-foreground">{queue.detail}</p>
                      </div>
                      <span className="tabular-nums font-semibold">{queue.length}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Database counts</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {Object.entries(data.database).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-3">
                      <span className="text-muted-foreground">{key}</span>
                      <span className="tabular-nums font-medium">{value}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </section>

          <Card>
            <CardHeader>
              <CardTitle>Stage funnel</CardTitle>
              <CardDescription>Records entering vs leaving each pipeline stage</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="pb-2 pr-3 font-medium">Stage</th>
                    <th className="pb-2 pr-3 font-medium">In</th>
                    <th className="pb-2 pr-3 font-medium">Out</th>
                    <th className="pb-2 pr-3 font-medium">Drop-off</th>
                    <th className="pb-2 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.funnel.map((stage) => (
                    <tr key={stage.stage} className="border-t border-border/50">
                      <td className="py-2.5 pr-3 font-medium">{stage.stage}</td>
                      <td className="py-2.5 pr-3 tabular-nums">{stage.entering}</td>
                      <td className="py-2.5 pr-3 tabular-nums">{stage.leaving}</td>
                      <td className="py-2.5 pr-3 tabular-nums">{formatScore(stage.drop_off_percent, 1)}%</td>
                      <td className="py-2.5 text-muted-foreground">{stage.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {Object.keys(data.quality_reason_breakdown).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Quality reason codes (24h)</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(data.quality_reason_breakdown).map(([code, count]) => (
                  <div key={code} className="flex justify-between gap-3 rounded-lg border border-border/50 px-3 py-2 text-sm">
                    <span className="truncate text-muted-foreground">{code}</span>
                    <span className="tabular-nums font-medium">{count}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="space-y-2 py-5">
        <p className="text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p className="font-display text-2xl font-semibold capitalize">{value}</p>
        {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

function healthTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "healthy" || normalized === "ok") return "bg-emerald-500/15 text-emerald-200 ring-emerald-500/20";
  if (normalized === "degraded") return "bg-amber-500/15 text-amber-200 ring-amber-500/20";
  if (normalized === "down") return "bg-rose-500/15 text-rose-200 ring-rose-500/20";
  return "bg-slate-500/15 text-slate-200 ring-slate-500/20";
}
