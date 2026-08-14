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
  | "company"
  | "committee"
  | "contacts"
  | "technology"
  | "website"
  | "business"
  | "ai"
  | "sales"
  | "graph"
  | "verification"
  | "confidence"
  | "timeline";

export function AccountIntelligenceWorkspace() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const dashboard = useQuery({ queryKey: ["aip-dashboard"], queryFn: () => beaconApi.aipDashboard() });
  const search = useQuery({
    queryKey: ["aip-search", q],
    queryFn: () => beaconApi.aipSearch(q ? { q } : {}),
  });
  const company = useQuery({
    queryKey: ["aip-company", selectedId],
    queryFn: () => beaconApi.aipCompany(selectedId!),
    enabled: Boolean(selectedId),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.aipRefresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["aip-dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["aip-search"] });
    },
  });

  const accounts = useMemo(() => (dashboard.data?.accounts as Array<Record<string, unknown>>) ?? [], [dashboard.data]);
  const pack = company.data ?? null;

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "company", label: "Company" },
    { id: "committee", label: "Buying Committee" },
    { id: "contacts", label: "Verified Contacts" },
    { id: "technology", label: "Technology" },
    { id: "website", label: "Website" },
    { id: "business", label: "Business Profile" },
    { id: "ai", label: "AI Readiness" },
    { id: "sales", label: "Sales Readiness" },
    { id: "graph", label: "Relationship Graph" },
    { id: "verification", label: "Verification" },
    { id: "confidence", label: "Confidence" },
    { id: "timeline", label: "Timeline" },
  ];

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Account Intelligence unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>AIP v1</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Account Intelligence</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Master enrichment — transform every opportunity into a complete sales-ready account. No fabricated contacts.
          </p>
        </div>
        <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
          Refresh accounts
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Accounts" value={String(dashboard.data?.total_accounts ?? 0)} />
        <Stat label="Founder Ready" value={String((dashboard.data?.by_sales_readiness as Record<string, number> | undefined)?.founder_ready ?? 0)} />
        <Stat label="Sales Ready" value={String((dashboard.data?.by_sales_readiness as Record<string, number> | undefined)?.sales_ready ?? 0)} />
        <Stat label="Version" value={String(dashboard.data?.scoring_version ?? "aip-v1")} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          placeholder="Search company, industry, tech, DM…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <span className="text-xs text-muted-foreground">{search.data?.total ?? 0} results</span>
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
            <CardTitle className="text-base">Accounts</CardTitle>
            <CardDescription>Append-only enrichment snapshots</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(search.data?.results?.length ? search.data.results : accounts).length === 0 ? (
              <EmptyState title="No accounts" description="Refresh after GOAP discoveries." />
            ) : (
              (search.data?.results?.length ? search.data.results : accounts).map((a) => (
                <button
                  key={String(a.id || a.profile_id || a.company_id)}
                  className="flex w-full items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-left text-sm"
                  onClick={() => setSelectedId(String(a.company_id))}
                >
                  <div>
                    <div className="font-medium">{String(a.company_name)}</div>
                    <div className="text-xs text-muted-foreground">conf {String(a.overall_confidence)}</div>
                  </div>
                  <Badge variant="outline">{String(a.sales_readiness_category)}</Badge>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {pack && tab === "company" && <JsonCard title="Company Profile" data={pack.profile} />}
      {pack && tab === "committee" && <ListCard title="Buying Committee" rows={(pack.buying_committee as Array<Record<string, unknown>>) ?? []} />}
      {pack && tab === "contacts" && <ListCard title="Verified Contacts" rows={(pack.verified_contacts as Array<Record<string, unknown>>) ?? []} />}
      {pack && tab === "technology" && <JsonCard title="Technology" data={pack.technology} />}
      {pack && tab === "website" && <JsonCard title="Website" data={pack.website} />}
      {pack && tab === "business" && <JsonCard title="Business" data={pack.business} />}
      {pack && tab === "ai" && <JsonCard title="AI Readiness" data={pack.ai_readiness} />}
      {pack && tab === "sales" && <JsonCard title="Sales Readiness" data={pack.sales_readiness} />}
      {pack && tab === "graph" && <JsonCard title="Relationship Graph" data={pack.relationship_graph} />}
      {pack && tab === "verification" && <JsonCard title="Verification" data={pack.verification_history} />}
      {pack && tab === "confidence" && <JsonCard title="Confidence" data={pack.confidence} />}
      {pack && tab === "timeline" && <JsonCard title="Timeline" data={pack.timeline} />}
      {!pack && tab !== "overview" && <EmptyState title="Select an account" description="Choose an account from Overview." />}
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

function JsonCard({ title, data }: { title: string; data: unknown }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="max-h-[28rem] overflow-auto rounded-lg bg-muted/40 p-3 text-xs">{JSON.stringify(data, null, 2)}</pre>
      </CardContent>
    </Card>
  );
}

function ListCard({ title, rows }: { title: string; rows: Array<Record<string, unknown>> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.length === 0 ? (
          <EmptyState title="None" description="No fabricated contacts — only observed public people." />
        ) : (
          rows.map((r, i) => (
            <div key={i} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              <div className="font-medium">{String(r.full_name)}</div>
              <div className="text-xs text-muted-foreground">
                {String(r.role || r.verification || "")} · conf {String(r.confidence)}
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
