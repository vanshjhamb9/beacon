"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Server } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

function tone(status?: string) {
  const value = (status || "").toLowerCase();
  if (value === "pass" || value === "healthy" || value === "true") return "default" as const;
  if (value === "warning") return "secondary" as const;
  return "destructive" as const;
}

export function OperationsWorkspace() {
  const ops = useQuery({
    queryKey: ["operations"],
    queryFn: beaconApi.operations,
    refetchInterval: 10_000,
  });
  const odu = useQuery({
    queryKey: ["odu-ops-dashboard"],
    queryFn: () => beaconApi.oduDashboard(),
    refetchInterval: 60_000,
  });

  if (ops.isError) {
    return (
      <ErrorState
        description="Operations API unavailable. Confirm API + Redis 7 + migrations."
        onRetry={() => void ops.refetch()}
      />
    );
  }

  const data = ops.data;
  const oduData = odu.data || {};
  const oduKpis = (oduData.kpis || {}) as Record<string, unknown>;
  const sourceHealth = ((oduData.source_health as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const oduRecovery = ((oduData.recovery as { items?: Array<Record<string, unknown>>; count?: number }) ||
    {}) as { items?: Array<Record<string, unknown>>; count?: number };

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>System Operations</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Operations</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Live infrastructure, Celery, migrations, pipeline stages, and production gate — refreshes every 10s.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void ops.refetch()} disabled={ops.isFetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${ops.isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </header>

      {ops.isLoading || !data ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric label="Readiness" value={`${data.readiness_score}`} hint={data.production_gate.allow_production ? "Production allowed" : "Production blocked"} />
            <Metric label="Redis" value={data.redis.version || "—"} hint={data.redis.ok ? "Streams OK" : (data.redis.errors?.[0] as string) || "FAIL"} />
            <Metric label="Alembic" value={data.migrations.current_revision || "—"} hint={`head ${data.migrations.head_revision}`} />
            <Metric label="Worker" value={data.celery.worker_online ? "online" : "offline"} hint={`queue ${data.celery.queue_depth}`} />
            <Metric label="Beat" value={data.celery.beat_online ? "online" : "offline"} hint={`${data.celery.scheduled_tasks} scheduled`} />
            <Metric label="Active tasks" value={String(data.celery.active_tasks)} hint={`registered ${data.celery.registered_task_count}`} />
            <Metric label="Enrichment coverage" value={`${data.enrichment.coverage_pct ?? 0}%`} hint={`${data.enrichment.enrichment_reports}/${data.enrichment.opportunities}`} />
            <Metric label="Alerts" value={String(data.alerts.length)} hint={data.alerts[0]?.code || "none"} />
          </section>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-4 w-4" /> Infrastructure
              </CardTitle>
              <CardDescription>Redis · Postgres · Celery · Beat · API</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.infrastructure.map((item) => (
                <div key={item.name} className="rounded-lg border border-border/60 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{item.name}</p>
                    <Badge variant={tone(item.status)}>{item.status}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{item.detail || "—"}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pipeline stages</CardTitle>
              <CardDescription>Input → output coverage by stage</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="pb-2 pr-3">Stage</th>
                    <th className="pb-2 pr-3">Input</th>
                    <th className="pb-2 pr-3">Output</th>
                    <th className="pb-2 pr-3">Dropped</th>
                    <th className="pb-2 pr-3">Success %</th>
                    <th className="pb-2 pr-3">Worker</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.pipeline.map((stage) => (
                    <tr key={stage.stage} className="border-t border-border/50">
                      <td className="py-2 pr-3 font-medium">{stage.stage}</td>
                      <td className="py-2 pr-3">{stage.input_count}</td>
                      <td className="py-2 pr-3">{stage.output_count}</td>
                      <td className="py-2 pr-3">{stage.dropped_count}</td>
                      <td className="py-2 pr-3">{stage.success_percent}</td>
                      <td className="py-2 pr-3 text-xs text-muted-foreground">{stage.worker_task || "—"}</td>
                      <td className="py-2">
                        <Badge variant={tone(stage.status)}>{stage.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Alerts</CardTitle>
              <CardDescription>Severity · cause · evidence · recommended fix</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.alerts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active operational alerts.</p>
              ) : (
                data.alerts.map((alert) => (
                  <div key={alert.code + alert.cause} className="rounded-lg border border-border/60 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={tone(alert.severity)}>{alert.severity}</Badge>
                      <p className="text-sm font-medium">{alert.code}</p>
                    </div>
                    <p className="mt-1 text-sm">{alert.cause}</p>
                    <p className="mt-1 text-xs text-muted-foreground">Fix: {alert.recommended_fix}</p>
                    <p className="mt-1 text-xs text-muted-foreground">Evidence: {(alert.evidence || []).join(" · ")}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Freshness</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 md:grid-cols-2 xl:grid-cols-3 text-sm">
              {Object.entries(data.freshness || {}).map(([key, value]) => (
                <div key={key} className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">{key}</p>
                  <p className="font-medium">{value ? String(value) : "—"}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Production gate</CardTitle>
              <CardDescription>Blocks unsafe production deployments</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                Allow production:{" "}
                <Badge variant={data.production_gate.allow_production ? "default" : "destructive"}>
                  {String(data.production_gate.allow_production)}
                </Badge>{" "}
                · score {data.production_gate.score}
              </p>
              <p className="text-muted-foreground">Blockers: {(data.production_gate.blockers || []).join(", ") || "none"}</p>
              <p className="text-muted-foreground">Warnings: {(data.production_gate.warnings || []).join(", ") || "none"}</p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      {hint ? <CardContent className="text-xs text-muted-foreground">{hint}</CardContent> : null}
    </Card>
  );
}

function recoveryCount(items?: Array<Record<string, unknown>>) {
  return items?.length ?? 0;
}
