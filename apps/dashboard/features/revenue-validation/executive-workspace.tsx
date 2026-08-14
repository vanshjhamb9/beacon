"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

export function ExecutiveWorkspace() {
  const dash = useQuery({
    queryKey: ["clr-executive"],
    queryFn: () => beaconApi.clrExecutive(),
    refetchInterval: 60_000,
  });

  if (dash.isError) {
    return <ErrorState title="Executive Dashboard unavailable" description="API /revenue-validation/executive failed." />;
  }
  if (dash.isLoading) return <Skeleton className="h-40 w-full" />;

  const d = dash.data || {};
  const metrics: Array<[string, string]> = [
    ["Revenue Ready", String(d.revenue_ready ?? 0)],
    ["Contacted", String(d.companies_contacted ?? 0)],
    ["Replies", String(d.replies ?? 0)],
    ["Meetings", String(d.meetings ?? 0)],
    ["Proposals", String(d.proposals ?? 0)],
    ["Negotiations", String(d.negotiations ?? 0)],
    ["Won", String(d.won ?? 0)],
    ["Lost", String(d.lost ?? 0)],
    ["Revenue", `$${formatScore(Number(d.revenue || 0), 0)}`],
    ["Pipeline", `$${formatScore(Number(d.pipeline_value || 0), 0)}`],
    ["Reply Rate", `${formatScore(Number(d.reply_rate || 0), 1)}%`],
    ["Meeting Rate", `${formatScore(Number(d.meeting_rate || 0), 1)}%`],
    ["Proposal Rate", `${formatScore(Number(d.proposal_rate || 0), 1)}%`],
    ["Win Rate", `${formatScore(Number(d.win_rate || 0), 1)}%`],
    ["Avg Deal", `$${formatScore(Number(d.average_deal_size || 0), 0)}`],
    ["Avg Cycle", String(d.average_sales_cycle ?? "—")],
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <SectionLabel>CEO · CLR v1</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Executive</h1>
        <p className="text-sm text-muted-foreground">Revenue outcomes only. No clutter.</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {metrics.map(([label, value]) => (
          <Card key={label}>
            <CardContent className="py-4">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-xl font-semibold tracking-tight">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
