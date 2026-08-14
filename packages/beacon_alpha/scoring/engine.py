from __future__ import annotations

from beacon_alpha.models.types import (
    CompanyScore,
    ContactEnrichmentResult,
    IdentityGateResult,
    IntentV2Result,
    ServiceBucket,
    SourceTransparency,
)

FOUNDER_THRESHOLD = 80.0

WEIGHTS = {
    "identity": 25.0,
    "website": 15.0,
    "intent": 20.0,
    "service_match": 20.0,
    "contacts": 10.0,
    "evidence": 10.0,
}


class CompanyScoringEngine:
    """Rule 5 — conservative scoring; only 80+ appear to founder."""

    def score(
        self,
        *,
        identity: IdentityGateResult,
        intent: IntentV2Result,
        contacts: ContactEnrichmentResult,
        transparency: SourceTransparency,
        website_ok: bool,
    ) -> CompanyScore:
        identity_pts = WEIGHTS["identity"] if identity.passed else max(0.0, WEIGHTS["identity"] * (1 - len(identity.missing) / 8))
        website_pts = WEIGHTS["website"] if website_ok else 0.0

        buying = intent.scores.buying_signal
        intent_pts = round(WEIGHTS["intent"] * min(1.0, buying / 100.0), 2)

        service_pts = 0.0
        if intent.primary_bucket != ServiceBucket.UNKNOWN and intent.best_service:
            service_pts = WEIGHTS["service_match"] * min(1.0, (intent.buckets.get(intent.primary_bucket.value, 0) / 100.0))
            service_pts = round(max(service_pts, WEIGHTS["service_match"] * 0.55 if intent.best_service else 0), 2)

        contact_pts = 0.0
        if contacts.emails:
            contact_pts += 5.0
        if contacts.phones:
            contact_pts += 2.5
        if contacts.decision_makers:
            contact_pts += 2.5
        contact_pts = min(WEIGHTS["contacts"], contact_pts)

        evidence_pts = WEIGHTS["evidence"] if transparency.complete else (WEIGHTS["evidence"] * 0.4 if transparency.evidence_snippets else 0.0)

        total = round(identity_pts + website_pts + intent_pts + service_pts + contact_pts + evidence_pts, 2)
        return CompanyScore(
            total=total,
            identity=round(identity_pts, 2),
            website=round(website_pts, 2),
            intent=intent_pts,
            service_match=round(service_pts, 2),
            contacts=round(contact_pts, 2),
            evidence_score=round(evidence_pts, 2),
            founder_visible=total >= FOUNDER_THRESHOLD,
            evidence=[
                f"total:{total}",
                f"threshold:{FOUNDER_THRESHOLD}",
                f"visible:{total >= FOUNDER_THRESHOLD}",
            ],
        )
