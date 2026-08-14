"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

const TONE: Record<string, string> = {
  GREEN: "bg-emerald-600 text-white",
  YELLOW: "bg-amber-500 text-black",
  RED: "bg-red-600 text-white",
};

export function CommunicationReadinessCard() {
  const card = useQuery({
    queryKey: ["execution-dashboard-card"],
    queryFn: () => beaconApi.executionDashboardCard(),
    refetchInterval: 30_000,
  });

  if (card.isError) {
    return (
      <ErrorState title="Communication Readiness unavailable" description="API /execution/dashboard-card failed." />
    );
  }
  if (card.isLoading) return <Skeleton className="h-40 w-full" />;

  const d = card.data || {};
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div>
            <SectionLabel>er-v1</SectionLabel>
            <CardTitle className="text-lg">Communication Readiness</CardTitle>
          </div>
          <Badge className={TONE[String(d.tone)] || ""}>{String(d.execution_mode || "PLANNING")}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          <span className="text-muted-foreground">Execution Mode · </span>
          {String(d.execution_mode)}
        </p>
        <p>
          <span className="text-muted-foreground">Email · </span>
          {String(d.email)}
        </p>
        <p>
          <span className="text-muted-foreground">WhatsApp · </span>
          {String(d.whatsapp)}
        </p>
        <p>
          <span className="text-muted-foreground">Tracking · </span>
          {String(d.tracking)}
        </p>
        <p>
          <span className="text-muted-foreground">Follow-ups · </span>
          {String(d.follow_ups)}
        </p>
        <p className="pt-1 font-medium">{String(d.recommendation)}</p>
        {d.reason ? <p className="text-xs text-muted-foreground">{String(d.reason)}</p> : null}
      </CardContent>
    </Card>
  );
}

export function CampaignExecutionBanner() {
  const status = useQuery({
    queryKey: ["execution-status"],
    queryFn: () => beaconApi.executionStatus(),
    refetchInterval: 30_000,
  });
  const mode = String(status.data?.current_mode || "PLANNING");
  if (mode === "EXECUTING") {
    return (
      <div className="rounded-md border border-emerald-700/40 bg-emerald-950/20 px-3 py-2 text-sm">
        <span className="font-medium text-emerald-500">Executing</span>
        <span className="text-muted-foreground"> · Tracking active · Delivery confirmed</span>
      </div>
    );
  }
  if (mode === "READY") {
    return (
      <div className="rounded-md border border-amber-600/40 bg-amber-950/20 px-3 py-2 text-sm">
        <span className="font-medium text-amber-400">Ready</span>
        <span className="text-muted-foreground"> · Provider connected · No verified delivery yet</span>
      </div>
    );
  }
  return (
    <div className="rounded-md border border-red-700/40 bg-red-950/20 px-3 py-2 text-sm">
      <span className="font-medium text-red-400">Planning</span>
      <span className="text-muted-foreground"> · No provider connected · No messages have been sent.</span>
    </div>
  );
}
