from __future__ import annotations

from typing import Any

from sales_readiness.models.types import ContactCompleteness, OutreachReadiness, OutreachReadinessStatus


class OutreachReadinessEngine:
    """Answer: can we contact today?"""

    def evaluate(self, payload: dict[str, Any], contacts: ContactCompleteness | None = None) -> OutreachReadiness:
        emails = list(payload.get("emails") or [])
        phones = list(payload.get("phones") or [])
        linkedin = bool(payload.get("linkedin_url") or payload.get("has_linkedin"))
        form = bool(payload.get("contact_form") or payload.get("has_contact_form"))
        website = bool(payload.get("website") or payload.get("primary_domain"))

        if contacts:
            for role in contacts.roles:
                if role.verified_email.value not in (None, "UNKNOWN", ""):
                    emails.append(str(role.verified_email.value))
                if role.verified_phone.value not in (None, "UNKNOWN", ""):
                    phones.append(str(role.verified_phone.value))
                if role.linkedin.value not in (None, "UNKNOWN", ""):
                    linkedin = True

        has_email = bool(emails)
        has_phone = bool(phones)
        evidence: list[str] = []
        if has_email:
            evidence.append(f"emails:{len(emails)}")
        if has_phone:
            evidence.append(f"phones:{len(phones)}")
        if linkedin:
            evidence.append("linkedin")
        if form:
            evidence.append("contact_form")
        if website:
            evidence.append("website")

        if has_email and (has_phone or linkedin):
            status = OutreachReadinessStatus.MULTI_CHANNEL_READY
        elif has_email or form:
            status = OutreachReadinessStatus.EMAIL_READY
        elif has_phone:
            status = OutreachReadinessStatus.PHONE_READY
        elif linkedin:
            status = OutreachReadinessStatus.LINKEDIN_READY
        elif website:
            status = OutreachReadinessStatus.NEEDS_MORE_RESEARCH
        else:
            status = OutreachReadinessStatus.NO

        can = status in {
            OutreachReadinessStatus.EMAIL_READY,
            OutreachReadinessStatus.PHONE_READY,
            OutreachReadinessStatus.LINKEDIN_READY,
            OutreachReadinessStatus.MULTI_CHANNEL_READY,
        }
        return OutreachReadiness(status=status, can_contact_today=can, evidence=evidence or ["no_channels"])
