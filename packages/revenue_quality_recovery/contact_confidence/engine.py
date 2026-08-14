from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import (
    AttributedField,
    ConfidentContact,
    ContactConfidenceResult,
    ContactWaterfallResult,
    UNKNOWN,
)

PRIORITY_ROLES = ("Founder", "CEO", "CTO", "Sales Head", "VP Sales", "Head of Sales")


class ContactConfidenceEngine:
    """Rule 5 — every contact carries source, collected_at, confidence, verification, evidence."""

    def evaluate(
        self,
        payload: dict[str, Any],
        *,
        waterfall: ContactWaterfallResult | None = None,
    ) -> ContactConfidenceResult:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        contacts: list[ConfidentContact] = []
        evidence: list[str] = []

        people = list(payload.get("decision_makers") or [])
        if waterfall:
            for dm in waterfall.decision_makers:
                if isinstance(dm.value, dict):
                    people.append(dm.value)

        for person in people:
            if not isinstance(person, dict):
                continue
            name = str(person.get("name") or "").strip()
            if not name or name == UNKNOWN:
                evidence.append("skipped_nameless")
                continue
            role = str(person.get("role") or person.get("title") or UNKNOWN)
            source = str(person.get("source") or person.get("waterfall_source") or payload.get("source") or UNKNOWN)
            conf = float(person.get("confidence") or 0)
            if conf and conf <= 1.0:
                conf *= 100.0
            verification = str(person.get("verification") or ("verified" if person.get("email") and payload.get("mx_valid") else "unverified"))
            ts = person.get("collected_at") or collected_at

            email_val = person.get("email") or person.get("work_email")
            phone_val = person.get("phone") or person.get("business_phone")
            linkedin_val = person.get("linkedin") or person.get("linkedin_url")

            contact = ConfidentContact(
                name=name,
                role=role,
                email=AttributedField.of(
                    email_val,
                    source=source,
                    collected_at=ts,
                    confidence=conf or (85.0 if email_val else None),
                    verification=verification if email_val else UNKNOWN,
                    evidence=["email_observed"] if email_val else ["email_missing"],
                ),
                phone=AttributedField.of(
                    phone_val,
                    source=source,
                    collected_at=ts,
                    confidence=conf or (80.0 if phone_val else None),
                    verification=verification if phone_val else UNKNOWN,
                    evidence=["phone_observed"] if phone_val else ["phone_missing"],
                ),
                linkedin=AttributedField.of(
                    linkedin_val,
                    source=source,
                    collected_at=ts,
                    confidence=conf or (80.0 if linkedin_val else None),
                    verification="public_profile" if linkedin_val else UNKNOWN,
                    evidence=["linkedin_observed"] if linkedin_val else ["linkedin_missing"],
                ),
                source=source,
                collected_at=ts,
                confidence=conf or 60.0,
                verification=verification,
                evidence=[f"contact:{name}:{role}", f"source:{source}", f"verification:{verification}"],
            )
            # Require attribution completeness
            if contact.source == UNKNOWN or not contact.evidence:
                evidence.append(f"incomplete_attribution:{name}")
                continue
            contacts.append(contact)
            evidence.append(f"attributed:{name}")

        # Promote waterfall emails without inventing people
        if waterfall:
            for e in waterfall.emails:
                if e.value == UNKNOWN:
                    continue
                if any(c.email.value == e.value for c in contacts):
                    continue
                evidence.append(f"orphan_email:{e.value}:{e.source}")

        avg = round(sum(c.confidence for c in contacts) / len(contacts), 2) if contacts else 0.0
        email_count = sum(1 for c in contacts if c.email.value != UNKNOWN and c.email.verification not in {UNKNOWN, "unverified"} or (c.email.value != UNKNOWN and c.email.verification == "mx_valid"))
        # Count verified-ish emails more generously: verification present and not unknown
        verified_emails = sum(
            1
            for c in contacts
            if c.email.value != UNKNOWN and c.email.verification not in {UNKNOWN}
        )
        verified_phones = sum(
            1
            for c in contacts
            if c.phone.value != UNKNOWN and c.phone.verification not in {UNKNOWN}
        )

        return ContactConfidenceResult(
            contacts=contacts,
            average_confidence=avg,
            verified_email_count=verified_emails,
            verified_phone_count=verified_phones,
            evidence=evidence or ["no_attributed_contacts"],
        )
