from __future__ import annotations

from lead_enrichment.models.types import (
    ContactEntry,
    ContactKind,
    EnrichedCompanyProfile,
    EnrichmentScores,
    PersonEntry,
    TechnologyEntry,
)


class EnrichmentScorer:
    def score(
        self,
        *,
        profile: EnrichedCompanyProfile,
        contacts: list[ContactEntry],
        technologies: list[TechnologyEntry],
        decision_makers: list[PersonEntry],
    ) -> EnrichmentScores:
        profile_fields = [
            profile.website,
            profile.domain,
            profile.industry,
            profile.description,
            profile.location,
            profile.country,
            profile.founded_year,
            profile.employee_count_estimate,
            profile.company_size_range,
        ]
        filled = sum(1 for field in profile_fields if field not in (None, "", 0))
        profile_completeness = round((filled / len(profile_fields)) * 100.0, 2)

        has_email = any(
            contact.kind in {ContactKind.COMPANY_EMAIL, ContactKind.ROLE_BASED_EMAIL} for contact in contacts
        )
        has_phone = any(contact.kind == ContactKind.BUSINESS_PHONE for contact in contacts)
        has_role_email = any(contact.kind == ContactKind.ROLE_BASED_EMAIL for contact in contacts)
        contact_availability = round(
            (40.0 if has_email else 0.0)
            + (30.0 if has_phone else 0.0)
            + (20.0 if has_role_email else 0.0)
            + (10.0 if contacts else 0.0),
            2,
        )

        if technologies:
            technology_confidence = round(
                sum(tech.confidence for tech in technologies) / len(technologies),
                2,
            )
        else:
            technology_confidence = 0.0

        if decision_makers:
            decision_maker_confidence = round(
                sum(person.confidence for person in decision_makers) / len(decision_makers),
                2,
            )
        else:
            decision_maker_confidence = 0.0

        overall = round(
            profile_completeness * 0.30
            + contact_availability * 0.30
            + technology_confidence * 0.20
            + decision_maker_confidence * 0.20,
            2,
        )
        return EnrichmentScores(
            profile_completeness=profile_completeness,
            contact_availability=min(100.0, contact_availability),
            technology_confidence=min(100.0, technology_confidence),
            decision_maker_confidence=min(100.0, decision_maker_confidence),
            overall_enrichment_confidence=min(100.0, overall),
        )
