"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function TrustDashboardWorkspace() {
  const trust = useQuery({
    queryKey: ["ph-trust"],
    queryFn: () => beaconApi.phTrust(),
    refetchInterval: 60_000,
  });
  const duplicates = useQuery({
    queryKey: ["ph-duplicates"],
    queryFn: () => beaconApi.phDuplicates(),
  });
  const signals = useQuery({
    queryKey: ["ph-health-signals"],
    queryFn: () => beaconApi.phHealthSignals(),
    refetchInterval: 30_000,
  });

  if (trust.isLoading) return <Skeleton className="h-72 w-full" />;
  if (trust.isError) {
    return <ErrorState description="Trust metrics unavailable." onRetry={() => void trust.refetch()} />;
  }

  const m = trust.data ?? {};
  const collectors = (m.collector_health ?? {}) as Record<string, Record<string, unknown>>;
  const conversion = (m.daily_pipeline_conversion ?? {}) as Record<string, number>;

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Internal QA</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Trust Dashboard</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Live pipeline quality — whether today&apos;s companies are trustworthy enough to contact.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Companies collected" value={m.companies_collected} />
        <Metric title="Qualified (website)" value={m.qualified} />
        <Metric title="Rejected" value={m.rejected} />
        <Metric title="Merged" value={m.merged} />
        <Metric title="Duplicate %" value={`${m.duplicate_percent ?? 0}%`} />
        <Metric title="Verified websites %" value={`${m.verified_websites_percent ?? 0}%`} />
        <Metric title="Verified emails %" value={`${m.verified_emails_percent ?? 0}%`} />
        <Metric title="Verified phones %" value={`${m.verified_phones_percent ?? 0}%`} />
        <Metric title="Decision makers %" value={`${m.decision_makers_percent ?? 0}%`} />
        <Metric title="Avg confidence" value={m.average_confidence} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Collector health</CardTitle>
            <CardDescription>Source status from live SourceHealth rows.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.keys(collectors).length === 0 ? (
              <p className="text-sm text-muted-foreground">No collector health rows yet.</p>
            ) : (
              Object.entries(collectors).map(([source, row]) => (
                <div key={source} className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm">
                  <span>{source}</span>
                  <div className="flex gap-2">
                    <Badge variant="outline">{String(row.status)}</Badge>
                    <Badge variant="outline">failures {String(row.failures ?? 0)}</Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Daily pipeline conversion</CardTitle>
            <CardDescription>Counts feeding trust percentages.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            {Object.entries(conversion).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span>{k}</span>
                <span className="tabular-nums text-foreground">{v}</span>
              </div>
            ))}
            <div className="flex justify-between border-t border-border/60 pt-2">
              <span>Duplicate plans</span>
              <span className="tabular-nums text-foreground">{duplicates.data?.total ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span>Health telemetry</span>
              <Badge variant="outline">{signals.data?.hardcoded === false ? "live" : "unknown"}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: unknown }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="font-display text-2xl tabular-nums">{String(value ?? "—")}</CardTitle>
      </CardHeader>
    </Card>
  );
}
