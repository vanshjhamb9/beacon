from __future__ import annotations

import hashlib

from revenue_operations.models.types import (
    LearningLabReport,
    LearningRecommendation,
    RecommendationStatus,
    RevenueOperationsInput,
    WinLossRecord,
)


class LearningLabEngine:
    """Daily learning insights — recommendations never modify production."""

    def analyze(self, item: RevenueOperationsInput, *, win_loss: list[WinLossRecord]) -> LearningLabReport:
        signals = item.learning_signals or {}
        won = [r for r in win_loss if r.outcome == "won"]
        industries = list(signals.get("best_industries") or self._top([r.industry for r in won] + item.top_industries))
        services = list(signals.get("best_services") or self._top([r.service_sold for r in won] + item.top_services))
        best_email = str(signals.get("best_email") or "pain-first + single CTA")
        best_whatsapp = str(signals.get("best_whatsapp") or "short nudge + calendly")
        best_meeting_time = str(signals.get("best_meeting_time") or "Tue–Thu 10:00–12:00")
        follow_up = int(signals.get("best_follow_up_interval_days") or 2)
        dms = list(
            signals.get("highest_converting_decision_makers")
            or self._top([r.decision_maker for r in won] + [dm for o in item.opportunities for dm in o.decision_makers])
        )
        sizes = list(
            signals.get("highest_converting_company_sizes")
            or self._top([o.company_size for o in item.opportunities if o.company_size])
        )
        countries = list(
            signals.get("highest_converting_countries")
            or self._top([o.country for o in item.opportunities if o.country])
        )
        techs = list(
            signals.get("highest_converting_technologies")
            or self._top([t for o in item.opportunities for t in o.technologies])
        )
        recommendations = [
            self._rec(
                "industries",
                "Double down on top industries",
                f"Prioritize: {', '.join(industries[:3]) or 'SaaS'}",
                industries[:3],
            ),
            self._rec(
                "services",
                "Push highest converting services",
                f"Lead with: {', '.join(services[:3]) or 'AI Automation'}",
                services[:3],
            ),
            self._rec(
                "email",
                "Standardize best email pattern",
                best_email,
                [best_email],
            ),
            self._rec(
                "follow_up",
                "Adopt best follow-up interval",
                f"{follow_up} days",
                [str(follow_up)],
            ),
            self._rec(
                "meeting_time",
                "Schedule meetings in peak window",
                best_meeting_time,
                [best_meeting_time],
            ),
        ]
        return LearningLabReport(
            best_industries=industries[:8],
            best_services=services[:8],
            best_email=best_email,
            best_whatsapp=best_whatsapp,
            best_meeting_time=best_meeting_time,
            best_follow_up_interval_days=follow_up,
            highest_converting_decision_makers=dms[:8],
            highest_converting_company_sizes=sizes[:8],
            highest_converting_countries=countries[:8],
            highest_converting_technologies=techs[:8],
            recommendations=recommendations,
            evidence=["learning_lab:daily", "modifies_production:false", "founder_approval_required:true"],
        )

    def _rec(self, category: str, title: str, detail: str, evidence_bits: list[str]) -> LearningRecommendation:
        rid = hashlib.sha256(f"{category}|{title}|{detail}".encode()).hexdigest()[:16]
        return LearningRecommendation(
            recommendation_id=rid,
            category=category,
            title=title,
            detail=detail,
            status=RecommendationStatus.PENDING_APPROVAL,
            evidence=[f"bit:{b}" for b in evidence_bits[:4]] + ["requires_founder_approval:true"],
            modifies_production=False,
        )

    def _top(self, values: list[str | None]) -> list[str]:
        counts: dict[str, int] = {}
        for v in values:
            if not v:
                continue
            counts[str(v)] = counts.get(str(v), 0) + 1
        return [k for k, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
