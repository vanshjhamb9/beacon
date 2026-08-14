from __future__ import annotations

from typing import Any

from revenue_data_recovery.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_recovery.dossier.engine import RevenueDossierBuilder
from revenue_data_recovery.fake_elimination.engine import FakeCompanyEliminationEngine
from revenue_data_recovery.identity_recovery.engine import IdentityRecoveryEngine
from revenue_data_recovery.intent_intelligence.engine import IntentIntelligenceEngine
from revenue_data_recovery.models.types import RdiSnapshot, SalesReadyStatus, UNKNOWN
from revenue_data_recovery.opportunity_validation.engine import OpportunityValidationEngine
from revenue_data_recovery.quality_gates.engine import QualityGateEngine
from revenue_data_recovery.recovery_queue.engine import RecoveryQueueEngine
from revenue_data_recovery.revenue_recommendation.engine import RevenueRecommendationEngine
from revenue_data_recovery.website_recovery.engine import WebsiteRecoveryEngine


class RevenueDataRecoveryPipeline:
    """Evidence → Identity → Intent → Contacts → Recommendation → Revenue."""

    def __init__(self) -> None:
        self.fake = FakeCompanyEliminationEngine()
        self.identity = IdentityRecoveryEngine()
        self.website = WebsiteRecoveryEngine()
        self.contacts = ContactRecoveryEngine()
        self.opportunity = OpportunityValidationEngine()
        self.intent = IntentIntelligenceEngine()
        self.recommendations = RevenueRecommendationEngine()
        self.quality = QualityGateEngine()
        self.queue = RecoveryQueueEngine()
        self.dossier = RevenueDossierBuilder()

    def evaluate(self, payload: dict[str, Any]) -> RdiSnapshot:
        company_id = str(payload.get("company_id") or payload.get("id") or UNKNOWN)
        company_name = str(payload.get("company_name") or payload.get("name") or payload.get("legal_name") or UNKNOWN)

        fake = self.fake.evaluate(payload)
        identity = self.identity.recover(payload)
        website = self.website.recover(payload)
        contacts = self.contacts.recover(payload)
        opportunity = self.opportunity.validate(payload)
        intent = self.intent.score(payload)

        enriched = {
            **payload,
            "intent_signals": [{"signal": s.signal} for s in intent.signals if s.matched],
            "signals": list(payload.get("signals") or []) + [s.signal for s in intent.signals if s.matched],
        }
        recommendations = self.recommendations.recommend(enriched)

        trust_score = self._trust(
            identity_complete=identity.identity_complete,
            website_verified=website.website_verified,
            is_business=fake.is_business and not fake.is_fake,
            intent_score=intent.score,
            contact_coverage=contacts.coverage_percent,
            opportunity_accepted=opportunity.accepted,
            identity_confidence=identity.confidence,
        )

        quality_gate = self.quality.evaluate(
            identity=identity,
            website=website,
            fake=fake,
            contacts=contacts,
            intent=intent,
            trust_score=trust_score,
            payload=payload,
        )

        queue_item = self.queue.advance(
            company_id=company_id,
            company_name=company_name,
            identity=identity,
            website=website,
            fake=fake,
            contacts=contacts,
            intent=intent,
            recommendations=recommendations,
            quality_gate=quality_gate,
            trust_score=trust_score,
        )

        dossier = self.dossier.build(
            company_id=company_id,
            company_name=company_name,
            identity=identity,
            website=website,
            contacts=contacts,
            intent=intent,
            recommendations=recommendations,
            quality_gate=quality_gate,
            queue_item=queue_item,
            trust_score=trust_score,
            payload=payload,
            fake=fake,
        )

        status = dossier.status
        if fake.is_fake:
            status = SalesReadyStatus.NOT_READY

        return RdiSnapshot(
            company_id=company_id,
            company_name=company_name,
            identity=identity,
            website=website,
            fake=fake,
            contacts=contacts,
            opportunity=opportunity,
            intent=intent,
            recommendations=recommendations,
            quality_gate=quality_gate,
            queue_item=queue_item,
            dossier=dossier,
            trust_score=trust_score,
            recovery_stage=queue_item.stage,
            status=status,
            eligible_for_revenue_hunter=quality_gate.passed and not fake.is_fake,
            visible_in_founder_queue=dossier.visible_in_founder_queue and not fake.is_fake,
            scoring_version="rdi-v1",
            evidence=[
                f"stage:{queue_item.stage.value}",
                f"trust:{trust_score}",
                f"gate:{quality_gate.passed}",
                f"fake:{fake.is_fake}",
                f"intent:{intent.score}",
            ],
        )

    def recover_many(self, payloads: list[dict[str, Any]]) -> list[RdiSnapshot]:
        return [self.evaluate(p) for p in payloads]

    def _trust(
        self,
        *,
        identity_complete: bool,
        website_verified: bool,
        is_business: bool,
        intent_score: float,
        contact_coverage: float,
        opportunity_accepted: bool,
        identity_confidence: float,
    ) -> float:
        score = 0.0
        if identity_complete:
            score += 25.0
        else:
            score += identity_confidence * 0.15
        if website_verified:
            score += 20.0
        if is_business:
            score += 15.0
        score += min(25.0, intent_score * 0.25)
        score += min(10.0, contact_coverage * 0.1)
        if opportunity_accepted:
            score += 5.0
        return round(min(100.0, score), 2)
