"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function OfcLearningDashboard() {
  const learning = useQuery({
    queryKey: ["ofc-learning"],
    queryFn: () => beaconApi.ofcLearning(),
    refetchInterval: 60_000,
  });

  if (learning.isError) {
    return <ErrorState title="Learning Dashboard unavailable" description="API /first-customer/learning failed." />;
  }
  if (learning.isLoading) return <Skeleton className="h-48 w-full" />;

  const data = ((learning.data?.learning || {}) as Record<string, unknown>) || {};

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <SectionLabel>OFC v2 · Analytics only</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Learning Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Patterns from outreach outcomes. Never auto-changes scoring or readiness rules.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Bucket title="Best industries" rows={asRows(data.best_industries)} />
        <Bucket title="Best services" rows={asRows(data.best_services)} />
        <Bucket title="Best Why Now triggers" rows={asRows(data.best_why_now_triggers)} />
        <Bucket title="Best decision maker roles" rows={asRows(data.best_decision_maker_roles)} />
        <Bucket title="Best company sizes" rows={asRows(data.best_company_sizes)} />
        <Bucket title="Worst rejection reasons" rows={asRows(data.worst_rejection_reasons)} />
      </div>
    </div>
  );
}

function asRows(raw: unknown): Array<{ label: string; count: number }> {
  if (!Array.isArray(raw)) return [];
  return raw.map((r) => ({
    label: String((r as { label?: string }).label || "—"),
    count: Number((r as { count?: number }).count || 0),
  }));
}

function Bucket({ title, rows }: { title: string; rows: Array<{ label: string; count: number }> }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {rows.length === 0 && <p className="text-muted-foreground">No data yet — log objections and outcomes.</p>}
        {rows.map((row) => (
          <div key={`${title}-${row.label}`} className="flex justify-between gap-2">
            <span className="truncate">{row.label}</span>
            <span className="text-muted-foreground">{row.count}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
