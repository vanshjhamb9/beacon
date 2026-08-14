"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

export function OfcRevenueDashboard() {
  const dash = useQuery({
    queryKey: ["ofc-revenue-dashboard"],
    queryFn: () => beaconApi.ofcRevenueDashboard(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return (
      <ErrorState title="OFC Revenue Dashboard unavailable" description="API /first-customer/revenue-dashboard failed." />
    );
  }
  if (dash.isLoading) return <Skeleton className="h-48 w-full" />;

  const funnel = ((dash.data?.funnel as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const rates = (dash.data?.conversion_rates || {}) as Record<string, number>;
  const today = (dash.data?.today_action || {}) as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <SectionLabel>OFC v2</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Revenue Dashboard</h1>
        <p className="text-sm text-muted-foreground">Live funnel and conversion rates toward the first paying customer.</p>
      </div>

      <Card className="border-emerald-700/40 bg-emerald-950/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Do this today</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p className="font-medium">{String(today.action || "—")}</p>
          <p className="text-muted-foreground">{String(today.why || "")}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Funnel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {funnel.map((step, idx) => (
            <div key={String(step.name)} className="flex items-center gap-3 text-sm">
              <div className="w-28 text-muted-foreground">{String(step.name)}</div>
              <div className="h-2 flex-1 rounded bg-muted">
                <div
                  className="h-2 rounded bg-emerald-600"
                  style={{ width: `${Math.min(100, Number(step.count || 0) * 10)}%` }}
                />
              </div>
              <div className="w-10 text-right font-medium">{String(step.count ?? 0)}</div>
              {idx < funnel.length - 1 ? <span className="text-muted-foreground">↓</span> : null}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Reply rate" value={`${formatScore(rates.reply_rate || 0, 1)}%`} />
        <Metric label="Meeting rate" value={`${formatScore(rates.meeting_rate || 0, 1)}%`} />
        <Metric label="Win rate" value={`${formatScore(rates.win_rate || 0, 1)}%`} />
        <Metric label="Contact rate" value={`${formatScore(rates.contact_rate || 0, 1)}%`} />
        <Metric label="Proposal rate" value={`${formatScore(rates.proposal_rate || 0, 1)}%`} />
        <Metric label="Pipeline value" value={`$${formatScore(Number(dash.data?.pipeline_value || 0), 0)}`} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}
