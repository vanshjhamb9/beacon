"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

type Tab = "accounts" | "health" | "committee" | "engagement" | "replies" | "timeline" | "followups" | "analytics";

export function AccountJourneyWorkspace() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("accounts");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);

  const dashboard = useQuery({
    queryKey: ["goi-dashboard"],
    queryFn: () => beaconApi.goiDashboard(),
  });
  const followups = useQuery({
    queryKey: ["goi-followups"],
    queryFn: () => beaconApi.goiFollowups(),
  });
  const health = useQuery({
    queryKey: ["goi-health"],
    queryFn: () => beaconApi.goiHealth(),
  });
  const replies = useQuery({
    queryKey: ["goi-replies"],
    queryFn: () => beaconApi.goiReplies(),
  });
  const analytics = useQuery({
    queryKey: ["goi-analytics"],
    queryFn: () => beaconApi.goiAnalytics(),
  });
  const company = useQuery({
    queryKey: ["goi-company", selectedCompanyId],
    queryFn: () => beaconApi.goiCompany(selectedCompanyId!),
    enabled: Boolean(selectedCompanyId),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.goiRefresh(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["goi-dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["goi-followups"] }),
        queryClient.invalidateQueries({ queryKey: ["goi-health"] }),
        queryClient.invalidateQueries({ queryKey: ["goi-replies"] }),
        queryClient.invalidateQueries({ queryKey: ["goi-analytics"] }),
      ]);
    },
  });

  const accounts = useMemo(() => dashboard.data?.accounts ?? [], [dashboard.data]);
  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "accounts", label: "Account Journey" },
    { id: "health", label: "Company Health" },
    { id: "committee", label: "Buying Committee" },
    { id: "engagement", label: "Engagement" },
    { id: "replies", label: "Reply Intelligence" },
    { id: "timeline", label: "Timeline" },
    { id: "followups", label: "Follow-up Planner" },
    { id: "analytics", label: "Global Analytics" },
  ];

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Account Journey unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Global Outreach Intelligence</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Account Journey</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Persistent account lifecycles, adaptive multi-touch plans, engagement health, and founder-approved follow-ups.
          </p>
        </div>
        <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
          Refresh journeys
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Journeys" value={String(dashboard.data?.total_journeys ?? 0)} />
        <Stat label="Hot / Critical" value={String((dashboard.data?.by_health?.hot ?? 0) + (dashboard.data?.by_health?.critical ?? 0))} />
        <Stat label="Follow-ups" value={String(followups.data?.total ?? 0)} />
        <Stat label="Replies classified" value={String(replies.data?.total ?? 0)} />
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "default" : "outline"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "accounts" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Accounts</CardTitle>
            <CardDescription>Append-only journey snapshots</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {accounts.length === 0 ? (
              <EmptyState title="No journeys yet" description="Refresh to evaluate accounts." />
            ) : (
              accounts.map((a) => (
                <button
                  key={String(a.id)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-border/60 px-3 py-2 text-left"
                  onClick={() => {
                    setSelectedCompanyId(String(a.company_id));
                    setTab("engagement");
                  }}
                >
                  <div>
                    <p className="text-sm font-medium">{String(a.company_name)}</p>
                    <p className="text-xs text-muted-foreground">{String(a.stage)}</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline">{String(a.health_category)}</Badge>
                    <Badge>{Math.round(Number(a.overall_engagement ?? 0))}</Badge>
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {tab === "health" && (
        <ListRows
          title="Company Health"
          rows={(health.data?.snapshots ?? []).map((s) => ({
            title: String(s.category),
            detail: String(s.reason),
            meta: String(s.score),
          }))}
        />
      )}

      {tab === "followups" && (
        <ListRows
          title="Follow-up Planner"
          empty="No follow-ups planned."
          note="Founder approval required before external sends."
          rows={(followups.data?.plans ?? []).map((p) => ({
            title: `${String(p.channel)} · ${String(p.next_action)}`,
            detail: String(p.reason),
            meta: String(p.urgency),
          }))}
        />
      )}

      {tab === "replies" && (
        <ListRows
          title="Reply Intelligence"
          rows={(replies.data?.replies ?? []).map((r) => ({
            title: String(r.classification),
            detail: String((r.structured_outcome as Record<string, unknown> | undefined)?.next_hint ?? ""),
            meta: String(r.confidence),
          }))}
        />
      )}

      {tab === "analytics" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Global Analytics</CardTitle>
            <CardDescription>Country · industry · size · tech · service · campaign · DM role</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg border border-border/60 bg-muted/30 p-3 text-xs">
              {JSON.stringify(analytics.data?.payload ?? {}, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {(tab === "committee" || tab === "engagement" || tab === "timeline") && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {tab === "committee" ? "Buying Committee" : tab === "engagement" ? "Engagement" : "Timeline"}
            </CardTitle>
            <CardDescription>
              {selectedCompanyId ? `Company ${selectedCompanyId}` : "Select an account from Account Journey first."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedCompanyId ? (
              <p className="text-sm text-muted-foreground">Pick an account to inspect committee, engagement, and timeline.</p>
            ) : company.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <CompanyDetail tab={tab} pack={company.data ?? {}} />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CompanyDetail({ tab, pack }: { tab: Tab; pack: Record<string, unknown> }) {
  if (tab === "engagement") {
    const e = (pack.engagement ?? {}) as Record<string, unknown>;
    return (
      <div className="grid gap-2 sm:grid-cols-2">
        {["open_score", "reply_score", "intent_score", "meeting_score", "relationship_score", "account_temperature", "overall_engagement"].map(
          (k) => (
            <div key={k} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              <p className="text-xs text-muted-foreground">{k}</p>
              <p className="font-medium">{String(e[k] ?? 0)}</p>
            </div>
          ),
        )}
      </div>
    );
  }
  if (tab === "committee") {
    const members = ((pack.buying_committee as Record<string, unknown> | undefined)?.members ?? []) as Array<
      Record<string, unknown>
    >;
    return members.length === 0 ? (
      <p className="text-sm text-muted-foreground">No committee members.</p>
    ) : (
      <div className="space-y-2">
        {members.map((m, idx) => (
          <div key={idx} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
            <p className="font-medium">{String(m.name)}</p>
            <p className="text-xs text-muted-foreground">
              {String(m.role)} · {String(m.title ?? "")}
            </p>
          </div>
        ))}
      </div>
    );
  }
  const events = (pack.timeline ?? []) as Array<Record<string, unknown>>;
  return (
    <div className="space-y-2">
      {events.map((e, idx) => (
        <div key={idx} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
          <p className="font-medium">{String(e.title)}</p>
          <p className="text-xs text-muted-foreground">{String(e.event_type)}</p>
        </div>
      ))}
      {pack.company_id ? (
        <Button asChild size="sm" variant="outline">
          <Link href={`/companies/${String(pack.company_id)}`}>Open company</Link>
        </Button>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/60 bg-background/40 px-4 py-3">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-xl font-semibold">{value}</p>
    </div>
  );
}

function ListRows({
  title,
  rows,
  empty = "Nothing yet.",
  note,
}: {
  title: string;
  rows: Array<{ title: string; detail: string; meta: string }>;
  empty?: string;
  note?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        {note ? <CardDescription>{note}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">{empty}</p>
        ) : (
          rows.slice(0, 20).map((r, idx) => (
            <div key={idx} className="flex items-center justify-between gap-3 rounded-lg border border-border/60 px-3 py-2">
              <div>
                <p className="text-sm font-medium">{r.title}</p>
                <p className="text-xs text-muted-foreground">{r.detail}</p>
              </div>
              <Badge variant="outline">{r.meta}</Badge>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
