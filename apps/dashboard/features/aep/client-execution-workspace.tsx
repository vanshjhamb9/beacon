"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

type Tab = "delivery" | "clients" | "health" | "handoffs" | "upsells" | "projects" | "founder";

export function ClientExecutionWorkspace() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("delivery");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);

  const dashboard = useQuery({
    queryKey: ["aep-dashboard"],
    queryFn: () => beaconApi.aepDashboard(),
  });
  const health = useQuery({
    queryKey: ["aep-health"],
    queryFn: () => beaconApi.aepHealth(),
  });
  const handoffs = useQuery({
    queryKey: ["aep-handoffs"],
    queryFn: () => beaconApi.aepHandoffs(),
  });
  const upsells = useQuery({
    queryKey: ["aep-upsells"],
    queryFn: () => beaconApi.aepUpsells(),
  });
  const projects = useQuery({
    queryKey: ["aep-projects"],
    queryFn: () => beaconApi.aepProjects(),
  });
  const client = useQuery({
    queryKey: ["aep-client", selectedCompanyId],
    queryFn: () => beaconApi.aepClient(selectedCompanyId!),
    enabled: Boolean(selectedCompanyId),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.aepRefresh(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["aep-dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["aep-health"] }),
        queryClient.invalidateQueries({ queryKey: ["aep-handoffs"] }),
        queryClient.invalidateQueries({ queryKey: ["aep-upsells"] }),
        queryClient.invalidateQueries({ queryKey: ["aep-projects"] }),
      ]);
    },
  });

  const approve = useMutation({
    mutationFn: (id: string) => beaconApi.aepApproveUpsell(id, true),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["aep-upsells"] });
    },
  });

  const clients = useMemo(() => dashboard.data?.clients ?? [], [dashboard.data]);
  const delivery = dashboard.data?.delivery ?? {};
  const founder = dashboard.data?.founder_view ?? {};

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "delivery", label: "Delivery Dashboard" },
    { id: "clients", label: "Clients" },
    { id: "health", label: "Client Health" },
    { id: "handoffs", label: "Handoffs" },
    { id: "upsells", label: "Upsells" },
    { id: "projects", label: "Projects" },
    { id: "founder", label: "Founder View" },
  ];

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Client Delivery unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Agency Execution Platform</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Client Delivery</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Sales Mode → Client Delivery Mode. Lifecycle, handoffs, health, renewals, and founder-gated upsells.
          </p>
        </div>
        <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
          Refresh clients
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Clients" value={String(dashboard.data?.total_clients ?? 0)} />
        <Stat label="At risk" value={String(dashboard.data?.by_health?.at_risk ?? 0)} />
        <Stat label="Upsells" value={String(upsells.data?.total ?? 0)} />
        <Stat label="Version" value={String(dashboard.data?.scoring_version ?? "aep-v1")} />
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "default" : "outline"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "delivery" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <ListCard title="Today's Deliveries" rows={(delivery.todays_deliveries as Array<Record<string, unknown>>) ?? []} keys={["company_name", "deliverable", "project"]} />
          <ListCard title="Upcoming Milestones" rows={(delivery.upcoming_milestones as Array<Record<string, unknown>>) ?? []} keys={["company_name", "milestone", "project"]} />
          <ListCard title="Blocked Projects" rows={(delivery.blocked_projects as Array<Record<string, unknown>>) ?? []} keys={["company_name", "project", "stage"]} />
          <ListCard title="At-Risk Projects" rows={(delivery.at_risk_projects as Array<Record<string, unknown>>) ?? []} keys={["company_name", "project", "reason"]} />
          <ListCard title="Renewals" rows={(delivery.renewals as Array<Record<string, unknown>>) ?? []} keys={["company_name", "renewal_date", "probability"]} />
          <ListCard title="Upsell Pipeline" rows={(delivery.upsells as Array<Record<string, unknown>>) ?? []} keys={["service", "title", "confidence"]} />
        </div>
      )}

      {tab === "clients" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Client Workspaces</CardTitle>
            <CardDescription>Append-only client profiles after win</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {clients.length === 0 ? (
              <EmptyState title="No clients yet" description="Refresh after a win to enter Delivery Mode." />
            ) : (
              clients.map((c) => (
                <button
                  key={String(c.id)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-border/60 px-3 py-2 text-left"
                  onClick={() => setSelectedCompanyId(String(c.company_id))}
                >
                  <div>
                    <div className="font-medium">{String(c.company_name)}</div>
                    <div className="text-xs text-muted-foreground">{String(c.stage)}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{String(c.health_status)}</Badge>
                    <span className="text-sm tabular-nums">{Number(c.contract_value ?? 0).toLocaleString()}</span>
                  </div>
                </button>
              ))
            )}
            {client.data && (
              <div className="mt-4 space-y-2 rounded-lg border border-border/60 p-3 text-sm">
                <div className="font-medium">{String(client.data.company_name)}</div>
                <p className="text-muted-foreground">
                  {String((client.data.workspace as Record<string, unknown> | undefined)?.executive_summary ?? "")}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Badge>{String(client.data.stage)}</Badge>
                  <Badge variant="outline">{String(client.data.health_status)}</Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "health" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Health Snapshots</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(health.data?.snapshots ?? []).length === 0 ? (
              <EmptyState title="No health data" description="Refresh to score clients." />
            ) : (
              (health.data?.snapshots ?? []).map((s) => (
                <div key={String(s.id)} className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm">
                  <span>{String(s.status)}</span>
                  <span className="tabular-nums">
                    health {Number(s.overall_health).toFixed(0)} · renew {Number(s.renewal_probability).toFixed(0)}%
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {tab === "handoffs" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Project Handoffs</CardTitle>
            <CardDescription>Sales context passed to delivery</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(handoffs.data?.handoffs ?? []).length === 0 ? (
              <EmptyState title="No handoffs" description="Win a deal to generate a dossier." />
            ) : (
              (handoffs.data?.handoffs ?? []).map((h) => {
                const payload = (h.payload as Record<string, unknown>) ?? {};
                return (
                  <div key={String(h.id)} className="rounded-lg border border-border/60 p-3 text-sm">
                    <div className="font-medium">{String(payload.client_dossier ?? "Handoff")}</div>
                    <p className="mt-1 text-muted-foreground">{String(payload.meeting_summary ?? "")}</p>
                    <p className="mt-1 text-xs">Scope: {String(payload.scope_summary ?? "")}</p>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      )}

      {tab === "upsells" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upsell Recommendations</CardTitle>
            <CardDescription>{upsells.data?.note ?? "Founder approval required"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(upsells.data?.recommendations ?? []).length === 0 ? (
              <EmptyState title="No upsells" description="Growth signals will surface suggestions." />
            ) : (
              (upsells.data?.recommendations ?? []).map((u) => (
                <div key={String(u.id)} className="flex items-center justify-between gap-3 rounded-lg border border-border/60 px-3 py-2">
                  <div>
                    <div className="font-medium text-sm">{String(u.title)}</div>
                    <div className="text-xs text-muted-foreground">{String(u.reason)}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{String(u.status)}</Badge>
                    {u.status === "pending_approval" && (
                      <Button size="sm" disabled={approve.isPending} onClick={() => approve.mutate(String(u.recommendation_id))}>
                        Approve
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {tab === "projects" && (
        <ListCard
          title="Projects"
          rows={(projects.data?.projects ?? []).map((p) => ({
            company_id: p.company_id,
            name: p.name,
            stage: p.stage,
            blocked: p.blocked ? "blocked" : p.at_risk ? "at risk" : "ok",
          }))}
          keys={["name", "stage", "blocked"]}
        />
      )}

      {tab === "founder" && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Revenue Closed" value={Number(founder.revenue_closed ?? 0).toLocaleString()} />
          <Stat label="Projects Running" value={String(founder.projects_running ?? 0)} />
          <Stat label="Revenue Delivered" value={Number(founder.revenue_delivered ?? 0).toLocaleString()} />
          <Stat label="Pending Payments" value={String(founder.pending_payments ?? "placeholder")} />
          <Stat label="Renewals" value={String(founder.renewals ?? 0)} />
          <Stat label="Upsells" value={String(founder.upsells ?? 0)} />
          <Stat label="Client Risks" value={String(founder.client_risks ?? 0)} />
          <Stat label="Team Capacity" value={String(founder.team_capacity ?? "placeholder")} />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tabular-nums">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function ListCard({
  title,
  rows,
  keys,
}: {
  title: string;
  rows: Array<Record<string, unknown>>;
  keys: string[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.length === 0 ? (
          <EmptyState title="Nothing here" description="No rows yet." />
        ) : (
          rows.map((row, i) => (
            <div key={i} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              {keys.map((k) => (
                <span key={k} className="mr-3 text-muted-foreground">
                  <span className="text-foreground">{String(row[k] ?? "—")}</span>
                </span>
              ))}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
