from __future__ import annotations

from revenue_data_recovery.models.types import (
    ContactRecoveryResult,
    FakeEliminationResult,
    IdentityRecoveryResult,
    IntentIntelligenceResult,
    QualityGateResult,
    RecoveryQueueItem,
    RecoveryStage,
    RevenueRecommendationResult,
    WebsiteRecoveryResult,
)

STAGE_ORDER = (
    RecoveryStage.NEW,
    RecoveryStage.IDENTITY_RECOVERY,
    RecoveryStage.WEBSITE_RECOVERY,
    RecoveryStage.CONTACT_RECOVERY,
    RecoveryStage.INTENT_ANALYSIS,
    RecoveryStage.SERVICE_MATCH,
    RecoveryStage.TRUST,
    RecoveryStage.SALES_READY,
    RecoveryStage.REVENUE_HUNTER,
)


class RecoveryQueueEngine:
    """Track companies through the recovery pipeline stages."""

    def advance(
        self,
        *,
        company_id: str,
        company_name: str,
        identity: IdentityRecoveryResult,
        website: WebsiteRecoveryResult,
        fake: FakeEliminationResult,
        contacts: ContactRecoveryResult,
        intent: IntentIntelligenceResult,
        recommendations: RevenueRecommendationResult,
        quality_gate: QualityGateResult,
        trust_score: float,
    ) -> RecoveryQueueItem:
        if fake.is_fake:
            return RecoveryQueueItem(
                company_id=company_id,
                company_name=company_name,
                stage=RecoveryStage.REJECTED,
                priority=0.0,
                progress_percent=0.0,
                next_action="Eliminate fake / non-business entity",
                blocked_reasons=fake.reasons,
                evidence=["stage:REJECTED"],
            )

        blocked: list[str] = []
        next_action = "Begin identity recovery"

        if not identity.identity_complete:
            stage = RecoveryStage.IDENTITY_RECOVERY
            blocked = list(identity.missing_fields)
            next_action = f"Recover identity fields: {', '.join(blocked[:4]) or 'core fields'}"
        elif not website.website_verified:
            stage = RecoveryStage.WEBSITE_RECOVERY
            blocked = [website.rejected_reason or "website_unverified"]
            next_action = "Recover and verify canonical website"
        elif contacts.coverage_percent < 8.0 and contacts.verified_decision_maker_count == 0:
            stage = RecoveryStage.CONTACT_RECOVERY
            blocked = ["insufficient_public_contacts"]
            next_action = "Recover public decision-maker contacts"
        elif intent.score < 25.0:
            stage = RecoveryStage.INTENT_ANALYSIS
            blocked = ["intent_below_threshold"]
            next_action = "Gather stronger buying / hiring / tech signals"
        elif not recommendations.recommendations:
            stage = RecoveryStage.SERVICE_MATCH
            blocked = ["no_service_match"]
            next_action = "Match concrete service from evidence"
        elif trust_score < 55.0:
            stage = RecoveryStage.TRUST
            blocked = ["trust_below_threshold"]
            next_action = "Improve trust via verification + evidence freshness"
        elif quality_gate.passed:
            stage = RecoveryStage.REVENUE_HUNTER
            next_action = "Route to Revenue Hunter"
        else:
            stage = RecoveryStage.SALES_READY
            blocked = list(quality_gate.failures)
            next_action = "Close quality-gate gaps for Revenue Hunter"

        progress = self._progress(stage)
        priority = round(
            (identity.confidence * 0.2)
            + (website.confidence * 0.15)
            + (intent.score * 0.35)
            + (trust_score * 0.2)
            + (contacts.coverage_percent * 0.1),
            2,
        )
        return RecoveryQueueItem(
            company_id=company_id,
            company_name=company_name,
            stage=stage,
            priority=priority,
            progress_percent=progress,
            next_action=next_action,
            blocked_reasons=blocked,
            evidence=[f"stage:{stage.value}", f"progress:{progress}"],
        )

    def _progress(self, stage: RecoveryStage) -> float:
        if stage == RecoveryStage.REJECTED:
            return 0.0
        try:
            idx = STAGE_ORDER.index(stage)
        except ValueError:
            return 0.0
        return round(100.0 * idx / (len(STAGE_ORDER) - 1), 2)
