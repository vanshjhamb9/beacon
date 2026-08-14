from pathlib import Path

from app.models.communication import (
    CampaignStopEvent,
    CommunicationMessage,
    CommunicationQueueItem,
    ConversationItemRow,
    ConversationThreadRow,
    DeliveryEvent,
    OAuthConnection,
    ProviderSecret,
    QAHealthSnapshot,
    SandboxScenario,
    WebhookEvent,
)


def test_communication_models_tablename_contract() -> None:
    assert OAuthConnection.__tablename__ == "oauth_connections"
    assert ProviderSecret.__tablename__ == "provider_secrets"
    assert CommunicationMessage.__tablename__ == "communication_messages"
    assert DeliveryEvent.__tablename__ == "delivery_events"
    assert WebhookEvent.__tablename__ == "webhook_events"
    assert CommunicationQueueItem.__tablename__ == "communication_queue_items"
    assert ConversationThreadRow.__tablename__ == "conversation_threads"
    assert ConversationItemRow.__tablename__ == "conversation_items"
    assert SandboxScenario.__tablename__ == "sandbox_scenarios"
    assert QAHealthSnapshot.__tablename__ == "qa_health_snapshots"
    assert CampaignStopEvent.__tablename__ == "campaign_stop_events"


def test_migration_0015_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = (
        root / "apps" / "api" / "alembic" / "versions" / "20260720_0015_create_communication_qa_tables.py"
    )
    text = migration.read_text(encoding="utf-8")
    for table in (
        "oauth_connections",
        "provider_secrets",
        "communication_messages",
        "delivery_events",
        "webhook_events",
        "communication_queue_items",
        "conversation_threads",
        "conversation_items",
        "sandbox_scenarios",
        "qa_health_snapshots",
        "campaign_stop_events",
    ):
        assert table in text
    assert "20260720_0014" in text


def test_migration_0019_foundation_indexes() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = (
        root / "apps" / "api" / "alembic" / "versions" / "20260723_0019_communication_gateway_foundation.py"
    )
    text = migration.read_text(encoding="utf-8")
    assert "20260723_0018" in text
    assert "ix_communication_messages_provider_message_id" in text
    assert "idempotency_key" in text
    assert CommunicationQueueItem.__table__.c.idempotency_key is not None
