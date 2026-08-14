"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

function Metric({ label, value, warn }: { label: string; value: unknown; warn?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${warn ? "border-red-500/50 bg-red-500/5" : "border-border/60"}`}>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{String(value ?? "—")}</p>
    </div>
  );
}

export function IdentityCoverageWorkspace() {
  const dash = useQuery({
    queryKey: ["ice-dashboard"],
    queryFn: () => beaconApi.iceDashboard(),
    refetchInterval: 60_000,
  });
  const recovery = useQuery({
    queryKey: ["ice-recovery"],
    queryFn: () => beaconApi.iceRecovery(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return <ErrorState title="Identity Coverage unavailable" description="API /identity-coverage/dashboard failed." />;
  }

  const d = dash.data || {};
  const funnel = ((d.funnel as { stages?: Array<Record<string, unknown>> })?.stages || []) as Array<
    Record<string, unknown>
  >;
  const collectors = ((d.collectors as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const impact = (d.business_impact || {}) as Record<string, unknown>;
  const answer = String(d.vansh_ready_answer || "NO");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>ice-v1</SectionLabel>
          <h1 className="text-3xl font-semibold tracking-tight">Identity Coverage</h1>
          <p className="text-sm text-muted-foreground">Raise recall. Zero fabricated identities. Compose-only.</p>
        </div>
        <Badge className={answer === "YES" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}>
          Vansh-ready: {answer}
        </Badge>
      </div>

      {dash.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Metric label="Revenue Ready" value={d.revenue_ready ?? impact.revenue_ready} warn={!d.revenue_ready} />
        <Metric label="Emails Ready" value={d.business_emails ?? impact.emails_ready} />
        <Metric label="Decision Makers Ready" value={d.decision_makers ?? impact.decision_makers_ready} />
        <Metric label="Verified Companies" value={d.verified_companies} />
        <Metric label="Recovery Pending" value={d.recovery_pending ?? recovery.data?.count} />
        <Metric label="Coverage %" value={formatScore(Number(d.coverage_pct || 0), 1)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coverage Funnel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {funnel.length === 0 && <p className="text-muted-foreground">Run expand / daily report to populate.</p>}
          {funnel.map((s) => (
            <div key={String(s.name)} className="flex flex-wrap items-center justify-between gap-2 border-b py-2">
              <span>{String(s.name)}</span>
              <div className="flex gap-2">
                <Badge variant="outline">{String(s.count)}</Badge>
                <Badge variant="secondary">{formatScore(Number(s.conversion_pct || 0), 1)}%</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Collector Leaderboard</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {collectors.length === 0 && <p className="text-muted-foreground">No metrics yet.</p>}
            {collectors.map((c) => (
              <div key={String(c.collector)} className="flex justify-between border-b py-2">
                <span>
                  {String(c.collector)} · cos {Number(c.companies || 0)} · web {Number(c.official_websites || 0)}
                </span>
                <Badge variant="outline">{String(c.recommendation)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recovery Queue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {((recovery.data?.items as Array<Record<string, unknown>>) || []).slice(0, 8).map((item) => (
              <div key={String(item.id)} className="flex justify-between border-b py-2">
                <span>{String(item.reason)}</span>
                <Badge variant="outline">{String(item.domain || item.signal_id).slice(0, 24)}</Badge>
              </div>
            ))}
            {!recovery.data?.count && <p className="text-muted-foreground">Queue empty or not loaded.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
