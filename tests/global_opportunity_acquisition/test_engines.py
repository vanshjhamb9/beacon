from global_opportunity_acquisition.community_intelligence.engine import CommunityIntelligenceEngine
from global_opportunity_acquisition.company_resolution.engine import CompanyResolutionEngine
from global_opportunity_acquisition.deduplication.engine import DeduplicationEngine
from global_opportunity_acquisition.freshness.engine import FreshnessEngine
from global_opportunity_acquisition.funding_intelligence.engine import FundingIntelligenceEngine
from global_opportunity_acquisition.job_intelligence.engine import JobIntelligenceEngine
from global_opportunity_acquisition.models.types import CompanyObservation
from global_opportunity_acquisition.normalizers.engine import NormalizerEngine
from global_opportunity_acquisition.models.types import RawSignal
from global_opportunity_acquisition.procurement_intelligence.engine import ProcurementIntelligenceEngine
from global_opportunity_acquisition.review_intelligence.engine import ReviewIntelligenceEngine
from global_opportunity_acquisition.website_analysis.engine import WebsiteAnalysisEngine
from global_opportunity_acquisition.benchmarking.engine import BenchmarkingEngine
from global_opportunity_acquisition.models.types import BenchmarkAction
from global_opportunity_acquisition.opportunity_graph.engine import OpportunityGraphEngine
from global_opportunity_acquisition.intent_detection.engine import IntentDetectionEngine
from global_opportunity_acquisition.technology_detection.engine import TechnologyDetectionEngine


def test_normalize_and_dedupe() -> None:
    signals = [
        RawSignal(signal_id="a", connector_id="reddit", company_name="Orbit", company_domain="orbit.io", title="t1", body="b1"),
        RawSignal(signal_id="b", connector_id="github", company_name="Orbit", company_domain="orbit.io", title="t2", body="b2"),
        RawSignal(signal_id="c", connector_id="rss", company_name="Other Co", title="x", body="y"),
    ]
    rows = NormalizerEngine().normalize(signals)
    merged, dupes = DeduplicationEngine().merge(rows)
    assert dupes == 1
    assert len(merged) == 2
    orbit = next(m for m in merged if m.company_name == "Orbit")
    assert set(orbit.source_connector_ids) == {"reddit", "github"}


def test_company_resolution_stable() -> None:
    r = CompanyResolutionEngine()
    assert r.resolve("Acme", "acme.com") == r.resolve("Acme", "acme.com")


def test_website_intelligence() -> None:
    w = WebsiteAnalysisEngine().analyze(
        company_name="Site Co",
        domain="site.co",
        hints=["react", "next.js", "https", "viewport", "google-analytics", "stripe", "application/ld+json", "calendly"],
    )
    assert w.framework in {"React", "Next.js"}
    assert w.ssl is True
    assert w.mobile_responsive is True
    assert w.has_analytics is True
    assert w.has_booking is True
    assert w.payment_provider == "Stripe"
    assert 0 <= w.modernization_score <= 100
    assert 0 <= w.opportunity_score <= 100


def test_hiring_intelligence() -> None:
    h = JobIntelligenceEngine().analyze(
        ["Senior Backend Engineer", "ML Engineer", "SDR", "Customer Support Specialist", "Growth Marketer", "Product Manager"]
    )
    assert h.engineering_expansion > 0
    assert h.ai_investment > 0
    assert h.sales_expansion > 0
    assert h.support_expansion > 0
    assert h.marketing_expansion > 0
    assert h.product_investment > 0
    assert h.growth > 0


def test_funding_intelligence() -> None:
    events = FundingIntelligenceEngine().detect(["Company raised series b and opened new office for global expansion"])
    rounds = {e.round for e in events}
    assert "series_b" in rounds
    assert "new_office" in rounds or "global_expansion" in rounds


def test_review_intelligence() -> None:
    r = ReviewIntelligenceEngine().analyze(["slow support", "missing reporting", "hard to use", "salesforce", "looking for alternative"])
    assert r.complaints
    assert r.missing_features
    assert r.pain_points
    assert "salesforce" in r.competitor_mentions
    assert r.migration_opportunities


def test_community_intelligence() -> None:
    c = CommunityIntelligenceEngine().detect(["We need a developer and need automation and need a chatbot"])
    assert "need developer" in c.needs
    assert "need automation" in c.needs
    assert "need chatbot" in c.needs
    assert c.confidence > 0


def test_procurement_intelligence() -> None:
    p = ProcurementIntelligenceEngine().detect(["Government tender and RFP for cloud services"])
    assert {x.tender_type for x in p} >= {"rfp", "tender"}


def test_freshness_bounds() -> None:
    f = FreshnessEngine().score(
        CompanyObservation(company_name="F", verified=True, last_seen_hours=2, engagement_score=90, activity_score=90),
        source_count=3,
    )
    assert 0 <= f.score <= 100
    assert set(f.factors) >= {"time", "source", "verification", "activity", "last_seen", "engagement"}


def test_benchmark_recommendations() -> None:
    benches = BenchmarkingEngine().rank(
        {
            "reddit": {
                "qualified_opportunities": 10,
                "meetings_booked": 4,
                "reply_rate": 20,
                "proposal_rate": 10,
                "close_rate": 5,
                "revenue_generated": 5000,
                "average_quality": 80,
                "false_positives": 0,
                "coverage": 70,
            },
            "crunchbase": {"qualified_opportunities": 0, "false_positives": 0},
        }
    )
    assert benches[0].rank == 1
    crunch = next(b for b in benches if b.connector_id == "crunchbase")
    assert crunch.recommendation == BenchmarkAction.DISABLE_CONNECTOR


def test_opportunity_graph_structure() -> None:
    company = CompanyObservation(
        company_name="Graph Co",
        company_domain="graph.co",
        industry="Fintech",
        decision_makers=["CTO"],
        campaigns=["Q3"],
        meetings=["Disco"],
        revenue_notes=["pipeline"],
        history=["outreach"],
        outcomes=["replied"],
    )
    intents = IntentDetectionEngine().detect(["hiring engineers", "raised series a"])
    techs = TechnologyDetectionEngine().detect(["react", "aws"])
    graph = OpportunityGraphEngine().build(
        company,
        intents=intents,
        technologies=techs,
        website=WebsiteAnalysisEngine().analyze(company_name="Graph Co", domain="graph.co", hints=["react"]),
        hiring=JobIntelligenceEngine().analyze(["Engineer"]),
        funding=FundingIntelligenceEngine().detect(["series a"]),
        reviews=ReviewIntelligenceEngine().analyze(["hard to use", "zendesk"]),
        community=CommunityIntelligenceEngine().detect(["need CRM"]),
    )
    types = {n.node_type.value for n in graph.nodes}
    assert "company" in types
    assert "industry" in types
    assert "technology" in types
    assert "buying_signal" in types
    assert graph.edges
    assert all("append_only:true" in n.evidence for n in graph.nodes)
