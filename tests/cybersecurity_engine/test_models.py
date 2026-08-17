"""Tests for cybersecurity_engine.models."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.models import (
    Company, CompanySize, Contact, ContactChannel, CybersecurityOpportunity,
    Evidence, EvidenceConfidence, BuyingEvent, OutreachClassification,
    OutreachPreparation, OpportunityPriority, OpportunityType, SalesReadiness,
    ServiceLane, SourceTier,
)


# ── Evidence ──────────────────────────────────────────────

class TestEvidence:
    def test_creation(self):
        e = Evidence(claim="test", value="val", source_name="src", source_type="post",
                     source_url="http://x.com", source_status="accessible")
        assert e.claim == "test"
        assert e.confidence == 0.0
        assert e.verified is False

    def test_to_dict(self):
        e = Evidence(claim="c", value="v", source_name="s", source_type="t",
                     source_url="http://u", source_status="ok",
                     published_at=datetime(2026, 1, 1, tzinfo=UTC))
        d = e.to_dict()
        assert d["claim"] == "c"
        assert d["published_at"] is not None

    def test_to_dict_no_published(self):
        e = Evidence(claim="c", value="v", source_name="s", source_type="t",
                     source_url="http://u", source_status="ok")
        d = e.to_dict()
        assert d["published_at"] is None


# ── Contact ───────────────────────────────────────────────

class TestContact:
    def test_creation_defaults(self):
        c = Contact()
        assert c.name == ""
        assert c.email_status == "unverified"

    def test_has_reliable_contact_verified_email(self):
        c = Contact(email="a@b.com", email_status="verified")
        assert c.has_reliable_contact is True

    def test_has_reliable_contact_verified_linkedin(self):
        c = Contact(linkedin_url="http://linkedin.com/in/x", linkedin_status="verified")
        assert c.has_reliable_contact is True

    def test_has_reliable_contact_verified_phone(self):
        c = Contact(phone="+1-555-0000", phone_status="verified")
        assert c.has_reliable_contact is True

    def test_has_reliable_contact_none(self):
        c = Contact()
        assert c.has_reliable_contact is False

    def test_to_dict(self):
        c = Contact(name="A", email="a@b.com", email_status="verified")
        d = c.to_dict()
        assert d["name"] == "A"
        assert d["email_status"] == "verified"


# ── Company ───────────────────────────────────────────────

class TestCompany:
    def test_creation(self):
        co = Company(name="X", url="x.io")
        assert co.name == "X"
        assert co.company_size == CompanySize.UNKNOWN

    def test_is_icp_match_saas(self):
        co = Company(name="X", url="x.io", industry="SaaS")
        assert co.is_icp_match is True

    def test_is_icp_match_fintech(self):
        co = Company(name="X", url="x.io", industry="Fintech")
        assert co.is_icp_match is True

    def test_is_icp_match_unknown(self):
        co = Company(name="X", url="x.io", industry="Manufacturing")
        assert co.is_icp_match is False

    def test_to_dict(self):
        co = Company(name="X", url="x.io", country="US", industry="SaaS")
        d = co.to_dict()
        assert d["name"] == "X"
        assert d["company_size"] == "unknown"


# ── BuyingEvent ───────────────────────────────────────────

class TestBuyingEvent:
    def test_creation(self):
        be = BuyingEvent(event_type="active_buying", description="test",
                         service_match="HIGH")
        assert be.event_type == "active_buying"
        assert be.urgency == "normal"

    def test_to_dict(self):
        be = BuyingEvent(event_type="verified_pain", description="desc",
                         service_match="HIGH", services_needed=["penetration_testing"])
        d = be.to_dict()
        assert d["event_type"] == "verified_pain"
        assert "penetration_testing" in d["services_needed"]


# ── CybersecurityOpportunity ──────────────────────────────

class TestCybersecurityOpportunity:
    def test_creation(self):
        opp = CybersecurityOpportunity(opportunity_id="id-1",
                                       company=Company(name="A", url="a.io"))
        assert opp.opportunity_id == "id-1"
        assert opp.evidence_count == 0

    def test_add_evidence(self, sample_opportunity):
        assert sample_opportunity.evidence_count == 3

    def test_verified_evidence_count(self, sample_opportunity):
        assert sample_opportunity.verified_evidence_count == 3

    def test_is_sales_ready(self, sample_opportunity):
        sample_opportunity.final_verdict = "SALES_READY"
        assert sample_opportunity.is_sales_ready is True

    def test_is_not_sales_ready(self, sample_opportunity):
        assert sample_opportunity.is_sales_ready is False

    def test_to_dict(self, sample_opportunity):
        d = sample_opportunity.to_dict()
        assert d["opportunity_id"] == "test-opp-001"
        assert d["company"]["name"] == "TestCo"
        assert len(d["evidence_chain"]) == 3


# ── Enums ─────────────────────────────────────────────────

class TestEnums:
    def test_priority_values(self):
        assert OpportunityPriority.P0.value == "ACTIVE_BUYING_EVENT"
        assert OpportunityPriority.P1.value == "VERIFIED_SECURITY_PAIN"
        assert OpportunityPriority.P2.value == "HIGH_POTENTIAL_OUTBOUND"

    def test_sales_readiness_values(self):
        assert SalesReadiness.SALES_READY.value == "SALES_READY"
        assert SalesReadiness.MARKETING_READY.value == "MARKETING_READY"

    def test_company_size_has_unknown(self):
        assert CompanySize.UNKNOWN.value == "unknown"

    def test_service_lane_values(self):
        assert ServiceLane.CYBERSECURITY.value == "CYBERSECURITY"
