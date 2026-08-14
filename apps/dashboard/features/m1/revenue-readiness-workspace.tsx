"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

function tone(status: string) {
  if (status === "PASS") return "default";
  if (status === "WARN") return "outline";
  return "outline";
}

export function RevenueReadinessValidationWorkspace() {
  const report = useQuery({
    queryKey: ["m1-report"],
    queryFn: () => beaconApi.m1Report(),
    refetchInterval: 120_000,
  });

  if (report.isLoading) return <Skeleton className="h-96 w-full" />;
  if (report.isError || !report.data) {
    return <ErrorState description="M1 validation report unavailable. Is the API running?" onRetry={() => void report.refetch()} />;
  }

  const d = report.data as Record<string, any>;
  const phases = (d.phases ?? []) as Array<Record<string, any>>;
  const metrics = (d.success_metrics ?? []) as Array<Record<string, any>>;
  const collection = phases.find((p) => p.phase === "1");
  const sre = phases.find((p) => p.phase === "5");

  return (
    <div className="mx-auto flex max-w-[1500px] flex-col gap-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <SectionLabel>Milestone M1</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Readiness Validation</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">{String(d.north_star)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge>{String(d.overall_status)}</Badge>
          <Badge variant="outline">~{String(d.estimated_qualified_per_100)} / 100 outreach-ready</Badge>
          <Badge variant="outline">Production {d.production_allowed ? "allowed" : "blocked"}</Badge>
          <Button variant="outline" onClick={() => void report.refetch()}>
            Refresh audit
          </Button>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map((m) => (
          <Card key={String(m.name)}>
            <CardHeader className="pb-2">
              <CardDescription>{String(m.name).replaceAll("_", " ")}</CardDescription>
              <CardTitle className="font-display text-xl tabular-nums">
                {String(m.actual ?? "—")}
                <span className="text-sm font-normal text-muted-foreground"> / {String(m.target)}{String(m.unit)}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant={m.hit ? "default" : "outline"}>{m.hit ? "HIT" : "MISS"}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Phase 1 — Collection</CardTitle>
          <CardDescription>{String(collection?.summary ?? "")}</CardDescription>
        </CardHeader>
        <CardContent className="overflow-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
              <tr>
                <th className="py-2">Source</th>
                <th>Status</th>
                <th>Today</th>
                <th>Emitted</th>
                <th>Qualified</th>
                <th>Rejected</th>
                <th>Dup %</th>
                <th>Err %</th>
                <th>Last run</th>
              </tr>
            </thead>
            <tbody>
              {(collection?.rows ?? []).map((r: Record<string, any>) => (
                <tr key={String(r.source)} className="border-t border-border/50">
                  <td className="py-2 font-medium">{String(r.source)}</td>
                  <td>{String(r.status)}</td>
                  <td className="tabular-nums">{String(r.today_collected)}</td>
                  <td className="tabular-nums">{String(r.today_emitted)}</td>
                  <td className="tabular-nums">{String(r.qualified_estimate)}</td>
                  <td className="tabular-nums">{String(r.rejected_estimate)}</td>
                  <td className="tabular-nums">{String(r.duplicate_rate)}</td>
                  <td className="tabular-nums">{String(r.error_rate)}</td>
                  <td className="text-muted-foreground">
                    {r.freshness_minutes != null ? `${r.freshness_minutes} min ago` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Phase 5 — Sales Readiness Audit</CardTitle>
          <CardDescription>{String(sre?.summary ?? "")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2">
            {(sre?.rows ?? []).map((r: Record<string, any>) => (
              <div key={String(r.stage)} className="flex justify-between rounded-lg border border-border/60 px-3 py-2 text-sm">
                <span>{String(r.stage)}</span>
                <span className="tabular-nums font-medium">{String(r.count)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {phases.map((p) => (
          <Card key={String(p.phase)}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base">
                  Phase {String(p.phase)} — {String(p.title)}
                </CardTitle>
                <Badge variant={tone(String(p.status))}>{String(p.status)}</Badge>
              </div>
              <CardDescription>{String(p.summary)}</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {Array.isArray(p.blockers) && p.blockers.length > 0 ? (
                <p>Blockers: {p.blockers.slice(0, 6).map(String).join(", ")}</p>
              ) : (
                <p>No blockers recorded.</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {(d.recommendations ?? []).map((rec: string, i: number) => (
            <p key={i}>• {rec}</p>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
