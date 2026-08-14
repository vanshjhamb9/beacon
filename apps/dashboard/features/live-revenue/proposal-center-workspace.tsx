"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function ProposalCenterWorkspace() {
  const proposals = useQuery({
    queryKey: ["lre-proposals"],
    queryFn: () => beaconApi.liveRevenueProposals(),
  });
  const dash = useQuery({
    queryKey: ["lre-dashboard"],
    queryFn: () => beaconApi.liveRevenueDashboard(),
  });

  if (proposals.isLoading || dash.isLoading) return <Skeleton className="h-72 w-full" />;
  if (proposals.isError) {
    return <ErrorState description="Proposal center unavailable." onRetry={() => void proposals.refetch()} />;
  }

  const rows = proposals.data?.proposals ?? [];

  return (
    <div className="space-y-6">
      <header>
        <SectionLabel>Live Revenue Execution</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Proposal Center</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Versioned proposal packages with tracking IDs. Opens and downloads update from LRE tracking events.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Awaiting approval" value={String(dash.data?.awaiting_approval ?? 0)} />
        <Stat label="Proposals" value={String(dash.data?.proposals ?? rows.length)} />
        <Stat label="Opens tracked" value={String(dash.data?.opens ?? 0)} />
        <Stat label="Clicks tracked" value={String(dash.data?.clicks ?? 0)} />
      </div>

      {rows.length === 0 ? (
        <EmptyState title="No proposals yet" description="Refresh LRE for a company after meeting stage to generate a proposal pack." />
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <Card key={String(row.id)}>
              <CardHeader className="flex flex-row items-start justify-between gap-3">
                <div>
                  <CardTitle className="font-display text-lg">{String(row.title)}</CardTitle>
                  <CardDescription>
                    Version {String(row.version)} · {String(row.pricing)}
                  </CardDescription>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge>{String(row.status)}</Badge>
                  <Badge variant="outline">Opens {String(row.opens ?? 0)}</Badge>
                  <Badge variant="outline">Downloads {String(row.downloads ?? 0)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Tracking ID: {String(row.tracking_id)}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/40 px-3 py-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-2xl font-semibold">{value}</p>
    </div>
  );
}
