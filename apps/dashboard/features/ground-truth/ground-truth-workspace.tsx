"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function GroundTruthWorkspace() {
  const dashboard = useQuery({
    queryKey: ["gt-dashboard"],
    queryFn: () => beaconApi.gtDashboard(),
    refetchInterval: 60_000,
  });
  const queue = useQuery({
    queryKey: ["gt-founder-queue"],
    queryFn: () => beaconApi.gtFounderQueue(),
    refetchInterval: 60_000,
  });
  const report = useQuery({
    queryKey: ["gt-daily-report"],
    queryFn: () => beaconApi.gtDailyReport(),
    refetchInterval: 120_000,
  });
  const acceptance = useQuery({
    queryKey: ["gt-acceptance"],
    queryFn: () => beaconApi.gtAcceptance(),
    refetchInterval: 60_000,
  });

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Ground Truth unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  const funnel = (dashboard.data?.funnel ?? {}) as Record<string, unknown>;
  const byReason = (funnel.by_rejection_reason ?? {}) as Record<string, number>;
  const items = queue.data?.items ?? [];
  const r = report.data ?? {};
  const a = acceptance.data ?? {};

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Stop features. Improve one KPI.</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Ground Truth</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          {String(dashboard.data?.question ?? "Would Vansh confidently send an email to this company today?")}
        </p>
        <Badge variant="outline">Production send locked</Badge>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Quality funnel</CardTitle>
          <CardDescription>Where companies die — so we know what to fix.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <FunnelLine label="Companies" value={funnel.companies} />
          <FunnelLine label="Rejected" value={funnel.rejected} />
          <FunnelLine label="Fake" value={funnel.fake} />
          <FunnelLine label="Missing website" value={funnel.missing_website} />
          <FunnelLine label="Missing evidence" value={funnel.missing_evidence} />
          <FunnelLine label="Sales ready" value={funnel.sales_ready} />
          <FunnelLine label="Enterprise ready" value={funnel.enterprise_ready} />
          {Object.keys(byReason).length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="font-medium">Rejection reasons</p>
              {Object.entries(byReason).map(([reason, count]) => (
                <div key={reason} className="flex justify-between text-muted-foreground">
                  <span>{reason}</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Founder Queue — Top 10</CardTitle>
            <CardDescription>Who should I contact today?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No unlocked companies yet.</p>
            ) : (
              items.map((item, idx) => (
                <div key={`${String(item.company_id)}-${idx}`} className="rounded-lg border border-border/60 p-3 text-sm">
                  <div className="flex justify-between gap-2">
                    <span className="font-medium">{String(item.company)}</span>
                    <Badge variant="outline">{String(item.estimated_deal)}</Badge>
                  </div>
                  <p className="mt-1 text-muted-foreground">{String(item.reason)}</p>
                  <p className="text-muted-foreground">
                    {String(item.decision_maker)} · {String(item.email)} · {String(item.service)}
                  </p>
                  <p className="mt-1">{String(item.next_step)}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Morning report</CardTitle>
            <CardDescription>Yesterday → today&apos;s best.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm sm:grid-cols-2">
            <Metric label="Collected" value={r.collected} />
            <Metric label="Rejected" value={r.rejected} />
            <Metric label="Sales Ready" value={r.sales_ready} />
            <Metric label="Emails recovered" value={r.emails_recovered} />
            <Metric label="Phones recovered" value={r.phones_recovered} />
            <Metric label="Fake removed" value={r.fake_removed} />
            <Metric label="Avg quality" value={r.average_quality} />
            <Metric label="Best company" value={r.todays_best_company} />
            <div className="sm:col-span-2 text-muted-foreground">
              Potential: {String(r.todays_best_potential)} · Missing: {String(r.todays_best_missing)}
            </div>
            {(a.failures as string[] | undefined)?.length ? (
              <div className="sm:col-span-2 space-y-1">
                <p className="font-medium">Acceptance still locked</p>
                {(a.failures as string[]).slice(0, 6).map((f) => (
                  <p key={f} className="text-muted-foreground">
                    {f}
                  </p>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function FunnelLine({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="flex justify-between border-b border-border/40 py-1">
      <span>{label}</span>
      <span className="font-medium">{String(value ?? 0)}</span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <p className="text-muted-foreground">{label}</p>
      <p className="text-lg font-medium">{String(value ?? "—")}</p>
    </div>
  );
}
