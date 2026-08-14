"""Normalize incoming live events before classification."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LiveEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1)
    url: str
    discovered_at: datetime
    headline: str = Field(min_length=1)
    category: str | None = None
    confidence: float = Field(default=50.0, ge=0, le=100)


class LiveEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    company_name: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    description: str = ""
    source: str = Field(min_length=1)
    url: str
    event_timestamp: datetime
    evidence: tuple[LiveEvidence, ...]
    company_size: int | None = Field(default=None, ge=0)
    funding_amount: float | None = Field(default=None, ge=0)
    has_decision_maker: bool = False
    revenue_potential: float | None = Field(default=None, ge=0, le=100)
    competition: float | None = Field(default=None, ge=0, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoveryRouter:
    def normalize(self, payload: dict[str, Any]) -> LiveEvent:
        evidence = tuple(payload.get("evidence") or ())
        if not evidence:
            evidence = (
                {
                    "source": payload["source"],
                    "url": payload["url"],
                    "discovered_at": payload["event_timestamp"],
                    "headline": payload["headline"],
                    "confidence": payload.get("confidence", 50.0),
                },
            )
        return LiveEvent(
            company_name=str(payload["company_name"]).strip(),
            headline=str(payload["headline"]).strip(),
            description=str(payload.get("description") or "").strip(),
            source=str(payload["source"]).strip(),
            url=str(payload["url"]).strip(),
            event_timestamp=payload["event_timestamp"],
            evidence=tuple(LiveEvidence.model_validate(item) for item in evidence),
            company_size=payload.get("company_size"),
            funding_amount=payload.get("funding_amount"),
            has_decision_maker=bool(payload.get("has_decision_maker", False)),
            revenue_potential=payload.get("revenue_potential"),
            competition=payload.get("competition"),
            metadata=dict(payload.get("metadata") or {}),
        )
