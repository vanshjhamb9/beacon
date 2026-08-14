"""Tests for connector capabilities taxonomy."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_capabilities import (
    CONNECTOR_CATEGORIES,
    CATEGORY_BY_NAME,
    ConnectorCapability,
    all_known_connectors,
    category_for,
    connectors_in_category,
)


class TestCategoryFor:
    def test_identity_product_hunt(self):
        assert category_for("Product Hunt") == "Identity"

    def test_identity_github(self):
        assert category_for("GitHub") == "Technology"

    def test_identity_crunchbase(self):
        assert category_for("Crunchbase") == "Identity"

    def test_identity_yc(self):
        assert category_for("YC") == "Identity"

    def test_identity_company_website(self):
        assert category_for("Company Website") == "Identity"

    def test_conversation_reddit(self):
        assert category_for("Reddit") == "Conversation"

    def test_conversation_hn(self):
        assert category_for("HN") == "Conversation"

    def test_conversation_devto(self):
        assert category_for("Dev.to") == "Conversation"

    def test_conversation_rss(self):
        assert category_for("RSS") == "Conversation"

    def test_intent_google_news(self):
        assert category_for("Google News") == "Intent"

    def test_intent_press_releases(self):
        assert category_for("Press Releases") == "Intent"

    def test_intent_jobs(self):
        assert category_for("Jobs") == "Intent"

    def test_intent_greenhouse(self):
        assert category_for("Greenhouse") == "Intent"

    def test_intent_lever(self):
        assert category_for("Lever") == "Intent"

    def test_intent_ashby(self):
        assert category_for("Ashby") == "Intent"

    def test_intent_workday(self):
        assert category_for("Workday") == "Intent"

    def test_technology_stackshare(self):
        assert category_for("StackShare") == "Technology"

    def test_technology_builtwith(self):
        assert category_for("BuiltWith") == "Technology"

    def test_technology_wappalyzer(self):
        assert category_for("Wappalyzer") == "Technology"

    def test_enrichment_hunter(self):
        assert category_for("Hunter") == "Enrichment"

    def test_enrichment_apollo(self):
        assert category_for("Apollo") == "Enrichment"

    def test_enrichment_people_data_labs(self):
        assert category_for("People Data Labs") == "Enrichment"

    def test_enrichment_linkedin(self):
        assert category_for("LinkedIn") == "Enrichment"

    def test_enrichment_clearbit(self):
        assert category_for("Clearbit") == "Enrichment"

    def test_unknown_connector(self):
        assert category_for("UnknownSource") == "Unknown"

    def test_case_insensitive(self):
        assert category_for("github") == "Technology"
        assert category_for("REDDIT") == "Conversation"

    def test_whitespace_stripped(self):
        assert category_for("  GitHub  ") == "Technology"

    def test_empty_string(self):
        assert category_for("") == "Unknown"


class TestAllKnownConnectors:
    def test_returns_dict(self):
        result = all_known_connectors()
        assert isinstance(result, dict)

    def test_has_github(self):
        result = all_known_connectors()
        assert "github" in result

    def test_has_reddit(self):
        result = all_known_connectors()
        assert "reddit" in result

    def test_has_linkedin(self):
        result = all_known_connectors()
        assert "linkedin" in result

    def test_values_are_categories(self):
        result = all_known_connectors()
        for cat in result.values():
            assert cat in CONNECTOR_CATEGORIES


class TestConnectorsInCategory:
    def test_identity(self):
        names = connectors_in_category("Identity")
        assert "GitHub" in names
        assert "Product Hunt" in names

    def test_conversation(self):
        names = connectors_in_category("Conversation")
        assert "Reddit" in names
        assert "HN" in names

    def test_intent(self):
        names = connectors_in_category("Intent")
        assert "Google News" in names

    def test_technology(self):
        names = connectors_in_category("Technology")
        assert "BuiltWith" in names

    def test_enrichment(self):
        names = connectors_in_category("Enrichment")
        assert "Hunter" in names

    def test_unknown_category(self):
        assert connectors_in_category("NonExistent") == ()


class TestConnectorCategories:
    def test_all_categories_present(self):
        expected = {"Identity", "Conversation", "Intent", "Technology", "Enrichment"}
        assert set(CONNECTOR_CATEGORIES.keys()) == expected

    def test_category_by_name_complete(self):
        for cat, names in CONNECTOR_CATEGORIES.items():
            for name in names:
                assert name.lower() in CATEGORY_BY_NAME
                # GitHub appears in two categories; last one wins
                if name.lower() == "github":
                    continue
                assert CATEGORY_BY_NAME[name.lower()] == cat


class TestConnectorCapabilityDataclass:
    def test_create_identity(self):
        cap = ConnectorCapability(category="Identity", event_types=("Hiring",))
        assert cap.category == "Identity"
        assert cap.event_types == ("Hiring",)
        assert cap.emits_evidence_only is True
        assert cap.supports_incremental_sync is True
        assert cap.supports_historical is False
        assert cap.max_batch_size == 100
        assert cap.requires_authentication is False

    def test_create_enrichment(self):
        cap = ConnectorCapability(
            category="Enrichment",
            event_types=("Executive Hire",),
            emits_evidence_only=True,
            supports_incremental_sync=False,
            supports_historical=True,
            max_batch_size=500,
            requires_authentication=True,
        )
        assert cap.category == "Enrichment"
        assert cap.requires_authentication is True
        assert cap.max_batch_size == 500

    def test_frozen(self):
        cap = ConnectorCapability(category="Test")
        with pytest.raises(AttributeError):
            cap.category = "Other"  # type: ignore[misc]

    def test_multiple_event_types(self):
        cap = ConnectorCapability(
            category="Intent",
            event_types=("Hiring", "Funding", "Expansion"),
        )
        assert len(cap.event_types) == 3

    def test_empty_event_types(self):
        cap = ConnectorCapability(category="Test")
        assert cap.event_types == ()
