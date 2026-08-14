from __future__ import annotations

from typing import Any

from beacon_alpha.admission.engine import ColdEmailAdmissionEngine
from beacon_alpha.contact_enrichment.engine import ContactEnrichmentEngine
from beacon_alpha.founder_queue.engine import FounderQueueEngine
from beacon_alpha.identity_gate.engine import IdentityGateEngine
from beacon_alpha.intent_v2.engine import IntentV2Engine
from beacon_alpha.manual_qa.engine import ManualQaEngine
from beacon_alpha.models.types import AlphaSnapshot, AlphaVerdict, UNKNOWN
from beacon_alpha.scoring.engine import CompanyScoringEngine
from beacon_alpha.transparency.engine import SourceTransparencyEngine


class BeaconAlphaPipeline:
    """Alpha — data quality only. REJECTED or SALES_READY for founder-visible outbound."""

    def __init__(self) -> None:
        self.admission = ColdEmailAdmissionEngine()
        self.identity = IdentityGateEngine()
        self.contacts = ContactEnrichmentEngine()
        self.intent = IntentV2Engine()
        self.transparency = SourceTransparencyEngine()
        self.scoring = CompanyScoringEngine()
        self.founder_queue = FounderQueueEngine()
        self.manual_qa = ManualQaEngine()

    def evaluate(self, payload: dict[str, Any]) -> AlphaSnapshot:
        company_id = str(payload.get("company_id") or payload.get("id") or UNKNOWN)
        company_name = str(payload.get("company_name") or payload.get("legal_name") or payload.get("name") or UNKNOWN)

        admission = self.admission.evaluate(payload)
        identity = self.identity.evaluate(payload)
        transparency = self.transparency.build(payload)

        # Only enrich contacts after identity passes (Rule 3)
        if identity.passed:
            contacts = self.contacts.enrich(payload)
        else:
            from beacon_alpha.models.types import ContactEnrichmentResult

            contacts = ContactEnrichmentResult(evidence=["skipped_until_identity_passes"])

        intent = self.intent.classify(payload)
        website_ok = bool(payload.get("website") or payload.get("domain") or payload.get("website_alive"))
        score = self.scoring.score(
            identity=identity,
            intent=intent,
            contacts=contacts,
            transparency=transparency,
            website_ok=website_ok,
        )

        verdict = AlphaVerdict.REJECTED
        if admission.admit and identity.passed and score.founder_visible and intent.primary_bucket.value != "UNKNOWN":
            verdict = AlphaVerdict.SALES_READY
        elif admission.admit and identity.passed and score.total >= 80 and intent.best_service != UNKNOWN:
            verdict = AlphaVerdict.SALES_READY

        founder_card = None
        qa_card = None
        if verdict == AlphaVerdict.SALES_READY:
            founder_card = self.founder_queue.build_card(
                company_id=company_id,
                company_name=company_name,
                intent=intent,
                contacts=contacts,
                score=score,
                payload=payload,
            )
            qa_card = self.manual_qa.build_card(
                company_id=company_id,
                payload=payload,
                intent=intent,
                contacts=contacts,
                transparency=transparency,
                score=score,
            )
        else:
            # Ensure not visible
            score = score.model_copy(update={"founder_visible": False})

        return AlphaSnapshot(
            company_id=company_id,
            company_name=company_name,
            verdict=verdict,
            admission=admission,
            identity=identity,
            contacts=contacts,
            intent=intent,
            score=score,
            transparency=transparency,
            founder_card=founder_card,
            qa_card=qa_card,
            scoring_version="alpha-v1",
            evidence=[
                f"verdict:{verdict.value}",
                f"score:{score.total}",
                f"admit:{admission.admit}",
                f"identity:{identity.passed}",
            ],
        )

    def evaluate_many(self, payloads: list[dict[str, Any]]) -> list[AlphaSnapshot]:
        return [self.evaluate(p) for p in payloads]
