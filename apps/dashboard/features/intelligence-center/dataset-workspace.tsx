"use client";

import { useQuery } from "@tanstack/react-query";
import { Database, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

const STAT_KEYS: Array<{ key: string; label: string }> = [
  { key: "signals_collected", label: "Signals Collected" },
  { key: "duplicates", label: "Duplicates" },
  { key: "spam", label: "Spam" },
  { key: "dead_websites", label: "Dead Websites" },
  { key: "working_websites", label: "Working Websites" },
  { key: "emails_found", label: "Emails Found" },
  { key: "verified_emails", label: "Verified Emails" },
  { key: "generic_emails", label: "Generic Emails" },
  { key: "founder_emails", label: "Founder Emails" },
  { key: "decision_makers", label: "Decision Makers" },
  { key: "revenue_ready", label: "Revenue Ready" },
  { key: "outreach_ready", label: "Outreach Ready" },
];

type RangeKey = "today" | "yesterday" | "7" | "30";

export function DatasetWorkspace() {
  const [range, setRange] = useState<RangeKey>("30");
  const [frameIdx, setFrameIdx] = useState(0);
  const [selectedStat, setSelectedStat] = useState<string | null>(null);

  const days = range === "7" ? 7 : 30;
  const stats = useQuery({
    queryKey: ["dataset-statistics", days],
    queryFn: () => beaconApi.datasetStatistics(days),
    refetchInterval: 30_000,
  });
  const replay = useQuery({
    queryKey: ["pipeline-replay"],
    queryFn: beaconApi.pipelineReplay,
    refetchInterval: 60_000,
  });

  const activeStats = useMemo(() => {
    if (!stats.data) return null;
    if (range === "today") return stats.data.today;
    if (range === "yesterday") return stats.data.yesterday;
    return stats.data.current;
  }, [stats.data, range]);

  const todayEmpty = useMemo(() => {
    if (!stats.data?.today) return false;
    const t = stats.data.today;
    return (
      Number(t.signals_collected ?? 0) === 0 &&
      Number(t.revenue_ready ?? 0) === 0 &&
      Number(t.emails_found ?? 0) === 0
    );
  }, [stats.data]);

  const trendRows = useMemo(() => {
    const rows = stats.data?.trends ?? [];
    if (range === "7") return rows.slice(-7);
    if (range === "30") return rows.slice(-30);
    return rows.slice(-7);
  }, [stats.data, range]);

  const frames = replay.data?.frames ?? [];
  const frame = frames[Math.min(frameIdx, Math.max(frames.length - 1, 0))];

  if (stats.isError) {
    return <ErrorState description="API /dataset/statistics failed." onRetry={() => void stats.refetch()} />;
  }

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Intelligence Center</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Dataset</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Deterministic dataset explorer — duplicates, spam, verification, enrichment coverage, and pipeline replay.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["today", "yesterday", "7", "30"] as const).map((key) => (
            <Button key={key} size="sm" variant={range === key ? "default" : "outline"} onClick={() => setRange(key)}>
              {key === "7" ? "7 days" : key === "30" ? "30 days" : key}
            </Button>
          ))}
          <Button variant="outline" size="sm" onClick={() => void stats.refetch()} disabled={stats.isFetching}>
            <RefreshCw className={cn("mr-2 h-4 w-4", stats.isFetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </header>

      {!stats.data || !activeStats ? (
        <Skeleton className="h-48 w-full" />
      ) : (
        <>
          {range === "today" && todayEmpty ? (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              No collection activity today yet (workers may be idle). Switch to{" "}
              <button type="button" className="underline" onClick={() => setRange("30")}>
                30 days
              </button>{" "}
              or{" "}
              <button type="button" className="underline" onClick={() => setRange("yesterday")}>
                yesterday
              </button>{" "}
              for populated totals. Rates below still use lifetime dataset quality.
            </div>
          ) : null}
          <section className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
            {STAT_KEYS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedStat(key)}
                className="text-left"
              >
                <Card
                  className={cn(
                    "border-border/60 bg-card/40 transition hover:border-primary/40",
                    selectedStat === key && "border-primary/50",
                  )}
                >
                  <CardHeader className="pb-2">
                    <CardDescription>{label}</CardDescription>
                    <CardTitle className="text-2xl tabular-nums">
                      {Number(activeStats[key] ?? 0).toLocaleString()}
                    </CardTitle>
                  </CardHeader>
                </Card>
              </button>
            ))}
          </section>

          <div className="grid gap-4 md:grid-cols-4">
            <RateCard label="Duplicate rate" value={Number(stats.data.current.duplicate_rate ?? 0)} />
            <RateCard label="Spam rate" value={Number(stats.data.current.spam_rate ?? 0)} />
            <RateCard label="Verification rate" value={Number(stats.data.current.verification_rate ?? 0)} />
            <RateCard label="Enrichment coverage" value={Number(stats.data.current.enrichment_coverage ?? 0)} />
          </div>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Daily Trends</CardTitle>
              <CardDescription>
                {range === "7" ? "Last 7 days" : range === "30" ? "Last 30 days" : "Recent daily series"}
                {selectedStat ? ` · highlighting ${selectedStat.replaceAll("_", " ")}` : ""}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trendRows.length === 0 ? (
                <p className="text-sm text-muted-foreground">No trend rows yet — sync BIC to seed daily stats.</p>
              ) : (
                <div className="space-y-3">
                  <TrendBars
                    rows={trendRows}
                    metric={selectedStat || "signals_collected"}
                  />
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-sm">
                      <thead className="text-xs text-muted-foreground">
                        <tr>
                          <th className="pb-2 pr-3 text-left">Date</th>
                          <th className="pb-2 pr-3 text-left">Signals</th>
                          <th className="pb-2 pr-3 text-left">Duplicates</th>
                          <th className="pb-2 pr-3 text-left">Emails</th>
                          <th className="pb-2 pr-3 text-left">DMs</th>
                          <th className="pb-2 text-left">RR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trendRows.map((row) => (
                          <tr key={String(row.date)} className="border-t border-border/50">
                            <td className="py-2 pr-3">{String(row.date)}</td>
                            <td className="py-2 pr-3 tabular-nums">{Number(row.signals_collected ?? 0)}</td>
                            <td className="py-2 pr-3 tabular-nums">{Number(row.duplicates ?? 0)}</td>
                            <td className="py-2 pr-3 tabular-nums">{Number(row.emails_found ?? 0)}</td>
                            <td className="py-2 pr-3 tabular-nums">{Number(row.decision_makers ?? 0)}</td>
                            <td className="py-2 tabular-nums">{Number(row.revenue_ready ?? 0)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Intelligence Heatmap</CardTitle>
              <CardDescription>Collector → Company → Website → Email → DM → Revenue Ready</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
              {(stats.data.heatmap ?? []).map((cell) => (
                <div
                  key={cell.stage}
                  className={cn(
                    "rounded-xl border p-3",
                    cell.tone === "green" && "border-emerald-500/40 bg-emerald-500/10",
                    cell.tone === "yellow" && "border-amber-500/40 bg-amber-500/10",
                    cell.tone === "red" && "border-rose-500/40 bg-rose-500/10",
                  )}
                >
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{cell.stage.replaceAll("_", " ")}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums">{cell.count}</p>
                  <p className="text-xs text-muted-foreground">{cell.success_pct}% · {cell.failures} fails</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-4 w-4" /> Live Pipeline Replay
              </CardTitle>
              <CardDescription>Grafana-style reconstruction of funnel movement from append-only events</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {frames.length === 0 ? (
                <p className="text-sm text-muted-foreground">No replay frames yet. Sync BIC to seed hourly frames.</p>
              ) : (
                <>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(frames.length - 1, 0)}
                    value={Math.min(frameIdx, frames.length - 1)}
                    onChange={(e) => setFrameIdx(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex flex-wrap gap-2 text-xs">
                    {frames.map((f, i) => (
                      <Badge key={`${f.hour}-${i}`} variant={i === frameIdx ? "default" : "outline"} className="cursor-pointer" onClick={() => setFrameIdx(i)}>
                        {f.hour}
                      </Badge>
                    ))}
                  </div>
                  {frame ? (
                    <div className="grid gap-3 sm:grid-cols-4 xl:grid-cols-8">
                      {(
                        [
                          ["Signals", frame.signals],
                          ["Companies", frame.companies],
                          ["Websites", frame.websites],
                          ["Emails", frame.emails],
                          ["DMs", frame.decision_makers],
                          ["Sales Ready", frame.sales_ready],
                          ["RR", frame.revenue_ready],
                          ["Contacted", frame.contacted],
                        ] as const
                      ).map(([label, value]) => (
                        <div key={label} className="rounded-lg border border-border/60 p-3">
                          <p className="text-xs text-muted-foreground">{label}</p>
                          <p className="text-xl font-semibold tabular-nums">{value}</p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {frame?.movements?.length ? (
                    <div className="max-h-48 space-y-1 overflow-y-auto font-mono text-xs">
                      {frame.movements.map((m, i) => (
                        <div key={i} className="rounded border border-border/40 bg-[#0d1524] px-2 py-1">
                          {String(m.at || "").slice(11, 19)} · {String(m.event_type)} · {String(m.company || "—")}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function RateCard({ label, value }: { label: string; value: number }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tabular-nums">{value}%</CardTitle>
      </CardHeader>
    </Card>
  );
}

function TrendBars({
  rows,
  metric,
}: {
  rows: Array<Record<string, unknown>>;
  metric: string;
}) {
  const values = rows.map((r) => Number(r[metric] ?? 0));
  const max = Math.max(...values, 1);
  return (
    <div className="flex h-32 items-end gap-1">
      {rows.map((row, i) => {
        const value = Number(row[metric] ?? 0);
        const height = Math.max((value / max) * 100, value > 0 ? 4 : 1);
        return (
          <div key={`${String(row.date)}-${i}`} className="flex flex-1 flex-col items-center gap-1" title={`${String(row.date)}: ${value}`}>
            <div className="w-full rounded-t bg-primary/70" style={{ height: `${height}%` }} />
            <span className="truncate text-[10px] text-muted-foreground">{String(row.date).slice(5)}</span>
          </div>
        );
      })}
    </div>
  );
}
