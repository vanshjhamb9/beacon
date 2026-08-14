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

function Funnel({ title, stages }: { title: string; stages: Array<Record<string, unknown>> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {stages.length === 0 && <p className="text-muted-foreground">No data yet — run unlock.</p>}
        {stages.map((s) => (
          <div key={String(s.name)} className="flex items-center justify-between border-b py-2">
            <span>{String(s.name)}</span>
            <Badge variant="outline">{String(s.count ?? 0)}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function DatasetUnlockWorkspace() {
  const dash = useQuery({
    queryKey: ["odu-dashboard"],
    queryFn: () => beaconApi.oduDashboard(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return <ErrorState title="Dataset Unlock unavailable" description="API /operations/odu/dashboard failed." />;
  }

  const d = dash.data || {};
  const kpis = (d.kpis || {}) as Record<string, unknown>;
  const answer = String(d.vansh_ready_answer || "NO");
  const connectors = ((d.connectors as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const health = ((d.source_health as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const recovery = ((d.recovery as { items?: Array<Record<string, unknown>> })?.items || []) as Array<
    Record<string, unknown>
  >;
  const failures = (d.top_failures || {}) as Record<string, number>;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>odu-v1</SectionLabel>
          <h1 className="text-3xl font-semibold tracking-tight">Dataset Unlock</h1>
          <p className="text-sm text-muted-foreground">
            Verified identity sources → companies Vansh can contact today.
          </p>
        </div>
        <Badge className={answer === "YES" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}>
          Contact-ready ≥10: {answer}
        </Badge>
      </div>

      {dash.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Metric label="Verified Companies" value={kpis.verified_companies} />
        <Metric label="Business Emails" value={kpis.business_emails} />
        <Metric label="Decision Makers" value={kpis.decision_makers} />
        <Metric label="Sales Ready" value={kpis.sales_ready} warn={!kpis.sales_ready} />
        <Metric label="Revenue Ready" value={kpis.revenue_ready} warn={!kpis.revenue_ready} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Funnel title="Identity Funnel" stages={(d.funnel_identity as Array<Record<string, unknown>>) || []} />
        <Funnel title="Contacts Funnel" stages={(d.funnel_contacts as Array<Record<string, unknown>>) || []} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Connector Ranking</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {connectors.length === 0 && <p className="text-muted-foreground">Run unlock to populate.</p>}
            {connectors.slice(0, 12).map((c) => (
              <div key={String(c.connector)} className="flex justify-between border-b py-2">
                <span>
                  {String(c.connector)} · co {Number(c.companies || 0)} · email {Number(c.emails || 0)} · dm{" "}
                  {Number(c.decision_makers || 0)}
                </span>
                <Badge variant="secondary">{formatScore(Number(c.yield_pct || 0), 1)}%</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Source Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {health.map((h) => (
              <div key={String(h.connector)} className="flex justify-between border-b py-2">
                <span>
                  {String(h.connector)} · {String(h.note || "").slice(0, 48)}
                </span>
                <Badge variant="outline">{String(h.health)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recovery Queue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {recovery.slice(0, 10).map((item) => (
              <div key={String(item.id)} className="flex justify-between border-b py-2">
                <span>{String(item.reason)}</span>
                <Badge variant="outline">{String(item.domain || "").slice(0, 28)}</Badge>
              </div>
            ))}
            {!recovery.length && <p className="text-muted-foreground">Queue empty.</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Failures</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.entries(failures)
              .slice(0, 10)
              .map(([reason, count]) => (
                <div key={reason} className="flex justify-between border-b py-2">
                  <span>{reason}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
            {!Object.keys(failures).length && <p className="text-muted-foreground">No failures logged.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
