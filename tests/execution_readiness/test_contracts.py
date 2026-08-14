"""Sprint 36 execution readiness contracts."""

from __future__ import annotations

from pathlib import Path

from execution_readiness.enums import ExecutionMode, ProviderKind
from execution_readiness.models import ProviderSnapshot
from execution_readiness.service import ExecutionReadinessEngine
from execution_readiness.validators import derive_mode, sanitize_next_step, truthful_kpi_contacted
from revenue_validation.briefs.engine import DailyBriefEngine


def test_migration_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260726_0047_execution_readiness.py"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "communication_provider_status" in text
    assert "execution_status" in text
    assert 'revision = "20260726_0047"' in text


def test_planning_mode_no_provider():
    mode, _ = derive_mode(providers=[], verified_deliveries=0)
    assert mode == ExecutionMode.PLANNING


def test_ready_mode_gmail():
    providers = [
        ProviderSnapshot(
            provider=ProviderKind.GMAIL,
            connected=True,
            oauth_valid=True,
            webhook_verified=True,
            can_send=True,
        )
    ]
    mode, _ = derive_mode(providers=providers, verified_deliveries=0)
    assert mode == ExecutionMode.READY


def test_executing_after_delivery():
    providers = [
        ProviderSnapshot(
            provider=ProviderKind.GMAIL,
            connected=True,
            oauth_valid=True,
            webhook_verified=True,
            can_send=True,
        )
    ]
    mode, _ = derive_mode(providers=providers, verified_deliveries=2)
    assert mode == ExecutionMode.EXECUTING


def test_brief_suppresses_monitor_opens_in_planning():
    brief = DailyBriefEngine().build(
        records=[
            {
                "company_id": "1",
                "company": "Heroic Labs",
                "status": "EMAIL_SENT",
                "brief": {
                    "decision_maker": "Chris (CEO)",
                    "business_email": "sales@heroiclabs.com",
                    "why_now": "YC",
                    "revenue_ready_score": 99,
                },
            }
        ],
        outcomes=[{"company_id": "1", "outcome": "EMAIL_SENT", "timestamp": "2026-07-25T00:00:00+00:00"}],
        execution_mode="PLANNING",
        execution_reason="No verified communication provider connected.",
    )
    next_step = str(brief["contact_first"]["next_step"]).lower()
    assert "monitor" not in next_step
    assert "follow-up" not in next_step
    assert brief["contact_first"]["status"] == "READY TO SEND"
    assert brief["follow_ups_due"] == []
    assert brief["meetings_today"] == []


def test_contacted_kpi_planning_zero():
    assert truthful_kpi_contacted(mode=ExecutionMode.PLANNING, verified_delivered_companies=99) == 0


def test_sanitize_ready():
    assert "send" in sanitize_next_step("Monitor opens", ExecutionMode.READY).lower()


def test_engine_transitions():
    engine = ExecutionReadinessEngine()
    planning = engine.evaluate(providers=[], verified_deliveries=0)
    assert planning.execution_mode == ExecutionMode.PLANNING
    ready = engine.evaluate(
        providers=[
            ProviderSnapshot(
                provider=ProviderKind.META_WHATSAPP,
                connected=True,
                oauth_valid=True,
                can_send=True,
            )
        ],
        verified_deliveries=0,
    )
    assert ready.execution_mode == ExecutionMode.READY
    executing = engine.evaluate(
        providers=[
            ProviderSnapshot(
                provider=ProviderKind.GMAIL,
                connected=True,
                oauth_valid=True,
                webhook_verified=True,
                can_send=True,
            )
        ],
        verified_deliveries=1,
        messages_sent=1,
    )
    assert executing.execution_mode == ExecutionMode.EXECUTING
    assert executing.tracking_ready is True
