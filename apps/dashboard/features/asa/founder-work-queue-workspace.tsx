"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

const KIND_LABEL: Record<string, string> = {
  meet_today: "Meet today",
  proposal_pending: "Proposal pending",
  negotiation: "Negotiation",
  needs_approval: "Needs approval",
  high_intent_reply: "High intent reply",
  urgent_follow_up: "Urgent follow-up",
};

export function FounderWorkQueueWorkspace() {
  const queryClient = useQueryClient();

  const queue = useQuery({
    queryKey: ["asa-work-queue"],
    queryFn: () => beaconApi.asaWorkQueue(true),
  });
  const brief = useQuery({
    queryKey: ["asa-morning-brief"],
    queryFn: () => beaconApi.asaMorningBrief(),
  });

  const refresh = useMutation({
    mutationFn: async () => {
      await beaconApi.asaMorningBriefRefresh();
      await beaconApi.asaWorkQueue(true);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["asa-work-queue"] });
      await queryClient.invalidateQueries({ queryKey: ["asa-morning-brief"] });
    },
  });

  const items = useMemo(() => queue.data?.items ?? [], [queue.data]);
  const grouped = useMemo(() => {
    const map = new Map<string, typeof items>();
    for (const item of items) {
      const kind = String(item.kind || "other");
      const list = map.get(kind) ?? [];
      list.push(item);
      map.set(kind, list);
    }
    return map;
  }, [items]);

  if (queue.isLoading || brief.isLoading) return <Skeleton className="h-72 w-full" />;
  if (queue.isError) {
    return <ErrorState description="Founder work queue unavailable." onRetry={() => void queue.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Autonomous Sales Agent</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Founder Work Queue</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Only founder-critical work: meetings, proposals, negotiation, approvals, high-intent replies, and urgent
            follow-ups. Everything else is automated.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link href="/morning-brief">Morning Brief</Link>
          </Button>
          <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            Refresh
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Today&apos;s focus</CardTitle>
          <CardDescription>
            Forecast ${(brief.data?.revenue_forecast ?? 0).toLocaleString()} ·{" "}
            {(brief.data?.follow_ups_due ?? []).length} follow-ups due
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {(brief.data?.priorities ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No founder priorities right now.</p>
          ) : (
            (brief.data?.priorities ?? []).slice(0, 5).map((p) => (
              <div key={p} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                {p}
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {items.length === 0 ? (
        <EmptyState title="Queue clear" description="Automation is handling the rest of the pipeline." />
      ) : (
        <div className="space-y-5">
          {[...grouped.entries()].map(([kind, list]) => (
            <section key={kind} className="space-y-3">
              <div className="flex items-center gap-2">
                <h2 className="font-display text-lg font-semibold">{KIND_LABEL[kind] ?? kind}</h2>
                <Badge variant="outline">{list.length}</Badge>
              </div>
              <div className="space-y-3">
                {list.map((item, idx) => (
                  <Card key={`${item.company_id}-${kind}-${idx}`}>
                    <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <CardTitle className="text-base">{String(item.company_name)}</CardTitle>
                        <CardDescription>{String(item.summary)}</CardDescription>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge>{String(item.priority || "P1")}</Badge>
                        {item.stage ? <Badge variant="outline">{String(item.stage)}</Badge> : null}
                        {item.next_action ? <Badge variant="outline">{String(item.next_action)}</Badge> : null}
                      </div>
                    </CardHeader>
                    {item.company_id ? (
                      <CardContent>
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/companies/${String(item.company_id)}`}>Open company</Link>
                        </Button>
                      </CardContent>
                    ) : null}
                  </Card>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
