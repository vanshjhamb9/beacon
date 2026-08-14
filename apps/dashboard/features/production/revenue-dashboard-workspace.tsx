"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function RevenueDashboardWorkspace() {
  const dash = useQuery({
    queryKey: ["production-revenue"],
    queryFn: () => beaconApi.productionRevenue(),
    refetchInterval: 30_000,
  });

  if (dash.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dash.isError) {
    return <ErrorState description="Revenue dashboard unavailable." onRetry={() => void dash.refetch()} />;
  }

  const revenue = (dash.data?.revenue ?? {}) as Record<string, unknown>;
  const board = (dash.data?.founder_board ?? {}) as Record<string, unknown>;
  const doNow = (board.do_now as string[] | undefined) ?? [];
  const weekly = (dash.data?.weekly_report ?? {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Business Health</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Dashboard</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Understand revenue health in under 10 seconds — no vanity charts.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/production-health">Production Health</Link>
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Revenue Today" value={money(Number(revenue.revenue_today ?? 0))} />
        <Stat label="Pipeline Value" value={money(Number(revenue.pipeline_value ?? 0))} />
        <Stat label="Revenue Closed" value={money(Number(revenue.revenue_closed ?? 0))} />
        <Stat label="Forecast" value={money(Number(revenue.forecast ?? 0))} />
        <Stat label="Qualified" value={String(revenue.qualified_companies ?? 0)} />
        <Stat label="Sales Ready" value={String(revenue.sales_ready ?? 0)} />
        <Stat label="Campaigns" value={String(revenue.campaigns ?? 0)} />
        <Stat label="Replies" value={String(revenue.replies ?? 0)} />
        <Stat label="Meetings" value={String(revenue.meetings ?? 0)} />
        <Stat label="Proposals" value={String(revenue.proposals ?? 0)} />
        <Stat label="Win Rate" value={`${Number(revenue.win_rate ?? 0).toFixed(1)}%`} />
        <Stat label="Avg Deal" value={money(Number(revenue.average_deal_size ?? 0))} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>What should I do now?</CardTitle>
            <CardDescription>Founder action board from live queues.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {doNow.length === 0 ? (
              <EmptyState title="No urgent actions" description="Check Approval Center for pending campaigns." />
            ) : (
              doNow.map((item) => (
                <div key={item} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                  {item}
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Weekly Snapshot</CardTitle>
            <CardDescription>Auto-composed revenue report excerpt.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <div className="flex justify-between"><span>Companies found</span><span>{String(weekly.companies_found ?? 0)}</span></div>
            <div className="flex justify-between"><span>Sales ready</span><span>{String(weekly.sales_ready ?? 0)}</span></div>
            <div className="flex justify-between"><span>Emails</span><span>{String(weekly.emails ?? 0)}</span></div>
            <div className="flex justify-between"><span>Lost deals</span><span>{String(weekly.lost_deals ?? 0)}</span></div>
            <div className="pt-2">
              {(weekly.top_industries as string[] | undefined)?.slice(0, 3).map((i) => (
                <Badge key={i} className="mr-2" variant="outline">{i}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/40 px-3 py-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-xl font-semibold">{value}</p>
    </div>
  );
}

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}
