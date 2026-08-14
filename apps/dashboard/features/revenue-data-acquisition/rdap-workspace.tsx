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

export function RevenueDataAcquisitionWorkspace() {
  const dash = useQuery({
    queryKey: ["rdap-dashboard"],
    queryFn: () => beaconApi.rdapDashboard(),
    refetchInterval: 60_000,
  });
  const recovery = useQuery({
    queryKey: ["rdap-recovery"],
    queryFn: () => beaconApi.rdapRecovery(),
    refetchInterval: 60_000,
  });
  const yields = useQuery({
    queryKey: ["rdap-yield"],
    queryFn: () => beaconApi.rdapRevenueYield(),
    refetchInterval: 60_000,
  });
  const reports = useQuery({
    queryKey: ["rdap-reports"],
    queryFn: () => beaconApi.rdapReports(),
    refetchInterval: 120_000,
  });

  if (dash.isError) {
    return (
      <ErrorState
        title="Revenue Data Acquisition unavailable"
        description="API /revenue-data-acquisition/dashboard failed."
      />
    );
  }

  const d = dash.data || {};
  const funnel = ((d.funnel as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const connectors = ((d.connectors as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const rejections = (d.top_rejections || {}) as Record<string, number>;
  const daily = (d.daily || {}) as Record<string, unknown>;
  const answer = String(d.vansh_ready_answer || "NO");
  const yieldItems = ((yields.data?.items || d.yields || []) as Array<Record<string, unknown>>) || [];
  const latestReport = (((reports.data as { items?: Array<Record<string, unknown>> })?.items || [])[0] ||
    {}) as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>rdap-v1</SectionLabel>
          <h1 className="text-3xl font-semibold tracking-tight">Revenue Data Acquisition</h1>
          <p className="text-sm text-muted-foreground">
            How many new companies entered the Revenue Ready pipeline today?
          </p>
        </div>
        <Badge className={answer === "YES" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}>
          Vansh-ready: {answer}
        </Badge>
      </div>

      {dash.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Verified Companies" value={d.verified_companies} />
        <Metric label="Business Emails" value={d.business_emails} />
        <Metric label="Decision Makers" value={d.decision_makers} />
        <Metric label="Sales Ready" value={d.sales_ready} warn={!d.sales_ready} />
        <Metric label="Revenue Ready" value={d.revenue_ready} warn={!d.revenue_ready} />
        <Metric label="Official Websites" value={d.official_websites} />
        <Metric label="Recovery Pending" value={d.recovery_pending ?? recovery.data?.count} />
        <Metric label="New RR Today" value={daily.new_revenue_ready} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Revenue Funnel</CardTitle>
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
            <CardTitle className="text-base">Connector Leaderboard</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {connectors.length === 0 && <p className="text-muted-foreground">No connector scores yet.</p>}
            {connectors.slice(0, 12).map((c) => (
              <div key={String(c.connector)} className="flex justify-between border-b py-2">
                <span>
                  {String(c.connector)} · yield {formatScore(Number(c.revenue_yield || 0), 1)}% · email{" "}
                  {Number(c.business_emails || 0)} · dm {Number(c.decision_makers || 0)}
                </span>
                <Badge variant="outline">{String(c.grade || c.status || "—")}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Rejection Reasons</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.keys(rejections).length === 0 && <p className="text-muted-foreground">No rejections logged.</p>}
            {Object.entries(rejections)
              .slice(0, 10)
              .map(([reason, count]) => (
                <div key={reason} className="flex justify-between border-b py-2">
                  <span>{reason}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Revenue Yield</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {yieldItems.length === 0 && <p className="text-muted-foreground">Yield empty until expand runs.</p>}
            {yieldItems.slice(0, 10).map((y) => (
              <div key={String(y.connector)} className="flex justify-between border-b py-2">
                <span>
                  {String(y.connector)} · {Number(y.signals || 0)}→{Number(y.revenue_ready || 0)} RR
                </span>
                <Badge variant="secondary">{formatScore(Number(y.yield_pct || 0), 1)}%</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recovery Queue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {((recovery.data?.items as Array<Record<string, unknown>>) || []).slice(0, 10).map((item) => (
              <div key={String(item.id)} className="flex justify-between border-b py-2">
                <span>{String(item.reason)}</span>
                <Badge variant="outline">{String(item.domain || item.signal_id || "").slice(0, 28)}</Badge>
              </div>
            ))}
            {!recovery.data?.count && <p className="text-muted-foreground">Queue empty or not loaded.</p>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Daily Executive Report</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="New Companies" value={daily.new_companies} />
          <Metric label="New Emails" value={daily.new_emails} />
          <Metric label="New DMs" value={daily.new_decision_makers} />
          <Metric label="New Sales Ready" value={daily.new_sales_ready} />
          <Metric label="New Revenue Ready" value={daily.new_revenue_ready} />
          {latestReport.id ? (
            <p className="sm:col-span-2 lg:col-span-5 text-muted-foreground">
              Latest report {String(latestReport.id).slice(0, 8)}… · Vansh-ready{" "}
              {String(latestReport.vansh_ready_answer || "—")} · RR {String(latestReport.revenue_ready ?? "—")}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
