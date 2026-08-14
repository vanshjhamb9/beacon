"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function RqpQaWorkspace() {
  const kpi = useQuery({
    queryKey: ["rqp-kpi"],
    queryFn: () => beaconApi.rqpKpi(),
    refetchInterval: 60_000,
  });
  const acceptance = useQuery({
    queryKey: ["rqp-acceptance"],
    queryFn: () => beaconApi.rqpAcceptance(),
    refetchInterval: 60_000,
  });
  const dashboard = useQuery({
    queryKey: ["rqp-dashboard"],
    queryFn: () => beaconApi.rqpDashboard(),
    refetchInterval: 60_000,
  });
  const founder = useQuery({
    queryKey: ["rqp-founder-queue"],
    queryFn: () => beaconApi.rqpFounderQueue(40),
    refetchInterval: 60_000,
  });

  if (kpi.isLoading) return <Skeleton className="h-72 w-full" />;
  if (kpi.isError) {
    return <ErrorState description="RQP KPI unavailable." onRetry={() => void kpi.refetch()} />;
  }

  const m = kpi.data ?? {};
  const a = acceptance.data ?? {};
  const d = dashboard.data ?? {};
  const founderItems = founder.data?.items ?? [];
  const unlocked = Boolean(a.production_unlocked);

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Internal QA</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Quality Recovery</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Binary revenue gate — REJECTED or SALES READY. Production send stays locked until acceptance passes.
        </p>
        <Badge variant={unlocked ? "default" : "outline"}>
          {unlocked ? "Production unlocked" : "Production send disabled"}
        </Badge>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Collected today" value={m.collected_today ?? d.total_snapshots} />
        <Metric title="Rejected today" value={m.rejected_today ?? d.rejected} />
        <Metric title="Recovered today" value={m.recovered_today} />
        <Metric title="Identity %" value={`${m.identity_percent ?? 0}%`} />
        <Metric title="Website %" value={`${m.website_percent ?? 0}%`} />
        <Metric title="Contacts %" value={`${m.contacts_percent ?? 0}%`} />
        <Metric title="Decision makers %" value={`${m.decision_makers_percent ?? 0}%`} />
        <Metric title="Sales Ready %" value={`${m.sales_ready_percent ?? 0}%`} />
        <Metric title="Enterprise %" value={`${m.enterprise_percent ?? 0}%`} />
        <Metric title="Avg confidence" value={m.average_confidence ?? 0} />
        <Metric title="Duplicates" value={m.duplicates ?? 0} />
        <Metric title="Fake companies" value={m.fake_companies ?? 0} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Acceptance gate</CardTitle>
            <CardDescription>Production unlock criteria (Rule 12).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(a.failures as string[] | undefined)?.length ? (
              (a.failures as string[]).map((f) => (
                <div key={f} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                  {f}
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                {unlocked ? "All acceptance criteria met." : "No failure list yet — run KPI evaluation."}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Founder queue (Sales Ready only)</CardTitle>
            <CardDescription>Hidden unless CONTACT / SALES / ENTERPRISE READY.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {founderItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No sales-ready companies yet.</p>
            ) : (
              founderItems.slice(0, 12).map((item, idx) => (
                <div
                  key={`${String(item.company_id)}-${idx}`}
                  className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm"
                >
                  <span className="truncate pr-3">{String(item.company_name ?? item.company_id)}</span>
                  <Badge variant="outline">{item.sales_ready_badge ? "SALES READY" : String(item.verdict)}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string | number | undefined }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl">{value ?? "—"}</CardTitle>
      </CardHeader>
    </Card>
  );
}
