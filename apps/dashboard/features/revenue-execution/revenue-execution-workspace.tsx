"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

export function RevenueExecutionWorkspace() {
  const qc = useQueryClient();
  const dash = useQuery({
    queryKey: ["rev-dashboard"],
    queryFn: () => beaconApi.revDashboard(),
    refetchInterval: 60_000,
  });
  const qa = useQuery({
    queryKey: ["rev-qa-pending"],
    queryFn: () => beaconApi.revQaPending(),
    refetchInterval: 60_000,
  });
  const rate = useMutation({
    mutationFn: (payload: { company_id?: string; company_name?: string; rating: string }) => beaconApi.revQaSubmit(payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["rev-qa-pending"] });
      await qc.invalidateQueries({ queryKey: ["rev-dashboard"] });
    },
  });
  const rebuild = useMutation({
    mutationFn: () => beaconApi.revRebuild(500),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["rev-dashboard"] });
    },
  });

  if (dash.isError) {
    return <ErrorState title="Revenue Execution unavailable" description="API /revenue-execution-validation/dashboard failed." />;
  }

  const funnel = ((dash.data?.funnel as { stages?: Array<Record<string, unknown>> })?.stages || []) as Array<Record<string, unknown>>;
  const connectors = ((dash.data?.connector_scores as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const rejections = ((dash.data?.rejection_top as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const daily = (dash.data?.daily || {}) as Record<string, unknown>;
  const acceptance = (dash.data?.acceptance || {}) as Record<string, unknown>;
  const qaItems = ((qa.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const ratings = ((qa.data?.ratings as string[]) || []) as string[];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <SectionLabel>Execution phase</SectionLabel>
          <h1 className="text-2xl font-semibold tracking-tight">Revenue Reality</h1>
          <p className="text-sm text-muted-foreground">
            Only metrics that prove companies Vansh can contact in 60 seconds.
          </p>
        </div>
        <Button disabled={rebuild.isPending} onClick={() => rebuild.mutate()}>
          {rebuild.isPending ? "Rebuilding…" : "Rebuild validation"}
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Acceptance gates</CardTitle>
          <CardDescription>Production stays locked until every gate passes.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Badge variant={acceptance.production_unlocked ? "default" : "secondary"}>
            {acceptance.production_unlocked ? "UNLOCKED" : "LOCKED"}
          </Badge>
          <Badge variant="outline">Ready {String(acceptance.revenue_ready_count ?? 0)}</Badge>
          <Badge variant="outline">Emails {String(acceptance.verified_emails ?? 0)}</Badge>
          <Badge variant="outline">DMs {String(acceptance.named_decision_makers ?? 0)}</Badge>
          <Badge variant="outline">QA {formatScore(Number(acceptance.manual_qa_accuracy || 0), 0)}%</Badge>
          <Badge variant="outline">Dup {formatScore(Number(acceptance.duplicate_rate || 0), 0)}%</Badge>
          {Array.isArray(acceptance.failures) && (acceptance.failures as string[]).length > 0 ? (
            <p className="w-full text-xs text-muted-foreground">Failures: {(acceptance.failures as string[]).join(" · ")}</p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Revenue Reality Funnel</CardTitle>
          <CardDescription>Count · % · failures · sources — no vanity metrics</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-2 pr-3 font-medium">Stage</th>
                <th className="py-2 pr-3 font-medium">Count</th>
                <th className="py-2 pr-3 font-medium">%</th>
                <th className="py-2 pr-3 font-medium">Avg ms</th>
                <th className="py-2 font-medium">Top sources</th>
              </tr>
            </thead>
            <tbody>
              {dash.isLoading &&
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="py-3" colSpan={5}>
                      <Skeleton className="h-5 w-full" />
                    </td>
                  </tr>
                ))}
              {funnel.map((s) => (
                <tr key={String(s.name)} className="border-b">
                  <td className="py-2 pr-3 font-medium">{String(s.name)}</td>
                  <td className="py-2 pr-3">{Number(s.count || 0)}</td>
                  <td className="py-2 pr-3">{formatScore(Number(s.percent || 0), 1)}%</td>
                  <td className="py-2 pr-3">{formatScore(Number(s.avg_processing_ms || 0), 1)}</td>
                  <td className="py-2 text-muted-foreground">
                    {Array.isArray(s.top_sources)
                      ? (s.top_sources as Array<Record<string, unknown>>)
                          .slice(0, 3)
                          .map((x) => `${x.source}:${x.count}`)
                          .join(" · ")
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Connector Scoreboard</CardTitle>
            <CardDescription>Excellent · Good · Weak · Disable Candidate</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {connectors.length === 0 && <p className="text-sm text-muted-foreground">No connector scores yet.</p>}
            {connectors.map((c) => (
              <div key={String(c.connector)} className="flex flex-wrap items-center justify-between gap-2 border-b py-2 text-sm">
                <div>
                  <p className="font-medium">{String(c.connector)}</p>
                  <p className="text-xs text-muted-foreground">
                    Ready {Number(c.revenue_ready || 0)} · Emails {Number(c.emails || 0)} · Dup {formatScore(Number(c.duplicate_rate || 0), 0)}%
                  </p>
                </div>
                <Badge>{String(c.grade)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top rejection reasons</CardTitle>
            <CardDescription>Why companies never reach Revenue Ready</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {rejections.length === 0 && <p className="text-sm text-muted-foreground">No rejections recorded.</p>}
            {rejections.slice(0, 10).map((r) => (
              <div key={String(r.reason)} className="flex justify-between border-b py-2 text-sm">
                <span>{String(r.reason)}</span>
                <span className="text-muted-foreground">{Number(r.count || 0)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Daily Revenue Report</CardTitle>
          <CardDescription>{String(daily.recommendation || "Run rebuild to generate morning report.")}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          {[
            ["Signals", daily.signals_collected],
            ["Verified", daily.companies_verified],
            ["Revenue Ready", daily.revenue_ready],
            ["Emails", daily.business_emails_found],
            ["Decision Makers", daily.decision_makers_found],
            ["Founder Queue", daily.founder_queue],
            ["High Intent", daily.new_high_intent],
            ["Biggest Failure", daily.biggest_failure],
          ].map(([label, value]) => (
            <div key={String(label)}>
              <p className="text-xs text-muted-foreground">{String(label)}</p>
              <p className="font-medium">{String(value ?? "—")}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Manual QA Workspace</CardTitle>
          <CardDescription>Internal ratings become analytics only — never auto-modify rules.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {qaItems.slice(0, 8).map((item) => (
            <div key={String(item.company_id)} className="rounded-lg border border-border/60 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium">{String(item.company)}</p>
                  <p className="text-xs text-muted-foreground">
                    {String(item.website)} · {String(item.service_match)} · {String(item.email)}
                  </p>
                </div>
                <Badge variant={item.revenue_ready ? "default" : "secondary"}>
                  {item.revenue_ready ? "Revenue Ready" : "Not ready"}
                </Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {ratings.map((r) => (
                  <Button
                    key={r}
                    size="sm"
                    variant="outline"
                    disabled={rate.isPending}
                    onClick={() =>
                      rate.mutate({
                        company_id: item.company_id ? String(item.company_id) : undefined,
                        company_name: String(item.company || ""),
                        rating: r,
                      })
                    }
                  >
                    {r}
                  </Button>
                ))}
              </div>
            </div>
          ))}
          {qaItems.length === 0 && <p className="text-sm text-muted-foreground">No QA cards yet — rebuild after CIR admits companies.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
