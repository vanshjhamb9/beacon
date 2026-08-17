"""COMAI B2B Partner Leads — ORM Model.

Stores discovered agency/partner leads for the COMAI B2B Partner Acquisition Engine.
Separate from buying_events, ecommerce_leads, and sales_accounts.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class PartnerLead(Base, TimestampMixin, SoftDeleteMixin):
    """A discovered agency/partner lead for COMAI B2B partner acquisition."""

    __tablename__ = "partner_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ──────────────────────────────────────────────
    agency_name: Mapped[str] = mapped_column(String(500), nullable=False)
    agency_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)
    agency_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employees: Mapped[str | None] = mapped_column(String(100), nullable=True)
    founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Clients & Revenue ─────────────────────────────────────
    clients: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue_generated: Mapped[str | None] = mapped_column(String(500), nullable=True)
    revenue_managed: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notable_clients: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notable_results: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # ── Decision Makers ───────────────────────────────────────
    decision_maker: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decision_maker_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision_makers: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # ── Contact ───────────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    contactability: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Services & Certifications ─────────────────────────────
    services: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # ── Scoring ───────────────────────────────────────────────
    tier: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A, B, C
    client_access_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comai_fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Analysis ──────────────────────────────────────────────
    why_this_agency: Mapped[str | None] = mapped_column(Text, nullable=True)
    comai_fit: Mapped[str | None] = mapped_column(Text, nullable=True)
    pitch_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Status & Pipeline ─────────────────────────────────────
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, default="NEW")
    # NEW → CONTACTED → RESPONSE_RECEIVED → MEETING_SCHEDULED → PARTNERED → REJECTED
    outreach_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    outreach_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    meeting_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    partner_converted: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Evidence & Metadata ───────────────────────────────────
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(50), nullable=True, default="comai_b2b")
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
