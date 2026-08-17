from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ComaiB2BPartnerRow(BaseModel):
    """COMAI B2B Partner Discovery — agency/consultant/partner database table."""

    __tablename__ = "comai_b2b_partners"
    __table_args__ = (
        Index("ix_comai_b2b_partners_agency_name", "agency_name", unique=True),
        Index("ix_comai_b2b_partners_partner_tier", "partner_tier"),
        Index("ix_comai_b2b_partners_client_access_score", "client_access_score"),
        Index("ix_comai_b2b_partners_comai_partner_fit", "comai_partner_fit"),
        Index("ix_comai_b2b_partners_country", "country"),
        Index("ix_comai_b2b_partners_agency_type", "agency_type"),
        Index("ix_comai_b2b_partners_partner_intent", "partner_intent"),
        Index("ix_comai_b2b_partners_final_verdict", "final_verdict"),
    )

    # Agency basics
    agency_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    agency_type: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    # marketing, technology, creative, consultant
    country: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    city: Mapped[str] = mapped_column(String(128), default="", nullable=False)

    # Decision maker
    founder_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    founder_role: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    identity_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Services & clients
    services: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    client_count_evidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    client_examples: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    client_industries: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Partner intent
    partner_intent: Mapped[str] = mapped_column(String(64), default="UNKNOWN", nullable=False)
    # EXPLICIT, HIGH_POTENTIAL, MEDIUM, LOW, REJECT, UNKNOWN
    partner_intent_evidence: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Scoring
    client_access_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    client_access_evidence: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    comai_partner_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    comai_fit_evidence: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Contact
    email: Mapped[str] = mapped_column(String(320), default="", nullable=False)
    email_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    # VERIFIED, PUBLIC_UNVERIFIED, INVALID, UNKNOWN
    email_evidence: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    phone: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    linkedin_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    contactability: Mapped[str] = mapped_column(String(32), default="NONE", nullable=False)
    # HIGH, MEDIUM, LOW, NONE
    contactability_evidence: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Classification
    partner_tier: Mapped[str] = mapped_column(String(16), default="C", nullable=False)
    # A, B, C
    final_verdict: Mapped[str] = mapped_column(String(32), default="NURTURE", nullable=False)
    # PARTNER_READY, OUTREACH_QUEUE, NURTURE, REJECT
    rejection_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Outreach
    recommended_pitch_angle: Mapped[str] = mapped_column(Text, default="", nullable=False)
    why_this_agency: Mapped[str] = mapped_column(Text, default="", nullable=False)
    client_overlap: Mapped[str] = mapped_column(Text, default="", nullable=False)
    comai_fit_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    partner_opportunity: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Safety
    competitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_clear: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    source: Mapped[str] = mapped_column(String(64), default="b2b_partner_extraction", nullable=False)
    discovery_source: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    evidence_audit: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
