"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function RdiQaWorkspace() {
  const qa = useQuery({
    queryKey: ["rdi-qa"],
    queryFn: () => beaconApi.rdiQa(),
    refetchInterval: 60_000,
  });
  const dashboard = useQuery({
    queryKey: ["rdi-dashboard"],
    queryFn: () => beaconApi.rdiDashboard(),
    refetchInterval: 60_000,
  });
  const queue = useQuery({
    queryKey: ["rdi-queue"],
    queryFn: () => beaconApi.rdiQueue({ limit: 40 }),
    refetchInterval: 60_000,
  });
  const founder = useQuery({
    queryKey: ["rdi-founder-queue"],
    queryFn: () => beaconApi.rdiFounderQueue(40),
    refetchInterval: 60_000,
  });

  if (qa.isLoading) return <Skeleton className="h-72 w-full" />;
  if (qa.isError) {
    return <ErrorState description="RDI QA metrics unavailable." onRetry={() => void qa.refetch()} />;
  }

  const m = qa.data ?? {};
  const d = dashboard.data ?? {};
  const queueItems = queue.data?.items ?? [];
  const founderItems = founder.data?.items ?? [];

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Internal QA</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Data Recovery</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Engineering recovery coverage — identity, website, contacts, sales-ready, and fake elimination.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Identity %" value={`${m.identity_percent ?? 0}%`} />
        <Metric title="Website %" value={`${m.website_percent ?? 0}%`} />
        <Metric title="Intent %" value={`${m.intent_percent ?? 0}%`} />
        <Metric title="Contacts %" value={`${m.contacts_percent ?? 0}%`} />
        <Metric title="Sales Ready %" value={`${m.sales_ready_percent ?? 0}%`} />
        <Metric title="Recovery %" value={`${m.recovery_percent ?? 0}%`} />
        <Metric title="Fake companies" value={String(m.fake_companies ?? d.fake_companies ?? 0)} />
        <Metric title="Unknown fields" value={String(m.unknown_fields ?? 0)} />
        <Metric title="Recovery failures" value={String(m.recovery_failures ?? 0)} />
        <Metric title="Duplicate %" value={`${m.duplicate_percent ?? 0}%`} />
        <Metric title="Founder queue" value={String(m.founder_queue ?? d.founder_queue ?? 0)} />
        <Metric title="Recovery success" value={String(m.recovery_success ?? 0)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recovery queue</CardTitle>
            <CardDescription>Companies moving through identity → sales ready.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {queueItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recovery queue rows yet.</p>
            ) : (
              queueItems.slice(0, 12).map((item, idx) => (
                <div
                  key={`${String(item.company_id)}-${idx}`}
                  className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm"
                >
                  <span className="truncate pr-3">{String(item.company_name ?? item.company_id)}</span>
                  <div className="flex gap-2">
                    <Badge variant="outline">{String(item.stage)}</Badge>
                    <Badge variant="outline">{String(item.progress_percent ?? 0)}%</Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Founder queue preview</CardTitle>
            <CardDescription>Sales-ready dossiers with verified contact paths.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {founderItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No founder-ready companies yet.</p>
            ) : (
              founderItems.slice(0, 12).map((item, idx) => (
                <div
                  key={`${String(item.company_id)}-${idx}`}
                  className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm"
                >
                  <span className="truncate pr-3">{String(item.company_name ?? item.company_id)}</span>
                  <div className="flex gap-2">
                    <Badge variant="outline">{String(item.stars ?? 0)}★</Badge>
                    <Badge variant="outline">{String(item.estimated_deal ?? "—")}</Badge>
                  </div>
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
