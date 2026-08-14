"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function ProductionHealthWorkspace() {
  const queryClient = useQueryClient();
  const health = useQuery({
    queryKey: ["production-health"],
    queryFn: () => beaconApi.productionHealth(),
    refetchInterval: 30_000,
  });
  const alerts = useQuery({
    queryKey: ["production-alerts"],
    queryFn: () => beaconApi.productionAlerts(),
    refetchInterval: 30_000,
  });
  const refresh = useMutation({
    mutationFn: () => beaconApi.productionValidationRefresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["production-health"] });
      await queryClient.invalidateQueries({ queryKey: ["production-alerts"] });
      await queryClient.invalidateQueries({ queryKey: ["production-report"] });
    },
  });

  if (health.isLoading) return <Skeleton className="h-72 w-full" />;
  if (health.isError) {
    return <ErrorState description="Production health unavailable." onRetry={() => void health.refetch()} />;
  }

  const components = (health.data?.components ?? []) as Array<Record<string, unknown>>;
  const alertRows = (alerts.data?.alerts ?? []) as Array<Record<string, unknown>>;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Production Readiness</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Production Health</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Live health for API, workers, collectors, campaigns, email, WhatsApp, OAuth, queues, DB, Redis, Celery, and
            pipeline.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/revenue-dashboard">Revenue</Link>
          </Button>
          <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            {refresh.isPending ? "Refreshing…" : "Refresh validation"}
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        <Badge>Status {String(health.data?.overall_status ?? "—")}</Badge>
        <Badge variant="outline">Score {String(health.data?.overall_score ?? "—")}</Badge>
        <Badge variant="outline">Version {String(health.data?.scoring_version ?? "prrv-v1")}</Badge>
        <Badge variant="outline">Telemetry {String((health.data as { telemetry?: string } | undefined)?.telemetry ?? "live")}</Badge>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {components.map((c) => (
          <Card key={String(c.name)}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base capitalize">{String(c.name)}</CardTitle>
              <CardDescription>{String(c.recommendation ?? "Healthy")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1 text-sm text-muted-foreground">
              <div className="flex justify-between">
                <span>Status</span>
                <Badge variant="outline">{String(c.status)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Success</span>
                <span>{String(c.success_rate)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Latency</span>
                <span>{String(c.latency_ms)} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Queue</span>
                <span>{String(c.queue_depth)}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actionable Alerts</CardTitle>
          <CardDescription>Every issue includes severity, recommendation, and owner.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {alertRows.length === 0 ? (
            <EmptyState title="No open alerts" description="Platform signals are within thresholds." />
          ) : (
            alertRows.map((a, idx) => (
              <div key={`${a.code}-${idx}`} className="rounded-xl border border-border/60 p-3">
                <div className="flex flex-wrap gap-2">
                  <p className="font-medium">{String(a.title)}</p>
                  <Badge>{String(a.severity)}</Badge>
                  <Badge variant="outline">{String(a.owner)}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{String(a.recommendation)}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
