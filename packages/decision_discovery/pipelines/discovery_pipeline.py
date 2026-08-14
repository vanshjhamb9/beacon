from __future__ import annotations

from decision_discovery.connectors.licensed import LicensedPeopleConnector
from decision_discovery.extractors.channels import ContactChannelExtractor
from decision_discovery.extractors.departments import DepartmentExtractor
from decision_discovery.extractors.people import DecisionMakerExtractor
from decision_discovery.matching.buyer import BuyerMatcher
from decision_discovery.metrics.timing import DiscoveryTimer
from decision_discovery.models.types import (
    DecisionDiscoveryInput,
    DecisionMakerReport,
    DiscoverySourceType,
    EvidenceChainItem,
    SourceAttribution,
)
from decision_discovery.ranking.channels import ContactChannelRanker
from decision_discovery.ranking.confidence import DiscoveryConfidenceEngine
from decision_discovery.validators.discovery import DiscoveryValidator


class DecisionDiscoveryPipeline:
    def __init__(
        self,
        *,
        people: DecisionMakerExtractor | None = None,
        channels: ContactChannelExtractor | None = None,
        departments: DepartmentExtractor | None = None,
        matcher: BuyerMatcher | None = None,
        ranker: ContactChannelRanker | None = None,
        confidence: DiscoveryConfidenceEngine | None = None,
        validator: DiscoveryValidator | None = None,
        licensed: LicensedPeopleConnector | None = None,
        timer: DiscoveryTimer | None = None,
    ) -> None:
        self.people = people or DecisionMakerExtractor()
        self.channels = channels or ContactChannelExtractor()
        self.departments = departments or DepartmentExtractor()
        self.matcher = matcher or BuyerMatcher()
        self.ranker = ranker or ContactChannelRanker()
        self.confidence = confidence or DiscoveryConfidenceEngine()
        self.validator = validator or DiscoveryValidator()
        self.licensed = licensed or LicensedPeopleConnector(enabled=False)
        self.timer = timer or DiscoveryTimer()

    def process(self, item: DecisionDiscoveryInput) -> DecisionMakerReport:
        result, latency_ms = self.timer.time_call(lambda: self._process(item))
        return result.model_copy(update={"processing_latency_ms": latency_ms})

    def _process(self, item: DecisionDiscoveryInput) -> DecisionMakerReport:
        people_rows = list(item.enrichment_people) + list(item.known_people)
        licensed_notes: list[str] = []
        for licensed in self.licensed.fetch(company_name=item.company_name, domain=item.domain):
            licensed_notes.append(licensed.notes)
            if licensed.enabled and licensed.people:
                people_rows.extend(licensed.people)

        makers = self.people.extract(people_rows)
        leadership = self.people.to_leadership(makers)
        departments = self.departments.extract(makers, item.context_intelligence, item.lead_profile)
        raw_channels = self.channels.extract_channels(
            contacts=item.enrichment_contacts,
            profiles=item.enrichment_profiles,
            lead_profile=item.lead_profile,
            domain=item.domain,
        )
        profiles = self.channels.extract_profiles(item.enrichment_profiles)

        preferred = self.matcher.preferred_roles(item.recommended_service, item.buyer_persona)
        primary, secondary, ranked_makers = self.matcher.select_primary_secondary(makers, preferred)
        ranked_channels, outreach = self.ranker.rank(raw_channels, primary, secondary)
        ranked_makers, ranked_channels = self.validator.reject_invented_contacts(ranked_makers, ranked_channels)

        buyer_match_confidence = 0.0
        if primary is not None:
            buyer_match_confidence = primary.buyer_match_score
        elif preferred:
            buyer_match_confidence = 20.0

        confidence = self.confidence.score(
            makers=ranked_makers,
            leadership=leadership,
            departments=departments,
            channels=ranked_channels,
            buyer_match_confidence=buyer_match_confidence,
        )

        reason = self._reason(item, primary, secondary, ranked_channels)
        evidence = self._evidence(item, primary, ranked_channels, departments)
        attributions = self._attributions(ranked_makers, ranked_channels, profiles, licensed_notes)

        report = DecisionMakerReport(
            company_id=item.company_id,
            opportunity_id=item.opportunity_id,
            verification_report_id=item.verification_report_id,
            enrichment_report_id=item.enrichment_report_id,
            company_name=item.company_name,
            opportunity_score=item.opportunity_score,
            business_pain=item.business_pain,
            recommended_service=item.recommended_service,
            primary_decision_maker=primary,
            secondary_decision_maker=secondary,
            decision_makers=ranked_makers,
            departments=departments,
            leadership=leadership,
            contact_channels=ranked_channels,
            public_profiles=profiles,
            best_outreach_sequence=outreach,
            buyer_match_confidence=buyer_match_confidence,
            reason=reason,
            evidence_chain=evidence,
            source_attribution=attributions,
            confidence=confidence,
            report_payload={
                "preferred_roles": [role.value for role in preferred],
                "licensed_provider_notes": licensed_notes,
            },
        )
        return self.validator.validate_report(report)

    def _reason(
        self,
        item: DecisionDiscoveryInput,
        primary: object,
        secondary: object,
        channels: list,
    ) -> str:
        if primary is None:
            if channels:
                return (
                    f"No named public decision maker confirmed for {item.recommended_service}; "
                    "official business contact channels are available for outreach sequencing."
                )
            return (
                f"No verified public decision maker or business contact was found for {item.company_name}."
            )
        primary_name = getattr(primary, "name", "Unknown")
        primary_role = getattr(primary, "role", "Unknown")
        secondary_bit = ""
        if secondary is not None:
            secondary_bit = f" Secondary: {getattr(secondary, 'name', '')} ({getattr(secondary, 'role', '')})."
        return (
            f"For recommended service '{item.recommended_service}', primary buyer is "
            f"{primary_name} ({primary_role}) based on public role evidence and revenue buyer matching."
            f"{secondary_bit}"
        )

    def _evidence(self, item, primary, channels, departments) -> list[EvidenceChainItem]:
        items: list[EvidenceChainItem] = [
            EvidenceChainItem(
                category="opportunity",
                summary=f"Opportunity score {item.opportunity_score:.1f} with pain '{item.business_pain}'",
                source=DiscoverySourceType.BEACON_REVENUE,
                confidence=min(100.0, item.opportunity_score),
            )
        ]
        if primary is not None:
            items.append(
                EvidenceChainItem(
                    category="decision_maker",
                    summary=getattr(primary, "evidence", "Primary decision maker selected"),
                    source=getattr(primary, "source", DiscoverySourceType.BEACON_ENRICHMENT),
                    source_url=getattr(primary, "source_url", None),
                    confidence=float(getattr(primary, "confidence", 0.0)),
                )
            )
        for channel in channels[:5]:
            items.append(
                EvidenceChainItem(
                    category="contact_channel",
                    summary=channel.evidence or channel.value,
                    source=channel.source,
                    source_url=channel.source_url,
                    confidence=channel.confidence,
                )
            )
        for department in departments[:4]:
            items.append(
                EvidenceChainItem(
                    category="department",
                    summary=department.evidence,
                    source=department.source,
                    source_url=department.source_url,
                    confidence=department.signal_strength,
                )
            )
        return items

    def _attributions(self, makers, channels, profiles, licensed_notes) -> list[SourceAttribution]:
        grouped: dict[str, SourceAttribution] = {}
        for maker in makers:
            key = maker.source.value
            current = grouped.get(key)
            fields = list(current.fields) if current else []
            fields.extend(["decision_maker", "role"])
            grouped[key] = SourceAttribution(
                source=maker.source,
                source_url=maker.source_url,
                fields=sorted(set(fields)),
                confidence=maker.confidence,
                notes="",
            )
        for channel in channels:
            key = channel.source.value
            current = grouped.get(key)
            fields = list(current.fields) if current else []
            fields.append("contact_channel")
            grouped[key] = SourceAttribution(
                source=channel.source,
                source_url=channel.source_url,
                fields=sorted(set(fields)),
                confidence=channel.confidence,
            )
        for profile in profiles:
            key = profile.source.value
            current = grouped.get(key)
            fields = list(current.fields) if current else []
            fields.append("public_profile")
            grouped[key] = SourceAttribution(
                source=profile.source,
                source_url=profile.source_url,
                fields=sorted(set(fields)),
                confidence=profile.confidence,
            )
        if licensed_notes:
            grouped["licensed_provider"] = SourceAttribution(
                source=DiscoverySourceType.LICENSED_PROVIDER,
                fields=[],
                confidence=0.0,
                licensed=True,
                notes="; ".join(licensed_notes),
            )
        return list(grouped.values())
