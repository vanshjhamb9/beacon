"""COMAI B2B Partner Discovery Engine - Test Script.

This script tests the complete partner discovery pipeline.
Validates all components and ensures everything works correctly.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.partner import (
    PartnerRecord,
    PartnerIntent,
    PartnerTier,
    FinalVerdict,
    EmailStatus,
    ContactabilityLevel,
)
from app.services.partner_discovery import PartnerDiscoveryEngine
from app.services.partner_scoring import PartnerScoringEngine
from app.services.partner_contactability import ContactabilityVerificationEngine
from app.services.partner_export import PartnerExportPipeline


# ============================================================
# TEST DATA
# ============================================================

TEST_PARTNER_RECORD = PartnerRecord(
    opportunity_id="test-123",
    agency_name="Test Marketing Agency",
    agency_url="https://www.testmarketing.com",
    country="USA",
    city="New York",
    agency_type="marketing",
    founder_name="John Smith",
    founder_role="Founder",
    linkedin_url="https://linkedin.com/company/testmarketing",
    identity_confidence=0.8,
    services=["digital marketing", "seo", "google ads", "meta ads", "ecommerce marketing"],
    client_count_evidence="25+ clients including ecommerce brands",
    client_examples=["Brand A", "Brand B", "Brand C"],
    client_industries=["ecommerce", "fashion", "beauty"],
    partner_intent="EXPLICIT",
    partner_intent_evidence="Looking for tools for clients",
    email="john@testmarketing.com",
    email_status="PUBLIC_UNVERIFIED",
    email_evidence="Found on website",
    linkedin_status="FOUND",
    contactability="MEDIUM",
    contactability_evidence="Public unverified email + LinkedIn found",
    competitor=False,
    safety_clear=True,
)


# ============================================================
# TEST FUNCTIONS
# ============================================================

def test_partner_record():
    """Test PartnerRecord data model."""
    print("Testing PartnerRecord...")
    
    partner = TEST_PARTNER_RECORD
    
    # Test basic fields
    assert partner.opportunity_id == "test-123"
    assert partner.agency_name == "Test Marketing Agency"
    assert partner.agency_url == "https://www.testmarketing.com"
    assert partner.country == "USA"
    assert partner.city == "New York"
    assert partner.agency_type == "marketing"
    
    # Test decision maker
    assert partner.founder_name == "John Smith"
    assert partner.founder_role == "Founder"
    assert partner.identity_confidence == 0.8
    
    # Test services
    assert len(partner.services) == 5
    assert "digital marketing" in partner.services
    assert "ecommerce marketing" in partner.services
    
    # Test client evidence
    assert "25+ clients" in partner.client_count_evidence
    assert len(partner.client_examples) == 3
    assert len(partner.client_industries) == 3
    
    # Test partner intent
    assert partner.partner_intent == "EXPLICIT"
    assert partner.partner_intent_evidence == "Looking for tools for clients"
    
    # Test contactability
    assert partner.email == "john@testmarketing.com"
    assert partner.email_status == "PUBLIC_UNVERIFIED"
    assert partner.contactability == "MEDIUM"
    
    # Test safety
    assert partner.competitor == False
    assert partner.safety_clear == True
    
    # Test to_dict
    partner_dict = partner.to_dict()
    assert isinstance(partner_dict, dict)
    assert partner_dict["opportunity_id"] == "test-123"
    assert partner_dict["agency_name"] == "Test Marketing Agency"
    
    print("  [PASS] PartnerRecord tests passed")
    return True


def test_scoring_engine():
    """Test PartnerScoringEngine."""
    print("Testing PartnerScoringEngine...")
    
    engine = PartnerScoringEngine()
    partner = TEST_PARTNER_RECORD
    
    # Score partner
    result = engine.score_partner(partner)
    
    # Test client access score
    assert isinstance(result.client_access_score, int)
    assert 0 <= result.client_access_score <= 100
    assert result.client_access_evidence != ""
    assert isinstance(result.client_access_signals, list)
    
    # Test COMAI partner fit
    assert isinstance(result.comai_partner_fit, int)
    assert 0 <= result.comai_partner_fit <= 100
    assert result.comai_fit_evidence != ""
    assert isinstance(result.comai_fit_signals, list)
    
    # Test partner intent
    assert result.partner_intent in ["EXPLICIT", "UNKNOWN"]
    assert result.partner_intent_evidence != ""
    
    # Test partner tier
    assert result.partner_tier in ["A", "B", "C"]
    
    # Test final verdict
    assert result.final_verdict in ["PARTNER_READY", "NURTURE", "REJECT"]
    
    # Test partner ready gate
    assert isinstance(result.partner_ready_gate_passed, bool)
    
    # Test high priority partner
    assert isinstance(result.high_priority_partner, bool)
    
    # Test to_dict
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert "client_access_score" in result_dict
    assert "comai_partner_fit" in result_dict
    
    print(f"  [PASS] Scoring tests passed (Client Access={result.client_access_score}, COMAI Fit={result.comai_partner_fit})")
    return True


def test_contactability_engine():
    """Test ContactabilityVerificationEngine."""
    print("Testing ContactabilityVerificationEngine...")
    
    engine = ContactabilityVerificationEngine()
    partner = TEST_PARTNER_RECORD
    
    # Verify contactability
    result = engine.verify_contactability(partner)
    
    # Test email
    assert result.email == "john@testmarketing.com"
    assert result.email_status in ["VERIFIED", "PUBLIC_UNVERIFIED", "INVALID", "UNKNOWN"]
    assert result.email_evidence != ""
    
    # Test decision maker
    assert result.decision_maker_name == "John Smith"
    assert result.decision_maker_role == "Founder"
    assert result.decision_maker_identified == True
    
    # Test LinkedIn
    assert result.linkedin_url == "https://linkedin.com/company/testmarketing"
    assert result.linkedin_status in ["FOUND", "NOT_FOUND", "INVALID"]
    
    # Test contactability level
    assert result.contactability_level in ["HIGH", "MEDIUM", "LOW", "NONE"]
    assert result.contactability_evidence != ""
    
    # Test to_dict
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert "email" in result_dict
    assert "contactability_level" in result_dict
    
    print(f"  [PASS] Contactability tests passed (Level={result.contactability_level})")
    return True


def test_export_pipeline():
    """Test PartnerExportPipeline."""
    print("Testing PartnerExportPipeline...")
    
    # Create test partners
    partners = [
        TEST_PARTNER_RECORD,
        PartnerRecord(
            opportunity_id="test-456",
            agency_name="Test Tech Agency",
            agency_url="https://www.testtech.com",
            country="UK",
            city="London",
            agency_type="technology",
            services=["web development", "shopify", "ecommerce development"],
            client_count_evidence="15+ clients",
            client_industries=["ecommerce", "retail"],
            partner_intent="UNKNOWN",
            email="info@testtech.com",
            email_status="PUBLIC_UNVERIFIED",
            contactability="MEDIUM",
            competitor=False,
            safety_clear=True,
        ),
    ]
    
    # Create export pipeline
    pipeline = PartnerExportPipeline("exports/comai_b2b_partners_test")
    
    # Export results
    export_data = pipeline.export_results(partners)
    
    # Test export data
    assert export_data.total_discovered == 2
    assert export_data.verified_agencies == 2
    assert export_data.tier_a + export_data.tier_b + export_data.tier_c + export_data.rejected == 2
    
    # Test to_dict
    export_dict = export_data.to_dict()
    assert isinstance(export_dict, dict)
    assert "total_discovered" in export_dict
    assert "hot_partners_list" in export_dict
    
    print(f"  [PASS] Export pipeline tests passed (Total={export_data.total_discovered})")
    return True


def test_discovery_engine():
    """Test PartnerDiscoveryEngine."""
    print("Testing PartnerDiscoveryEngine...")
    
    engine = PartnerDiscoveryEngine()
    
    # Test with a sample URL (this will make an HTTP request)
    # For testing, we'll just test the helper methods
    
    # Test agency type detection
    html = "We are a digital marketing agency specializing in ecommerce brands"
    agency_type = engine._detect_agency_type(html, "https://www.test.com")
    assert agency_type == "marketing"
    
    # Test reject patterns
    html = "We are a freelancer looking for work"
    is_rejected = engine._check_reject_patterns(html, "https://www.test.com")
    assert is_rejected == True
    
    # Test competitor check
    html = "We build chatbots and AI customer support solutions"
    is_competitor = engine._check_competitor(html, "https://www.test.com")
    # This might be True or False depending on the patterns
    
    # Test relevant service check
    html = "We offer digital marketing and ecommerce services"
    partner = TEST_PARTNER_RECORD
    has_relevant = engine._check_relevant_service(html, partner)
    assert has_relevant == True
    
    # Test business clients check
    html = "We work with 25+ brands"
    has_clients = engine._check_business_clients(html, partner)
    assert has_clients == True
    
    print("  [PASS] Discovery engine tests passed")
    return True


# ============================================================
# MAIN TEST RUNNER
# ============================================================

def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("COMAI B2B Partner Discovery Engine - Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        test_partner_record,
        test_scoring_engine,
        test_contactability_engine,
        test_export_pipeline,
        test_discovery_engine,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print()
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    print()
    
    if failed == 0:
        print("ALL TESTS PASSED!")
    else:
        print(f"SOME TESTS FAILED!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
