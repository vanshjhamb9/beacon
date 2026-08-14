"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

const REVIEW_LABELS = ["Perfect", "Good", "Wrong Contact", "Wrong Service", "Wrong Intent", "Not Interested"] as const;

export function FounderQueueV4Workspace() {
  const qc = useQueryClient();
  const queue = useQuery({
    queryKey: ["rrp-founder-queue-v4"],
    queryFn: () => beaconApi.rrpFounderQueue(),
    refetchInterval: 60_000,
  });
  const review = useMutation({
    mutationFn: ({ companyId, label }: { companyId: string; label: string }) =>
      beaconApi.rrpReview(companyId, label),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["rrp-founder-queue-v4"] }),
  });

  if (queue.isError) {
    return <ErrorState title="Founder Queue v4 unavailable" description="API /revenue-ready/founder-queue failed." />;
  }

  const items = ((queue.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <SectionLabel>Top 10 · rrp-v1</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Founder Queue v4</h1>
        <p className="text-sm text-muted-foreground">
          Fresh leads only (last 48h triggers). Directory/YC batch membership is excluded.
          Revenue Ready cards with decision makers, why-now, and manual review.
        </p>
        {queue.data?.fresh_only ? (
          <Badge className="mt-2" tone="info">
            Fresh ≤{String(queue.data.freshness_hours ?? 48)}h · LQS bar
          </Badge>
        ) : null}
      </div>

      {queue.isLoading && <Skeleton className="h-40 w-full" />}
      {!queue.isLoading && items.length === 0 && (
        <Card>
          <CardContent className="py-8 text-sm text-muted-foreground">
            No fresh high-quality leads yet (≤48h + LQS bar). HN/PH/Reddit collectors are enabled — check again shortly.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {items.slice(0, 10).map((card, idx) => (
          <Card key={`${card.company_id}-${idx}`}>
            <CardHeader className="pb-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <SectionLabel>#{idx + 1}</SectionLabel>
                  <CardTitle className="text-xl">{String(card.company)}</CardTitle>
                </div>
                <div className="flex flex-wrap gap-2">
                  {card.perfect_lead ? <Badge tone="ready">Perfect lead</Badge> : null}
                  <Badge tone="info">
                    LQS {String(card.lead_quality_score ?? "—")} {String(card.lead_quality_grade || "")}
                  </Badge>
                  <Badge className="bg-emerald-600 text-white">Revenue Ready</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                <span className="text-muted-foreground">Website · </span>
                {String(card.website || "—")}
              </p>
              <p>
                <span className="text-muted-foreground">Decision Maker · </span>
                {String(card.decision_maker || "—")}
              </p>
              <p>
                <span className="text-muted-foreground">DM Email · </span>
                {String(card.decision_maker_email || "—")}
              </p>
              <p>
                <span className="text-muted-foreground">Business Email · </span>
                {String(card.business_email || "—")}
              </p>
              <p>
                <span className="text-muted-foreground">Why Now · </span>
                {String(card.why_now || "—")}
              </p>
              <p>
                <span className="text-muted-foreground">Service · </span>
                {String(card.recommended_service || "—")}
              </p>
              <p>
                Confidence {formatScore(Number(card.confidence || 0), 0)} · Evidence {String(card.evidence_count ?? 0)} ·
                Verified {String(card.last_verified || "—")}
              </p>
              <div className="flex flex-wrap gap-2 pt-2">
                {REVIEW_LABELS.map((label) => (
                  <Button
                    key={label}
                    size="sm"
                    variant="outline"
                    disabled={review.isPending}
                    onClick={() =>
                      review.mutate({ companyId: String(card.company_id), label })
                    }
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
