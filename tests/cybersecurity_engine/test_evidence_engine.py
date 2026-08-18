"""Tests for cybersecurity_engine.evidence_engine."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.evidence_engine import (
    SalesReadinessEvaluator,
    assess_contactability,
    evaluate_evidence_chain,
    is_competitor,
    verify_company,
)
from cybersecurity_engine.models import (
    Company, CompanySize, Contact, CybersecurityOpportunity,
    Evidence, EvidenceConfidence, OpportunityPriority, OpportunityType,
)


# ── is_competitor ─────────────────────────────────────────

class TestIsCompetitor:
    def test_crowdstrike(self):
        assert is_competitor("CrowdStrike") is True

    def test_palo_alto(self):
        assert is_competitor("Palo Alto Networks") is True

    def test_hackerone(self):
        assert is_competitor("HackerOne") is True

    def test_normal_company(self):
        assert is_competitor("SecureFlow") is False

    def test_partial_match(self):
        assert is_competitor("MyCrowdStrike Clone") is True


# ── verify_company ────────────────────────────────────────

class TestVerifyCompany:
    def test_valid_company(self):
        co = Company(name="X", url="x.io", country="US")
        valid, reasons = verify_company(co)
        assert valid is True
        assert reasons == []

    def test_missing_name(self):
        co = Company(name="", url="x.io", country="US")
        valid, reasons = verify_company(co)
        assert valid is False
        assert any("name" in r.lower() for r in reasons)

    def test_missing_url(self):
        co = Company(name="X", url="", country="US")
        valid, reasons = verify_company(co)
        assert valid is False

    def test_missing_country(self):
        co = Company(name="X", url="x.io", country="")
        valid, reasons = verify_company(co)
        assert valid is False

    def test_too_large(self):
        co = Company(name="X", url="x.io", country="US",
                     company_size=CompanySize.ENTERPRISE, employee_count=15000)
        valid, reasons = verify_company(co)
        assert valid is False
        assert any("large" in r.lower() for r in reasons)


# ── evaluate_evidence_chain ───────────────────────────────

class TestEvaluateEvidenceChain:
    def test_empty_evidence(self):
        conf, issues = evaluate_evidence_chain([])
        assert conf == EvidenceConfidence.LOW
        assert any("no evidence" in i.lower() for i in issues)

    def test_single_source_type(self):
        evidence = [
            Evidence(claim="a", value="b", source_name="s", source_type="post",
                     source_url="http://u", source_status="ok", verified=True,
                     confidence=85, published_at=datetime(2026, 8, 1, tzinfo=UTC)),
        ]
        conf, issues = evaluate_evidence_chain(evidence)
        assert any("single source" in i.lower() for i in issues)

    def test_high_confidence(self):
        evidence = [
            Evidence(claim="a", value="b", source_name="s1", source_type="procurement",
                     source_url="http://u1", source_status="ok", verified=True,
                     confidence=90, published_at=datetime(2026, 8, 1, tzinfo=UTC)),
            Evidence(claim="c", value="d", source_name="s2", source_type="founder_post",
                     source_url="http://u2", source_status="ok", verified=True,
                     confidence=85, published_at=datetime(2026, 8, 5, tzinfo=UTC)),
            Evidence(claim="e", value="f", source_name="s3", source_type="company_announcement",
                     source_url="http://u3", source_status="ok", verified=True,
                     confidence=88, published_at=datetime(2026, 8, 10, tzinfo=UTC)),
        ]
        conf, issues = evaluate_evidence_chain(evidence)
        assert conf == EvidenceConfidence.HIGH

    def test_medium_confidence(self):
        evidence = [
            Evidence(claim="a", value="b", source_name="s", source_type="post",
                     source_url="http://u", source_status="ok", verified=True,
                     confidence=85, published_at=datetime(2026, 8, 1, tzinfo=UTC)),
        ]
        conf, issues = evaluate_evidence_chain(evidence)
        assert conf == EvidenceConfidence.MEDIUM


# ── assess_contactability ─────────────────────────────────

class TestAssessContactability:
    def test_high_with_email(self):
        c = Contact(email="a@b.com", email_status="verified")
        level, channels = assess_contactability(c)
        assert level == "high"
        assert "decision_maker_verified_email" in channels

    def test_medium_linkedin_only(self):
        c = Contact(linkedin_url="http://linkedin.com/in/x", linkedin_status="verified")
        level, channels = assess_contactability(c)
        assert level == "medium"

    def test_unreachable(self):
        c = Contact()
        level, channels = assess_contactability(c)
        assert level == "unreachable"
        assert channels == []


# ── SalesReadinessEvaluator ───────────────────────────────

class TestSalesReadinessEvaluator:
    def test_sales_ready(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict == "SALES_READY"

    def test_not_ready_competitor(self, sample_opportunity):
        sample_opportunity.company.name = "CrowdStrike Solutions"
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict == "NOT_READY"

    def test_not_ready_no_signal(self, sample_opportunity):
        sample_opportunity.buying_event.event_type = "no_signal"
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict == "NOT_READY"

    def test_not_ready_low_service_match(self, sample_opportunity):
        sample_opportunity.buying_event.service_match = "LOW"
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict in {"NOT_READY", "MARKETING_READY"}

    def test_not_ready_no_contact(self, sample_opportunity):
        sample_opportunity.contact = Contact()
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.final_verdict == "NOT_READY"

    def test_marketing_ready(self, sample_opportunity):
        sample_opportunity.contact = Contact()
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        # Missing contact = unreachable = NOT_READY
        assert result.final_verdict in {"NOT_READY", "MARKETING_READY"}

    def test_outreach_classification_p0(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.outreach_classification.value == "ACTIVE_BUYING_EVENT"

    def test_outreach_preparation_generated(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.outreach_preparation.buyer_name == "Alex Chen"
        assert result.outreach_preparation.company_name == "TestCo"

    def test_contactability_set(self, sample_opportunity):
        evaluator = SalesReadinessEvaluator()
        result = evaluator.evaluate(sample_opportunity)
        assert result.contactability == "high"
