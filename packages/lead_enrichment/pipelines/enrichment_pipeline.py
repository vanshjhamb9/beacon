from __future__ import annotations

from collections import defaultdict

from lead_enrichment.connectors.dns_mx import DnsMxConnector
from lead_enrichment.connectors.licensed import LicensedProviderConnector
from lead_enrichment.connectors.public_profiles import PublicProfileConnector
from lead_enrichment.connectors.technology import TechnologyConnector
from lead_enrichment.connectors.website import WebsiteConnector
from lead_enrichment.extractors.company import CompanyProfileExtractor
from lead_enrichment.extractors.contacts import ContactExtractor
from lead_enrichment.extractors.jobs import JobsExtractor
from lead_enrichment.extractors.people import PeopleExtractor
from lead_enrichment.metrics.timing import EnrichmentTimer
from lead_enrichment.models.types import (
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    EvidenceChainItem,
    SalesReadyLeadProfile,
    SourceAttribution,
)
from lead_enrichment.scoring.engine import EnrichmentScorer
from lead_enrichment.validators.enrichment import EnrichmentValidator


class EnrichmentPipeline:
    def __init__(
        self,
        *,
        website: WebsiteConnector | None = None,
        dns: DnsMxConnector | None = None,
        public_profiles: PublicProfileConnector | None = None,
        technology: TechnologyConnector | None = None,
        licensed: LicensedProviderConnector | None = None,
        company_extractor: CompanyProfileExtractor | None = None,
        contact_extractor: ContactExtractor | None = None,
        people_extractor: PeopleExtractor | None = None,
        jobs_extractor: JobsExtractor | None = None,
        validator: EnrichmentValidator | None = None,
        scorer: EnrichmentScorer | None = None,
        timer: EnrichmentTimer | None = None,
    ) -> None:
        self.website = website or WebsiteConnector()
        self.dns = dns or DnsMxConnector()
        self.public_profiles = public_profiles or PublicProfileConnector()
        self.technology = technology or TechnologyConnector()
        self.licensed = licensed or LicensedProviderConnector()
        self.company_extractor = company_extractor or CompanyProfileExtractor()
        self.contact_extractor = contact_extractor or ContactExtractor()
        self.people_extractor = people_extractor or PeopleExtractor()
        self.jobs_extractor = jobs_extractor or JobsExtractor()
        self.validator = validator or EnrichmentValidator()
        self.scorer = scorer or EnrichmentScorer()
        self.timer = timer or EnrichmentTimer()

    def process(self, item: EnrichmentOpportunityInput) -> SalesReadyLeadProfile:
        def _run() -> SalesReadyLeadProfile:
            website = self.website.collect(item)
            dns = self.dns.collect(item)
            licensed_results = self.licensed.collect(item)
            technologies = self.technology.collect(item, website=website, dns=dns)
            for licensed_result in licensed_results:
                technologies.extend(licensed_result.technologies)

            profile = self.validator.validate_profile(self.company_extractor.extract(item, website))
            contacts = self.validator.validate_contacts(self.contact_extractor.extract(item, website))
            people = self.validator.validate_people(self.people_extractor.extract(item, website))
            technologies = self.validator.validate_technologies(technologies)
            social = self.validator.validate_social(self.public_profiles.collect(item, website=website))
            jobs, team_insights = self.jobs_extractor.extract(item, website, people_count=len(people))
            scores = self.scorer.score(
                profile=profile,
                contacts=contacts,
                technologies=technologies,
                decision_makers=people,
            )

            revenue = item.revenue_recommendation
            business_pain = str(revenue.get("business_pain") or self._primary_pain(item) or "Operational inefficiency")
            recommended_service = str(revenue.get("recommended_service") or "Service recommendation pending")
            buyer_persona = str(revenue.get("buyer_persona") or (people[0].role if people else "Founder"))
            estimated_budget = (
                str(revenue["estimated_budget_range"])
                if revenue.get("estimated_budget_range") is not None
                else profile.revenue_estimate
            )
            priority = str(revenue["priority"]) if revenue.get("priority") is not None else None
            why_now = self._why_now(item, revenue)
            outreach_angle = str(
                revenue.get("conversation_angle")
                or f"Connect {buyer_persona} pain around {business_pain} to {recommended_service}."
            )

            evidence_chain = self._evidence_chain(item, website_fetched=bool(website and website.fetched), dns=dns)
            source_attribution = self._source_attribution(
                profile_attributions=profile.attributions,
                contacts=contacts,
                people=people,
                technologies=technologies,
                social=social,
                licensed=licensed_results,
            )

            return SalesReadyLeadProfile(
                company_id=item.company_id,
                opportunity_id=item.opportunity_id,
                company_name=item.company_name,
                opportunity_score=item.opportunity_score,
                business_pain=business_pain,
                recommended_service=recommended_service,
                buyer_persona=buyer_persona,
                company_profile=profile,
                technology_stack=technologies,
                decision_makers=people,
                public_contact_information=contacts,
                team_insights=team_insights,
                social_profiles=social,
                open_jobs=jobs,
                estimated_budget=estimated_budget,
                priority=priority,
                why_now=why_now,
                best_outreach_angle=outreach_angle,
                evidence_chain=evidence_chain,
                source_attribution=source_attribution,
                enrichment_confidence=scores,
            )

        result, latency_ms = self.timer.measure(_run)
        return result.model_copy(update={"processing_latency_ms": latency_ms})

    def _primary_pain(self, item: EnrichmentOpportunityInput) -> str | None:
        if not item.pains:
            return None
        top = max(item.pains, key=lambda pain: float(pain.get("confidence") or 0.0))
        value = top.get("value") or top.get("category")
        return str(value) if value else None

    def _why_now(self, item: EnrichmentOpportunityInput, revenue: dict[str, object]) -> str:
        if item.opportunity_narrative:
            return item.opportunity_narrative
        priority = revenue.get("priority")
        return (
            f"{item.company_name} is {item.opportunity_status} with opportunity score "
            f"{item.opportunity_score:.1f}"
            + (f" and revenue priority {priority}." if priority else ".")
        )

    def _evidence_chain(
        self,
        item: EnrichmentOpportunityInput,
        *,
        website_fetched: bool,
        dns: object,
    ) -> list[EvidenceChainItem]:
        chain: list[EvidenceChainItem] = [
            EvidenceChainItem(
                category="opportunity",
                summary=f"Opportunity score {item.opportunity_score:.1f} ({item.opportunity_status})",
                source=EnrichmentSourceType.BEACON_OPPORTUNITY,
                confidence=min(100.0, item.opportunity_score),
                reference_id=str(item.opportunity_id),
            )
        ]
        if item.revenue_recommendation:
            chain.append(
                EvidenceChainItem(
                    category="revenue",
                    summary=str(
                        item.revenue_recommendation.get("recommended_service")
                        or "Revenue recommendation available"
                    ),
                    source=EnrichmentSourceType.BEACON_REVENUE,
                    confidence=float(item.revenue_recommendation.get("confidence") or 70.0),
                )
            )
        if website_fetched:
            chain.append(
                EvidenceChainItem(
                    category="website",
                    summary="Public company website pages fetched for enrichment",
                    source=EnrichmentSourceType.COMPANY_WEBSITE,
                    confidence=80.0,
                    source_url=item.website,
                )
            )
        if dns is not None and getattr(dns, "mx_hosts", None):
            chain.append(
                EvidenceChainItem(
                    category="dns_mx",
                    summary=f"MX provider {getattr(dns, 'mail_provider', None) or 'detected'}",
                    source=EnrichmentSourceType.DNS_MX,
                    confidence=float(getattr(dns, "confidence", 0.0) or 0.0),
                )
            )
        for evidence in item.opportunity_evidence[:8]:
            chain.append(
                EvidenceChainItem(
                    category=str(evidence.get("category") or "signal"),
                    summary=str(evidence.get("summary") or "Opportunity evidence"),
                    source=EnrichmentSourceType.BEACON_OPPORTUNITY,
                    confidence=float(evidence.get("confidence") or 60.0),
                    reference_id=str(evidence.get("reference_id")) if evidence.get("reference_id") else None,
                )
            )
        return chain

    def _source_attribution(
        self,
        *,
        profile_attributions: list[object],
        contacts: list[object],
        people: list[object],
        technologies: list[object],
        social: list[object],
        licensed: list[object],
    ) -> list[SourceAttribution]:
        buckets: dict[EnrichmentSourceType, dict[str, object]] = defaultdict(
            lambda: {"fields": set(), "confidence": [], "url": None, "licensed": False}
        )

        for attribution in profile_attributions:
            source = attribution.source  # type: ignore[attr-defined]
            buckets[source]["fields"].add(attribution.field_name)  # type: ignore[attr-defined]
            buckets[source]["confidence"].append(attribution.confidence)  # type: ignore[attr-defined]
            if attribution.source_url:  # type: ignore[attr-defined]
                buckets[source]["url"] = attribution.source_url  # type: ignore[attr-defined]

        for contact in contacts:
            buckets[contact.source]["fields"].add(f"contact:{contact.kind.value}")  # type: ignore[attr-defined]
            buckets[contact.source]["confidence"].append(contact.confidence)  # type: ignore[attr-defined]
            if contact.source_url:  # type: ignore[attr-defined]
                buckets[contact.source]["url"] = contact.source_url  # type: ignore[attr-defined]

        for person in people:
            buckets[person.source]["fields"].add(f"person:{person.role}")  # type: ignore[attr-defined]
            buckets[person.source]["confidence"].append(person.confidence)  # type: ignore[attr-defined]

        for tech in technologies:
            buckets[tech.source]["fields"].add(f"tech:{tech.name}")  # type: ignore[attr-defined]
            buckets[tech.source]["confidence"].append(tech.confidence)  # type: ignore[attr-defined]

        for profile in social:
            buckets[profile.source]["fields"].add(f"social:{profile.platform}")  # type: ignore[attr-defined]
            buckets[profile.source]["confidence"].append(profile.confidence)  # type: ignore[attr-defined]
            buckets[profile.source]["url"] = profile.url  # type: ignore[attr-defined]

        for result in licensed:
            source = result.provider  # type: ignore[attr-defined]
            buckets[source]["licensed"] = True
            if result.enabled:  # type: ignore[attr-defined]
                buckets[source]["fields"].add("licensed_provider")
                buckets[source]["confidence"].append(60.0)
            else:
                buckets[source]["fields"].add("skipped_unlicensed")
                buckets[source]["confidence"].append(0.0)

        attributions: list[SourceAttribution] = []
        for source, payload in buckets.items():
            confidences = payload["confidence"]
            avg = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
            attributions.append(
                SourceAttribution(
                    source=source,
                    source_url=payload["url"] if isinstance(payload["url"], str) else None,
                    fields=sorted(payload["fields"]),
                    confidence=avg,
                    licensed=bool(payload["licensed"]),
                    notes="Lawful public, licensed, or user-provided source only.",
                )
            )
        return sorted(attributions, key=lambda item: item.confidence, reverse=True)
