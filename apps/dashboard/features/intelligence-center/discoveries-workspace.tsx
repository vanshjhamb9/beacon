"use client";

import { useQuery } from "@tanstack/react-query";
import { Radar, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

export function DiscoveriesWorkspace() {
  const [collector, setCollector] = useState("");
  const [industry, setIndustry] = useState("");
  const [status, setStatus] = useState("");
  const [connector, setConnector] = useState("");
  const [company, setCompany] = useState("");
  const [revenueReadyOnly, setRevenueReadyOnly] = useState(false);
  const [errorsOnly, setErrorsOnly] = useState(false);

  const feed = useQuery({
    queryKey: [
      "discoveries-live",
      collector,
      industry,
      status,
      connector,
      company,
      revenueReadyOnly,
      errorsOnly,
    ],
    queryFn: () =>
      beaconApi.discoveriesLive({
        limit: 80,
        collector: collector || undefined,
        industry: industry || undefined,
        status: status || undefined,
        connector: connector || undefined,
        company: company || undefined,
        revenue_ready_only: revenueReadyOnly,
        errors_only: errorsOnly,
      }),
    refetchInterval: 5_000,
    placeholderData: (prev) => prev,
  });

  const facets = feed.data?.facets;

  const items = useMemo(() => feed.data?.items ?? [], [feed.data]);

  if (feed.isError) {
    return (
      <ErrorState
        title="Discovery Feed unavailable"
        description="API /discoveries/live failed. Run BIC sync or confirm migration 0049."
        onRetry={() => void feed.refetch()}
      />
    );
  }

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Beacon Intelligence Center</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Discoveries</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Live heartbeat of every lifecycle movement — signal to won. Auto-refreshes every 5 seconds.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void feed.refetch()} disabled={feed.isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", feed.isFetching && "animate-spin")} />
          Refresh
        </Button>
      </header>

      <Card className="border-border/60 bg-card/40">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filters</CardTitle>
          <CardDescription>Collector · Industry · Status · Connector · Company</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <SelectFilter label="Collector" value={collector} onChange={setCollector} options={facets?.collectors} />
          <SelectFilter label="Industry" value={industry} onChange={setIndustry} options={facets?.industries} />
          <SelectFilter label="Status" value={status} onChange={setStatus} options={facets?.statuses} />
          <SelectFilter label="Connector" value={connector} onChange={setConnector} options={facets?.connectors} />
          <div>
            <p className="mb-1 text-[11px] uppercase tracking-wide text-muted-foreground">Company</p>
            <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Search company" />
          </div>
          <div className="flex flex-col justify-end gap-2">
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={revenueReadyOnly} onChange={(e) => setRevenueReadyOnly(e.target.checked)} />
              Revenue Ready only
            </label>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={errorsOnly} onChange={(e) => setErrorsOnly(e.target.checked)} />
              Errors only
            </label>
          </div>
        </CardContent>
      </Card>

      {!feed.data ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <Card className="border-border/60 bg-card/40 p-8 text-center text-sm text-muted-foreground">
          No discovery events yet. Trigger <code className="text-xs">POST /intelligence/sync</code> or wait for the BIC beat task.
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const href = item.company_id ? `/lead-explorer?company_id=${item.company_id}` : null;
            const card = (
              <Card
                className={cn(
                  "border-border/60 bg-[#0d1524]/80 transition hover:border-primary/40",
                  item.is_error && "border-rose-500/30",
                  href && "cursor-pointer",
                )}
              >
                <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span className="tabular-nums font-medium text-foreground">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                      {item.collector ? <Badge variant="outline">{item.collector}</Badge> : null}
                      <Badge variant={item.is_error ? "destructive" : "secondary"}>{item.event_type}</Badge>
                      {item.is_revenue_ready && item.event_type !== "Revenue Ready" ? (
                        <Badge>Revenue Ready</Badge>
                      ) : null}
                    </div>
                    <div className="flex items-start gap-2">
                      <Radar className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <div>
                        <p className="font-medium">{item.headline || item.event_type}</p>
                        {item.detail ? <p className="text-sm text-muted-foreground">{item.detail}</p> : null}
                        {item.company_name ? (
                          <p className="mt-1 text-sm">
                            <span className="text-primary">{item.company_name}</span>
                            {item.industry ? <span className="text-muted-foreground"> · {item.industry}</span> : null}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </div>
                  {href ? (
                    <Button size="sm" variant="outline" tabIndex={-1}>
                      Open Company
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            );
            return href ? (
              <Link key={item.id} href={href} className="block">
                {card}
              </Link>
            ) : (
              <div key={item.id}>{card}</div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SelectFilter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options?: string[];
}) {
  return (
    <div>
      <p className="mb-1 text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <select
        className="h-9 w-full rounded-md border border-border/60 bg-background px-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All</option>
        {(options || []).map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
