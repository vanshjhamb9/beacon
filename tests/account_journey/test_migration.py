from pathlib import Path

from app.models.account_journey import (
    AccountHealthSnapshot,
    AccountJourneyRow,
    AccountTimelineRow,
    BuyingCommitteeRow,
    CampaignAnalyticsSnapshot,
    EngagementScoreRow,
    FollowUpPlanRow,
    ReplyClassificationRow,
)


def test_goi_tablenames() -> None:
    assert AccountJourneyRow.__tablename__ == "account_journeys"
    assert EngagementScoreRow.__tablename__ == "engagement_scores"
    assert AccountHealthSnapshot.__tablename__ == "account_health_snapshots"
    assert BuyingCommitteeRow.__tablename__ == "buying_committees"
    assert FollowUpPlanRow.__tablename__ == "followup_plans"
    assert ReplyClassificationRow.__tablename__ == "reply_classifications"
    assert AccountTimelineRow.__tablename__ == "account_timelines"
    assert CampaignAnalyticsSnapshot.__tablename__ == "campaign_analytics_snapshots"


def test_migration_0025_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0025_create_account_journey_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "account_journeys",
        "engagement_scores",
        "account_health_snapshots",
        "buying_committees",
        "followup_plans",
        "reply_classifications",
        "account_timelines",
        "campaign_analytics_snapshots",
    ]:
        assert table in text
    assert "20260724_0024" in text
    assert 'revision: str = "20260724_0025"' in text


def test_timeline_immutable_and_followup_approval_flag() -> None:
    assert "immutable" in AccountTimelineRow.__table__.columns.keys()
    assert "requires_founder_approval" in FollowUpPlanRow.__table__.columns.keys()
