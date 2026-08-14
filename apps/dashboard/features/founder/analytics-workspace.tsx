"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatMoney, funnelCount } from "@/lib/lead";

export function AnalyticsWorkspace() {
  const revenue = useQuery({
    queryKey: ["ofc-revenue-dashboard"],
    queryFn: () => beaconApi.ofcRevenueDashboard(),
  });
  const learning = useQuery({
    queryKey: ["ofc-learning"],
    queryFn: () => beaconApi.ofcLearning(),
  });
  const rrp = useQuery({
    queryKey: ["rrp-dashboard"],
    queryFn: () => beaconApi.rrpDashboard(),
  });
  const roc = useQuery({
    queryKey: ["revenue-operations-dashboard"],
    queryFn: () => beaconApi.rocDashboard(),
  });

  const metrics = useMemo(() => {
    const funnel = (revenue.data?.funnel as Array<Record<string, unknown>>) || [];
    const rates = (revenue.data?.conversion_rates as Record<string, unknown>) || {};
    const rrpKpis = (rrp.data?.kpis as Record<string, unknown>) || {};
    const ready = Number(rrpKpis.revenue_ready ?? funnelCount(funnel, "Revenue Ready"));
    const pipeline = Number(revenue.data?.pipeline_value ?? roc.data?.pipeline_value ?? 0);
    const replyRate = Math.round(Number(rates.reply_rate ?? 0) * (Number(rates.reply_rate) <= 1 ? 100 : 1));
    const meetingRate = Math.round(Number(rates.meeting_rate ?? 0) * (Number(rates.meeting_rate) <= 1 ? 100 : 1));
    const conversion = Math.round(Number(rates.win_rate ?? rates.overall_win_rate ?? 0) * (Number(rates.win_rate ?? rates.overall_win_rate ?? 0) <= 1 ? 100 : 1));

    return [
      { label: "Revenue Ready", value: String(ready) },
      { label: "Reply Rate", value: `${replyRate}%` },
      { label: "Meeting Rate", value: `${meetingRate}%` },
      { label: "Conversion", value: `${conversion}%` },
      { label: "Pipeline", value: formatMoney(pipeline) },
    ];
  }, [revenue.data, rrp.data, roc.data]);

  const pack = (learning.data?.learning as Record<string, unknown>) || {};
  const industries = ((pack.best_industries as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const services = ((pack.best_services as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const whyNow = ((pack.best_why_now_triggers as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const funnel = ((revenue.data?.funnel as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;

  if (revenue.isLoading || learning.isLoading) return <Skeleton className="h-72 w-full" />;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">One page. The numbers that matter.</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Analytics</h1>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardContent className="px-4 py-4">
              <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{metric.label}</p>
              <p className="mt-1 font-display text-2xl font-semibold">{metric.value}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Funnel</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-4 lg:grid-cols-7">
          {funnel.map((row) => (
            <div key={String(row.name)} className="rounded-lg border border-border/50 px-3 py-2">
              <p className="text-[11px] text-muted-foreground">{String(row.name)}</p>
              <p className="font-display text-xl font-semibold">{String(row.count ?? 0)}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <ListCard title="Top Industries" rows={industries} />
        <ListCard title="Top Services" rows={services} />
        <ListCard title="Top Why Now" rows={whyNow} />
      </div>
    </div>
  );
}

function ListCard({ title, rows }: { title: string; rows: Array<Record<string, unknown>> }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {rows.length === 0 ? (
          <p className="text-muted-foreground">Not enough data yet.</p>
        ) : (
          rows.slice(0, 6).map((row, idx) => (
            <div key={idx} className="flex items-start justify-between gap-2">
              <span className="leading-snug">{String(row.label || row.name || row.value || "—")}</span>
              <span className="shrink-0 text-muted-foreground">{String(row.count ?? row.score ?? "")}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
