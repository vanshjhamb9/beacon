from pathlib import Path

from app.models.autonomous_sales_agent import (
    AutonomousSalesAgentRun,
    AutonomousSalesTimelineEvent,
    AutonomousSalesWorkQueueSnapshot,
    AutonomousSalesWorkflowTransition,
)


def test_asa_tablenames() -> None:
    assert AutonomousSalesAgentRun.__tablename__ == "autonomous_sales_agent_runs"
    assert AutonomousSalesWorkflowTransition.__tablename__ == "asa_workflow_transitions"
    assert AutonomousSalesTimelineEvent.__tablename__ == "asa_timeline_events"
    assert AutonomousSalesWorkQueueSnapshot.__tablename__ == "asa_work_queue_snapshots"


def test_migration_0023_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0023_create_autonomous_sales_agent_tables.py"
    text = migration.read_text(encoding="utf-8")
    assert "autonomous_sales_agent_runs" in text
    assert "asa_workflow_transitions" in text
    assert "asa_timeline_events" in text
    assert "asa_work_queue_snapshots" in text
    assert "20260723_0022" in text
    assert 'revision: str = "20260723_0023"' in text


def test_transition_model_has_required_audit_fields() -> None:
    cols = set(AutonomousSalesWorkflowTransition.__table__.columns.keys())
    for required in {"from_stage", "to_stage", "reason", "evidence", "actor", "next_action", "occurred_at", "immutable"}:
        assert required in cols


def test_timeline_immutable_flag() -> None:
    assert "immutable" in AutonomousSalesTimelineEvent.__table__.columns.keys()
