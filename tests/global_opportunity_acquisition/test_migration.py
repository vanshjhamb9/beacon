from pathlib import Path

from app.models.global_opportunity_acquisition import (
    CommunitySignalRow,
    ConnectorBenchmarkRow,
    ConnectorHistoryRow,
    ConnectorScoreRow,
    FundingEventRow,
    HiringEventRow,
    OpportunityGraphEdgeRow,
    OpportunityGraphNodeRow,
    ProcurementSignalRow,
    ReviewSignalRow,
    SourceAlertRow,
    SourceConnectorRow,
    SourceRunRow,
    TechnologyProfileRow,
    WebsiteProfileRow,
)


def test_goap_tablenames() -> None:
    assert SourceConnectorRow.__tablename__ == "source_connectors"
    assert SourceRunRow.__tablename__ == "source_runs"
    assert OpportunityGraphNodeRow.__tablename__ == "opportunity_graph_nodes"
    assert OpportunityGraphEdgeRow.__tablename__ == "opportunity_graph_edges"
    assert ConnectorScoreRow.__tablename__ == "connector_scores"
    assert ConnectorBenchmarkRow.__tablename__ == "connector_benchmarks"
    assert WebsiteProfileRow.__tablename__ == "website_profiles"
    assert TechnologyProfileRow.__tablename__ == "technology_profiles"
    assert FundingEventRow.__tablename__ == "funding_events"
    assert HiringEventRow.__tablename__ == "hiring_events"
    assert ReviewSignalRow.__tablename__ == "review_signals"
    assert CommunitySignalRow.__tablename__ == "community_signals"
    assert ProcurementSignalRow.__tablename__ == "procurement_signals"
    assert SourceAlertRow.__tablename__ == "source_alerts"
    assert ConnectorHistoryRow.__tablename__ == "connector_history"


def test_migration_0027_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0027_create_global_opportunity_acquisition_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "source_connectors",
        "source_runs",
        "opportunity_graph_nodes",
        "opportunity_graph_edges",
        "connector_scores",
        "connector_benchmarks",
        "website_profiles",
        "technology_profiles",
        "funding_events",
        "hiring_events",
        "review_signals",
        "community_signals",
        "procurement_signals",
        "source_alerts",
        "connector_history",
    ]:
        assert table in text
    assert "20260724_0026" in text
    assert 'revision: str = "20260724_0027"' in text


def test_graph_immutable_flags() -> None:
    assert "immutable" in OpportunityGraphNodeRow.__table__.columns.keys()
    assert "immutable" in OpportunityGraphEdgeRow.__table__.columns.keys()
    assert "immutable" in ConnectorHistoryRow.__table__.columns.keys()
