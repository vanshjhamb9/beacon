"""Execution readiness gate — unit tests."""

from __future__ import annotations

from execution_readiness.enums import ExecutionMode, ProviderKind
from execution_readiness.models import ProviderSnapshot
from execution_readiness.service import ExecutionReadinessEngine
from execution_readiness.validators import derive_mode, sanitize_next_step, truthful_kpi_contacted


def test_no_provider_planning():
    mode, reason = derive_mode(providers=[], verified_deliveries=0)
    assert mode == ExecutionMode.PLANNING
    assert "No verified" in reason


def test_gmail_ready():
    providers = [
        ProviderSnapshot(
            provider=ProviderKind.GMAIL,
            connected=True,
            oauth_valid=True,
            webhook_verified=True,
            can_send=True,
            can_receive=True,
        )
    ]
    mode, _ = derive_mode(providers=providers, verified_deliveries=0)
    assert mode == ExecutionMode.READY


def test_delivery_executing():
    providers = [
        ProviderSnapshot(
            provider=ProviderKind.GMAIL,
            connected=True,
            oauth_valid=True,
            webhook_verified=True,
            can_send=True,
        )
    ]
    mode, _ = derive_mode(providers=providers, verified_deliveries=1)
    assert mode == ExecutionMode.EXECUTING


def test_sanitize_planning_forbids_monitor_opens():
    step = sanitize_next_step("Monitor opens; prepare follow-up", ExecutionMode.PLANNING)
    assert "monitor" not in step.lower()
    assert "follow-up" not in step.lower()
    assert "Connect Gmail" in step


def test_contacted_kpi_zero_in_planning():
    assert truthful_kpi_contacted(mode=ExecutionMode.PLANNING, verified_delivered_companies=10) == 0


def test_contacted_kpi_executing():
    assert truthful_kpi_contacted(mode=ExecutionMode.EXECUTING, verified_delivered_companies=3) == 3


def test_engine_report_section_planning():
    engine = ExecutionReadinessEngine()
    snap = engine.evaluate(providers=[], verified_deliveries=0, messages_sent=5)
    section = engine.report_section(snap)
    assert section["mode"] == "PLANNING"
    assert section["messages_sent"] == 0
    assert section["deliveries"] == 0
    assert section["open_tracking"] == "Disabled"
    assert section["learning_mode"] == "Offline"


def test_planning_card():
    engine = ExecutionReadinessEngine()
    snap = engine.evaluate(providers=[], verified_deliveries=0)
    card = engine.planning_card(snap, company="Heroic Labs", email="sales@heroiclabs.com", why_now="YC")
    assert card.status == "READY TO SEND"
    assert "Connect Gmail" in card.next_action
    assert "Disabled" in card.tracking
