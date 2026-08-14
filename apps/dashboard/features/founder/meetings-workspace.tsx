"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";

export function MeetingsWorkspace() {
  const brief = useQuery({
    queryKey: ["clr-daily-brief"],
    queryFn: () => beaconApi.clrDailyBrief(),
  });
  const morning = useQuery({
    queryKey: ["asa-morning-brief"],
    queryFn: () => beaconApi.asaMorningBrief(),
  });
  const roc = useQuery({
    queryKey: ["revenue-operations-dashboard"],
    queryFn: () => beaconApi.rocDashboard(),
  });

  if (brief.isLoading && morning.isLoading) return <Skeleton className="h-64 w-full" />;

  const today = ((brief.data?.meetings_today as Array<Record<string, unknown>>) ||
    (morning.data?.expected_meetings as Array<Record<string, unknown>>) ||
    (((roc.data?.command_center as Record<string, unknown>)?.meetings as Array<Record<string, unknown>>) ||
      [])) as Array<Record<string, unknown>>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">Show up prepared. Close the meeting.</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Meetings</h1>
      </header>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Today</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {today.length === 0 ? (
            <p className="text-sm text-muted-foreground">No meetings scheduled. Book one from outreach replies.</p>
          ) : (
            today.map((row, idx) => (
              <div
                key={idx}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium">{String(row.company || row.company_name || row.title || "Meeting")}</p>
                  <p className="text-xs text-muted-foreground">
                    {String(row.time || row.scheduled_at || row.summary || "Scheduled")}
                  </p>
                </div>
                <StatusBadge tone="info">Meeting</StatusBadge>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
