"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
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

export function OutcomesWorkspace() {
  const dashboard = useQuery({ queryKey: ["outcomes-dashboard"], queryFn: beaconApi.outcomesDashboard });
  const analytics = useQuery({ queryKey: ["outcomes-analytics"], queryFn: beaconApi.outcomesAnalytics });

  if (dashboard.isError) {
    return <ErrorState description="Outcome Intelligence APIs unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  const data = dashboard.data;
  const funnel = (data?.funnel ?? []).map((item) => ({
    name: item.stage.replaceAll("_", " "),
    count: item.count,
  }));
  const collectorAccuracy = (data?.collector_accuracy ?? []).slice(0, 8).map((item) => ({
    name: item.key,
    accuracy: item.accuracy_score,
  }));
  const serviceAccuracy = (data?.service_accuracy ?? []).slice(0, 8).map((item) => ({
    name: item.key,
    accuracy: item.accuracy_score,
  }));
  const industryAccuracy = (data?.industry_accuracy ?? []).slice(0, 8).map((item) => ({
    name: item.key,
    accuracy: item.accuracy_score,
  }));

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Outcome Intelligence</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Outcomes</h1>
        <p className="text-sm text-muted-foreground">
          Measure whether Beacon predictions convert into meetings, proposals, and revenue.
        </p>
      </header>

      {dashboard.isLoading || !data ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-6">
          <Metric label="Reply rate" value={formatPercent(data.rates.reply_rate)} />
          <Metric label="Meeting rate" value={formatPercent(data.rates.meeting_rate)} />
          <Metric label="Proposal rate" value={formatPercent(data.rates.proposal_rate)} />
          <Metric label="Close rate" value={formatPercent(data.rates.close_rate)} />
          <Metric label="Revenue" value={`$${formatScore(data.revenue.total_revenue, 0)}`} />
          <Metric label="ROI index" value={formatScore(Number(data.roi.roi_index ?? 0), 2)} />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Sales Funnel</CardTitle>
            <CardDescription>Opportunities by lifecycle stage</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {funnel.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnel}>
                  <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Dashboard</CardTitle>
            <CardDescription>Won deals and pipeline value</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {data ? (
              <>
                <Row label="Total revenue" value={`$${formatScore(data.revenue.total_revenue, 0)}`} />
                <Row label="Average deal size" value={`$${formatScore(data.revenue.average_deal_size, 0)}`} />
                <Row label="Avg sales cycle" value={`${formatScore(data.revenue.average_sales_cycle_days, 1)} days`} />
                <Row label="Open pipeline" value={`$${formatScore(data.revenue.open_pipeline_value, 0)}`} />
                <Row label="Won deals" value={String(data.revenue.won_deals)} />
                <div className="pt-2">
                  <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Top services</p>
                  <div className="flex flex-wrap gap-2">
                    {(data.revenue_by_service ?? []).slice(0, 5).map((item) => (
                      <Badge key={item.key} className="bg-muted/60 text-foreground">
                        {item.key}: ${formatScore(item.revenue, 0)}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <Empty />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <AccuracyCard title="Collector Accuracy" data={collectorAccuracy} />
        <AccuracyCard title="Service Accuracy" data={serviceAccuracy} />
        <AccuracyCard title="Industry Accuracy" data={industryAccuracy} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Prediction Accuracy</CardTitle>
          <CardDescription>Score calibration and lead quality against realized outcomes</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {(data?.prediction_accuracy ?? []).length ? (
            (data?.prediction_accuracy ?? []).map((item) => (
              <div key={`${item.category}-${item.key}`} className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2 text-sm">
                <div>
                  <p className="font-medium">
                    {item.category}: {item.key}
                  </p>
                  <p className="text-xs text-muted-foreground">n={item.sample_size}</p>
                </div>
                <div className="text-right">
                  <p>{formatScore(item.accuracy_score, 1)}%</p>
                  <p className="text-xs text-muted-foreground">err {formatScore(item.average_prediction_error, 1)}</p>
                </div>
              </div>
            ))
          ) : (
            <Empty />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ROI & Learning Recommendations</CardTitle>
          <CardDescription>Approval-required suggestions for the Improvement Engine — never auto-applied</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {data ? (
            <div className="mb-4 grid gap-3 md:grid-cols-4">
              <Metric label="Tracked opps" value={String(data.roi.opportunities_tracked ?? 0)} />
              <Metric label="Rev / opp" value={`$${formatScore(Number(data.roi.revenue_per_opportunity ?? 0), 0)}`} />
              <Metric label="Avg accuracy" value={formatScore(Number(analytics.data?.accuracy_summary?.average_accuracy ?? 0), 1)} />
              <Metric label="Recommendations" value={String(data.learning_recommendations.length)} />
            </div>
          ) : null}
          {(data?.learning_recommendations ?? []).length ? (
            (data?.learning_recommendations ?? []).map((item) => (
              <div key={`${item.area}-${item.target_key}-${item.recommendation}`} className="rounded-lg border border-border/60 px-3 py-3">
                <div className="mb-1 flex items-center gap-2">
                  <Badge className="bg-primary/15 text-primary">{item.area}</Badge>
                  <Badge className="bg-muted/60 text-foreground">{item.target_key}</Badge>
                  {item.requires_approval ? (
                    <Badge className="bg-amber-500/15 text-amber-200">requires approval</Badge>
                  ) : null}
                </div>
                <p className="text-sm font-medium">{item.recommendation}</p>
                <p className="text-xs text-muted-foreground">{item.reason}</p>
              </div>
            ))
          ) : (
            <Empty label="No learning recommendations yet — record outcomes to calibrate." />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AccuracyCard({ title, data }: { title: string; data: Array<{ name: string; accuracy: number }> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-56">
        {data.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="accuracy" fill="#2dd4bf" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Empty />
        )}
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/60 bg-muted/30 px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-xl font-semibold">{value}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function Empty({ label = "No outcome data yet." }: { label?: string }) {
  return <p className="text-sm text-muted-foreground">{label}</p>;
}

const tooltipStyle = {
  background: "#0f172a",
  border: "1px solid rgba(148,163,184,0.2)",
  borderRadius: 12,
};
