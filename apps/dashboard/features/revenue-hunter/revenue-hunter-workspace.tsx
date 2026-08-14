"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import {
  beaconApi,
  type RevenueHunterDossierRecord,
  type RevenueHunterWorkQueueItem,
} from "@/lib/api/beacon";

const ACTIONS = ["approve", "send", "reply", "book_meeting"] as const;

export function RevenueHunterWorkspace() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const dashboard = useQuery({
    queryKey: ["revenue-hunter-dashboard"],
    queryFn: beaconApi.revenueHunterDashboard,
  });
  const queue = useQuery({
    queryKey: ["revenue-hunter-queue"],
    queryFn: () => beaconApi.revenueHunterWorkQueue({ limit: 50 }),
  });
  const dossiers = useQuery({
    queryKey: ["revenue-hunter-dossiers"],
    queryFn: () => beaconApi.revenueHunterDossiers({ limit: 25 }),
  });
  const detail = useQuery({
    queryKey: ["revenue-hunter-dossier", selectedId],
    queryFn: () => beaconApi.revenueHunterDossier(selectedId!),
    enabled: Boolean(selectedId),
  });

  const act = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      beaconApi.revenueHunterWorkAction(id, action),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["revenue-hunter-queue"] });
      await queryClient.invalidateQueries({ queryKey: ["revenue-hunter-dashboard"] });
    },
  });

  if (dashboard.isLoading && queue.isLoading) return <Skeleton className="h-64 w-full" />;
  if (dashboard.isError && queue.isError) {
    return (
      <ErrorState
        description="Revenue Hunter unavailable."
        onRetry={() => {
          void dashboard.refetch();
          void queue.refetch();
        }}
      />
    );
  }

  const selected = detail.data ?? dossiers.data?.dossiers.find((d) => d.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Operation First Client</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Hunter</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Who to contact today — A+ and A only. Approve, send, reply, book meeting.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
        <Stat title="Expected revenue" value={money(dashboard.data?.expected_revenue)} />
        <Stat title="Expected pipeline" value={money(dashboard.data?.expected_pipeline)} />
        <Stat title="Meetings today" value={String(dashboard.data?.meetings_today ?? 0)} />
        <Stat title="Campaign queue" value={String(dashboard.data?.campaign_queue ?? 0)} />
        <Stat title="Reply queue" value={String(dashboard.data?.reply_queue ?? 0)} />
        <Stat title="Follow ups" value={String(dashboard.data?.follow_ups ?? 0)} />
        <Stat title="Hot opportunities" value={String(dashboard.data?.hot_opportunities ?? 0)} />
        <Stat title="Top 25" value={String(dashboard.data?.top_25_companies?.length ?? 0)} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s Top Opportunities</CardTitle>
            <CardDescription>Work queue — nothing else.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(queue.data?.items ?? []).length === 0 ? (
              <EmptyState title="Queue clear" description="No A+/A opportunities pending action." />
            ) : (
              (queue.data?.items ?? []).map((item) => (
                <QueueRow
                  key={item.id}
                  item={item}
                  busy={act.isPending}
                  onAction={(action) => act.mutate({ id: item.id, action })}
                  onOpen={() => setSelectedId(item.dossier_id ?? null)}
                />
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Dossier</CardTitle>
            <CardDescription>Evidence-backed pitch pack.</CardDescription>
          </CardHeader>
          <CardContent>
            {!selected ? (
              <EmptyState title="Select a target" description="Open a work-queue company to load its dossier." />
            ) : (
              <DossierPanel dossier={selected} />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top 25 Companies</CardTitle>
          <CardDescription>Ranked by revenue hunter score.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {(dashboard.data?.top_25_companies ?? []).map((row, idx) => (
            <button
              key={String(row.company_id)}
              type="button"
              className="flex w-full items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-left text-sm hover:bg-muted/40"
              onClick={() => {
                const match = dossiers.data?.dossiers.find((d) => d.company_id === row.company_id);
                if (match) setSelectedId(match.id);
              }}
            >
              <span className="font-medium">
                {idx + 1}. {String(row.company_name)}
              </span>
              <span className="flex items-center gap-2 text-muted-foreground">
                <Badge variant="outline">{String(row.priority_grade)}</Badge>
                <span>{Number(row.revenue_score).toFixed(1)}</span>
                <span>{String(row.recommended_service)}</span>
              </span>
            </button>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function QueueRow({
  item,
  busy,
  onAction,
  onOpen,
}: {
  item: RevenueHunterWorkQueueItem;
  busy: boolean;
  onAction: (action: string) => void;
  onOpen: () => void;
}) {
  return (
    <div className="rounded-lg border border-border/70 p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <button type="button" className="text-left" onClick={onOpen}>
          <p className="font-medium">
            #{item.rank} {item.company_name}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{item.why_today}</p>
        </button>
        <div className="flex items-center gap-2">
          <Badge>{item.priority_grade}</Badge>
          <Badge variant="outline">{item.recommended_service}</Badge>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>{item.expected_budget}</span>
        <span>{item.probability.toFixed(0)}% probability</span>
        {item.primary_contact?.name ? <span>→ {String(item.primary_contact.name)}</span> : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {ACTIONS.map((action) => (
          <Button
            key={action}
            size="sm"
            variant={action === "book_meeting" ? "default" : "outline"}
            disabled={busy}
            onClick={() => onAction(action)}
          >
            {labelAction(action)}
          </Button>
        ))}
      </div>
    </div>
  );
}

function DossierPanel({ dossier }: { dossier: RevenueHunterDossierRecord }) {
  const why = dossier.why_now ?? {};
  const pains = dossier.pain_points ?? [];
  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap gap-2">
        <Badge>{dossier.priority_grade}</Badge>
        <Badge variant="outline">{dossier.recommended_service}</Badge>
        <Badge variant="outline">{dossier.revenue_score.toFixed(1)} score</Badge>
      </div>
      <p>{String(dossier.dossier?.company_summary ?? dossier.company_name)}</p>
      <p className="text-muted-foreground">{String(why.why_this_company ?? "")}</p>
      <p className="text-muted-foreground">{String(why.why_today ?? "")}</p>
      <p className="text-muted-foreground">{String(why.why_us ?? "")}</p>
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">Pain points</p>
        <ul className="mt-1 list-disc space-y-1 pl-4">
          {pains.map((p) => (
            <li key={String(p.problem)}>
              {String(p.problem)} ({Number(p.confidence).toFixed(0)}%)
            </li>
          ))}
        </ul>
      </div>
      <div className="grid gap-1 text-xs text-muted-foreground">
        <span>Budget: {dossier.expected_budget}</span>
        <span>Timeline: {dossier.expected_timeline}</span>
        <span>Probability: {dossier.probability.toFixed(0)}%</span>
        <span>Proposal: {String(dossier.dossier?.proposal_strategy ?? "—")}</span>
      </div>
    </div>
  );
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function money(value: number | undefined) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value ?? 0);
}

function labelAction(action: string) {
  if (action === "book_meeting") return "Book Meeting";
  return action.charAt(0).toUpperCase() + action.slice(1);
}
