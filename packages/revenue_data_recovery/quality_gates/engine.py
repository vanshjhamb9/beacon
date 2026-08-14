from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import (
    ContactRecoveryResult,
    FakeEliminationResult,
    IdentityRecoveryResult,
    IntentIntelligenceResult,
    QualityGateResult,
    WebsiteRecoveryResult,
    UNKNOWN,
)

DEFAULT_INTENT_THRESHOLD = 25.0
DEFAULT_TRUST_THRESHOLD = 55.0


class QualityGateEngine:
    """Block Revenue Hunter unless identity/website/business/intent/trust + one contact path."""

    def __init__(
        self,
        *,
        intent_threshold: float = DEFAULT_INTENT_THRESHOLD,
        trust_threshold: float = DEFAULT_TRUST_THRESHOLD,
    ) -> None:
        self.intent_threshold = intent_threshold
        self.trust_threshold = trust_threshold

    def evaluate(
        self,
        *,
        identity: IdentityRecoveryResult,
        website: WebsiteRecoveryResult,
        fake: FakeEliminationResult,
        contacts: ContactRecoveryResult,
        intent: IntentIntelligenceResult,
        trust_score: float,
        payload: dict[str, Any] | None = None,
    ) -> QualityGateResult:
        payload = payload or {}
        failures: list[str] = []
        paths: list[str] = []
        evidence: list[str] = []

        identity_ok = identity.identity_complete
        website_ok = website.website_verified
        business_ok = fake.is_business and not fake.is_fake
        intent_ok = intent.score >= self.intent_threshold
        trust_ok = trust_score >= self.trust_threshold

        if not identity_ok:
            failures.append("identity_incomplete")
        if not website_ok:
            failures.append("website_unverified")
        if not business_ok:
            failures.append("business_unverified")
        if not intent_ok:
            failures.append("intent_below_threshold")
        if not trust_ok:
            failures.append("trust_below_threshold")

        # Contact paths
        if contacts.verified_email_count > 0 or any(
            c.email.value != UNKNOWN for c in contacts.contacts
        ):
            paths.append("verified_public_business_email")
        if payload.get("contact_form") or payload.get("has_contact_form"):
            paths.append("verified_contact_form")
        if contacts.verified_decision_maker_count > 0:
            paths.append("verified_public_decision_maker")
        linkedin = (
            identity.linkedin_company_url.value
            if identity.linkedin_company_url.value != UNKNOWN
            else payload.get("linkedin_url") or payload.get("linkedin_company_url")
        )
        if linkedin:
            paths.append("verified_linkedin_company_page")
        if contacts.verified_phone_count > 0 or any(c.phone.value != UNKNOWN for c in contacts.contacts):
            paths.append("verified_phone")

        contact_ok = len(paths) >= 1
        if not contact_ok:
            failures.append("no_verified_contact_path")

        passed = (
            identity_ok
            and website_ok
            and business_ok
            and intent_ok
            and trust_ok
            and contact_ok
        )
        evidence.append(f"gate:{'pass' if passed else 'fail'}")
        evidence.extend(f"path:{p}" for p in paths)
        evidence.extend(f"fail:{f}" for f in failures)

        return QualityGateResult(
            passed=passed,
            identity_complete=identity_ok,
            website_verified=website_ok,
            business_verified=business_ok,
            intent_above_threshold=intent_ok,
            trust_above_threshold=trust_ok,
            contact_path_ok=contact_ok,
            contact_paths=paths,
            failures=failures,
            evidence=evidence,
        )
