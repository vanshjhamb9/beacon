"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { CampaignExecutionBanner } from "@/features/execution-readiness/communication-readiness-card";
import { beaconApi, type CampaignRecord } from "@/lib/api/beacon";
import { formatDateTime, formatLabel, formatScore, priorityTone, scoreTone } from "@/lib/utils";

const VIEWS = ["Pipeline", "Calendar", "Approvals", "Schedules", "Analytics", "Company Timeline"] as const;
type View = (typeof VIEWS)[number];

export function CampaignsWorkspace() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<View>("Pipeline");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [timelineCompanyId, setTimelineCompanyId] = useState("");

  const list = useQuery({ queryKey: ["campaigns"], queryFn: () => beaconApi.campaigns({ limit: 200 }) });
  const dashboard = useQuery({ queryKey: ["campaigns-dashboard"], queryFn: beaconApi.campaignsDashboard });
  const detail = useQuery({
    queryKey: ["campaign", selectedId],
    queryFn: () => beaconApi.campaign(selectedId!),
    enabled: Boolean(selectedId),
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    await queryClient.invalidateQueries({ queryKey: ["campaigns-dashboard"] });
    if (selectedId) {
      await queryClient.invalidateQueries({ queryKey: ["campaign", selectedId] });
    }
  };

  const approve = useMutation({
    mutationFn: (id: string) => beaconApi.campaignApprove(id, { actor: "operator" }),
    onSuccess: invalidate,
  });
  const pause = useMutation({
    mutationFn: (id: string) => beaconApi.campaignPause(id, { actor: "operator" }),
    onSuccess: invalidate,
  });
  const cancel = useMutation({
    mutationFn: (id: string) => beaconApi.campaignCancel(id, { actor: "operator" }),
    onSuccess: invalidate,
  });

  const campaigns = list.data?.campaigns ?? [];
  const selected = detail.data ?? campaigns.find((item) => item.id === selectedId) ?? null;

  const timelineRows = useMemo(() => {
    if (!timelineCompanyId) return [];
    if (selected && selected.company_id === timelineCompanyId) {
      return (selected.approvals ?? [])
        .map((approval) => ({
          ...approval,
          company_name: selected.company_name,
          campaign_id: selected.id,
          status: selected.status,
        }))
        .sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
    }
    return [];
  }, [selected, timelineCompanyId]);

  if (list.isError && dashboard.isError) {
    return (
      <ErrorState
        description="Campaign Intelligence APIs unavailable."
        onRetry={() => {
          void list.refetch();
          void dashboard.refetch();
        }}
      />
    );
  }

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Campaign Intelligence</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Campaigns</h1>
        <p className="text-sm text-muted-foreground">
          Orchestrate approved Sales Copilot packages into reviewable outreach campaigns. Messages are never sent
          automatically.
        </p>
      </header>

      <CampaignExecutionBanner />

      {dashboard.isLoading || !dashboard.data ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <Metric label="Total" value={String(dashboard.data.total_campaigns)} />
          <Metric label="Needs review" value={String(dashboard.data.needs_review)} />
          <Metric label="Approved / scheduled" value={String(dashboard.data.approved_or_scheduled)} />
          <Metric label="Paused" value={String(dashboard.data.paused)} />
          <Metric label="Avg confidence" value={formatScore(dashboard.data.average_confidence, 0)} />
          <Metric label="Delivery" value={dashboard.data.delivery_enabled ? "On" : "Off"} />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {VIEWS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setView(item)}
            className={`rounded-md px-3 py-1.5 text-xs transition ${
              view === item ? "bg-foreground text-background" : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {view === "Pipeline" ? (
        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Pipeline</CardTitle>
              <CardDescription>Plans awaiting review or ready for human-triggered execution</CardDescription>
            </CardHeader>
            <CardContent>
              {list.isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : campaigns.length === 0 ? (
                <EmptyState
                  title="No campaigns yet"
                  description="Create a campaign from a company with an approved Sales Copilot package."
                />
              ) : (
                <div className="space-y-2">
                  {campaigns.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`w-full rounded-lg border px-3 py-3 text-left transition ${
                        selectedId === item.id ? "border-primary/50 bg-primary/5" : "border-border/60 hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="font-medium">{item.company_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatLabel(item.primary_channel)} · {formatLabel(item.status)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge className={priorityTone(item.priority)}>{formatLabel(item.priority)}</Badge>
                          <Badge className="bg-muted text-muted-foreground ring-border">
                            {formatScore(item.expected_confidence, 0)}
                          </Badge>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Campaign Detail</CardTitle>
              <CardDescription>Channel, timing, message selection, evidence, and confidence</CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedId ? (
                <EmptyState title="Select a campaign" description="Choose a campaign from the pipeline." />
              ) : detail.isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : selected ? (
                <CampaignDetail
                  campaign={selected}
                  onApprove={() => approve.mutate(selected.id)}
                  onPause={() => pause.mutate(selected.id)}
                  onCancel={() => cancel.mutate(selected.id)}
                  busy={approve.isPending || pause.isPending || cancel.isPending}
                />
              ) : (
                <EmptyState title="Campaign unavailable" description="Unable to load campaign detail." />
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {view === "Calendar" || view === "Schedules" ? (
        <Card>
          <CardHeader>
            <CardTitle>{view === "Calendar" ? "Schedule Calendar" : "Schedules"}</CardTitle>
            <CardDescription>Planned step windows — no provider delivery</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(dashboard.data?.upcoming_schedules ?? []).length === 0 ? (
              <EmptyState title="No schedules" description="Approve a campaign to materialize readiness schedules." />
            ) : (
              (dashboard.data?.upcoming_schedules ?? []).map((item) => (
                <div
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 py-2 text-sm"
                >
                  <span>
                    {formatDateTime(item.planned_at)} · {item.timezone}
                  </span>
                  <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(item.status)}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      ) : null}

      {view === "Approvals" ? (
        <Card>
          <CardHeader>
            <CardTitle>Approvals Queue</CardTitle>
            <CardDescription>Campaigns in draft or needs_review</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(dashboard.data?.pending_approvals ?? []).length === 0 ? (
              <EmptyState title="Queue clear" description="No campaigns waiting for approval." />
            ) : (
              (dashboard.data?.pending_approvals ?? []).map((item) => (
                <div
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/60 p-3"
                >
                  <div>
                    <p className="font-medium">{item.company_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatLabel(item.primary_channel)} · confidence {formatScore(item.expected_confidence, 0)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setSelectedId(item.id)}>
                      Open
                    </Button>
                    <Button size="sm" disabled={approve.isPending} onClick={() => approve.mutate(item.id)}>
                      Approve
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      ) : null}

      {view === "Analytics" ? (
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard title="By status" data={dashboard.data?.by_status ?? {}} />
          <StatCard title="By priority" data={dashboard.data?.by_priority ?? {}} />
          <StatCard title="By primary channel" data={dashboard.data?.by_primary_channel ?? {}} />
        </div>
      ) : null}

      {view === "Company Timeline" ? (
        <Card>
          <CardHeader>
            <CardTitle>Company Timeline</CardTitle>
            <CardDescription>Immutable approval and status audit events for a company</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <input
                className="min-w-[280px] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
                placeholder="Company ID"
                value={timelineCompanyId}
                onChange={(event) => setTimelineCompanyId(event.target.value.trim())}
              />
              <Button
                variant="outline"
                onClick={() => {
                  if (selected?.company_id) setTimelineCompanyId(selected.company_id);
                }}
              >
                Use selected campaign company
              </Button>
            </div>
            {!timelineCompanyId ? (
              <EmptyState title="Enter a company ID" description="Audit events appear after campaigns are created." />
            ) : timelineRows.length === 0 ? (
              <EmptyState
                title="No audit events loaded"
                description="Open campaign details first or create campaigns for this company."
              />
            ) : (
              <div className="space-y-2">
                {timelineRows.map((row) => (
                  <div key={row.id} className="border-b border-border/50 py-2 text-sm">
                    <p className="font-medium">
                      {formatLabel(row.action)} · {row.company_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {row.from_status} → {row.to_status} · {row.actor} · {formatDateTime(row.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function CampaignDetail({
  campaign,
  onApprove,
  onPause,
  onCancel,
  busy,
}: {
  campaign: CampaignRecord;
  onApprove: () => void;
  onPause: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-display text-xl font-semibold">{campaign.company_name}</p>
          <p className="text-muted-foreground">{campaign.recommended_service || "Service pending"}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(campaign.status)}</Badge>
            <Badge className={priorityTone(campaign.priority)}>{formatLabel(campaign.priority)}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">
              {formatLabel(campaign.primary_channel)}
            </Badge>
          </div>
        </div>
        <p className={`font-display text-3xl font-semibold ${scoreTone(campaign.expected_confidence)}`}>
          {formatScore(campaign.expected_confidence, 0)}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" disabled={busy} onClick={onApprove}>
          Approve
        </Button>
        <Button size="sm" variant="outline" disabled={busy} onClick={onPause}>
          Pause
        </Button>
        <Button size="sm" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button asChild size="sm" variant="outline">
          <Link href={`/companies/${campaign.company_id}`}>Company</Link>
        </Button>
      </div>

      <ReasonBlock title="Reason for channel choice" body={campaign.channel_choice_reason} />
      <ReasonBlock title="Reason for timing" body={campaign.timing_reason} />
      <ReasonBlock title="Reason for message selection" body={campaign.message_selection_reason} />

      <div>
        <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence</p>
        <ul className="space-y-1">
          {(campaign.evidence ?? []).slice(0, 8).map((item, index) => (
            <li key={`${item.summary}-${index}`} className="text-muted-foreground">
              {String(item.category || "evidence")}: {String(item.summary || "")}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Sequence</p>
        <div className="space-y-2">
          {(campaign.steps ?? []).map((step) => (
            <div key={step.id} className="rounded-md border border-border/60 p-3">
              <p className="font-medium">
                Step {step.sequence}: {formatLabel(step.channel)} · {formatLabel(step.kind)}
              </p>
              <p className="text-xs text-muted-foreground">{step.message_selection_reason}</p>
              <p className="text-xs text-muted-foreground">{step.timing_reason}</p>
              {step.subject_preview ? <p className="mt-1">Subject: {step.subject_preview}</p> : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReasonBlock({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <p className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{title}</p>
      <p>{body}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/70 bg-card/50 p-4">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="font-display text-2xl font-semibold">{value}</p>
    </div>
  );
}

function StatCard({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {entries.length === 0 ? (
          <p className="text-muted-foreground">No data</p>
        ) : (
          entries.map(([key, value]) => (
            <div key={key} className="flex justify-between gap-2">
              <span>{formatLabel(key)}</span>
              <span>{value}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
