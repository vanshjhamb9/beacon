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

export function ProductionReadinessWorkspace() {
  const prod = useQuery({
    queryKey: ["clr-production-readiness"],
    queryFn: () => beaconApi.clrProductionReadiness(),
    refetchInterval: 60_000,
  });

  if (prod.isError) {
    return (
      <ErrorState
        title="Production Readiness unavailable"
        description="API /revenue-validation/production-readiness failed."
      />
    );
  }
  if (prod.isLoading) return <Skeleton className="h-40 w-full" />;

  const health = ((prod.data?.health as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <SectionLabel>CLR v1</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Production Readiness</h1>
        <p className="text-sm text-muted-foreground">GREEN / YELLOW / RED against revenue execution KPIs.</p>
      </div>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Health</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {health.map((h) => (
            <div key={String(h.metric)} className="flex items-center justify-between gap-3 text-sm">
              <div>
                <p className="font-medium">{String(h.metric)}</p>
                {h.detail ? <p className="text-xs text-muted-foreground">{String(h.detail)}</p> : null}
              </div>
              <div className="flex items-center gap-2">
                <span>{String(h.value)}</span>
                <Badge className={TONE[String(h.tone)] || ""}>{String(h.tone)}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
