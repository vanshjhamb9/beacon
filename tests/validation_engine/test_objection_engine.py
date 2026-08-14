"""Tests for ObjectionEngine."""

from __future__ import annotations

import pytest

from validation_engine import OBJECTION_CATEGORIES
from validation_engine.objection_engine import ObjectionEngine


class TestObjectionEngineRecordObjection:
    def test_record_valid_objection(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget")
        assert event.company_id == "company_1"
        assert event.category == "no_budget"

    def test_record_invalid_category_raises(self, objection_engine: ObjectionEngine) -> None:
        with pytest.raises(ValueError, match="Invalid category"):
            objection_engine.record_objection("company_1", "invalid")

    def test_record_all_categories(self, objection_engine: ObjectionEngine) -> None:
        for category in OBJECTION_CATEGORIES:
            event = objection_engine.record_objection("company_1", category)
            assert event.category == category

    def test_record_with_industry(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget", industry="healthcare")
        assert event.industry == "healthcare"

    def test_record_with_service(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget", service="ai_automation")
        assert event.service == "ai_automation"

    def test_record_with_connector(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget", connector="linkedin")
        assert event.connector == "linkedin"

    def test_record_with_persona(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget", persona="founder")
        assert event.persona == "founder"


class TestObjectionEngineGetByCategory:
    def test_get_by_category_empty(self, objection_engine: ObjectionEngine) -> None:
        objections = objection_engine.get_by_category("no_budget")
        assert objections == []

    def test_get_by_category_filtered(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget")
        objection_engine.record_objection("company_2", "wrong_timing")
        objection_engine.record_objection("company_3", "no_budget")
        objections = objection_engine.get_by_category("no_budget")
        assert len(objections) == 2


class TestObjectionEngineGetByIndustry:
    def test_get_by_industry_empty(self, objection_engine: ObjectionEngine) -> None:
        objections = objection_engine.get_by_industry("healthcare")
        assert objections == []

    def test_get_by_industry_filtered(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", industry="healthcare")
        objection_engine.record_objection("company_2", "no_budget", industry="fintech")
        objections = objection_engine.get_by_industry("healthcare")
        assert len(objections) == 1


class TestObjectionEngineGetByService:
    def test_get_by_service_empty(self, objection_engine: ObjectionEngine) -> None:
        objections = objection_engine.get_by_service("ai_automation")
        assert objections == []

    def test_get_by_service_filtered(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", service="ai_automation")
        objection_engine.record_objection("company_2", "no_budget", service="crm")
        objections = objection_engine.get_by_service("ai_automation")
        assert len(objections) == 1


class TestObjectionEngineGetByConnector:
    def test_get_by_connector_filtered(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", connector="linkedin")
        objection_engine.record_objection("company_2", "no_budget", connector="email")
        objections = objection_engine.get_by_connector("linkedin")
        assert len(objections) == 1


class TestObjectionEngineGetByPersona:
    def test_get_by_persona_filtered(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", persona="founder")
        objection_engine.record_objection("company_2", "no_budget", persona="cto")
        objections = objection_engine.get_by_persona("founder")
        assert len(objections) == 1


class TestObjectionEngineGetTopObjections:
    def test_get_top_objections_empty(self, objection_engine: ObjectionEngine) -> None:
        top = objection_engine.get_top_objections()
        assert top == []

    def test_get_top_objections(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget")
        objection_engine.record_objection("company_2", "no_budget")
        objection_engine.record_objection("company_3", "no_budget")
        objection_engine.record_objection("company_4", "wrong_timing")
        top = objection_engine.get_top_objections(limit=2)
        assert len(top) == 2
        assert top[0]["category"] == "no_budget"
        assert top[0]["count"] == 3


class TestObjectionEngineCategoryCounts:
    def test_category_counts(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget")
        objection_engine.record_objection("company_2", "no_budget")
        objection_engine.record_objection("company_3", "wrong_timing")
        counts = objection_engine.get_category_counts()
        assert counts["no_budget"] == 2
        assert counts["wrong_timing"] == 1
