"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function MorningBriefWorkspace() {
  const queryClient = useQueryClient();

  const brief = useQuery({
    queryKey: ["asa-morning-brief"],
    queryFn: () => beaconApi.asaMorningBrief(true),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.asaMorningBriefRefresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["asa-morning-brief"] });
    },
  });

  if (brief.isLoading) return <Skeleton className="h-72 w-full" />;
  if (brief.isError) {
    return <ErrorState description="Morning brief unavailable." onRetry={() => void brief.refetch()} />;
  }

  const data = brief.data;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Autonomous Sales Agent</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Morning Brief</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Priorities, meetings, expected replies, high-risk deals, attention list, revenue forecast, and follow-ups
            due — nothing more.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link href="/founder-work-queue">Work Queue</Link>
          </Button>
          <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            Refresh brief
          </Button>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Today&apos;s priorities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(data?.priorities ?? []).length === 0 ? (
              <EmptyState title="Clear morning" description="No founder priorities queued." />
            ) : (
              (data?.priorities ?? []).map((p) => (
                <div key={p} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                  {p}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Revenue forecast</CardTitle>
            <CardDescription>Pipeline-weighted estimate</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="font-display text-3xl font-semibold">${(data?.revenue_forecast ?? 0).toLocaleString()}</p>
          </CardContent>
        </Card>

        <BriefList title="Expected meetings" rows={data?.expected_meetings ?? []} empty="No meetings today." />
        <BriefList title="Expected replies" rows={data?.expected_replies ?? []} empty="No high-intent replies." />
        <BriefList title="High-risk deals" rows={data?.high_risk_deals ?? []} empty="No high-risk deals." />
        <BriefList
          title="Companies requiring attention"
          rows={data?.companies_requiring_attention ?? []}
          empty="No attention flags."
        />
        <BriefList title="Follow-ups due" rows={data?.follow_ups_due ?? []} empty="No follow-ups due." />
      </div>
    </div>
  );
}

function BriefList({
  title,
  rows,
  empty,
}: {
  title: string;
  rows: Array<Record<string, unknown>>;
  empty: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{rows.length} items</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">{empty}</p>
        ) : (
          rows.slice(0, 6).map((row, idx) => (
            <div key={`${title}-${idx}`} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              <p className="font-medium">{String(row.company_name ?? row.hint ?? "Item")}</p>
              <p className="text-xs text-muted-foreground">
                {String(row.summary ?? row.reason ?? row.hint ?? row.channel ?? "")}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
