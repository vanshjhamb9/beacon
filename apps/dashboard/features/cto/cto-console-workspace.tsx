"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

function Metric({ label, value, warn }: { label: string; value: unknown; warn?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${warn ? "border-red-500/60 bg-red-500/5" : "border-border/60"}`}>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{String(value ?? "—")}</p>
    </div>
  );
}

/** CTO console — business impact KPIs only (ICE / REV). */
export function CtoConsoleWorkspace() {
  const ice = useQuery({ queryKey: ["cto-ice"], queryFn: () => beaconApi.iceDashboard(), refetchInterval: 60_000 });
  const acceptance = useQuery({
    queryKey: ["cto-acceptance"],
    queryFn: () => beaconApi.revAcceptance(),
    refetchInterval: 60_000,
  });
  const fq = useQuery({ queryKey: ["cto-fq"], queryFn: () => beaconApi.revFounderQueue(), refetchInterval: 60_000 });

  if (ice.isError && acceptance.isError) {
    return <ErrorState title="CTO console unavailable" description="Identity coverage / revenue APIs failed." />;
  }

  const gate = (acceptance.data || {}) as Record<string, unknown>;
  const locked = !gate.production_unlocked;
  const impact = ((ice.data?.business_impact as Record<string, unknown>) || {}) as Record<string, unknown>;
  const answer = String(ice.data?.vansh_ready_answer || "NO");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>Operation First Client</SectionLabel>
          <h1 className="text-3xl font-semibold tracking-tight">CTO Console</h1>
          <p className="text-sm text-muted-foreground">Business impact only — Revenue Ready companies you can contact.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge className={answer === "YES" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"}>
            Vansh-ready {answer}
          </Badge>
          <Badge className={locked ? "bg-red-600 text-white hover:bg-red-600" : "bg-emerald-600 text-white"}>
            {locked ? "PRODUCTION LOCKED" : "PRODUCTION UNLOCKED"}
          </Badge>
        </div>
      </div>

      {(ice.isLoading || acceptance.isLoading) && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Metric label="Revenue Ready" value={Number(ice.data?.revenue_ready ?? gate.revenue_ready_count ?? 0)} warn />
        <Metric label="Emails Ready" value={Number(ice.data?.business_emails ?? gate.verified_emails ?? 0)} />
        <Metric label="Decision Makers Ready" value={Number(ice.data?.decision_makers ?? gate.named_decision_makers ?? 0)} />
        <Metric label="Meetings Possible" value={Number(impact.meetings_possible ?? 0)} />
        <Metric label="Pipeline Value" value={String(impact.pipeline_value ?? "$0")} />
        <Metric label="Revenue Yield %" value={String(impact.revenue_yield ?? 0)} />
        <Metric label="Verified Companies" value={Number(ice.data?.verified_companies ?? 0)} />
        <Metric label="Founder Queue" value={Number(fq.data?.count ?? 0)} />
        <Metric label="Production" value={locked ? "LOCKED" : "READY"} warn={locked} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">North star</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          If Vansh opens Beacon tomorrow, are there ≥20 real companies with verified website, business email, named
          decision maker, and clear buying intent? Current answer: <strong>{answer}</strong>.
        </CardContent>
      </Card>
    </div>
  );
}
