from __future__ import annotations

from typing import Any

from ground_truth.models.types import (
    CompanyTruthProfile,
    ContactWaterfallV2Result,
    GtVerdict,
    RejectionReason,
    RejectionRecord,
    UNKNOWN,
)
from production_hardening.admission.engine import FAKE_NAME_PATTERNS


class RejectionEngine:
    """Rule 9 — every rejection needs a clear explanation."""

    def evaluate(
        self,
        payload: dict[str, Any],
        *,
        truth: CompanyTruthProfile,
        contacts: ContactWaterfallV2Result,
        is_duplicate: bool = False,
    ) -> RejectionRecord | None:
        reasons: list[RejectionReason] = []
        name = truth.company_name
        entity = str(payload.get("entity_type") or "").lower()
        url = str(payload.get("url") or payload.get("source_url") or payload.get("website") or "")

        if name.lower() in FAKE_NAME_PATTERNS or entity in {"fake", "noise"}:
            reasons.append(RejectionReason.FAKE)
        if is_duplicate:
            reasons.append(RejectionReason.DUPLICATE)
        if truth.website.value == UNKNOWN:
            reasons.append(RejectionReason.NO_WEBSITE)
        if not contacts.emails and not contacts.phones and not truth.contacts_email and not payload.get("contact_form"):
            reasons.append(RejectionReason.NO_CONTACT)
        if "marketplace" in entity or "marketplace" in url.lower() or entity in {"listing"}:
            reasons.append(RejectionReason.MARKETPLACE_LISTING)
        if "github.com/" in url.lower() or entity in {"repository", "library", "opensource"}:
            reasons.append(RejectionReason.GITHUB_REPOSITORY)
        if entity in {"blog", "individual", "community", "documentation"} or not truth.description.value or truth.description.value == UNKNOWN:
            if entity in {"blog", "individual", "community", "documentation"}:
                reasons.append(RejectionReason.NO_BUSINESS)
        if truth.intent.value in (UNKNOWN, "Low") and "why_need_us" in truth.questions.missing:
            reasons.append(RejectionReason.LOW_INTENT)
        if not (payload.get("evidence") or payload.get("timeline")):
            reasons.append(RejectionReason.NO_EVIDENCE)
        for q, reason in (
            ("who_are_they", RejectionReason.UNKNOWN_IDENTITY),
            ("why_need_us", RejectionReason.UNKNOWN_WHY_NEED_US),
            ("where_found", RejectionReason.UNKNOWN_SOURCE),
            ("who_decides", RejectionReason.UNKNOWN_DECISION_MAKER),
            ("why_now", RejectionReason.UNKNOWN_WHY_NOW),
        ):
            if q in truth.questions.missing:
                reasons.append(reason)
        if truth.trust < 90 and truth.sales_ready is False:
            reasons.append(RejectionReason.LOW_TRUST)
        if not truth.sales_ready:
            reasons.append(RejectionReason.LOW_READINESS)

        # Deduplicate reasons while preserving order
        seen: set[RejectionReason] = set()
        unique: list[RejectionReason] = []
        for r in reasons:
            if r in seen:
                continue
            seen.add(r)
            unique.append(r)

        if truth.questions.all_answered and truth.sales_ready and not is_duplicate and RejectionReason.FAKE not in unique:
            return None

        explanation = " → ".join(r.value for r in unique) if unique else "Rejected"
        return RejectionRecord(
            company_id=truth.company_id,
            company_name=name,
            reasons=unique,
            explanation=explanation,
            evidence=[f"reason:{r.value}" for r in unique],
        )
