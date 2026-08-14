"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, RefreshCw, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

export function AnalyticsV2Workspace() {
  const [q, setQ] = useState("");
  const analytics = useQuery({
    queryKey: ["analytics-v2"],
    queryFn: beaconApi.analyticsV2,
    refetchInterval: 30_000,
  });
  const search = useQuery({
    queryKey: ["intelligence-search", q],
    queryFn: () => beaconApi.intelligenceSearch(q),
    enabled: q.trim().length >= 2,
  });

  if (analytics.isError) {
    return <ErrorState description="API /analytics/v2 failed." onRetry={() => void analytics.refetch()} />;
  }

  const data = analytics.data as Record<string, any> | undefined;

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Intelligence Center</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Analytics V2</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Every section filled from deterministic operational data — no placeholders.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void analytics.refetch()} disabled={analytics.isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", analytics.isFetching && "animate-spin")} />
          Refresh
        </Button>
      </header>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-4 w-4" /> Operations Search
          </CardTitle>
          <CardDescription>Search company journeys, events, evidence, and connector history</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search Heroic, Clay, GitHub…" />
          {search.data ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Companies</p>
                {search.data.companies.map((c) => (
                  <Link key={c.id} href={`/lead-explorer?company_id=${c.id}`} className="block rounded-lg border border-border/60 px-3 py-2 text-sm hover:border-primary/40">
                    {c.name} <span className="text-muted-foreground">· {c.domain || "no domain"}</span>
                  </Link>
                ))}
              </div>
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Events</p>
                {search.data.events.slice(0, 8).map((ev, i) => (
                  <div key={i} className="rounded-lg border border-border/60 px-3 py-2 text-xs">
                    <Badge variant="outline">{String(ev.event_type)}</Badge> {String(ev.headline || ev.detail || "")}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {!data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <>
          <SectionGrid title="Discovery" icon={<BarChart3 className="h-4 w-4" />} items={asPairs(data.discovery)} />
          <SectionGrid title="Quality" items={asPairs(data.quality)} />
          <SectionGrid title="Revenue" items={asPairs(data.revenue)} />
          <SectionGrid title="Pipeline" items={asPairs(data.pipeline)} />
          <SectionGrid title="Outreach" items={asPairs(data.outreach)} />
          <SectionGrid title="Enrichment" items={asPairs(data.enrichment)} />
          <SectionGrid title="Decision Makers" items={asPairs(data.decision_makers)} />
          <SectionGrid title="Meetings" items={asPairs(data.meetings)} />
          <SectionGrid title="Forecast" items={asPairs(data.forecast)} />

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Services</CardTitle>
              <CardDescription>Industry / service demand from operational company data</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 md:grid-cols-3">
              {(data.services as Array<Record<string, unknown>> | undefined)?.length ? (
                (data.services as Array<Record<string, unknown>>).map((row) => (
                  <div key={String(row.service)} className="rounded-lg border border-border/60 p-3 text-sm">
                    <p className="font-medium">{String(row.service)}</p>
                    <p className="text-muted-foreground tabular-nums">{String(row.companies ?? row.revenue_ready ?? 0)} companies</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No service segments yet.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Connectors</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="pb-2 pr-3 text-left">Connector</th>
                    <th className="pb-2 pr-3 text-left">RR</th>
                    <th className="pb-2 pr-3 text-left">Emails</th>
                    <th className="pb-2 pr-3 text-left">Cost</th>
                    <th className="pb-2 pr-3 text-left">Success</th>
                    <th className="pb-2 text-left">Win %</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.connectors as Array<Record<string, unknown>> | undefined)?.map((row) => (
                    <tr key={String(row.connector)} className="border-t border-border/50">
                      <td className="py-2 pr-3 capitalize">{String(row.connector).replaceAll("_", " ")}</td>
                      <td className="py-2 pr-3 tabular-nums">{String(row.revenue_ready)}</td>
                      <td className="py-2 pr-3 tabular-nums">{String(row.emails)}</td>
                      <td className="py-2 pr-3 tabular-nums">${String(row.api_cost)}</td>
                      <td className="py-2 pr-3 tabular-nums">{String(row.success_pct)}%</td>
                      <td className="py-2 tabular-nums">{String(row.win_pct)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Industries</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 md:grid-cols-3">
              {(data.industries as Array<Record<string, unknown>> | undefined)?.map((row) => (
                <Link
                  key={String(row.industry)}
                  href={`/lead-explorer?q=${encodeURIComponent(String(row.industry))}`}
                  className="rounded-lg border border-border/60 p-3 text-sm transition hover:border-primary/40"
                >
                  <p className="font-medium">{String(row.industry)}</p>
                  <p className="text-muted-foreground tabular-nums">{String(row.count)} companies</p>
                </Link>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Heatmap</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
              {(data.heatmap as Array<Record<string, unknown>> | undefined)?.map((cell) => (
                <div
                  key={String(cell.stage)}
                  className={cn(
                    "rounded-xl border p-3",
                    cell.tone === "green" && "border-emerald-500/40 bg-emerald-500/10",
                    cell.tone === "yellow" && "border-amber-500/40 bg-amber-500/10",
                    cell.tone === "red" && "border-rose-500/40 bg-rose-500/10",
                  )}
                >
                  <p className="text-xs uppercase text-muted-foreground">{String(cell.stage)}</p>
                  <p className="text-xl font-semibold tabular-nums">{String(cell.count)}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function asPairs(obj: unknown): Array<[string, string]> {
  if (!obj || typeof obj !== "object") return [];
  return Object.entries(obj as Record<string, unknown>)
    .filter(([, v]) => v !== null && typeof v !== "object")
    .map(([k, v]) => [k.replaceAll("_", " "), String(v)]);
}

function SectionGrid({
  title,
  items,
  icon,
}: {
  title: string;
  items: Array<[string, string]>;
  icon?: React.ReactNode;
}) {
  if (!items.length) return null;
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        {items.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-border/60 p-3">
            <p className="text-xs capitalize text-muted-foreground">{label}</p>
            <p className="mt-1 text-xl font-semibold tabular-nums">{value}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
