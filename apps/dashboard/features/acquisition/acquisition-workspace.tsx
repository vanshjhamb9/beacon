"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatLabel, formatRelativeTime, formatScore, scoreTone } from "@/lib/utils";

export function AcquisitionWorkspace() {
  const dashboard = useQuery({
    queryKey: ["acquisition-dashboard"],
    queryFn: () => beaconApi.acquisitionDashboard(),
    refetchInterval: 60_000,
  });
  const alerts = useQuery({
    queryKey: ["acquisition-alerts"],
    queryFn: () => beaconApi.acquisitionAlerts(),
    refetchInterval: 60_000,
  });
  const report = useQuery({
    queryKey: ["acquisition-daily-report"],
    queryFn: () => beaconApi.acquisitionDailyReport(),
    retry: false,
  });

  if (dashboard.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (dashboard.isError || !dashboard.data) {
    return (
      <ErrorState
        description="Acquisition dashboard unavailable."
        onRetry={() => void dashboard.refetch()}
      />
    );
  }

  const data = dashboard.data;

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Data Acquisition</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Connector Health</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Coverage, yield, latency, duplicates, and alerts across compliant public collectors.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Coverage score"
          value={`${formatScore(data.overall_coverage_score, 0)}`}
          tone={scoreTone(data.overall_coverage_score)}
        />
        <Metric label="Signals (24h)" value={String(data.signals_24h)} />
        <Metric label="Companies (24h)" value={String(data.companies_24h)} />
        <Metric
          label="High-value opps (24h)"
          value={String(data.high_value_opportunities_24h)}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Connector Leaderboard</CardTitle>
            <CardDescription>Sources ranked by high-value opportunity contribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.leaderboard.length === 0 ? (
              <EmptyState title="No benchmarks yet" description="Run collectors to populate rankings." />
            ) : (
              data.leaderboard.map((item) => (
                <div key={item.source} className="rounded-lg border border-border/60 px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium">
                      #{item.rank} {formatLabel(item.source)}
                    </p>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      Quality {formatScore(item.quality_score, 0)}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{item.explanation}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    HV yield {item.high_value_yield} · Dup {formatScore(item.duplicate_rate, 0)}% · Fail{" "}
                    {formatScore(item.failure_rate, 0)}% · {formatScore(item.average_latency_ms, 0)} ms
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Open Alerts</CardTitle>
            <CardDescription>
              Healthy {data.healthy_connectors} · Degraded {data.degraded_connectors} · Down{" "}
              {data.down_connectors}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(alerts.data?.alerts ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No open connector alerts.</p>
            ) : (
              (alerts.data?.alerts ?? []).map((alert) => (
                <div key={alert.id} className="rounded-lg border border-border/60 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{formatLabel(alert.source)}</p>
                    <Badge className="bg-muted text-muted-foreground ring-border">{alert.severity}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{alert.message}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connector Audit</CardTitle>
          <CardDescription>24h signals, companies, opportunities, duplicates, failures</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.08em] text-muted-foreground">
              <tr>
                <th className="py-2 pr-3">Source</th>
                <th className="py-2 pr-3">Health</th>
                <th className="py-2 pr-3">Signals</th>
                <th className="py-2 pr-3">Companies</th>
                <th className="py-2 pr-3">Opps</th>
                <th className="py-2 pr-3">HV Opps</th>
                <th className="py-2 pr-3">Dup %</th>
                <th className="py-2 pr-3">Fail %</th>
                <th className="py-2 pr-3">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {data.connectors.map((connector) => (
                <tr key={connector.source} className="border-t border-border/50">
                  <td className="py-2 pr-3 font-medium">{formatLabel(connector.source)}</td>
                  <td className="py-2 pr-3">{formatLabel(connector.health_status)}</td>
                  <td className="py-2 pr-3">{connector.signals_collected_24h}</td>
                  <td className="py-2 pr-3">{connector.companies_discovered_24h}</td>
                  <td className="py-2 pr-3">{connector.opportunities_produced_24h}</td>
                  <td className="py-2 pr-3">{connector.high_value_opportunities_24h}</td>
                  <td className="py-2 pr-3">{formatScore(connector.duplicate_rate_24h, 0)}</td>
                  <td className="py-2 pr-3">{formatScore(connector.failure_rate_24h, 0)}</td>
                  <td className={`py-2 pr-3 ${scoreTone(connector.coverage_score)}`}>
                    {formatScore(connector.coverage_score, 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Daily Report</CardTitle>
          <CardDescription>New companies, opportunities, collector performance, missing-data trends</CardDescription>
        </CardHeader>
        <CardContent>
          {report.isError ? (
            <EmptyState
              title="No daily report yet"
              description="The acquisition.generate_daily_report worker writes this once per day."
            />
          ) : report.data?.report ? (
            <div className="space-y-3">
              <p className="text-sm">{report.data.report.summary}</p>
              <div className="flex flex-wrap gap-2">
                <Badge className="bg-muted text-muted-foreground ring-border">
                  Companies {report.data.report.new_companies}
                </Badge>
                <Badge className="bg-muted text-muted-foreground ring-border">
                  Opportunities {report.data.report.new_opportunities}
                </Badge>
                <Badge className="bg-muted text-muted-foreground ring-border">
                  Coverage growth {formatScore(report.data.report.coverage_growth, 0)}%
                </Badge>
                <Badge className="bg-muted text-muted-foreground ring-border">
                  Dup rate {formatScore(report.data.report.duplicate_rate, 0)}%
                </Badge>
              </div>
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  Missing data trends
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(report.data.report.missing_data_trends || {}).map(([key, value]) => (
                    <Badge key={key} className="bg-muted text-muted-foreground ring-border">
                      {formatLabel(key)}: {value}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <Skeleton className="h-24 w-full" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p className={`mt-2 font-display text-3xl font-semibold ${tone || ""}`}>{value}</p>
        <p className="mt-1 text-[11px] text-muted-foreground">{formatRelativeTime(new Date().toISOString())}</p>
      </CardContent>
    </Card>
  );
}
