"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

const LABELS: Record<string, string> = {
  collectors: "Collector Health",
  pipeline: "Pipeline Health",
  campaigns: "Campaign Health",
  communication: "Communication Health",
  queues: "Queue Health",
  workers: "Worker Health",
  webhooks: "Webhook Health",
  providers: "Provider Health",
  database: "Database Health",
  redis: "Redis Health",
  api: "API",
  llm: "LLM",
  dashboard: "Dashboard",
};

export function SystemHealthWorkspace() {
  const health = useQuery({ queryKey: ["system-health"], queryFn: beaconApi.systemHealth, refetchInterval: 30_000 });

  if (health.isLoading) return <Skeleton className="h-64 w-full" />;
  if (health.isError) {
    return <ErrorState description="System health unavailable." onRetry={() => void health.refetch()} />;
  }

  const report = health.data;

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Observability</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">System Health</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Live probes across collectors, pipeline, campaigns, communication, queues, workers, and providers.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Overall system score</CardTitle>
          <CardDescription>{report?.mode} mode</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <p className="font-display text-5xl font-semibold">{report?.overall_score?.toFixed(1)}</p>
          <Badge>{report?.status}</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(report?.components ?? []).map((component) => (
          <Card key={component.name}>
            <CardHeader>
              <CardTitle className="text-base">{LABELS[component.name] ?? component.name}</CardTitle>
              <CardDescription>Score {component.score.toFixed(1)}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1">
              <Badge className="bg-muted text-muted-foreground ring-border">{component.status}</Badge>
              {component.latency_ms != null ? (
                <p className="text-xs text-muted-foreground">{component.latency_ms} ms</p>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
