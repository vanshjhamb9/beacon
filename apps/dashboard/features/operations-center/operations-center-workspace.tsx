"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowDown,
  Gauge,
  Radio,
  RefreshCw,
  Server,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import {
  beaconApi,
  type OperationsCenterConnector,
  type OperationsCenterLive,
  type OperationsCenterStage,
} from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

const STAGE_LABELS: Record<string, string> = {
  signals: "Signals",
  identity_candidates: "Identity Candidates",
  verified_websites: "Verified Websites",
  companies: "Companies",
  emails: "Emails",
  decision_makers: "Decision Makers",
  sales_ready: "Sales Ready",
  revenue_ready: "Revenue Ready",
  contacted: "Contacted",
  meetings: "Meetings",
  won: "Won",
};

function fmt(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}

function money(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function deltaBadge(delta: number | null | undefined) {
  if (delta == null) return null;
  const up = delta >= 0;
  return (
    <span className={cn("text-xs font-medium", up ? "text-emerald-300" : "text-rose-300")}>
      {up ? "↑" : "↓"} {Math.abs(delta)}%
    </span>
  );
}

function healthTone(status?: string) {
  const value = (status || "").toLowerCase();
  if (["healthy", "running", "connected", "green", "true"].includes(value)) return "default" as const;
  if (["degraded", "idle", "waiting_token", "yellow", "warning"].includes(value)) return "secondary" as const;
  return "destructive" as const;
}

function connectorLabel(name: string) {
  return name
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function OperationsCenterWorkspace() {
  const live = useQuery({
    queryKey: ["operations-center-live"],
    queryFn: beaconApi.operationsCenterLive,
    // Live payload can be heavy; 5s stampedes the API and leaves the UI blank.
    refetchInterval: 15_000,
    staleTime: 10_000,
    placeholderData: (previous) => previous,
  });

  if (live.isError) {
    return (
      <ErrorState
        title="Operations Center unavailable"
        description="API /operations/live failed. Confirm API + Postgres + migrations (20260726_0048)."
        onRetry={() => void live.refetch()}
      />
    );
  }

  const data = live.data;

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Beacon Operations Center</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Operations</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Real-time pipeline health from signal collection to Revenue Ready. Auto-refreshes every 5 seconds.
            No SQL. No logs. No terminal.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/operations/runtime">Runtime infra</Link>
          </Button>
          <Button variant="outline" size="sm" onClick={() => void live.refetch()} disabled={live.isFetching}>
            <RefreshCw className={cn("mr-2 h-4 w-4", live.isFetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </header>

      {!data ? (
        <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-8">
          {Array.from({ length: 8 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : (
        <>
          <HealthBanner health={data.health} generatedAt={data.generated_at} />

          <section className="grid gap-3 grid-cols-2 md:grid-cols-4 xl:grid-cols-8">
            <TopCard label="Signals Today" card={data.cards.signals} />
            <TopCard label="Verified" card={data.cards.verified} />
            <TopCard label="Emails" card={data.cards.emails} />
            <TopCard label="Decision Makers" card={data.cards.decision_makers} />
            <TopCard label="Sales Ready" card={data.cards.sales_ready} />
            <TopCard label="Revenue Ready" card={data.cards.revenue_ready} />
            <TopCard label="Meetings" card={data.cards.meetings} />
            <TopCard
              label="Pipeline"
              card={{ current: data.cards.pipeline?.value, today: undefined, delta_pct: null }}
              moneyFormat
            />
          </section>

          <LivePipeline stages={data.pipeline} />
          <div className="grid gap-6 xl:grid-cols-2">
            <ConnectorHealthTable connectors={data.connectors} />
            <PipelineConversion conversions={data.conversions} />
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <DailyTimeline timeline={data.timeline} />
            <TodayProgressCard progress={data.progress} revenue={data.revenue} />
          </div>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            <WorkerStatus workers={data.workers} />
            <QueueStatus queues={data.queues} />
            <TopFailures failures={data.failures} />
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <RealtimeFeed feed={data.feed} />
            <RevenueEngine revenue={data.revenue} />
          </div>
          <SourceMap sourceMap={data.source_map} />
        </>
      )}
    </div>
  );
}

function HealthBanner({
  health,
  generatedAt,
}: {
  health: OperationsCenterLive["health"];
  generatedAt: string;
}) {
  const tone =
    health.tone === "GREEN"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
      : health.tone === "RED"
        ? "border-rose-500/30 bg-rose-500/10 text-rose-100"
        : "border-amber-500/30 bg-amber-500/10 text-amber-100";
  return (
    <div className={cn("rounded-xl border px-4 py-3 text-sm", tone)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <Radio className="h-4 w-4" />
          {health.summary}
        </div>
        <p className="text-xs opacity-70">Updated {new Date(generatedAt).toLocaleTimeString()}</p>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs opacity-90">
        <span>Collecting: {health.collecting ? "yes" : "no"}</span>
        <span>
          Connectors: {health.connectors_healthy}/{health.connectors_total}
        </span>
        <span>
          Workers: {health.workers_running}/{health.workers_total}
        </span>
        {health.biggest_bottleneck ? <span>Bottleneck: {health.biggest_bottleneck}</span> : null}
      </div>
    </div>
  );
}

function TopCard({
  label,
  card,
  moneyFormat,
}: {
  label: string;
  card?: { current?: number; today?: number; delta_pct?: number | null; value?: number };
  moneyFormat?: boolean;
}) {
  const primary = moneyFormat ? money(card?.current ?? card?.value) : fmt(card?.today ?? card?.current);
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tabular-nums">{primary}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{moneyFormat ? "pipeline" : `current ${fmt(card?.current)}`}</span>
        {deltaBadge(card?.delta_pct)}
      </CardContent>
    </Card>
  );
}

function LivePipeline({ stages }: { stages: OperationsCenterStage[] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Workflow className="h-4 w-4" /> Live Pipeline
        </CardTitle>
        <CardDescription>Current · Today · Yesterday · 7-day trend</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {stages.map((stage, index) => (
            <div key={stage.stage} className="flex items-center gap-3">
              <div className="min-w-[150px] rounded-xl border border-border/60 bg-[#0d1524] p-3">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  {STAGE_LABELS[stage.stage] || stage.stage}
                </p>
                <p className="mt-1 text-2xl font-semibold tabular-nums">{fmt(stage.today)}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Current {fmt(stage.current)} · Yday {fmt(stage.yesterday)}
                </p>
                <div className="mt-2 flex items-center justify-between">
                  {deltaBadge(stage.delta_pct)}
                  <MiniSpark values={stage.trend_7d} />
                </div>
              </div>
              {index < stages.length - 1 ? (
                <ArrowDown className="hidden h-4 w-4 shrink-0 rotate-[-90deg] text-muted-foreground xl:block" />
              ) : null}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function MiniSpark({ values }: { values: number[] }) {
  if (!values?.length) return <span className="text-[10px] text-muted-foreground">—</span>;
  const max = Math.max(...values, 1);
  return (
    <div className="flex h-4 items-end gap-0.5">
      {values.map((value, index) => (
        <span
          key={index}
          className="w-1 rounded-sm bg-emerald-400/70"
          style={{ height: `${Math.max((value / max) * 100, 8)}%` }}
        />
      ))}
    </div>
  );
}

function ConnectorHealthTable({ connectors }: { connectors: OperationsCenterConnector[] }) {
  const active = connectors.filter(
    (c) => c.enabled || c.records_total > 0 || !["disabled", "idle"].includes(c.status),
  );
  const rows = active.length ? active : connectors.filter((c) => c.enabled).slice(0, 12);
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-4 w-4" /> Connector Health
        </CardTitle>
        <CardDescription>Collectors + reserved enrichment providers</CardDescription>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr>
              <th className="pb-2 pr-3">Connector</th>
              <th className="pb-2 pr-3">Healthy</th>
              <th className="pb-2 pr-3">Today</th>
              <th className="pb-2 pr-3">Success %</th>
              <th className="pb-2 pr-3">Runtime</th>
              <th className="pb-2 pr-3">Rate Limit</th>
              <th className="pb-2">Errors</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.connector} className="border-t border-border/50">
                <td className="py-2 pr-3 font-medium">
                  <div>{connectorLabel(row.connector)}</div>
                  {row.detail ? <div className="text-[11px] text-muted-foreground">{row.detail}</div> : null}
                </td>
                <td className="py-2 pr-3">
                  <Badge variant={healthTone(row.status)}>{row.status}</Badge>
                </td>
                <td className="py-2 pr-3 tabular-nums">{fmt(row.records_today)}</td>
                <td className="py-2 pr-3 tabular-nums">{row.success_rate}%</td>
                <td className="py-2 pr-3 tabular-nums">{row.avg_runtime ? `${row.avg_runtime}s` : "—"}</td>
                <td className="py-2 pr-3">{row.rate_limited ? "Yes" : "No"}</td>
                <td className="py-2 tabular-nums">{fmt(row.error_count)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function PipelineConversion({
  conversions,
}: {
  conversions: OperationsCenterLive["conversions"];
}) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Gauge className="h-4 w-4" /> Pipeline Conversion
        </CardTitle>
        <CardDescription>Conversion % and drop % between stages</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {conversions.slice(0, 8).map((step) => (
          <div key={`${step.from_stage}-${step.to_stage}`} className="rounded-lg border border-border/60 p-3">
            <div className="flex items-center justify-between gap-3 text-sm">
              <div>
                <p className="font-medium">
                  {STAGE_LABELS[step.from_stage] || step.from_stage}{" "}
                  <span className="text-muted-foreground">→</span>{" "}
                  {STAGE_LABELS[step.to_stage] || step.to_stage}
                </p>
                <p className="text-xs text-muted-foreground">
                  {fmt(step.from_count)} → {fmt(step.to_count)}
                </p>
              </div>
              <div className="text-right text-xs">
                {step.from_count === 0 && step.to_count > 0 ? (
                  <>
                    <p className="text-sky-300">bypass / parallel path</p>
                    <p className="text-muted-foreground">not a drop</p>
                  </>
                ) : step.to_count > step.from_count && step.from_count > 0 ? (
                  <>
                    <p className="text-sky-300">expansion</p>
                    <p className="text-emerald-300">{step.conversion_pct}% retained</p>
                  </>
                ) : (
                  <>
                    <p className="text-emerald-300">{step.conversion_pct}% conversion</p>
                    <p className="text-rose-300">{step.drop_pct}% drop</p>
                  </>
                )}
              </div>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted/40">
              <div
                className="h-full rounded-full bg-emerald-400/80"
                style={{ width: `${Math.min(step.conversion_pct, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DailyTimeline({ timeline }: { timeline: OperationsCenterLive["timeline"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Daily Timeline</CardTitle>
        <CardDescription>Hourly progress for today</CardDescription>
      </CardHeader>
      <CardContent className="max-h-[360px] space-y-2 overflow-y-auto">
        {timeline.length === 0 ? (
          <p className="text-sm text-muted-foreground">No hourly snapshots yet. Beat will write one each hour.</p>
        ) : (
          timeline.map((row) => (
            <div key={row.hour} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
              <p className="font-medium tabular-nums">{row.hour}</p>
              <p className="text-xs text-muted-foreground">
                Collected {fmt(row.collected)} · Verified {fmt(row.verified)} · Emails +{fmt(row.emails)} · DM{" "}
                {fmt(row.decision_makers)} · RR {fmt(row.revenue_ready)}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function TodayProgressCard({
  progress,
  revenue,
}: {
  progress: OperationsCenterLive["progress"];
  revenue: OperationsCenterLive["revenue"];
}) {
  const positive = progress.difference >= 0;
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Today&apos;s Progress</CardTitle>
        <CardDescription>Revenue Ready movement since start of day</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-3">
        <Metric label="Started Day" value={fmt(progress.started_revenue_ready)} />
        <Metric label="Current" value={fmt(progress.current_revenue_ready)} />
        <Metric
          label="Difference"
          value={`${positive ? "+" : ""}${fmt(progress.difference)}`}
          hint={positive ? "gained" : "lost"}
        />
        <Metric label="Meetings" value={fmt(revenue.meetings)} />
        <Metric label="Won" value={fmt(revenue.won)} />
        <Metric label="Projected" value={money(revenue.projected)} />
      </CardContent>
    </Card>
  );
}

function WorkerStatus({ workers }: { workers: OperationsCenterLive["workers"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Worker Status</CardTitle>
        <CardDescription>Celery worker families</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {workers.map((worker) => (
          <div key={worker.worker_name} className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2">
            <div>
              <p className="text-sm font-medium capitalize">{worker.worker_name.replaceAll("_", " ")}</p>
              <p className="text-xs text-muted-foreground">
                Queue {fmt(worker.queue_size)} · done {fmt(worker.jobs_completed)}
              </p>
            </div>
            <Badge variant={healthTone(worker.status)}>{worker.status}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function QueueStatus({ queues }: { queues: OperationsCenterLive["queues"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Queues</CardTitle>
        <CardDescription>Pending jobs</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2">
        {queues.map((queue) => (
          <div key={queue.name} className="rounded-lg border border-border/60 p-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">{queue.name} queue</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{fmt(queue.pending)}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function TopFailures({ failures }: { failures: OperationsCenterLive["failures"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TriangleAlert className="h-4 w-4" /> Top Failures
        </CardTitle>
        <CardDescription>From append-only ingestion events</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {failures.length === 0 ? (
          <p className="text-sm text-muted-foreground">No failures recorded yet.</p>
        ) : (
          failures.map((failure) => (
            <div key={failure.reason} className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-sm">
              <span className="pr-3">{failure.reason}</span>
              <span className="tabular-nums font-medium">{fmt(failure.count)}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function RealtimeFeed({ feed }: { feed: OperationsCenterLive["feed"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4" /> Real-time Feed
        </CardTitle>
        <CardDescription>Grafana-style live event stream · click company → Lead Explorer</CardDescription>
      </CardHeader>
      <CardContent className="max-h-[360px] space-y-2 overflow-y-auto font-mono text-xs">
        {feed.length === 0 ? (
          <p className="font-sans text-sm text-muted-foreground">Waiting for collector events…</p>
        ) : (
          feed.map((item, index) => {
            const href = item.company
              ? `/lead-explorer?q=${encodeURIComponent(item.company)}`
              : "/lead-explorer";
            return (
              <Link
                key={`${item.timestamp}-${index}`}
                href={href}
                className="block rounded border border-border/40 bg-[#0d1524] px-3 py-2 transition hover:border-primary/40"
              >
                <span className="text-muted-foreground">{new Date(item.timestamp).toLocaleTimeString()}</span>{" "}
                <span>{item.message}</span>
              </Link>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

function RevenueEngine({ revenue }: { revenue: OperationsCenterLive["revenue"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Revenue Engine</CardTitle>
        <CardDescription>Pipeline value and outcomes</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2">
        <Metric label="Pipeline" value={money(revenue.pipeline)} />
        <Metric label="Projected" value={money(revenue.projected)} />
        <Metric label="Meetings" value={fmt(revenue.meetings)} />
        <Metric label="Won" value={fmt(revenue.won)} />
      </CardContent>
    </Card>
  );
}

function SourceMap({ sourceMap }: { sourceMap: OperationsCenterLive["source_map"] }) {
  return (
    <Card className="border-border/60 bg-card/40">
      <CardHeader>
        <CardTitle>Live Source Map</CardTitle>
        <CardDescription>Per-connector funnel: Signals → Verified → Emails → DM → RR</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {sourceMap.length === 0 ? (
          <p className="text-sm text-muted-foreground">No source activity today yet.</p>
        ) : (
          sourceMap.map((row) => (
            <div key={row.connector} className="rounded-xl border border-border/60 bg-[#0d1524] p-3 text-sm">
              <p className="font-medium">{connectorLabel(row.connector)}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {fmt(row.signals)} → Verified {fmt(row.verified)} → Emails {fmt(row.emails)} → DM{" "}
                {fmt(row.decision_makers)} → RR {fmt(row.revenue_ready)}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-border/60 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums">{value}</p>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
