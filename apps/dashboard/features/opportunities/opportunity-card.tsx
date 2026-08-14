"use client";

import Link from "next/link";
import { ExternalLink, MessageSquareWarning, ThumbsDown, ThumbsUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { RevenueOpportunity } from "@/lib/types/api";
import {
  formatLabel,
  formatRelativeTime,
  formatScore,
  priorityTone,
  scoreTone,
} from "@/lib/utils";

export function OpportunityCard({
  item,
  onReview,
  reviewing,
}: {
  item: RevenueOpportunity;
  onReview?: (outcome: "accepted" | "dismissed" | "false_positive" | "needs_review") => void;
  reviewing?: boolean;
}) {
  return (
    <Card className="h-full transition hover:border-primary/25">
      <CardContent className="flex h-full flex-col gap-4 py-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <Link
              href={`/companies/${item.company.id}`}
              className="font-display text-lg font-semibold tracking-tight hover:text-primary"
            >
              {item.company.name}
            </Link>
            <p className="text-sm text-muted-foreground">
              {item.company.industry || "Industry unknown"} · Updated {formatRelativeTime(item.created_at)}
            </p>
          </div>
          <div className="text-right">
            <p className={`font-display text-2xl font-semibold tabular-nums ${scoreTone(item.opportunity_score)}`}>
              {formatScore(item.opportunity_score, 0)}
            </p>
            <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Score</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge className={priorityTone(item.priority)}>{formatLabel(item.priority) || "Unprioritized"}</Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            {item.recommended_service}
          </Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            Budget {formatLabel(item.estimated_budget_range)}
          </Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            Conf {formatScore(item.confidence, 0)}
          </Badge>
        </div>

        <div className="grid gap-3 text-sm">
          <Field label="Buyer persona" value={item.buyer_persona?.persona || "—"} />
          <Field label="Business pain" value={item.business_pain || "—"} />
          <Field label="Why Beacon recommends it" value={item.reason} />
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-2 border-t border-border/60 pt-4">
          <Button asChild size="sm">
            <Link href={`/companies/${item.company.id}`}>
              Open company
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={reviewing || !onReview}
            onClick={() => onReview?.("accepted")}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
            Reviewed
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={reviewing || !onReview}
            onClick={() => onReview?.("needs_review")}
          >
            <MessageSquareWarning className="h-3.5 w-3.5" />
            Needs review
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={reviewing || !onReview}
            onClick={() => onReview?.("dismissed")}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 line-clamp-3 text-sm leading-relaxed text-foreground/90">{value}</p>
    </div>
  );
}
