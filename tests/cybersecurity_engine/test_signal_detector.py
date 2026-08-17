"""Tests for cybersecurity_engine.signal_detector."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.models import OpportunityPriority, ServiceLane
from cybersecurity_engine.signal_detector import (
    CybersecuritySignalDetector,
    detect_service_needs,
    calculate_service_match,
)


@pytest.fixture
def detector():
    return CybersecuritySignalDetector()


# ── detect_service_needs ──────────────────────────────────

class TestDetectServiceNeeds:
    def test_penetration_testing(self):
        services = detect_service_needs("need a penetration test for our app")
        assert "penetration_testing" in services

    def test_vulnerability_assessment(self):
        services = detect_service_needs("looking for vulnerability assessment")
        assert "vulnerability_assessment" in services

    def test_web_app_security(self):
        services = detect_service_needs("web application security test needed")
        assert "web_app_security" in services

    def test_api_security(self):
        services = detect_service_needs("api security testing required")
        assert "api_security" in services

    def test_cloud_security(self):
        services = detect_service_needs("cloud security assessment for AWS")
        assert "cloud_security" in services

    def test_compliance(self):
        services = detect_service_needs("need SOC 2 compliance support")
        assert "compliance" in services

    def test_multiple_services(self):
        text = "need penetration testing and web app security and api security"
        services = detect_service_needs(text)
        assert len(services) >= 3

    def test_no_services(self):
        services = detect_service_needs("nice weather today")
        assert services == []


# ── calculate_service_match ───────────────────────────────

class TestCalculateServiceMatch:
    def test_high_with_many(self):
        assert calculate_service_match(["a", "b", "c"]) == "HIGH"

    def test_high_with_one(self):
        assert calculate_service_match(["a"]) == "HIGH"

    def test_low_empty(self):
        assert calculate_service_match([]) == "LOW"


# ── CybersecuritySignalDetector ───────────────────────────

class TestCybersecuritySignalDetector:
    def test_p0_direct_request(self, detector):
        text = "Looking for penetration testing company for our SaaS"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0
        assert event.event_type == "active_buying"
        assert event.service_match == "HIGH"

    def test_p0_rfp(self, detector):
        text = "RFP for security testing vendor, need proposals"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0

    def test_p0_compliance_driven(self, detector):
        text = "Need penetration testing for SOC 2 compliance"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0

    def test_p0_enterprise_requirement(self, detector):
        text = "Enterprise customer requires penetration testing"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0

    def test_p0_source_tier_3_not_p0(self, detector):
        text = "Looking for penetration testing company"
        priority, event = detector.detect_priority(text, source_tier=3)
        # Tier 3 with P0 pattern should NOT be P0 (requires tier <= 2)
        assert priority != OpportunityPriority.P0

    def test_p1_vulnerability_discovered(self, detector):
        text = "Discovered a critical SQL injection vulnerability in production"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P1
        assert event.event_type == "verified_pain"

    def test_p1_compliance_pressure(self, detector):  # noqa
        text = "SOC 2 compliance deadline approaching, enterprise customer requires security assessment"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P1

    def test_p1_operational_pressure(self, detector):
        text = "Security team overwhelmed, need external security testing help"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P1

    def test_p2_growth_signals(self, detector):
        text = "Series B funding raised, rapidly growing SaaS, hiring security engineers"
        priority, event = detector.detect_priority(text, source_tier=3)
        assert priority == OpportunityPriority.P2

    def test_p2_new_product_launch(self, detector):
        text = "Launching new mobile app, enterprise customer acquisition, preparing SOC 2"
        priority, event = detector.detect_priority(text, source_tier=3)
        assert priority == OpportunityPriority.P2

    def test_p3_no_signal(self, detector):
        text = "Nice weather today, went for a walk in the park"
        priority, event = detector.detect_priority(text, source_tier=3)
        assert priority == OpportunityPriority.P3
        assert event.event_type == "no_signal"

    def test_p0_urgency_urgent(self, detector):
        text = "Looking for penetration testing company, deadline next week"
        priority, event = detector.detect_priority(text, source_tier=1)
        assert event.urgency == "urgent"

    def test_p0_why_now_pre_launch(self, detector):
        text = "Before launch need penetration testing for our platform"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert "launch" in event.why_now.lower() or "audit" in event.why_now.lower()

    def test_services_detected_in_p0(self, detector):
        text = "Need web application penetration testing and API security testing"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert "web_app_security" in event.services_needed
        assert "api_security" in event.services_needed

    def test_cloud_security_p0(self, detector):
        text = "Looking for cloud security assessment company"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0
        assert "cloud_security" in event.services_needed

    def test_mobile_security_p0(self, detector):
        text = "Need mobile application penetration test"
        priority, event = detector.detect_priority(text, source_tier=2)
        assert priority == OpportunityPriority.P0
        assert "penetration_testing" in event.services_needed
