from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import (
    AlphaSnapshot,
    AlphaVerdict,
    CompanyScore,
    ContactEnrichmentResult,
    IntentV2Result,
    ManualQaCard,
    ManualQaDecision,
    QaRating,
    SourceTransparency,
    UNKNOWN,
)


class ManualQaEngine:
    """Rule 9 — internal review workspace cards + rating analytics (never auto-change production rules)."""

    POSITIVE = frozenset({QaRating.EXCELLENT, QaRating.GOOD})
    NEGATIVE = frozenset(
        {QaRating.POOR, QaRating.FAKE, QaRating.DUPLICATE, QaRating.WRONG_SERVICE, QaRating.WRONG_INTENT}
    )

    def build_card(
        self,
        *,
        company_id: str,
        payload: dict[str, Any],
        intent: IntentV2Result,
        contacts: ContactEnrichmentResult,
        transparency: SourceTransparency,
        score: CompanyScore,
    ) -> ManualQaCard:
        reasoning = (
            f"Bucket={intent.primary_bucket.value}; pain={intent.scores.pain_score}; "
            f"urgency={intent.scores.urgency}; buying={intent.scores.buying_signal}; "
            f"window={intent.scores.decision_window}"
        )
        return ManualQaCard(
            company_id=company_id,
            website=payload.get("website") or UNKNOWN,
            linkedin=payload.get("linkedin_company") or payload.get("linkedin_url") or UNKNOWN,
            source=payload.get("source") or transparency.collected_from,
            evidence_snippets=transparency.evidence_snippets,
            contacts=[
                {
                    "name": d.get("name"),
                    "title": d.get("title"),
                    "email": d.get("email"),
                    "phone": d.get("phone"),
                    "source": d.get("source"),
                    "confidence": d.get("confidence"),
                }
                for d in contacts.decision_makers
            ],
            opportunity=intent.why_now if intent.why_now != UNKNOWN else intent.pain,
            industry=payload.get("industry") or UNKNOWN,
            confidence=score.total,
            ai_reasoning=reasoning,
            service_match=intent.best_service,
            score=score.total,
        )

    def analytics(self, decisions: list[ManualQaDecision] | list[dict[str, Any]]) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for d in decisions:
            if isinstance(d, ManualQaDecision):
                rows.append(d.model_dump(mode="json"))
            else:
                rows.append(dict(d))
        n = len(rows)
        if n == 0:
            return {
                "total": 0,
                "excellent": 0,
                "good": 0,
                "poor": 0,
                "fake": 0,
                "duplicate": 0,
                "wrong_service": 0,
                "wrong_intent": 0,
                "positive_percent": 0.0,
                "service_correct_percent": 0.0,
                "real_business_percent": 0.0,
                "note": "analytics_only_never_auto_tunes_production_rules",
            }

        def count(rating: str) -> int:
            return sum(1 for r in rows if str(r.get("rating")) == rating)

        excellent = count(QaRating.EXCELLENT.value)
        good = count(QaRating.GOOD.value)
        poor = count(QaRating.POOR.value)
        fake = count(QaRating.FAKE.value)
        duplicate = count(QaRating.DUPLICATE.value)
        wrong_service = count(QaRating.WRONG_SERVICE.value)
        wrong_intent = count(QaRating.WRONG_INTENT.value)
        positive = excellent + good
        # Service correct = not wrong_service among rated (exclude fake/dup from denom optionally)
        service_denom = max(1, n - fake - duplicate)
        service_correct = service_denom - wrong_service
        real = n - fake
        return {
            "total": n,
            "excellent": excellent,
            "good": good,
            "poor": poor,
            "fake": fake,
            "duplicate": duplicate,
            "wrong_service": wrong_service,
            "wrong_intent": wrong_intent,
            "positive_percent": round(100.0 * positive / n, 2),
            "service_correct_percent": round(100.0 * max(0, service_correct) / service_denom, 2),
            "real_business_percent": round(100.0 * real / n, 2),
            "note": "analytics_only_never_auto_tunes_production_rules",
        }

    def pending_from_snapshots(self, snapshots: list[AlphaSnapshot]) -> list[ManualQaCard]:
        return [
            s.qa_card
            for s in snapshots
            if s.verdict == AlphaVerdict.SALES_READY and s.qa_card is not None and s.score.founder_visible
        ]
