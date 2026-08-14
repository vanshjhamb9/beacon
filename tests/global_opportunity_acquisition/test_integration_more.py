import pytest

from global_opportunity_acquisition import GlobalOpportunityAcquisitionPipeline
from global_opportunity_acquisition.models.types import CompanyObservation, GOAPInput, RawSignal
from global_opportunity_acquisition.source_scoring.engine import SourceScoringEngine
from global_opportunity_acquisition.analytics.engine import AnalyticsEngine
from global_opportunity_acquisition.benchmarking.engine import BenchmarkingEngine
from global_opportunity_acquisition.collector_manager.engine import CollectorManagerEngine


@pytest.mark.parametrize(
    "texts,intent_substr",
    [
        (["we're hiring backend engineers"], "hiring"),
        (["company raised series c"], "funding"),
        (["opening office in london"], "expansion"),
        (["adopting ai and llm tools"], "ai_adoption"),
        (["digital transformation initiative"], "digital_transformation"),
        (["rebuild site and redesign website"], "website_rebuild"),
        (["salesforce migration project"], "crm_migration"),
        (["erp migration to netsuite"], "erp_migration"),
        (["cloud migration to aws"], "cloud_migration"),
        (["workflow automation initiative"], "automation"),
        (["scale support with zendesk"], "customer_support_scaling"),
        (["scale marketing demand gen"], "marketing_scaling"),
        (["just launched startup launch"], "startup_launch"),
        (["company acquires rival"], "acquisition"),
        (["files s-1 for ipo"], "ipo"),
        (["announcing new product launch"], "product_launch"),
        (["platform migration rewrite"], "technology_migration"),
        (["infrastructure kubernetes upgrade"], "infrastructure_upgrades"),
        (["international expansion enter market"], "international_expansion"),
        (["soc2 compliance program"], "compliance_changes"),
        (["security investment zero trust"], "security_investment"),
        (["platform modernization legacy"], "platform_modernization"),
    ],
)
def test_intent_integration_cases(texts: list[str], intent_substr: str) -> None:
    d = GlobalOpportunityAcquisitionPipeline().process(
        GOAPInput(companies=[CompanyObservation(company_name="X", source_texts=texts)])
    )
    intents = {i.intent.value for i in d.companies[0].intents}
    assert intent_substr in intents


def test_source_scoring_engine() -> None:
    scores = SourceScoringEngine().score_all({"reddit": {"signals": 5, "opportunities": 3, "companies": 2}})
    assert scores
    reddit = next(s for s in scores if s.connector_id == "reddit")
    assert reddit.quality_score > 0


def test_collector_manager_disabled_emit_none() -> None:
    signals, metrics = CollectorManagerEngine().refresh(context={})
    assert isinstance(signals, list)
    assert len(metrics) == len(CollectorManagerEngine().registry.all())
    crunch = next(m for m in metrics if m.connector_id == "crunchbase")
    assert crunch.health in {"disabled", "pending"}


def test_analytics_daily_report() -> None:
    d = GlobalOpportunityAcquisitionPipeline().process(
        GOAPInput(
            companies=[CompanyObservation(company_name="A", source_texts=["hiring"])],
            connector_outcomes={"reddit": {"opportunities": 2, "meetings": 1}},
        )
    )
    assert d.analytics.total_connectors > 20
    assert d.daily_report is not None
    assert "GOAP daily" in d.daily_report.summary


def test_cross_source_signal_merge_in_pipeline() -> None:
    d = GlobalOpportunityAcquisitionPipeline().process(
        GOAPInput(
            raw_signals=[
                RawSignal(signal_id="1", connector_id="reddit", company_name="Same", company_domain="same.io", title="a", body="hiring"),
                RawSignal(signal_id="2", connector_id="hn", company_name="Same", company_domain="same.io", title="b", body="funding"),
            ]
        )
    )
    assert any(len(n.source_connector_ids) >= 2 for n in d.normalized)


def test_benchmark_engine_ranks_all_connectors() -> None:
    benches = BenchmarkingEngine().rank({})
    assert len(benches) == len(set(b.connector_id for b in benches))
    assert benches[0].rank == 1
