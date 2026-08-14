from __future__ import annotations

from datetime import datetime
from typing import Any

from data_verification.models.types import FieldObservation


class ObservationBuilder:
    def build(
        self,
        lead_profile: dict[str, Any],
        *,
        enriched_at: datetime,
        source_rows: list[dict[str, Any]],
    ) -> list[FieldObservation]:
        observations: list[FieldObservation] = []
        profile = lead_profile.get("company_profile") or {}
        attributions = list(profile.get("attributions") or [])

        for attribution in attributions:
            field_name = str(attribution.get("field_name") or "")
            if not field_name:
                continue
            observations.append(
                FieldObservation(
                    field_name=f"company_profile.{field_name}",
                    value=attribution.get("value"),
                    source=str(attribution.get("source") or "unknown"),
                    source_url=attribution.get("source_url"),
                    confidence=float(attribution.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(attribution.get("source") or "unknown"),
                )
            )

        for key in (
            "website",
            "domain",
            "industry",
            "description",
            "location",
            "country",
            "founded_year",
            "employee_count_estimate",
            "company_size_range",
            "revenue_estimate",
        ):
            if profile.get(key) is None or profile.get(key) == "":
                continue
            if any(item.field_name == f"company_profile.{key}" for item in observations):
                continue
            observations.append(
                FieldObservation(
                    field_name=f"company_profile.{key}",
                    value=profile.get(key),
                    source="beacon_intelligence",
                    confidence=70.0,
                    collected_at=enriched_at,
                    connector="beacon_intelligence",
                )
            )

        for contact in lead_profile.get("public_contact_information") or []:
            kind = str(contact.get("kind") or "general")
            observations.append(
                FieldObservation(
                    field_name=f"contact.{kind}",
                    value=contact.get("value"),
                    source=str(contact.get("source") or "unknown"),
                    source_url=contact.get("source_url"),
                    confidence=float(contact.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(contact.get("source") or "unknown"),
                )
            )

        for person in lead_profile.get("decision_makers") or []:
            role = str(person.get("role") or "person").lower().replace(" ", "_")
            observations.append(
                FieldObservation(
                    field_name=f"leadership.{role}.name",
                    value=person.get("name"),
                    source=str(person.get("source") or "unknown"),
                    source_url=person.get("source_url"),
                    confidence=float(person.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(person.get("source") or "unknown"),
                )
            )
            if person.get("linkedin_url"):
                observations.append(
                    FieldObservation(
                        field_name=f"leadership.{role}.linkedin_url",
                        value=person.get("linkedin_url"),
                        source=str(person.get("source") or "unknown"),
                        confidence=float(person.get("confidence") or 50.0),
                        collected_at=enriched_at,
                        connector=str(person.get("source") or "unknown"),
                    )
                )

        for tech in lead_profile.get("technology_stack") or []:
            name = str(tech.get("name") or "").strip()
            if not name:
                continue
            observations.append(
                FieldObservation(
                    field_name=f"tech.{name.lower()}",
                    value=name,
                    source=str(tech.get("source") or "unknown"),
                    source_url=tech.get("source_url"),
                    confidence=float(tech.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(tech.get("source") or "unknown"),
                )
            )

        for social in lead_profile.get("social_profiles") or []:
            platform = str(social.get("platform") or "social")
            observations.append(
                FieldObservation(
                    field_name=f"social.{platform}",
                    value=social.get("url"),
                    source=str(social.get("source") or "unknown"),
                    confidence=float(social.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(social.get("source") or "unknown"),
                )
            )

        for job in lead_profile.get("open_jobs") or []:
            title = str(job.get("title") or "").strip()
            if not title:
                continue
            observations.append(
                FieldObservation(
                    field_name=f"job.{title.lower()}",
                    value=title,
                    source=str(job.get("source") or "unknown"),
                    source_url=job.get("source_url"),
                    confidence=float(job.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(job.get("source") or "unknown"),
                )
            )

        for key in ("recommended_service", "business_pain", "buyer_persona", "estimated_budget", "priority"):
            if lead_profile.get(key):
                observations.append(
                    FieldObservation(
                        field_name=f"revenue.{key}",
                        value=lead_profile.get(key),
                        source="beacon_revenue",
                        confidence=float((lead_profile.get("enrichment_confidence") or {}).get("overall_enrichment_confidence") or 70.0),
                        collected_at=enriched_at,
                        connector="beacon_revenue",
                    )
                )

        for index, evidence in enumerate(lead_profile.get("evidence_chain") or []):
            observations.append(
                FieldObservation(
                    field_name=f"evidence.{index}.{evidence.get('category') or 'signal'}",
                    value=evidence.get("summary"),
                    source=str(evidence.get("source") or "unknown"),
                    source_url=evidence.get("source_url"),
                    confidence=float(evidence.get("confidence") or 50.0),
                    collected_at=enriched_at,
                    connector=str(evidence.get("source") or "unknown"),
                )
            )

        for row in source_rows:
            for field_name in row.get("fields") or []:
                observations.append(
                    FieldObservation(
                        field_name=str(field_name),
                        value=True,
                        source=str(row.get("source") or "unknown"),
                        source_url=row.get("source_url"),
                        confidence=float(row.get("confidence") or 50.0),
                        collected_at=enriched_at,
                        connector=str(row.get("source") or "unknown"),
                    )
                )

        return observations
