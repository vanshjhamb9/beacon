"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi, type TargetAccountRecord } from "@/lib/api/beacon";
import { formatLabel } from "@/lib/utils";

const VIEWS = [
  "Revenue Ranking",
  "ICP Manager",
  "Hunter Mode",
  "Why Now",
  "Buying Signals",
  "Heat Map",
  "Industries",
  "Countries",
  "Pipeline",
] as const;
type View = (typeof VIEWS)[number];

export function TargetsWorkspace() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<View>("Revenue Ranking");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const list = useQuery({ queryKey: ["targets"], queryFn: () => beaconApi.targets({ limit: 200 }) });
  const dashboard = useQuery({ queryKey: ["targets-dashboard"], queryFn: beaconApi.targetsDashboard });
  const icps = useQuery({ queryKey: ["icps"], queryFn: beaconApi.icps });
  const detail = useQuery({
    queryKey: ["target", selectedId],
    queryFn: () => beaconApi.target(selectedId!),
    enabled: Boolean(selectedId),
  });
  const hunter = useQuery({
    queryKey: ["hunter-status"],
    queryFn: () => beaconApi.hunterStatus(),
    refetchInterval: 15_000,
  });

  const selected = detail.data ?? list.data?.targets.find((t) => t.id === selectedId) ?? null;

  const startHunter = useMutation({
    mutationFn: (companyId: string) => beaconApi.hunterStart(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hunter-status"] });
      await queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
  });

  const ranked = useMemo(
    () => [...(list.data?.targets ?? [])].sort((a, b) => b.revenue_opportunity_score - a.revenue_opportunity_score),
    [list.data],
  );

  if (list.isLoading && dashboard.isLoading) return <Skeleton className="h-64 w-full" />;
  if (list.isError && dashboard.isError) {
    return (
      <ErrorState
        description="Target Account Intelligence unavailable."
        onRetry={() => {
          void list.refetch();
          void dashboard.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Master Brain</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Target Accounts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          ICP-matched accounts ranked by fit, intent, budget, urgency, accessibility, and competition.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {VIEWS.map((item) => (
          <Button
            key={item}
            size="sm"
            variant={view === item ? "default" : "outline"}
            onClick={() => setView(item)}
          >
            {item}
          </Button>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Stat title="Accounts" value={String(dashboard.data?.total ?? ranked.length)} />
        <Stat title="Avg revenue score" value={(dashboard.data?.avg_revenue_score ?? 0).toFixed(1)} />
        <Stat title="Pipeline ready" value={String(dashboard.data?.pipeline_ready ?? 0)} />
        <Stat title="Hunter triggered" value={String(dashboard.data?.hunter_triggered ?? 0)} />
      </div>

      {view === "ICP Manager" ? (
        <Card>
          <CardHeader>
            <CardTitle>ICP profiles</CardTitle>
            <CardDescription>Configurable Ideal Customer Profiles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(icps.data ?? []).map((icp) => (
              <div key={icp.id} className="rounded-lg border border-border/60 px-3 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">{icp.name}</p>
                  <Badge className="bg-muted text-muted-foreground ring-border">{icp.service_match}</Badge>
                  <Badge className="bg-muted text-muted-foreground ring-border">priority {icp.priority}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {icp.industries.slice(0, 6).join(", ") || "Any industry"} ·{" "}
                  {icp.employee_count_min ?? "?"}–{icp.employee_count_max ?? "?"} employees
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Pains: {icp.pain_points.slice(0, 4).join(", ") || "—"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {view === "Hunter Mode" ? (
        <Card>
          <CardHeader>
            <CardTitle>Hunter Mode</CardTitle>
            <CardDescription>Deep enrichment when revenue score exceeds threshold</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">Latest status: {hunter.data?.status ?? "idle"}</p>
            {hunter.data?.tasks?.length ? (
              <div className="flex flex-wrap gap-2">
                {hunter.data.tasks.map((task) => (
                  <Badge key={task} className="bg-muted text-muted-foreground ring-border">
                    {task}
                  </Badge>
                ))}
              </div>
            ) : null}
            {selected ? (
              <Button
                onClick={() => startHunter.mutate(selected.company_id)}
                disabled={startHunter.isPending}
              >
                {startHunter.isPending ? "Starting…" : `Hunt ${selected.company_name}`}
              </Button>
            ) : (
              <EmptyState title="Select an account" description="Pick a target to launch Hunter Mode." />
            )}
          </CardContent>
        </Card>
      ) : null}

      {view === "Heat Map" || view === "Industries" || view === "Countries" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Industries</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(dashboard.data?.industries ?? {}).map(([key, count]) => (
                <Row key={key} label={key} value={String(count)} />
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Countries</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(dashboard.data?.countries ?? {}).map(([key, count]) => (
                <Row key={key} label={key} value={String(count)} />
              ))}
            </CardContent>
          </Card>
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Heat ranking</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(dashboard.data?.heat ?? []).map((item) => (
                <Row
                  key={item.company_id}
                  label={`${item.company_name} · ${item.tier} · ${item.icp ?? "—"}`}
                  value={item.score.toFixed(1)}
                />
              ))}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {view === "Pipeline" ? (
        <Card>
          <CardHeader>
            <CardTitle>Auto pipeline</CardTitle>
            <CardDescription>Only top-tier accounts proceed to Sales Copilot and Campaigns</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {ranked
              .filter((item) => item.proceed_to_copilot)
              .map((item) => (
                <TargetRow key={item.id} item={item} selected={selectedId === item.id} onSelect={setSelectedId} />
              ))}
            {ranked.filter((item) => item.proceed_to_copilot).length === 0 ? (
              <EmptyState title="No top-tier accounts yet" description="Run TAI scoring to populate pipeline." />
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {["Revenue Ranking", "Why Now", "Buying Signals"].includes(view) ? (
        <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>{view}</CardTitle>
              <CardDescription>{ranked.length} scored accounts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {ranked.length === 0 ? (
                <EmptyState title="No targets" description="Wait for the TAI worker or score opportunities." />
              ) : (
                ranked.map((item) => (
                  <TargetRow key={item.id} item={item} selected={selectedId === item.id} onSelect={setSelectedId} />
                ))
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>{selected?.company_name ?? "Account detail"}</CardTitle>
              <CardDescription>{selected?.why_now || "Select an account"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selected ? (
                <EmptyState title="Select a target" description="Inspect scores, evidence, and why-now." />
              ) : (
                <>
                  <div className="flex flex-wrap gap-2">
                    <Badge>{formatLabel(selected.tier)}</Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {selected.matched_icp_name || "No ICP"}
                    </Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      ROS {selected.revenue_opportunity_score.toFixed(1)}
                    </Badge>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-3">
                    <Score label="Fit" value={selected.fit_score} />
                    <Score label="Intent" value={selected.intent_score} />
                    <Score label="Budget" value={selected.budget_score} />
                    <Score label="Urgency" value={selected.urgency_score} />
                    <Score label="Accessibility" value={selected.accessibility_score} />
                    <Score label="Competition" value={selected.competition_score} />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Buying signals</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selected.buying_signals.map((signal) => (
                        <Badge key={signal} className="bg-muted text-muted-foreground ring-border">
                          {signal}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Evidence</p>
                    <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {selected.evidence_chain.slice(0, 12).map((item) => (
                        <li key={item}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                  {selected.hunter_triggered ? (
                    <Button
                      variant="outline"
                      onClick={() => startHunter.mutate(selected.company_id)}
                      disabled={startHunter.isPending}
                    >
                      Re-run Hunter
                    </Button>
                  ) : null}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="font-display text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border/60 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value.toFixed(1)}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-border/50 px-3 py-2 text-sm">
      <span className="truncate text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function TargetRow({
  item,
  selected,
  onSelect,
}: {
  item: TargetAccountRecord;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item.id)}
      className={`w-full rounded-lg border px-3 py-3 text-left ${
        selected ? "border-primary/50 bg-primary/10" : "border-border/60"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="truncate text-sm font-medium">{item.company_name}</p>
        <span className="text-sm font-semibold">{item.revenue_opportunity_score.toFixed(1)}</span>
      </div>
      <div className="mt-1 flex flex-wrap gap-2">
        <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(item.tier)}</Badge>
        <Badge className="bg-muted text-muted-foreground ring-border">{item.service_match || "—"}</Badge>
      </div>
    </button>
  );
}
