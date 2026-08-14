"""Additional tests for connector events — edge cases and comprehensive coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from opportunity_connector_platform.connector_events import (
    SUPPORTED_CATEGORIES,
    SUPPORTED_EVENT_TYPES,
    EvidenceEvent,
    EventBatch,
    RoutedEvidenceEvent,
)


def _make_event(**overrides: object) -> EvidenceEvent:
    now = datetime.now(UTC)
    defaults = dict(
        connector_id="c", connector_version="1.0", headline="h",
        event_type="Hiring", event_category="Identity",
        published_at=now, captured_at=now, evidence="e", collector="t",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestSupportedEventTypes:
    def test_hiring(self):
        assert "Hiring" in SUPPORTED_EVENT_TYPES

    def test_funding(self):
        assert "Funding" in SUPPORTED_EVENT_TYPES

    def test_expansion(self):
        assert "Expansion" in SUPPORTED_EVENT_TYPES

    def test_new_office(self):
        assert "New Office" in SUPPORTED_EVENT_TYPES

    def test_technology_adoption(self):
        assert "Technology Adoption" in SUPPORTED_EVENT_TYPES

    def test_migration(self):
        assert "Migration" in SUPPORTED_EVENT_TYPES

    def test_product_launch(self):
        assert "Product Launch" in SUPPORTED_EVENT_TYPES

    def test_compliance(self):
        assert "Compliance" in SUPPORTED_EVENT_TYPES

    def test_procurement(self):
        assert "Procurement" in SUPPORTED_EVENT_TYPES

    def test_executive_hire(self):
        assert "Executive Hire" in SUPPORTED_EVENT_TYPES

    def test_partnership(self):
        assert "Partnership" in SUPPORTED_EVENT_TYPES

    def test_customer_win(self):
        assert "Customer Win" in SUPPORTED_EVENT_TYPES

    def test_pricing_change(self):
        assert "Pricing Change" in SUPPORTED_EVENT_TYPES

    def test_acquisition(self):
        assert "Acquisition" in SUPPORTED_EVENT_TYPES

    def test_security_incident(self):
        assert "Security Incident" in SUPPORTED_EVENT_TYPES

    def test_infrastructure_upgrade(self):
        assert "Infrastructure Upgrade" in SUPPORTED_EVENT_TYPES

    def test_hiring_freeze(self):
        assert "Hiring Freeze" in SUPPORTED_EVENT_TYPES

    def test_layoffs(self):
        assert "Layoffs" in SUPPORTED_EVENT_TYPES

    def test_api_release(self):
        assert "API Release" in SUPPORTED_EVENT_TYPES

    def test_sdk_release(self):
        assert "SDK Release" in SUPPORTED_EVENT_TYPES

    def test_marketplace_listing(self):
        assert "Marketplace Listing" in SUPPORTED_EVENT_TYPES

    def test_press_release(self):
        assert "Press Release" in SUPPORTED_EVENT_TYPES

    def test_conference(self):
        assert "Conference" in SUPPORTED_EVENT_TYPES

    def test_award(self):
        assert "Award" in SUPPORTED_EVENT_TYPES

    def test_patent(self):
        assert "Patent" in SUPPORTED_EVENT_TYPES

    def test_government_tender(self):
        assert "Government Tender" in SUPPORTED_EVENT_TYPES

    def test_developer_activity(self):
        assert "Developer Activity" in SUPPORTED_EVENT_TYPES

    def test_community_growth(self):
        assert "Community Growth" in SUPPORTED_EVENT_TYPES

    def test_count(self):
        assert len(SUPPORTED_EVENT_TYPES) == 28


class TestSupportedCategories:
    def test_identity(self):
        assert "Identity" in SUPPORTED_CATEGORIES

    def test_conversation(self):
        assert "Conversation" in SUPPORTED_CATEGORIES

    def test_intent(self):
        assert "Intent" in SUPPORTED_CATEGORIES

    def test_technology(self):
        assert "Technology" in SUPPORTED_CATEGORIES

    def test_enrichment(self):
        assert "Enrichment" in SUPPORTED_CATEGORIES

    def test_count(self):
        assert len(SUPPORTED_CATEGORIES) == 5


class TestEvidenceEventComprehensive:
    def test_all_fields(self):
        now = datetime.now(UTC)
        eid = uuid4()
        event = EvidenceEvent(
            event_id=eid,
            connector_id="linkedin",
            connector_version="2.1.0",
            company_name="Acme Corp",
            headline="Acme raising Series C",
            summary="Acme announced a $50M Series C round",
            event_type="Funding",
            event_category="Enrichment",
            url="https://techcrunch.com/acme-series-c",
            published_at=now,
            captured_at=now,
            country="US",
            language="en",
            confidence=95.0,
            evidence="Press release from Acme Corp",
            raw_metadata={"source": "techcrunch", "author": "Jane"},
            collector="techcrunch",
        )
        assert event.event_id == eid
        assert event.connector_id == "linkedin"
        assert event.company_name == "Acme Corp"
        assert event.confidence == 95.0

    def test_minimal_event(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline="h",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
        )
        assert event.company_name is None
        assert event.url is None
        assert event.country is None
        assert event.language == "unknown"
        assert event.summary == ""
        assert event.raw_metadata == {}

    def test_confidence_range(self):
        now = datetime.now(UTC)
        for conf in [0.0, 25.0, 50.0, 75.0, 100.0]:
            event = EvidenceEvent(
                connector_id="c", connector_version="1", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
                confidence=conf,
            )
            assert event.confidence == conf

    def test_confidence_over_100_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="c", connector_version="1", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
                confidence=101.0,
            )

    def test_confidence_negative_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="c", connector_version="1", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
                confidence=-1.0,
            )

    def test_empty_connector_id_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="", connector_version="1", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
            )

    def test_empty_headline_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="c", connector_version="1", headline="",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
            )

    def test_empty_collector_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="c", connector_version="1", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="",
            )

    def test_empty_event_type_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="c", connector_version="1", headline="h",
                event_type="", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
            )

    def test_long_headline(self):
        now = datetime.now(UTC)
        headline = "x" * 500
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline=headline,
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
        )
        assert event.headline == headline

    def test_unicode_company_name(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline="h",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
            company_name="株式会社テスト",
        )
        assert event.company_name == "株式会社テスト"

    def test_long_url(self):
        now = datetime.now(UTC)
        url = "https://example.com/" + "a" * 2000
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline="h",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
            url=url,
        )
        assert event.url == url

    def test_deeply_nested_metadata(self):
        now = datetime.now(UTC)
        meta = {"level1": {"level2": {"level3": [1, 2, {"level4": True}]}}}
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline="h",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
            raw_metadata=meta,
        )
        assert event.raw_metadata == meta


class TestEventBatchComprehensive:
    def test_with_events(self):
        now = datetime.now(UTC)
        events = (
            EvidenceEvent(
                connector_id="c", connector_version="1", headline=f"h{i}",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now, evidence="e", collector="t",
            )
            for i in range(3)
        )
        batch = EventBatch(
            connector_id="c1", connector_version="1.0",
            events=tuple(events), total_collected=5,
            total_accepted=3, total_rejected=2,
        )
        assert len(batch.events) == 3
        assert batch.total_collected == 5

    def test_frozen(self):
        batch = EventBatch(connector_id="c", connector_version="1")
        with pytest.raises(Exception):
            batch.connector_id = "changed"  # type: ignore[misc]

    def test_collected_at_auto(self):
        batch = EventBatch(connector_id="c", connector_version="1")
        assert batch.collected_at is not None


class TestRoutedEvidenceEventComprehensive:
    def test_with_custom_route(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=True, route="custom_route")
        assert routed.route == "custom_route"

    def test_rejection_reason_none_on_accept(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=True)
        assert routed.rejection_reason is None

    def test_rejection_reason_set_on_reject(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(
            event=event, accepted=False, rejection_reason="expired"
        )
        assert routed.rejection_reason == "expired"
