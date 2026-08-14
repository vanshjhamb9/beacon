import time

from global_opportunity_acquisition import GlobalOpportunityAcquisitionPipeline
from global_opportunity_acquisition.company_resolution.engine import CompanyResolutionEngine
from global_opportunity_acquisition.deduplication.engine import DeduplicationEngine
from global_opportunity_acquisition.models.types import CompanyObservation, GOAPInput, RawSignal
from global_opportunity_acquisition.normalizers.engine import NormalizerEngine
from global_opportunity_acquisition.opportunity_graph.engine import OpportunityGraphEngine
from global_opportunity_acquisition.intent_detection.engine import IntentDetectionEngine
from global_opportunity_acquisition.technology_detection.engine import TechnologyDetectionEngine
from global_opportunity_acquisition.job_intelligence.engine import JobIntelligenceEngine
from global_opportunity_acquisition.funding_intelligence.engine import FundingIntelligenceEngine
from global_opportunity_acquisition.review_intelligence.engine import ReviewIntelligenceEngine
from global_opportunity_acquisition.community_intelligence.engine import CommunityIntelligenceEngine
from global_opportunity_acquisition.website_analysis.engine import WebsiteAnalysisEngine


def test_500_companies_under_5_seconds() -> None:
    pipeline = GlobalOpportunityAcquisitionPipeline()
    companies = [
        CompanyObservation(
            company_name=f"Co {i}",
            company_domain=f"co{i}.io",
            source_texts=["hiring engineers", "raised series a" if i % 2 == 0 else "need automation"],
            html_hints=["react", "aws"] if i % 3 == 0 else ["wordpress"],
            job_titles=["Engineer"] if i % 2 == 0 else [],
            verified=i % 5 == 0,
            last_seen_hours=float(i % 48),
        )
        for i in range(500)
    ]
    started = time.perf_counter()
    pipeline.process(GOAPInput(companies=companies))
    assert (time.perf_counter() - started) < 5.0


def test_500_graph_builds_under_5_seconds() -> None:
    graph = OpportunityGraphEngine()
    intent = IntentDetectionEngine()
    tech = TechnologyDetectionEngine()
    jobs = JobIntelligenceEngine()
    funding = FundingIntelligenceEngine()
    reviews = ReviewIntelligenceEngine()
    community = CommunityIntelligenceEngine()
    website = WebsiteAnalysisEngine()
    started = time.perf_counter()
    for i in range(500):
        company = CompanyObservation(company_name=f"G{i}", company_domain=f"g{i}.io", industry="SaaS")
        texts = ["hiring", "series a", "react"]
        graph.build(
            company,
            intents=intent.detect(texts),
            technologies=tech.detect(texts),
            website=website.analyze(company_name=company.company_name, domain=company.company_domain, hints=texts),
            hiring=jobs.analyze(["Engineer"]),
            funding=funding.detect(texts),
            reviews=reviews.analyze(["slow support"]),
            community=community.detect(["need AI"]),
        )
    assert (time.perf_counter() - started) < 5.0


def test_1000_deduplications_under_3_seconds() -> None:
    signals = []
    for i in range(1000):
        name = f"DupCo {i % 200}"
        domain = f"dup{i % 200}.io"
        signals.append(
            RawSignal(
                signal_id=str(i),
                connector_id=["reddit", "rss", "github", "techcrunch", "devto"][i % 5],
                company_name=name,
                company_domain=domain,
                title=f"t{i}",
                body=f"b{i}",
            )
        )
    started = time.perf_counter()
    rows = NormalizerEngine().normalize(signals)
    merged, dupes = DeduplicationEngine().merge(rows)
    elapsed = time.perf_counter() - started
    assert elapsed < 3.0
    assert len(merged) == 200
    assert dupes == 800
    # resolution sanity
    assert CompanyResolutionEngine().resolve("DupCo 1", "dup1.io")
