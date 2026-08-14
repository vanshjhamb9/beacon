"use client";

import { useQuery } from "@tanstack/react-query";

import { CommunicationReadinessCard } from "@/features/execution-readiness/communication-readiness-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export default function ExecutionReadinessPage() {
  const readiness = useQuery({
    queryKey: ["execution-readiness"],
    queryFn: () => beaconApi.executionReadiness(),
    refetchInterval: 30_000,
  });

  const checks = ((readiness.data?.checks as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <SectionLabel>Sprint 36 · er-v1</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Execution Readiness Gate</h1>
        <p className="text-sm text-muted-foreground">
          Planning vs Ready vs Executing. No delivery metrics without verified provider events.
        </p>
      </div>

      <CommunicationReadinessCard />

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Readiness checks</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {readiness.isLoading && <Skeleton className="h-24 w-full" />}
          {checks.map((c) => (
            <div key={String(c.name)} className="flex justify-between gap-2">
              <span>
                {String(c.name)} — <span className="text-muted-foreground">{String(c.detail)}</span>
              </span>
              <span>{c.passed ? "PASS" : "FAIL"}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
