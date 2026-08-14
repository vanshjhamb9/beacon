from pathlib import Path

from app.models.campaign import (
    Campaign,
    CampaignApproval,
    CampaignAudit,
    CampaignChannel,
    CampaignExecutionLog,
    CampaignSchedule,
    CampaignStep,
    CampaignTemplate,
)


def test_campaign_models_tablename_contract() -> None:
    assert Campaign.__tablename__ == "campaigns"
    assert CampaignStep.__tablename__ == "campaign_steps"
    assert CampaignSchedule.__tablename__ == "campaign_schedules"
    assert CampaignChannel.__tablename__ == "campaign_channels"
    assert CampaignApproval.__tablename__ == "campaign_approvals"
    assert CampaignExecutionLog.__tablename__ == "campaign_execution_logs"
    assert CampaignTemplate.__tablename__ == "campaign_templates"
    assert CampaignAudit.__tablename__ == "campaign_audit"


def test_migration_0014_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260720_0014_create_campaign_intelligence_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "campaigns",
        "campaign_steps",
        "campaign_schedules",
        "campaign_channels",
        "campaign_approvals",
        "campaign_execution_logs",
        "campaign_templates",
        "campaign_audit",
    ):
        assert table in text
    assert 'revision: str = "20260720_0014"' in text
    assert 'down_revision: str | None = "20260720_0013"' in text
