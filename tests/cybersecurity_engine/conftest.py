"""Shared fixtures for cybersecurity engine tests."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.models import (
    Company, CompanySize, Contact, CybersecurityOpportunity,
    OpportunityPriority, OpportunityType, ServiceLane,
)
from cybersecurity_engine.sources import RawSignal


@pytest.fixture
def sample_company() -> Company:
    return Company(
        name="TestCo", url="testco.io", country="United States",
        industry="SaaS", company_size=CompanySize.MEDIUM, employee_count=85,
        description="B2B SaaS platform",
    )


@pytest.fixture
def sample_contact() -> Contact:
    return Contact(
        name="Alex Chen", role="CTO", email="alex@testco.io",
        email_status="verified", email_evidence="Found on company website",
        linkedin_url="https://linkedin.com/in/alexchen", linkedin_status="verified",
        phone="+1-555-0123", phone_status="verified", identity_confidence=95.0,
    )


@pytest.fixture
def sample_opportunity(sample_company, sample_contact) -> CybersecurityOpportunity:
    opp = CybersecurityOpportunity(
        opportunity_id="test-opp-001", company=sample_company,
        opportunity_type=OpportunityType.CYBERSECURITY,
        priority=OpportunityPriority.P0, contact=sample_contact,
        source_name="reddit", source_type="event",
        source_url="https://reddit.com/r/netsec/test", source_status="accessible",
    )
    opp.buying_event.event_type = "active_buying"
    opp.buying_event.description = "Looking for penetration testing company"
    opp.buying_event.service_match = "HIGH"
    opp.buying_event.services_needed = ["penetration_testing", "web_app_security"]
    opp.buying_event.why_now = "Pre-launch requirement"
    opp.buying_event.urgency = "urgent"

    opp.add_evidence(
        claim="buying_signal_detected", value="Looking for penetration testing",
        source_name="reddit", source_type="event",
        source_url="https://reddit.com/r/netsec/test", source_status="accessible",
        method="web_scrape", confidence=85.0, verified=True,
        published_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    opp.add_evidence(
        claim="company_verified", value="TestCo is a B2B SaaS company",
        source_name="company_website", source_type="company_announcement",
        source_url="https://testco.io/about", source_status="accessible",
        method="web_scrape", confidence=90.0, verified=True,
        published_at=datetime(2026, 8, 5, tzinfo=UTC),
    )
    opp.add_evidence(
        claim="decision_maker_identified", value="Alex Chen, CTO",
        source_name="company_website", source_type="founder_post",
        source_url="https://testco.io/team", source_status="accessible",
        method="web_scrape", confidence=92.0, verified=True,
        published_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    return opp


@pytest.fixture
def sample_raw_signal() -> RawSignal:
    return RawSignal(
        source="reddit", source_tier=2,
        url="https://reddit.com/r/netsec/test123",
        title="Looking for penetration testing company",
        content="We need a penetration testing company for our SaaS platform before enterprise launch.",
        author="cto_user", published_at=datetime(2026, 8, 10, tzinfo=UTC), score=15,
    )
