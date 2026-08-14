"""Tests for DQE enums and schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from discovery_quality_engine.quality_engine import (
    DEFAULT_EXPIRY,
    DEFAULT_FRESHNESS_LIMITS,
    DEFAULT_MIN_SOURCE_TRUST,
    DEFAULT_SOURCE_TRUST,
    DEFAULT_SUPPORTED_REGIONS,
    DEFAULT_AI_KEYWORDS,
    FreshnessLimit,
    OpportunityExpiry,
    QualityDecision,
    QualityEvent,
    QualityGate,
    QualitySnapshot,
    RejectionReason,
    SignalType,
)


class TestQualityDecision:
    def test_accept_value(self) -> None:
        assert QualityDecision.ACCEPT == "ACCEPT"

    def test_reject_value(self) -> None:
        assert QualityDecision.REJECT == "REJECT"

    def test_hold_value(self) -> None:
        assert QualityDecision.HOLD == "HOLD"

    def test_all_members(self) -> None:
        assert set(QualityDecision) == {QualityDecision.ACCEPT, QualityDecision.REJECT, QualityDecision.HOLD}

    def test_is_string(self) -> None:
        assert isinstance(QualityDecision.ACCEPT, str)


class TestQualityGate:
    def test_freshness(self) -> None:
        assert QualityGate.FRESHNESS == "FRESHNESS"

    def test_buying_signal(self) -> None:
        assert QualityGate.BUYING_SIGNAL == "BUYING_SIGNAL"

    def test_website_quality(self) -> None:
        assert QualityGate.WEBSITE_QUALITY == "WEBSITE_QUALITY"

    def test_company_validation(self) -> None:
        assert QualityGate.COMPANY_VALIDATION == "COMPANY_VALIDATION"

    def test_source_trust(self) -> None:
        assert QualityGate.SOURCE_TRUST == "SOURCE_TRUST"

    def test_duplicate_check(self) -> None:
        assert QualityGate.DUPLICATE_CHECK == "DUPLICATE_CHECK"

    def test_competitor_check(self) -> None:
        assert QualityGate.COMPETITOR_CHECK == "COMPETITOR_CHECK"

    def test_activity_check(self) -> None:
        assert QualityGate.ACTIVITY_CHECK == "ACTIVITY_CHECK"

    def test_industry_rules(self) -> None:
        assert QualityGate.INDUSTRY_RULES == "INDUSTRY_RULES"

    def test_region_rules(self) -> None:
        assert QualityGate.REGION_RULES == "REGION_RULES"

    def test_ai_company_filter(self) -> None:
        assert QualityGate.AI_COMPANY_FILTER == "AI_COMPANY_FILTER"

    def test_icp_filter(self) -> None:
        assert QualityGate.ICP_FILTER == "ICP_FILTER"

    def test_total_gates(self) -> None:
        assert len(QualityGate) == 12


class TestSignalType:
    def test_hiring(self) -> None:
        assert SignalType.HIRING == "HIRING"

    def test_funding(self) -> None:
        assert SignalType.FUNDING == "FUNDING"

    def test_product_launch(self) -> None:
        assert SignalType.PRODUCT_LAUNCH == "PRODUCT_LAUNCH"

    def test_technology_adoption(self) -> None:
        assert SignalType.TECHNOLOGY_ADOPTION == "TECHNOLOGY_ADOPTION"

    def test_partnership(self) -> None:
        assert SignalType.PARTNERSHIP == "PARTNERSHIP"

    def test_expansion(self) -> None:
        assert SignalType.EXPANSION == "EXPANSION"

    def test_conference(self) -> None:
        assert SignalType.CONFERENCE == "CONFERENCE"

    def test_award(self) -> None:
        assert SignalType.AWARD == "AWARD"

    def test_press_release(self) -> None:
        assert SignalType.PRESS_RELEASE == "PRESS_RELEASE"

    def test_government_tender(self) -> None:
        assert SignalType.GOVERNMENT_TENDER == "GOVERNMENT_TENDER"

    def test_executive_hiring(self) -> None:
        assert SignalType.EXECUTIVE_HIRING == "EXECUTIVE_HIRING"

    def test_office_expansion(self) -> None:
        assert SignalType.OFFICE_EXPANSION == "OFFICE_EXPANSION"

    def test_acquisition(self) -> None:
        assert SignalType.ACQUISITION == "ACQUISITION"

    def test_infrastructure_upgrade(self) -> None:
        assert SignalType.INFRASTRUCTURE_UPGRADE == "INFRASTRUCTURE_UPGRADE"

    def test_security_incident(self) -> None:
        assert SignalType.SECURITY_INCIDENT == "SECURITY_INCIDENT"

    def test_api_release(self) -> None:
        assert SignalType.API_RELEASE == "API_RELEASE"

    def test_marketplace_expansion(self) -> None:
        assert SignalType.MARKETPLACE_EXPANSION == "MARKETPLACE_EXPANSION"

    def test_compliance(self) -> None:
        assert SignalType.COMPLIANCE == "COMPLIANCE"

    def test_total_types(self) -> None:
        assert len(SignalType) == 18


class TestRejectionReason:
    def test_stale_signal(self) -> None:
        assert RejectionReason.STALE_SIGNAL == "STALE_SIGNAL"

    def test_no_buying_signal(self) -> None:
        assert RejectionReason.NO_BUYING_SIGNAL == "NO_BUYING_SIGNAL"

    def test_parked_domain(self) -> None:
        assert RejectionReason.PARKED_DOMAIN == "PARKED_DOMAIN"

    def test_coming_soon(self) -> None:
        assert RejectionReason.COMING_SOON == "COMING_SOON"

    def test_not_found_404(self) -> None:
        assert RejectionReason.NOT_FOUND_404 == "NOT_FOUND_404"

    def test_maintenance(self) -> None:
        assert RejectionReason.MAINTENANCE == "MAINTENANCE"

    def test_spam_website(self) -> None:
        assert RejectionReason.SPAM_WEBSITE == "SPAM_WEBSITE"

    def test_no_https(self) -> None:
        assert RejectionReason.NO_HTTPS == "NO_HTTPS"

    def test_low_content(self) -> None:
        assert RejectionReason.LOW_CONTENT == "LOW_CONTENT"

    def test_domain_for_sale(self) -> None:
        assert RejectionReason.DOMAIN_FOR_SALE == "DOMAIN_FOR_SALE"

    def test_inactive_website(self) -> None:
        assert RejectionReason.INACTIVE_WEBSITE == "INACTIVE_WEBSITE"

    def test_duplicate_domain(self) -> None:
        assert RejectionReason.DUPLICATE_DOMAIN == "DUPLICATE_DOMAIN"

    def test_duplicate_company(self) -> None:
        assert RejectionReason.DUPLICATE_COMPANY == "DUPLICATE_COMPANY"

    def test_duplicate_opportunity(self) -> None:
        assert RejectionReason.DUPLICATE_OPPORTUNITY == "DUPLICATE_OPPORTUNITY"

    def test_duplicate_evidence(self) -> None:
        assert RejectionReason.DUPLICATE_EVIDENCE == "DUPLICATE_EVIDENCE"

    def test_duplicate_signal(self) -> None:
        assert RejectionReason.DUPLICATE_SIGNAL == "DUPLICATE_SIGNAL"

    def test_competitor(self) -> None:
        assert RejectionReason.COMPETITOR == "COMPETITOR"

    def test_existing_client(self) -> None:
        assert RejectionReason.EXISTING_CLIENT == "EXISTING_CLIENT"

    def test_demo_company(self) -> None:
        assert RejectionReason.DEMO_COMPANY == "DEMO_COMPANY"

    def test_ai_company(self) -> None:
        assert RejectionReason.AI_COMPANY == "AI_COMPANY"

    def test_unsupported_region(self) -> None:
        assert RejectionReason.UNSUPPORTED_REGION == "UNSUPPORTED_REGION"

    def test_outside_icp(self) -> None:
        assert RejectionReason.OUTSIDE_ICP == "OUTSIDE_ICP"

    def test_low_source_trust(self) -> None:
        assert RejectionReason.LOW_SOURCE_TRUST == "LOW_SOURCE_TRUST"

    def test_no_recent_activity(self) -> None:
        assert RejectionReason.NO_RECENT_ACTIVITY == "NO_RECENT_ACTIVITY"

    def test_expired_opportunity(self) -> None:
        assert RejectionReason.EXPIRED_OPPORTUNITY == "EXPIRED_OPPORTUNITY"

    def test_unknown(self) -> None:
        assert RejectionReason.UNKNOWN == "UNKNOWN"

    def test_total_reasons(self) -> None:
        assert len(RejectionReason) == 26


class TestOpportunityExpiry:
    def test_default_expiry_count(self) -> None:
        assert len(DEFAULT_EXPIRY) == 18

    def test_hiring_expiry(self) -> None:
        hiring = [e for e in DEFAULT_EXPIRY if e.signal_type == SignalType.HIRING][0]
        assert hiring.max_age_days == 30

    def test_funding_expiry(self) -> None:
        funding = [e for e in DEFAULT_EXPIRY if e.signal_type == SignalType.FUNDING][0]
        assert funding.max_age_days == 90

    def test_conference_expiry(self) -> None:
        conf = [e for e in DEFAULT_EXPIRY if e.signal_type == SignalType.CONFERENCE][0]
        assert conf.max_age_days == 15

    def test_government_tender_expiry(self) -> None:
        gov = [e for e in DEFAULT_EXPIRY if e.signal_type == SignalType.GOVERNMENT_TENDER][0]
        assert gov.max_age_days == 9999


class TestFreshnessLimit:
    def test_default_limits_count(self) -> None:
        assert len(DEFAULT_FRESHNESS_LIMITS) == 10

    def test_hiring_limit(self) -> None:
        hiring = [f for f in DEFAULT_FRESHNESS_LIMITS if f.signal_type == "HIRING"][0]
        assert hiring.max_age_days == 30

    def test_funding_limit(self) -> None:
        funding = [f for f in DEFAULT_FRESHNESS_LIMITS if f.signal_type == "FUNDING"][0]
        assert funding.max_age_days == 90


class TestDefaults:
    def test_min_source_trust(self) -> None:
        assert DEFAULT_MIN_SOURCE_TRUST == 60.0

    def test_source_trust_count(self) -> None:
        assert len(DEFAULT_SOURCE_TRUST) == 10

    def test_supported_regions_count(self) -> None:
        assert len(DEFAULT_SUPPORTED_REGIONS) == 20

    def test_ai_keywords_count(self) -> None:
        assert len(DEFAULT_AI_KEYWORDS) > 20


class TestQualityEvent:
    def test_create_event(self) -> None:
        event = QualityEvent(
            company_id=uuid4(),
            company_name="Test Corp",
            signal_type="HIRING",
            source="linkedin",
            decision=QualityDecision.ACCEPT,
        )
        assert event.decision == QualityDecision.ACCEPT
        assert event.company_name == "Test Corp"

    def test_default_values(self) -> None:
        event = QualityEvent(
            company_id=uuid4(),
            company_name="Corp",
            signal_type="HIRING",
            source="web",
            decision=QualityDecision.REJECT,
        )
        assert event.gates_passed == []
        assert event.gates_failed == []
        assert event.rejection_reasons == []
        assert event.metadata == {}
        assert event.created_at is not None

    def test_with_rejection_reasons(self) -> None:
        event = QualityEvent(
            company_id=uuid4(),
            company_name="Corp",
            signal_type="HIRING",
            source="web",
            decision=QualityDecision.REJECT,
            rejection_reasons=["STALE_SIGNAL", "NO_BUYING_SIGNAL"],
        )
        assert len(event.rejection_reasons) == 2
        assert "STALE_SIGNAL" in event.rejection_reasons


class TestQualitySnapshot:
    def test_default_snapshot(self) -> None:
        snap = QualitySnapshot()
        assert snap.signals_collected == 0
        assert snap.signals_accepted == 0
        assert snap.signals_rejected == 0
        assert snap.acceptance_rate == 0.0

    def test_snapshot_with_values(self) -> None:
        snap = QualitySnapshot(
            signals_collected=100,
            signals_accepted=40,
            signals_rejected=60,
            acceptance_rate=40.0,
        )
        assert snap.signals_collected == 100
        assert snap.acceptance_rate == 40.0
