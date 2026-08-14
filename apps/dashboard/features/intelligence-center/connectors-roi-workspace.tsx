"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

function money(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

export function ConnectorsRoiWorkspace() {
  const roi = useQuery({
    queryKey: ["connectors-roi"],
    queryFn: beaconApi.connectorsRoi,
    refetchInterval: 30_000,
  });

  if (roi.isError) {
    return (
      <ErrorState
        description="API /connectors/roi failed."
        onRetry={() => void roi.refetch()}
      />
    );
  }

  const rows = roi.data?.connectors ?? [];
  const matrix = (roi.data?.enrichment_coverage ?? []) as Array<Record<string, unknown>>;

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>Intelligence Center</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Connectors</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Measurable ROI for every connector — signals, enrichment, revenue-ready yield, latency, and estimated API cost.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void roi.refetch()} disabled={roi.isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", roi.isFetching && "animate-spin")} />
          Refresh
        </Button>
      </header>

      {!roi.data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <>
          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-4 w-4" /> Connector ROI
              </CardTitle>
              <CardDescription>
                Lifetime yield snapshot · report date {roi.data.report_date}
              </CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[1100px] text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="pb-2 pr-3">Connector</th>
                    <th className="pb-2 pr-3">Healthy</th>
                    <th className="pb-2 pr-3">Signals</th>
                    <th className="pb-2 pr-3">Companies</th>
                    <th className="pb-2 pr-3">Emails</th>
                    <th className="pb-2 pr-3">DMs</th>
                    <th className="pb-2 pr-3">RR</th>
                    <th className="pb-2 pr-3">Meetings</th>
                    <th className="pb-2 pr-3">Win %</th>
                    <th className="pb-2 pr-3">Latency</th>
                    <th className="pb-2 pr-3">API Cost</th>
                    <th className="pb-2 pr-3">Quota</th>
                    <th className="pb-2">Success %</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const reserved =
                      /reserved|not configured/i.test(row.detail || "") &&
                      row.signals === 0 &&
                      row.emails === 0 &&
                      row.revenue_ready === 0;
                    return (
                    <tr key={row.connector} className="border-t border-border/50">
                      <td className="py-2 pr-3 font-medium capitalize">{row.connector.replaceAll("_", " ")}</td>
                      <td className="py-2 pr-3">
                        <Badge variant={reserved ? "outline" : row.healthy ? "default" : "destructive"}>
                          {reserved ? "Reserved" : row.healthy ? "Healthy" : "Unhealthy"}
                        </Badge>
                      </td>
                      <td className="py-2 pr-3 tabular-nums">{row.signals}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.companies}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.emails}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.decision_makers}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.revenue_ready}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.meetings}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.win_pct}%</td>
                      <td className="py-2 pr-3 tabular-nums">
                        {row.latency_ms <= 0
                          ? "—"
                          : row.latency_ms >= 1000
                            ? `${(row.latency_ms / 1000).toFixed(1)}s`
                            : `${Math.round(row.latency_ms)}ms`}
                      </td>
                      <td className="py-2 pr-3 tabular-nums">{row.api_cost ? money(row.api_cost) : "Free"}</td>
                      <td className="py-2 pr-3 tabular-nums">{row.quota_used_pct}%</td>
                      <td className="py-2 tabular-nums">{row.success_pct}%</td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/40">
            <CardHeader>
              <CardTitle>Enrichment Coverage</CardTitle>
              <CardDescription>Who enriches best — Hunter · Apollo · LinkedIn · PDL · Clearbit</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="pb-2 pr-3">Company</th>
                    <th className="pb-2 pr-3">Website</th>
                    <th className="pb-2 pr-3">Hunter</th>
                    <th className="pb-2 pr-3">Apollo</th>
                    <th className="pb-2 pr-3">LinkedIn</th>
                    <th className="pb-2 pr-3">PDL</th>
                    <th className="pb-2 pr-3">DM</th>
                    <th className="pb-2">RR</th>
                  </tr>
                </thead>
                <tbody>
                  {matrix.map((row) => (
                    <tr key={String(row.company_id)} className="border-t border-border/50">
                      <td className="py-2 pr-3 font-medium">{String(row.company)}</td>
                      <td className="py-2 pr-3">{row.website ? "✔" : "—"}</td>
                      <td className="py-2 pr-3">{row.hunter ? "✔" : "—"}</td>
                      <td className="py-2 pr-3">{row.apollo ? "✔" : "—"}</td>
                      <td className="py-2 pr-3">{row.linkedin ? "✔" : "—"}</td>
                      <td className="py-2 pr-3">{row.pdl ? "✔" : "—"}</td>
                      <td className="py-2 pr-3">{row.decision_maker ? "✔" : "—"}</td>
                      <td className="py-2">{row.revenue_ready ? "✔" : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
