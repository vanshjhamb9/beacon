from __future__ import annotations

from typing import Any

from beacon_alpha.dedupe.engine import AlphaDedupeEngine
from ground_truth.contact_waterfall_v2.engine import ContactWaterfallV2Engine
from ground_truth.founder_queue.engine import GtFounderQueueEngine
from ground_truth.intelligence_card.engine import IntelligenceCardBuilder
from ground_truth.models.types import GtSnapshot, GtVerdict, RejectionReason, UNKNOWN
from ground_truth.production_lock.engine import ProductionLockEngine
from ground_truth.rejection.engine import RejectionEngine
from ground_truth.timeline.engine import CompanyTimelineEngine
from ground_truth.truth_engine.engine import CompanyTruthEngine
from production_hardening.admission.engine import FAKE_NAME_PATTERNS


class GroundTruthPipeline:
    """Alpha+ — one truth profile. Would Vansh email this company today?"""

    def __init__(self) -> None:
        self.contacts = ContactWaterfallV2Engine()
        self.truth = CompanyTruthEngine()
        self.timeline = CompanyTimelineEngine()
        self.card = IntelligenceCardBuilder()
        self.rejection = RejectionEngine()
        self.lock = ProductionLockEngine()
        self.founder = GtFounderQueueEngine()
        self.dedupe = AlphaDedupeEngine()

    def evaluate(self, payload: dict[str, Any], *, peer_companies: list[dict[str, Any]] | None = None) -> GtSnapshot:
        company_id = str(payload.get("company_id") or payload.get("id") or UNKNOWN)
        company_name = str(payload.get("company_name") or payload.get("legal_name") or payload.get("name") or UNKNOWN)

        contacts = self.contacts.enrich(payload)
        contact_blob = {
            "emails": contacts.emails,
            "phones": contacts.phones,
            "linkedin": contacts.linkedin,
            "decision_makers": contacts.decision_makers,
        }
        truth = self.truth.build(payload, contacts=contact_blob)
        # Merge waterfall emails into truth if truth list empty
        if not truth.contacts_email and contacts.emails:
            truth = truth.model_copy(update={"contacts_email": contacts.emails})
        if not truth.contacts_phone and contacts.phones:
            truth = truth.model_copy(update={"contacts_phone": contacts.phones})

        timeline = self.timeline.build(payload)
        if truth.questions.why_now.value == UNKNOWN and timeline.why_now != UNKNOWN:
            from ground_truth.models.types import AttributedField

            why_now_f = AttributedField.of(
                timeline.why_now,
                source=str(payload.get("source") or "timeline"),
                collected_at=payload.get("collected_at"),
                confidence=80.0,
                evidence=["timeline_why_now"],
            )
            new_missing = [m for m in truth.questions.missing if m != "why_now"]
            questions = truth.questions.model_copy(
                update={
                    "why_now": why_now_f,
                    "missing": new_missing,
                    "all_answered": len(new_missing) == 0,
                    "evidence": [f"answered:{7 - len(new_missing)}/7"],
                }
            )
            truth = truth.model_copy(
                update={
                    "questions": questions,
                    "sales_ready": questions.all_answered and truth.trust >= 80 and truth.website.value != UNKNOWN,
                }
            )

        is_dup = False
        if peer_companies:
            for peer in peer_companies:
                if str(peer.get("company_id")) == company_id:
                    continue
                if self.dedupe.match(payload, peer).is_duplicate:
                    is_dup = True
                    break

        is_fake = company_name.lower() in FAKE_NAME_PATTERNS or str(payload.get("entity_type") or "").lower() in {
            "fake",
            "repository",
            "blog",
        }

        readiness = truth.trust
        lock = self.lock.evaluate(
            truth=truth,
            contacts=contacts,
            readiness=readiness,
            is_duplicate=is_dup,
            is_fake=is_fake,
            payload=payload,
        )

        rejection = self.rejection.evaluate(payload, truth=truth, contacts=contacts, is_duplicate=is_dup)
        card = self.card.build(truth=truth, timeline=timeline, contacts=contacts, payload=payload)

        verdict = GtVerdict.REJECTED
        founder_item = None
        if lock.unlocked and truth.questions.all_answered and not is_fake and not is_dup:
            emp = payload.get("employees") or payload.get("employee_estimate") or 0
            try:
                emp_n = int(emp)
            except (TypeError, ValueError):
                emp_n = 0
            verdict = GtVerdict.ENTERPRISE_READY if emp_n >= 500 or str(payload.get("stage") or "").lower() in {"enterprise", "public"} else GtVerdict.SALES_READY
            founder_item = self.founder.build_item(truth=truth, card=card, payload=payload)
            rejection = None
        elif rejection is None and not lock.unlocked:
            # ensure rejection exists when locked
            rejection = self.rejection.evaluate(
                payload,
                truth=truth.model_copy(update={"sales_ready": False}),
                contacts=contacts,
                is_duplicate=is_dup,
            )

        return GtSnapshot(
            company_id=company_id,
            company_name=company_name,
            verdict=verdict,
            questions=truth.questions,
            truth=truth,
            contacts=contacts,
            timeline=timeline,
            card=card,
            founder_item=founder_item,
            rejection=rejection,
            production_lock=lock,
            trust=truth.trust,
            readiness=readiness,
            scoring_version="alpha-plus-v1",
            evidence=[
                f"verdict:{verdict.value}",
                f"trust:{truth.trust}",
                f"lock:{lock.unlocked}",
                f"questions:{truth.questions.all_answered}",
            ],
        )

    def evaluate_many(self, payloads: list[dict[str, Any]]) -> list[GtSnapshot]:
        return [self.evaluate(p, peer_companies=payloads) for p in payloads]
