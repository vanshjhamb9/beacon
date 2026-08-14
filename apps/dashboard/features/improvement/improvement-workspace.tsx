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

export function ImprovementWorkspace() {
  const overview = useQuery({ queryKey: ["improvement-overview"], queryFn: beaconApi.improvementOverview });
  const collectors = useQuery({ queryKey: ["improvement-collectors"], queryFn: beaconApi.improvementCollectors });
  const rules = useQuery({ queryKey: ["improvement-rules"], queryFn: beaconApi.improvementRules });
  const opportunities = useQuery({
    queryKey: ["improvement-opportunities"],
    queryFn: beaconApi.improvementOpportunities,
  });
  const experiments = useQuery({
    queryKey: ["improvement-experiments"],
    queryFn: beaconApi.improvementExperiments,
  });
  const recommendations = useQuery({
    queryKey: ["improvement-recommendations"],
    queryFn: beaconApi.improvementRecommendations,
  });

  if (overview.isError && collectors.isError) {
    return <ErrorState description="Improvement APIs unavailable." onRetry={() => void overview.refetch()} />;
  }

  const overviewData = overview.data?.overview ?? {};
  const collectorChart = (collectors.data?.collectors ?? []).map((item) => ({
    name: String(item.collector),
    precision: Number(item.precision ?? 0),
    quality: Number(item.average_quality ?? 0),
  }));

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Learning Loop</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Improvement</h1>
        <p className="text-sm text-muted-foreground">Read-only view of evaluation metrics and optimization recommendations.</p>
      </header>

      {overview.isLoading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="grid gap-4 md:grid-cols-4">
          <Metric label="Learning events" value={String(overviewData.learning_events ?? "—")} />
          <Metric label="Feedback events" value={String(overviewData.feedback_events ?? "—")} />
          <Metric label="Optimization recs" value={String(overviewData.optimization_recommendations ?? "—")} />
          <Metric
            label="Scoring latency"
            value={
              overviewData.average_scoring_latency_ms != null
                ? `${formatScore(Number(overviewData.average_scoring_latency_ms), 0)} ms`
                : "—"
            }
          />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Collector Performance</CardTitle>
          <CardDescription>Precision and average quality by collector</CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          {collectorChart.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={collectorChart}>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    border: "1px solid rgba(148,163,184,0.2)",
                    borderRadius: 12,
                  }}
                />
                <Bar dataKey="precision" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                <Bar dataKey="quality" fill="#2dd4bf" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted-foreground">No collector performance rows yet.</p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Rule Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(rules.data?.rules ?? []).map((rule) => (
              <div key={String(rule.id || rule.rule_key)} className="rounded-lg border border-border/50 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{String(rule.rule_key)}</p>
                  <span className="text-muted-foreground">Conf {formatScore(Number(rule.confidence ?? 0), 0)}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Fired {String(rule.times_fired ?? 0)} · Correct {String(rule.correct_decisions ?? 0)} · Incorrect{" "}
                  {String(rule.incorrect_decisions ?? 0)} · Override {formatPercent(Number(rule.override_rate ?? 0))}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prediction Accuracy</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(opportunities.data?.opportunities ?? []).map((item) => (
              <div key={String(item.id)} className="rounded-lg border border-border/50 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{String(item.outcome_label || "Outcome")}</p>
                  <span className="text-muted-foreground">Err {formatScore(Number(item.prediction_error ?? 0), 1)}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Predicted {formatScore(Number(item.predicted_score ?? 0), 0)} · Actual{" "}
                  {formatScore(Number(item.actual_outcome_score ?? 0), 0)}
                </p>
              </div>
            ))}
            {(opportunities.data?.opportunities.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">No opportunity accuracy rows yet.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Optimization Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(recommendations.data?.recommendations ?? []).map((item) => (
              <div key={String(item.id)} className="rounded-lg border border-border/50 px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {String(item.target_type)} · {String(item.target_key)}
                  </p>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    {item.requires_approval ? "needs approval" : "informational"}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{String(item.recommendation || item.reason || "")}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Experiments</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(experiments.data?.experiments ?? []).map((item) => (
              <div key={String(item.id)} className="rounded-lg border border-border/50 px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{String(item.name || item.experiment_key)}</p>
                  <Badge className="bg-muted text-muted-foreground ring-border">{String(item.status)}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{String(item.hypothesis || "")}</p>
              </div>
            ))}
            {(experiments.data?.experiments.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">No experiments recorded.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>
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
