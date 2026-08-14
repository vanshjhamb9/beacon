"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function QAWorkspace() {
  const health = useQuery({ queryKey: ["qa-health"], queryFn: beaconApi.qaHealth });

  if (health.isLoading) return <Skeleton className="h-64 w-full" />;
  if (health.isError) {
    return <ErrorState description="QA platform unavailable." onRetry={() => void health.refetch()} />;
  }

  const report = health.data;

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Production QA</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">QA Platform</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Monitors API, workers, database, Redis, queues, LLM grounding, and communication providers.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Overall score</CardTitle>
          <CardDescription>Mode {report?.mode}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <p className="font-display text-4xl font-semibold">{report?.overall_score?.toFixed(1)}</p>
          <Badge>{report?.status}</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(report?.components ?? []).map((component) => (
          <Card key={String(component.name)}>
            <CardHeader>
              <CardTitle className="text-base">{String(component.name)}</CardTitle>
              <CardDescription>Score {Number(component.score ?? 0).toFixed(1)}</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge className="bg-muted text-muted-foreground ring-border">{String(component.status)}</Badge>
              {component.latency_ms != null ? (
                <p className="mt-2 text-xs text-muted-foreground">Latency {String(component.latency_ms)} ms</p>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>

      {(report?.recommendations?.length ?? 0) > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {report?.recommendations.map((item) => (
              <p key={item} className="text-sm text-muted-foreground">
                {item}
              </p>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
