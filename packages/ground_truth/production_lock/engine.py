from __future__ import annotations

from typing import Any

from ground_truth.models.types import (
    CompanyTruthProfile,
    ContactWaterfallV2Result,
    ProductionLockResult,
    UNKNOWN,
)


class ProductionLockEngine:
    """Rule 12 — lock Email/WhatsApp/Campaign/Founder Queue unless all gates pass."""

    def evaluate(
        self,
        *,
        truth: CompanyTruthProfile,
        contacts: ContactWaterfallV2Result,
        readiness: float,
        is_duplicate: bool = False,
        is_fake: bool = False,
        payload: dict[str, Any] | None = None,
    ) -> ProductionLockResult:
        payload = payload or {}
        identity = truth.company_name != UNKNOWN and "who_are_they" not in truth.questions.missing
        website = truth.website.value != UNKNOWN
        evidence_ok = bool(payload.get("evidence") or payload.get("timeline") or truth.evidence_sources)
        intent = truth.intent.value not in (UNKNOWN, "Low") and "why_need_us" not in truth.questions.missing
        dm_or_email = bool(truth.decision_makers or truth.contacts_email or contacts.emails)
        sales_80 = readiness >= 80 and truth.trust >= 80
        not_dup = not is_duplicate
        not_fake = not is_fake
        source_known = bool(payload.get("source")) and str(payload.get("source")) != UNKNOWN
        trust_90 = truth.trust >= 90

        checks = {
            "identity": identity,
            "website": website,
            "evidence": evidence_ok,
            "intent": intent,
            "decision_maker_or_email": dm_or_email,
            "sales_readiness_80": sales_80,
            "not_duplicate": not_dup,
            "not_fake": not_fake,
            "source_known": source_known,
            "trust_90": trust_90,
        }
        failures = [k for k, ok in checks.items() if not ok]
        unlocked = len(failures) == 0 and truth.questions.all_answered

        return ProductionLockResult(
            unlocked=unlocked,
            identity=identity,
            website=website,
            evidence_ok=evidence_ok,
            intent=intent,
            decision_maker_or_email=dm_or_email,
            sales_readiness_80=sales_80,
            not_duplicate=not_dup,
            not_fake=not_fake,
            source_known=source_known,
            trust_90=trust_90,
            failures=failures,
            evidence=[f"lock:{'open' if unlocked else 'closed'}", *[f"fail:{f}" for f in failures]],
        )
