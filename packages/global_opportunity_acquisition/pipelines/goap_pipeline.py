from __future__ import annotations

from datetime import UTC, datetime

from global_opportunity_acquisition.analytics.engine import AnalyticsEngine
from global_opportunity_acquisition.benchmarking.engine import BenchmarkingEngine
from global_opportunity_acquisition.collector_manager.engine import CollectorManagerEngine
from global_opportunity_acquisition.community_intelligence.engine import CommunityIntelligenceEngine
from global_opportunity_acquisition.company_resolution.engine import CompanyResolutionEngine
from global_opportunity_acquisition.deduplication.engine import DeduplicationEngine
from global_opportunity_acquisition.freshness.engine import FreshnessEngine
from global_opportunity_acquisition.funding_intelligence.engine import FundingIntelligenceEngine
from global_opportunity_acquisition.intent_detection.engine import IntentDetectionEngine
from global_opportunity_acquisition.job_intelligence.engine import JobIntelligenceEngine
from global_opportunity_acquisition.models.types import (
    SCORING_VERSION,
    CompanyIntelligencePack,
    CompanyObservation,
    GOAPDecision,
    GOAPInput,
)
from global_opportunity_acquisition.normalizers.engine import NormalizerEngine
from global_opportunity_acquisition.opportunity_graph.engine import OpportunityGraphEngine
from global_opportunity_acquisition.procurement_intelligence.engine import ProcurementIntelligenceEngine
from global_opportunity_acquisition.review_intelligence.engine import ReviewIntelligenceEngine
from global_opportunity_acquisition.technology_detection.engine import TechnologyDetectionEngine
from global_opportunity_acquisition.website_analysis.engine import WebsiteAnalysisEngine


class GlobalOpportunityAcquisitionPipeline:
    """Compose-only GOAP — Opportunity Intelligence Platform (goap-v1)."""

    def __init__(self) -> None:
        self.collector = CollectorManagerEngine()
        self.normalizer = NormalizerEngine()
        self.dedupe = DeduplicationEngine()
        self.resolver = CompanyResolutionEngine()
        self.intent = IntentDetectionEngine()
        self.tech = TechnologyDetectionEngine()
        self.website = WebsiteAnalysisEngine()
        self.jobs = JobIntelligenceEngine()
        self.funding = FundingIntelligenceEngine()
        self.procurement = ProcurementIntelligenceEngine()
        self.community = CommunityIntelligenceEngine()
        self.reviews = ReviewIntelligenceEngine()
        self.graph = OpportunityGraphEngine()
        self.freshness = FreshnessEngine()
        self.benchmarking = BenchmarkingEngine()
        self.analytics = AnalyticsEngine()

    def process(self, data: GOAPInput) -> GOAPDecision:
        now = data.now or datetime.now(UTC)
        context = {"signals": {}}
        for signal in data.raw_signals:
            context["signals"].setdefault(signal.connector_id, []).append(signal)

        collected, connector_metrics = self.collector.refresh(context=context, outcomes=data.connector_outcomes)
        by_id = {s.signal_id: s for s in collected}
        for signal in data.raw_signals:
            by_id[signal.signal_id] = signal
        all_signals = list(by_id.values())
        normalized_rows = self.normalizer.normalize(all_signals)
        merged, _dupes = self.dedupe.merge(normalized_rows)

        # Prefer explicit company observations; enrich from merged signals
        observations = list(data.companies)
        known = {self.resolver.resolve(c.company_name, c.company_domain) for c in observations}
        for m in merged:
            if m.canonical_key not in known:
                observations.append(
                    CompanyObservation(
                        company_name=m.company_name,
                        company_domain=m.company_domain,
                        source_texts=list(m.titles) + list(m.bodies),
                        source_connector_ids=list(m.source_connector_ids),
                        now=now,
                    )
                )
                known.add(m.canonical_key)

        packs: list[CompanyIntelligencePack] = []
        for company in observations:
            texts = list(company.source_texts) + list(company.funding_text) + list(company.community_text)
            intents = self.intent.detect(texts + company.job_titles + company.review_text)
            technologies = self.tech.detect(texts + company.html_hints)
            website = self.website.analyze(
                company_name=company.company_name,
                domain=company.company_domain,
                hints=company.html_hints or texts,
            )
            hiring = self.jobs.analyze(company.job_titles) if company.job_titles else self.jobs.analyze([])
            funding = self.funding.detect(company.funding_text or texts)
            reviews = self.reviews.analyze(company.review_text)
            community = self.community.detect(company.community_text or texts)
            procurement = self.procurement.detect(company.procurement_text)
            graph = self.graph.build(
                company,
                intents=intents,
                technologies=technologies,
                website=website,
                hiring=hiring,
                funding=funding,
                reviews=reviews,
                community=community,
            )
            fresh = self.freshness.score(company, source_count=max(1, len(company.source_connector_ids)))
            packs.append(
                CompanyIntelligencePack(
                    company_name=company.company_name,
                    company_domain=company.company_domain,
                    canonical_key=graph.company_key,
                    intents=intents,
                    technologies=technologies,
                    website=website,
                    hiring=hiring,
                    funding=funding,
                    reviews=reviews,
                    community=community,
                    procurement=procurement,
                    graph=graph,
                    freshness=fresh,
                    evidence=[f"intents:{len(intents)}", f"freshness:{fresh.score}"],
                )
            )

        benchmarks = self.benchmarking.rank(data.connector_outcomes)
        analytics = self.analytics.build(connectors=connector_metrics, companies=packs, benchmarks=benchmarks)
        report = self.analytics.daily_report(analytics, benchmarks, now=now)
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            "compose_only:true",
            "no_gpt:true",
            "public_information_only:true",
            f"companies:{len(packs)}",
            f"connectors:{len(connector_metrics)}",
            f"normalized:{len(merged)}",
        ]
        return GOAPDecision(
            scoring_version=SCORING_VERSION,
            connectors=connector_metrics,
            normalized=merged,
            companies=packs,
            benchmarks=benchmarks,
            analytics=analytics,
            daily_report=report,
            evidence_chain=evidence,
            evaluated_at=now,
        )
