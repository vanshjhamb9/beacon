"use client";

import { Button } from "@/components/ui/button";

const OUTCOMES = [
  { key: "accepted", label: "Approve" },
  { key: "rejected", label: "Reject" },
  { key: "false_positive", label: "False positive" },
  { key: "needs_review", label: "Needs review" },
] as const;

export function ReviewActions({
  onReview,
  disabled,
}: {
  onReview: (outcome: (typeof OUTCOMES)[number]["key"]) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {OUTCOMES.map((outcome) => (
        <Button
          key={outcome.key}
          size="sm"
          variant={outcome.key === "accepted" ? "secondary" : "outline"}
          disabled={disabled}
          onClick={() => onReview(outcome.key)}
        >
          {outcome.label}
        </Button>
      ))}
    </div>
  );
}
