from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import (
    AttributedValue,
    ContactRecoveryResult,
    FakeEliminationResult,
    IdentityRecoveryResult,
    IntentIntelligenceResult,
    QualityGateResult,
    RecoveryQueueItem,
    RevenueDossier,
    RevenueRecommendationResult,
    SalesReadyStatus,
    WebsiteRecoveryResult,
    UNKNOWN,
)


class RevenueDossierBuilder:
    """One-page sales dossier — no 25-card scroll."""

    def build(
        self,
        *,
        company_id: str,
        company_name: str,
        identity: IdentityRecoveryResult,
        website: WebsiteRecoveryResult,
        contacts: ContactRecoveryResult,
        intent: IntentIntelligenceResult,
        recommendations: RevenueRecommendationResult,
        quality_gate: QualityGateResult,
        queue_item: RecoveryQueueItem,
        trust_score: float,
        payload: dict[str, Any],
        fake: FakeEliminationResult,
    ) -> RevenueDossier:
        stars = self._stars(trust_score)
        status = SalesReadyStatus.NOT_READY
        if quality_gate.passed:
            status = SalesReadyStatus.SALES_READY
        elif identity.identity_complete and website.website_verified and not fake.is_fake:
            status = SalesReadyStatus.PARTIAL

        techs = [
            str(t.get("name") if isinstance(t, dict) else t)
            for t in (payload.get("technologies") or [])
            if t
        ]
        timeline: list[AttributedValue] = []
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                timeline.append(
                    AttributedValue.of(
                        row.get("summary") or row.get("signal_type"),
                        source=str(row.get("source") or payload.get("source") or UNKNOWN),
                        collected_at=row.get("timestamp") or row.get("at"),
                        confidence=row.get("confidence"),
                        evidence=["timeline"],
                    )
                )

        buying = [s.signal for s in intent.signals if s.matched][:12]
        dms = [c for c in contacts.contacts if c.role in {"Founder", "CEO", "CTO", "COO", "VP Engineering"}]
        verified = [
            c
            for c in contacts.contacts
            if c.email.value != UNKNOWN or c.phone.value != UNKNOWN or c.linkedin.value != UNKNOWN
        ]

        next_action = queue_item.next_action
        if status == SalesReadyStatus.SALES_READY:
            next_action = "Contact today using verified public channel"

        return RevenueDossier(
            company_id=company_id,
            company_name=company_name,
            stars=stars,
            status=status,
            identity=identity,
            industry=identity.industry.value,
            country=identity.country.value,
            website=website.verified_website.value if website.website_verified else identity.website.value,
            employees=identity.employee_estimate.value,
            technology=techs[:20],
            intent=intent,
            decision_makers=dms,
            verified_contacts=verified,
            buying_signals=buying,
            recommended_services=recommendations.recommendations,
            estimated_deal=recommendations.primary_estimate,
            evidence_timeline=timeline[:20],
            trust_score=trust_score,
            next_action=next_action,
            recovery_stage=queue_item.stage,
            eligible_for_revenue_hunter=quality_gate.passed,
            visible_in_founder_queue=quality_gate.passed
            or (
                status == SalesReadyStatus.PARTIAL
                and intent.score >= 45
                and contacts.verified_decision_maker_count > 0
            ),
            quality_gate=quality_gate,
            scoring_version="rdi-v1",
            evidence=[
                f"status:{status.value}",
                f"stars:{stars}",
                f"trust:{trust_score}",
                f"stage:{queue_item.stage.value}",
            ],
        )

    def _stars(self, trust: float) -> int:
        if trust >= 90:
            return 5
        if trust >= 75:
            return 4
        if trust >= 60:
            return 3
        if trust >= 40:
            return 2
        if trust >= 20:
            return 1
        return 0
