"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

type Tab =
  | "overview"
  | "connectors"
  | "hiring"
  | "funding"
  | "technology"
  | "website"
  | "community"
  | "reviews"
  | "graph"
  | "benchmarks"
  | "freshness"
  | "analytics";

export function GlobalOpportunityWorkspace() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null);

  const dashboard = useQuery({ queryKey: ["goap-dashboard"], queryFn: () => beaconApi.goapDashboard() });
  const connectors = useQuery({ queryKey: ["goap-connectors"], queryFn: () => beaconApi.goapConnectors() });
  const hiring = useQuery({ queryKey: ["goap-hiring"], queryFn: () => beaconApi.goapHiring() });
  const funding = useQuery({ queryKey: ["goap-funding"], queryFn: () => beaconApi.goapFunding() });
  const technology = useQuery({ queryKey: ["goap-technology"], queryFn: () => beaconApi.goapTechnology() });
  const websites = useQuery({ queryKey: ["goap-websites"], queryFn: () => beaconApi.goapWebsites() });
  const community = useQuery({ queryKey: ["goap-community"], queryFn: () => beaconApi.goapCommunity() });
  const reviews = useQuery({ queryKey: ["goap-reviews"], queryFn: () => beaconApi.goapReviews() });
  const benchmarks = useQuery({ queryKey: ["goap-benchmarks"], queryFn: () => beaconApi.goapBenchmarks() });
  const freshness = useQuery({ queryKey: ["goap-freshness"], queryFn: () => beaconApi.goapFreshness() });
  const analytics = useQuery({ queryKey: ["goap-analytics"], queryFn: () => beaconApi.goapAnalytics() });
  const connectorDetail = useQuery({
    queryKey: ["goap-connector", selectedConnector],
    queryFn: () => beaconApi.goapConnector(selectedConnector!),
    enabled: Boolean(selectedConnector),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.goapRefresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["goap-dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-connectors"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-hiring"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-funding"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-technology"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-websites"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-community"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-reviews"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-benchmarks"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-freshness"] });
      await queryClient.invalidateQueries({ queryKey: ["goap-analytics"] });
    },
  });

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "connectors", label: "Connectors" },
    { id: "hiring", label: "Hiring Intelligence" },
    { id: "funding", label: "Funding Intelligence" },
    { id: "technology", label: "Technology Intelligence" },
    { id: "website", label: "Website Intelligence" },
    { id: "community", label: "Community Intelligence" },
    { id: "reviews", label: "Review Intelligence" },
    { id: "graph", label: "Opportunity Graph" },
    { id: "benchmarks", label: "Benchmarks" },
    { id: "freshness", label: "Freshness" },
    { id: "analytics", label: "Analytics" },
  ];

  const analyticsData = useMemo(() => (dashboard.data?.analytics as Record<string, unknown>) ?? analytics.data ?? {}, [dashboard.data, analytics.data]);
  const companies = useMemo(() => (dashboard.data?.companies as Array<Record<string, unknown>>) ?? [], [dashboard.data]);

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Global Opportunity Acquisition unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>GOAP v1</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Global Opportunity Acquisition</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Discover companies most likely to buy software today. Every source scored, benchmarked, and competing.
          </p>
        </div>
        <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
          Refresh sources
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Connectors" value={String(analyticsData.total_connectors ?? connectors.data?.total ?? 0)} />
        <Stat label="Active" value={String(analyticsData.active_connectors ?? 0)} />
        <Stat label="Companies" value={String(analyticsData.unique_companies ?? companies.length)} />
        <Stat label="Avg Freshness" value={String(analyticsData.average_freshness ?? 0)} />
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "default" : "outline"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "overview" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Opportunity Pipeline</CardTitle>
            <CardDescription>Companies with detected buying intent</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {companies.length === 0 ? (
              <EmptyState title="No opportunities yet" description="Refresh to evaluate public sources." />
            ) : (
              companies.map((c) => (
                <div key={String(c.canonical_key)} className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm">
                  <div>
                    <div className="font-medium">{String(c.company_name)}</div>
                    <div className="text-xs text-muted-foreground">{Array.isArray(c.intents) ? (c.intents as string[]).join(", ") : ""}</div>
                  </div>
                  <Badge variant="outline">fresh {String(c.freshness)}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {tab === "connectors" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Source Connectors</CardTitle>
            </CardHeader>
            <CardContent className="max-h-[28rem] space-y-2 overflow-auto">
              {(connectors.data?.connectors ?? []).map((c) => (
                <button
                  key={String(c.connector_id)}
                  className="flex w-full items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-left text-sm"
                  onClick={() => setSelectedConnector(String(c.connector_id))}
                >
                  <span>{String(c.connector_name)}</span>
                  <Badge variant="outline">{String(c.status)}</Badge>
                </button>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Connector Detail</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              {connectorDetail.data ? (
                <pre className="overflow-auto rounded-lg bg-muted/40 p-3 text-xs">{JSON.stringify(connectorDetail.data, null, 2)}</pre>
              ) : (
                <EmptyState title="Select a connector" description="Click a source to inspect contract and status." />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "hiring" && <SimpleList title="Hiring Events" rows={(hiring.data?.events ?? []).map((e) => `${e.company_key} · growth ${e.growth}`)} />}
      {tab === "funding" && <SimpleList title="Funding Events" rows={(funding.data?.events ?? []).map((e) => `${e.company_key} · ${e.round}`)} />}
      {tab === "technology" && (
        <SimpleList title="Technology Hits" rows={(technology.data?.profiles ?? []).map((p) => `${p.company_key} · ${p.technology} (${p.category})`)} />
      )}
      {tab === "website" && (
        <SimpleList
          title="Website Profiles"
          rows={(websites.data?.profiles ?? []).map(
            (p) => `${p.company_name} · modern ${p.modernization_score} · opp ${p.opportunity_score}`,
          )}
        />
      )}
      {tab === "community" && (
        <SimpleList title="Community Signals" rows={(community.data?.signals ?? []).map((s) => `${s.company_key} · conf ${s.confidence}`)} />
      )}
      {tab === "reviews" && <SimpleList title="Review Signals" rows={(reviews.data?.signals ?? []).map((s) => String(s.company_key))} />}
      {tab === "graph" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Opportunity Graph</CardTitle>
            <CardDescription>Company → Industry → Funding → Hiring → Technology → Signals → Outcomes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {companies.slice(0, 12).map((c) => (
              <div key={String(c.canonical_key)} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                <div className="font-medium">{String(c.company_name)}</div>
                <div className="text-xs text-muted-foreground">key {String(c.canonical_key)}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {tab === "benchmarks" && (
        <SimpleList
          title="Source Benchmarks"
          rows={(benchmarks.data?.benchmarks ?? []).map(
            (b) => `#${b.rank ?? (b.payload && (b.payload as Record<string, unknown>).rank)} ${b.connector_id} · ${b.recommendation}`,
          )}
        />
      )}
      {tab === "freshness" && (
        <SimpleList
          title={`Freshness (avg ${String((freshness.data as Record<string, unknown> | undefined)?.average ?? 0)})`}
          rows={(((freshness.data as Record<string, unknown> | undefined)?.scores as Array<Record<string, unknown>>) ?? []).map(
            (s) => `${s.company_name} · ${s.freshness}`,
          )}
        />
      )}
      {tab === "analytics" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-muted/40 p-3 text-xs">{JSON.stringify(analyticsData, null, 2)}</pre>
          </CardContent>
        </Card>
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

function SimpleList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.length === 0 ? (
          <EmptyState title="No data" description="Refresh to populate." />
        ) : (
          rows.map((row, i) => (
            <div key={i} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              {row}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
