"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

function Metric({ label, value, warn }: { label: string; value: unknown; warn?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${warn ? "border-red-500/50 bg-red-500/5" : "border-border/60"}`}>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{String(value ?? "—")}</p>
    </div>
  );
}

export function RevenueReadyWorkspace() {
  const dash = useQuery({
    queryKey: ["rrp-dashboard"],
    queryFn: () => beaconApi.rrpDashboard(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return <ErrorState title="Revenue Ready unavailable" description="API /revenue-ready/dashboard failed." />;
  }

  const d = dash.data || {};
  const kpis = (d.kpis || {}) as Record<string, unknown>;
  const funnel = ((d.funnel as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const blockers = (d.blockers || {}) as Record<string, number>;
  const top = ((d.top_10 as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const answer = String(d.vansh_ready_answer || "NO");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>rrp-v1</SectionLabel>
          <h1 className="text-3xl font-semibold tracking-tight">Revenue Ready</h1>
          <p className="text-sm text-muted-foreground">
            Perfect existing Sales Ready companies — no new acquisition.
          </p>
        </div>
        <Badge className={answer === "YES" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}>
          Contact ≥10: {answer}
        </Badge>
      </div>

      {dash.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Revenue Ready" value={kpis.revenue_ready} warn={!kpis.revenue_ready} />
        <Metric label="Sales Ready" value={kpis.sales_ready} />
        <Metric label="Confidence ≥90" value={kpis.confidence_ge_90} />
        <Metric label="Trust ≥95" value={kpis.trust_ge_95} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Funnel</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {funnel.map((s) => (
              <div key={String(s.name)} className="flex justify-between border-b py-2">
                <span>{String(s.name)}</span>
                <Badge variant="outline">{String(s.count ?? 0)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Blockers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.keys(blockers).length === 0 && <p className="text-muted-foreground">No blockers logged.</p>}
            {Object.entries(blockers).map(([reason, count]) => (
              <div key={reason} className="flex justify-between border-b py-2">
                <span>{reason}</span>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top 10 Revenue Ready</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {top.length === 0 && <p className="text-muted-foreground">Run perfect to promote companies.</p>}
          {top.map((c) => (
            <Link
              key={String(c.company_id)}
              href={`/lead-explorer?company_id=${encodeURIComponent(String(c.company_id))}`}
              className="block border-b py-3 transition hover:bg-muted/20"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium">{String(c.company)}</p>
                <Badge className="bg-emerald-600 text-white">Revenue Ready</Badge>
              </div>
              <p className="text-muted-foreground">{String(c.website)}</p>
              <p>
                {String(c.decision_maker || "—")} · {String(c.business_email || "—")}
              </p>
              <p className="text-muted-foreground">{String(c.why_now || "")}</p>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
