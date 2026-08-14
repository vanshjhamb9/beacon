"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { ReviewActions } from "@/features/opportunities/review-actions";
import { beaconApi } from "@/lib/api/beacon";
import {
  formatDateTime,
  formatLabel,
  formatRelativeTime,
  formatScore,
  scoreTone,
} from "@/lib/utils";

export function OpportunityWorkspace({ opportunityId }: { opportunityId: string }) {
  const queryClient = useQueryClient();
  const opportunity = useQuery({
    queryKey: ["opportunity", opportunityId],
    queryFn: () => beaconApi.opportunity(opportunityId),
  });
  const evidence = useQuery({
    queryKey: ["opportunity-evidence", opportunityId],
    queryFn: () => beaconApi.opportunityEvidence(opportunityId),
  });
  const history = useQuery({
    queryKey: ["opportunity-history", opportunityId],
    queryFn: () => beaconApi.opportunityHistory(opportunityId),
  });
  const timeline = useQuery({
    queryKey: ["opportunity-timeline", opportunityId],
    queryFn: () => beaconApi.opportunityTimeline(opportunityId),
  });
  const recommendation = useQuery({
    queryKey: ["opportunity-recommendation", opportunityId],
    queryFn: () => beaconApi.opportunityRecommendation(opportunityId),
  });
  const revenue = useQuery({
    queryKey: ["company-revenue", opportunity.data?.company_id],
    queryFn: () => beaconApi.revenueCompany(opportunity.data!.company_id),
    enabled: Boolean(opportunity.data?.company_id),
    retry: false,
  });

  const feedback = useMutation({
    mutationFn: beaconApi.opportunityFeedback,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["opportunity-history", opportunityId] });
    },
  });

  if (opportunity.isLoading) return <Skeleton className="h-96 w-full" />;
  if (opportunity.isError || !opportunity.data) {
    return <ErrorState description="Opportunity not found." onRetry={() => void opportunity.refetch()} />;
  }

  const item = opportunity.data;

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-6">
      <header className="flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 shadow-soft lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <SectionLabel>Opportunity Workspace</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">{item.company_name}</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">{item.narrative}</p>
          <div className="flex flex-wrap gap-2">
            <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(item.status)}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(item.recommendation)}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">
              Updated {formatRelativeTime(item.created_at)}
            </Badge>
          </div>
        </div>
        <div className="space-y-3">
          <p className={`text-right font-display text-4xl font-semibold ${scoreTone(item.opportunity_score)}`}>
            {formatScore(item.opportunity_score, 0)}
          </p>
          <ReviewActions
            disabled={feedback.isPending}
            onReview={(outcome) =>
              feedback.mutate({
                opportunity_id: item.id,
                reviewer: "operator",
                review_outcome: outcome,
              })
            }
          />
          <Button asChild variant="outline" size="sm">
            <Link href={`/companies/${item.company_id}`}>Open company workspace</Link>
          </Button>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-4">
        <Score label="Opportunity" value={item.opportunity_score} />
        <Score label="Confidence" value={item.confidence_score} />
        <Score label="Timing" value={item.timing_score} />
        <Score label="Urgency" value={item.urgency_score} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recommendation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {recommendation.data ? (
              <>
                <p className="font-medium">{formatLabel(recommendation.data.action)}</p>
                <p className="text-sm text-muted-foreground">{recommendation.data.next_step}</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {recommendation.data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Recommendation pending.</p>
            )}
            {revenue.data ? (
              <div className="mt-4 rounded-lg border border-border/60 bg-background/40 p-3 text-sm">
                <p className="font-medium">Revenue fit: {revenue.data.recommended_service}</p>
                <p className="text-muted-foreground">{revenue.data.reason}</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Delta</CardTitle>
            <CardDescription>What changed since the previous score</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Direction: {formatLabel(String(item.delta.direction || "n/a"))}</p>
            <p>Score change: {formatScore(Number(item.delta.score_change ?? 0), 1)}</p>
            <p className="text-muted-foreground">{String(item.delta.reason || "No delta reason provided.")}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Evidence</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {(evidence.data?.evidence ?? []).map((itemEvidence) => (
              <div key={itemEvidence.id} className="rounded-lg border border-border/50 px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {formatLabel(itemEvidence.source_type)} · {itemEvidence.category}
                  </p>
                  <Badge className="bg-muted text-muted-foreground ring-border">{itemEvidence.polarity}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{itemEvidence.summary}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Confidence {formatScore(itemEvidence.confidence, 0)} · Weight {formatScore(itemEvidence.weight, 2)}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Timeline & History</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {(timeline.data?.timeline ?? []).map((event, index) => (
              <div key={`${event.created_at}-${index}`} className="rounded-lg border border-border/50 px-3 py-3">
                <p className="text-sm font-medium">{formatLabel(event.event_type)}</p>
                <p className="text-sm text-muted-foreground">{event.summary}</p>
                <p className="text-[11px] text-muted-foreground">{formatDateTime(event.created_at)}</p>
              </div>
            ))}
            {(history.data?.history ?? []).slice(0, 8).map((entry) => (
              <div key={entry.id} className="rounded-lg border border-border/50 px-3 py-3">
                <p className="text-sm font-medium">{formatLabel(entry.action)}</p>
                <p className="text-[11px] text-muted-foreground">
                  {entry.actor} · {formatDateTime(entry.created_at)}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p className={`mt-1 font-display text-2xl font-semibold ${scoreTone(value)}`}>{formatScore(value, 0)}</p>
      </CardContent>
    </Card>
  );
}
