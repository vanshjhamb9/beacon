"""Objection engine — stores and categorizes objections.

Store only. Never auto-learn. Never automatically change scores.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import OBJECTION_CATEGORIES
from validation_engine.models import ObjectionEvent


class ObjectionEngine:
    """Records and categorizes objections. Analytics only — never modifies scores."""

    def __init__(self) -> None:
        self._objections: list[ObjectionEvent] = []
        self._by_category: dict[str, list[ObjectionEvent]] = {}
        self._by_industry: dict[str, list[ObjectionEvent]] = {}
        self._by_service: dict[str, list[ObjectionEvent]] = {}
        self._by_connector: dict[str, list[ObjectionEvent]] = {}
        self._by_persona: dict[str, list[ObjectionEvent]] = {}

    def record_objection(
        self,
        company_id: str,
        category: str,
        *,
        evidence: dict[str, Any] | None = None,
        industry: str = "",
        service: str = "",
        connector: str = "",
        persona: str = "",
    ) -> ObjectionEvent:
        if category not in OBJECTION_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {OBJECTION_CATEGORIES}")

        event = ObjectionEvent(
            company_id=company_id,
            category=category,
            timestamp=datetime.now(UTC),
            evidence=evidence or {},
            industry=industry,
            service=service,
            connector=connector,
            persona=persona,
        )
        self._objections.append(event)
        self._by_category.setdefault(category, []).append(event)
        if industry:
            self._by_industry.setdefault(industry, []).append(event)
        if service:
            self._by_service.setdefault(service, []).append(event)
        if connector:
            self._by_connector.setdefault(connector, []).append(event)
        if persona:
            self._by_persona.setdefault(persona, []).append(event)
        return event

    def get_all_objections(self) -> list[ObjectionEvent]:
        return list(self._objections)

    def get_by_category(self, category: str) -> list[ObjectionEvent]:
        return list(self._by_category.get(category, []))

    def get_by_industry(self, industry: str) -> list[ObjectionEvent]:
        return list(self._by_industry.get(industry, []))

    def get_by_service(self, service: str) -> list[ObjectionEvent]:
        return list(self._by_service.get(service, []))

    def get_by_connector(self, connector: str) -> list[ObjectionEvent]:
        return list(self._by_connector.get(connector, []))

    def get_by_persona(self, persona: str) -> list[ObjectionEvent]:
        return list(self._by_persona.get(persona, []))

    def get_top_objections(self, limit: int = 10) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for event in self._objections:
            counts[event.category] = counts.get(event.category, 0) + 1
        sorted_objections = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"category": cat, "count": cnt} for cat, cnt in sorted_objections[:limit]]

    def get_objection_rate_by_industry(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for industry, events in self._by_industry.items():
            result[industry] = len(events)
        return result

    def get_objection_rate_by_service(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for service, events in self._by_service.items():
            result[service] = len(events)
        return result

    def get_category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self._objections:
            counts[event.category] = counts.get(event.category, 0) + 1
        return counts
