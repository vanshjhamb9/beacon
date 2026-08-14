from datetime import UTC, datetime

from global_opportunity_acquisition import (
    SCORING_VERSION,
    GOAPInput,
    GlobalOpportunityAcquisitionPipeline,
    GlobalOpportunityAcquisitionService,
)
from global_opportunity_acquisition.models.types import CompanyObservation, RawSignal


def _input(**overrides: object) -> GOAPInput:
    payload: dict[str, object] = {
        "raw_signals": [
            RawSignal(
                signal_id="1",
                connector_id="reddit",
                company_name="Acme AI",
                company_domain="acme.ai",
                title="Hiring ML engineers",
                body="We raised series a and need automation",
            ),
            RawSignal(
                signal_id="2",
                connector_id="techcrunch",
                company_name="Acme AI",
                company_domain="acme.ai",
                title="Acme raises Series A",
                body="Series A funding for AI adoption",
            ),
        ],
        "companies": [
            CompanyObservation(
                company_name="Acme AI",
                company_domain="acme.ai",
                industry="SaaS",
                source_texts=["raised series a", "hiring engineers", "need automation"],
                source_connector_ids=["reddit", "techcrunch"],
                html_hints=["react", "next.js", "https", "viewport", "stripe", "hubspot"],
                job_titles=["Senior Backend Engineer", "ML Engineer", "Account Executive"],
                funding_text=["raised series a"],
                review_text=["slow support", "looking for alternative"],
                community_text=["need a chatbot", "need automation"],
                decision_makers=["CEO"],
                verified=True,
                last_seen_hours=6,
                engagement_score=80,
                activity_score=75,
                now=datetime.now(UTC),
            )
        ],
        "connector_outcomes": {
            "reddit": {"opportunities": 5, "meetings": 2, "quality": 70, "coverage": 60, "revenue": 1000},
            "techcrunch": {"opportunities": 3, "meetings": 1, "quality": 80, "coverage": 50},
        },
    }
    payload.update(overrides)
    return GOAPInput.model_validate(payload)


def test_scoring_version() -> None:
    assert SCORING_VERSION == "goap-v1"


def test_pipeline_deterministic() -> None:
    data = _input()
    a = GlobalOpportunityAcquisitionPipeline().process(data)
    b = GlobalOpportunityAcquisitionPipeline().process(data)
    assert a.scoring_version == b.scoring_version
    assert len(a.companies) == len(b.companies)
    assert a.companies[0].canonical_key == b.companies[0].canonical_key
    assert a.companies[0].freshness.score == b.companies[0].freshness.score
    assert [x.intent for x in a.companies[0].intents] == [x.intent for x in b.companies[0].intents]


def test_pipeline_evidence() -> None:
    d = GlobalOpportunityAcquisitionPipeline().process(_input())
    assert "compose_only:true" in d.evidence_chain
    assert "no_gpt:true" in d.evidence_chain
    assert "public_information_only:true" in d.evidence_chain
    assert d.daily_report is not None
    assert d.analytics.unique_companies >= 1


def test_service_evaluate() -> None:
    d = GlobalOpportunityAcquisitionService().evaluate(_input())
    assert d.companies
    assert d.connectors
    assert d.benchmarks
    assert d.normalized


def test_dedupe_merges_cross_source() -> None:
    d = GlobalOpportunityAcquisitionPipeline().process(_input())
    assert len(d.normalized) == 1
    assert set(d.normalized[0].source_connector_ids) >= {"reddit", "techcrunch"}
