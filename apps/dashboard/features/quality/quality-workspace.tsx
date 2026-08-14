"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatPercent, formatScore } from "@/lib/utils";

export function QualityWorkspace() {
  const dashboard = useQuery({ queryKey: ["quality-dashboard"], queryFn: beaconApi.qualityDashboard });
  const statistics = useQuery({ queryKey: ["quality-statistics"], queryFn: beaconApi.qualityStatistics });
  const rules = useQuery({ queryKey: ["quality-rules"], queryFn: beaconApi.qualityRules });
  const sources = useQuery({ queryKey: ["quality-sources"], queryFn: beaconApi.qualitySources });
  const sourceHealth = useQuery({ queryKey: ["sources-health"], queryFn: beaconApi.sourcesHealth });
  const events = useQuery({
    queryKey: ["quality-events", "quality-page"],
    queryFn: () => beaconApi.qualityEvents({ limit: 30 }),
  });

  if (dashboard.isError && statistics.isError) {
    return <ErrorState description="Quality APIs unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  const dash = dashboard.data?.dashboard ?? {};
  const stats = statistics.data?.statistics ?? {};
  const trend = Array.isArray(dash.trend_graphs)
    ? (dash.trend_graphs as Array<Record<string, unknown>>)
    : Array.isArray(stats.trend)
      ? (stats.trend as Array<Record<string, unknown>>)
      : [];

  const chartData = trend.map((point, index) => ({
    name: String(point.label || point.day || index + 1),
    quality: Number(point.average_quality ?? point.quality ?? point.value ?? 0),
  }));

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Signal Trust</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Quality</h1>
        <p className="text-sm text-muted-foreground">Connected to Quality Engine dashboards, rules, and source health.</p>
      </header>

      {dashboard.isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric label="Acceptance / avg quality" value={formatScore(Number(dash.average_quality ?? stats.average_quality ?? 0), 0)} />
          <Metric label="Spam rate" value={formatPercent(Number(dash.spam_percent ?? stats.spam_percent ?? 0))} />
          <Metric label="Duplicate rate" value={formatPercent(Number(dash.duplicate_percent ?? stats.duplicate_percent ?? 0))} />
          <Metric label="Pipeline latency" value={`${formatScore(Number(dash.pipeline_latency_ms ?? 0), 0)} ms`} />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Quality Trend</CardTitle>
            <CardDescription>From Quality dashboard trend data when available</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      background: "#0f172a",
                      border: "1px solid rgba(148,163,184,0.2)",
                      borderRadius: 12,
                    }}
                  />
                  <Line type="monotone" dataKey="quality" stroke="#2dd4bf" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground">No trend series returned by the API yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Source Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(sourceHealth.data?.sources ?? []).map((source) => (
              <div key={source.source} className="flex items-center justify-between rounded-lg border border-border/50 px-3 py-2">
                <div>
                  <p className="text-sm font-medium">{source.source}</p>
                  <p className="text-xs text-muted-foreground">
                    Failures {source.consecutive_failures} · Latency{" "}
                    {source.average_latency_ms != null ? `${formatScore(source.average_latency_ms, 0)} ms` : "—"}
                  </p>
                </div>
                <Badge className="bg-muted text-muted-foreground ring-border">{source.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quality Rules</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(rules.data?.rules ?? []).map((rule) => (
              <div key={String(rule.id || rule.rule_key)} className="rounded-lg border border-border/50 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{String(rule.name || rule.rule_key)}</p>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    {rule.enabled ? "enabled" : "disabled"}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {String(rule.category)} · priority {String(rule.priority)} · threshold {String(rule.threshold)}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Collector / Source Accuracy</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(sources.data?.sources ?? []).map((source, index) => (
              <div key={`${String(source.source)}-${index}`} className="rounded-lg border border-border/50 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{String(source.source)}</p>
                  <span className="text-muted-foreground">
                    Q {formatScore(Number(source.average_quality ?? 0), 0)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Spam {formatPercent(Number(source.spam_percent ?? 0))} · Dup {formatPercent(Number(source.duplicate_percent ?? 0))} · Signals{" "}
                  {String(source.signals ?? "—")}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Quality Events</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {(events.data?.events ?? []).map((event) => (
            <div key={event.id} className="grid gap-2 rounded-lg border border-border/50 px-3 py-2 md:grid-cols-[1fr_auto_auto]">
              <div>
                <p className="text-sm font-medium">{event.source}</p>
                <p className="text-xs text-muted-foreground">{event.reason_codes.join(", ") || "No reason codes"}</p>
              </div>
              <Badge className="bg-muted text-muted-foreground ring-border">{event.decision}</Badge>
              <p className="text-sm tabular-nums text-muted-foreground">{formatScore(event.overall_quality_score, 0)}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="space-y-2 py-5">
        <p className="text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p className="font-display text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}
