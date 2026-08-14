"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-lg border border-border/60 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{String(value ?? "—")}</p>
    </div>
  );
}

export function IdentityGraphWorkspace() {
  const dash = useQuery({
    queryKey: ["igf-dashboard"],
    queryFn: () => beaconApi.igfDashboard(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return <ErrorState title="Identity Graph unavailable" description="API /identity-graph/dashboard failed." />;
  }

  const d = dash.data || {};
  const topSources = (d.top_sources || {}) as Record<string, number>;
  const topFailures = (d.top_failures || {}) as Record<string, number>;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <SectionLabel>igf-v1</SectionLabel>
        <h1 className="text-3xl font-semibold tracking-tight">Identity Graph</h1>
        <p className="text-sm text-muted-foreground">
          A company does not exist until Identity Graph admits it. Signals stay signals.
        </p>
      </div>

      {dash.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Signals" value={d.signals} />
        <Metric label="Identity Candidates" value={d.candidates} />
        <Metric label="Official Websites" value={d.official_websites} />
        <Metric label="Verified Companies" value={d.verified_companies ?? d.active_canonical} />
        <Metric label="Active Canonical" value={d.active_canonical} />
        <Metric label="Pending" value={d.pending_canonical} />
        <Metric label="Identity Precision" value={`${formatScore(Number(d.identity_precision || 0), 1)}%`} />
        <Metric label="RR Downstream" value={d.revenue_ready_downstream} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Identity Sources</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.keys(topSources).length === 0 && <p className="text-muted-foreground">Run rebuild to populate.</p>}
            {Object.entries(topSources).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b py-2">
                <span>{k}</span>
                <Badge variant="outline">{v}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Failure Reasons</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.keys(topFailures).length === 0 && <p className="text-muted-foreground">No failures recorded yet.</p>}
            {Object.entries(topFailures).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b py-2">
                <span className="pr-4">{k}</span>
                <Badge variant="outline">{v}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
