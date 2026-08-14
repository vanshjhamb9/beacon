"""Manual QA Workspace — analytics only. Never auto-modify rules."""

from __future__ import annotations

from typing import Any

from revenue_execution_validation.models.types import ManualQaRating, RevSnapshot

POSITIVE = frozenset({ManualQaRating.EXCELLENT, ManualQaRating.GOOD})
NEGATIVE = frozenset(
    {
        ManualQaRating.WRONG_COMPANY,
        ManualQaRating.WRONG_INTENT,
        ManualQaRating.WRONG_SERVICE,
        ManualQaRating.WRONG_CONTACT,
        ManualQaRating.DUPLICATE,
        ManualQaRating.FAKE,
    }
)


class ManualQaWorkspaceEngine:
    RATINGS = tuple(ManualQaRating)

    def build_card(self, snap: RevSnapshot) -> dict[str, Any]:
        c = snap.check
        return {
            "company_id": snap.company_id,
            "company": c.company_name,
            "website": c.website,
            "industry": c.industry,
            "country": c.country,
            "why_now": c.why_now,
            "opportunity": c.opportunity,
            "service_match": c.best_service,
            "email": c.email,
            "decision_maker": c.decision_maker_name,
            "confidence": c.confidence,
            "source": snap.source,
            "revenue_ready": c.is_revenue_ready,
            "evidence": [e.model_dump(mode="json") for e in c.evidence[:6]],
            "ratings": [r.value for r in ManualQaRating],
        }

    def queue(self, snapshots: list[RevSnapshot], *, limit: int = 40) -> list[dict[str, Any]]:
        # Prefer ready + near-ready for review
        ordered = sorted(
            snapshots,
            key=lambda s: (s.check.is_revenue_ready, s.check.confidence),
            reverse=True,
        )
        return [self.build_card(s) for s in ordered[:limit]]

    def analytics(self, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(decisions)
        counts = {r.value: 0 for r in ManualQaRating}
        for d in decisions:
            rating = str(d.get("rating") or "")
            if rating in counts:
                counts[rating] += 1
        positive = sum(counts[r.value] for r in POSITIVE)
        negative = sum(counts[r.value] for r in NEGATIVE)
        accuracy = round(100.0 * positive / max(positive + negative, 1), 2) if (positive + negative) else 0.0
        return {
            "total": n,
            "counts": counts,
            "positive": positive,
            "negative": negative,
            "accuracy_pct": accuracy,
            "note": "Analytics only — never auto-modifies production rules",
        }
