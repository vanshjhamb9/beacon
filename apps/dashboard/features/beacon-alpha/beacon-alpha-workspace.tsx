"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

const RATINGS = ["Excellent", "Good", "Poor", "Fake", "Duplicate", "Wrong Service", "Wrong Intent"] as const;

export function BeaconAlphaWorkspace() {
  const qc = useQueryClient();
  const queue = useQuery({
    queryKey: ["alpha-founder-queue"],
    queryFn: () => beaconApi.alphaFounderQueue(),
    refetchInterval: 60_000,
  });
  const pending = useQuery({
    queryKey: ["alpha-qa-pending"],
    queryFn: () => beaconApi.alphaQaPending(20),
    refetchInterval: 60_000,
  });
  const analytics = useQuery({
    queryKey: ["alpha-qa-analytics"],
    queryFn: () => beaconApi.alphaQaAnalytics(),
    refetchInterval: 60_000,
  });
  const acceptance = useQuery({
    queryKey: ["alpha-acceptance"],
    queryFn: () => beaconApi.alphaAcceptance(),
    refetchInterval: 60_000,
  });

  const decide = useMutation({
    mutationFn: (args: { companyId: string; rating: string }) =>
      beaconApi.alphaQaDecide(args.companyId, { rating: args.rating, reviewer: "founder" }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["alpha-qa-pending"] });
      await qc.invalidateQueries({ queryKey: ["alpha-qa-analytics"] });
      await qc.invalidateQueries({ queryKey: ["alpha-acceptance"] });
    },
  });

  if (queue.isLoading) return <Skeleton className="h-72 w-full" />;
  if (queue.isError) {
    return <ErrorState description="Alpha queue unavailable." onRetry={() => void queue.refetch()} />;
  }

  const items = queue.data?.items ?? [];
  const qaItems = pending.data?.items ?? [];
  const a = acceptance.data ?? {};
  const an = analytics.data ?? {};

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Revenue Dataset Perfection</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Beacon Alpha</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Top 10 outbound-ready companies + manual QA. Live Gmail/WhatsApp stay locked until acceptance passes.
        </p>
        <Badge variant={a.live_outreach_ready ? "default" : "outline"}>
          {a.live_outreach_ready ? "Live outreach ready" : "Live outreach locked"}
        </Badge>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Top 10 queue" value={items.length} />
        <Metric title="QA pending" value={qaItems.length} />
        <Metric title="Service correct %" value={`${an.service_correct_percent ?? 0}%`} />
        <Metric title="Real business %" value={`${an.real_business_percent ?? a.real_business_percent ?? 0}%`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Founder Queue — Top 10</CardTitle>
          <CardDescription>Score 80+ only. Why now, pain, budget, service, contact, first line.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">No outbound-ready companies yet.</p>
          ) : (
            items.map((item, idx) => (
              <div key={`${String(item.company_id)}-${idx}`} className="rounded-lg border border-border/60 p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium">{String(item.company)}</span>
                  <Badge variant="outline">{String(item.confidence ?? item.score)} pts</Badge>
                </div>
                <p className="mt-1 text-muted-foreground">
                  <strong>Why now:</strong> {String(item.why_now)}
                </p>
                <p className="text-muted-foreground">
                  <strong>Pain:</strong> {String(item.pain)} · <strong>Budget:</strong> {String(item.estimated_budget)}
                </p>
                <p className="text-muted-foreground">
                  <strong>Service:</strong> {String(item.best_service)} · <strong>DM:</strong> {String(item.decision_maker)} ·{" "}
                  <strong>Email:</strong> {String(item.email)}
                </p>
                <p className="mt-1 italic text-muted-foreground">{String(item.recommended_first_line)}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Manual QA</CardTitle>
          <CardDescription>Accept/reject Sales Ready companies. Ratings feed analytics only — never auto-change rules.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {qaItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">No pending QA items.</p>
          ) : (
            qaItems.slice(0, 8).map((item, idx) => (
              <div key={`${String(item.company_id)}-${idx}`} className="space-y-2 rounded-lg border border-border/60 p-3 text-sm">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{String(item.industry)}</Badge>
                  <Badge variant="outline">{String(item.service_match)}</Badge>
                  <Badge variant="outline">{String(item.confidence)} conf</Badge>
                </div>
                <p>
                  <strong>Website:</strong> {String(item.website)} · <strong>Source:</strong> {String(item.source)}
                </p>
                <p className="text-muted-foreground">{String(item.ai_reasoning)}</p>
                <div className="flex flex-wrap gap-2">
                  {RATINGS.map((rating) => (
                    <Button
                      key={rating}
                      size="sm"
                      variant="outline"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ companyId: String(item.company_id), rating })
                      }
                    >
                      {rating}
                    </Button>
                  ))}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string | number | undefined }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl">{value ?? "—"}</CardTitle>
      </CardHeader>
    </Card>
  );
}
