"""Buying Event model - Two-Lane Architecture.

CRITICAL RULES:
1. Keywords are ONLY discovery triggers - they NEVER qualify a lead
2. The original source must prove an actual business problem
3. Generic emails are NOT decision-maker contacts
4. QUALITY > QUANTITY
5. Two lanes: COMAI and INOWIX with separate ICPs
6. 6-level classification system
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BuyingEventStatus(StrEnum):
    """Lifecycle status of a buying event."""
    DETECTED = "detected"
    VERIFIED = "verified"
    DISQUALIFIED = "disqualified"
    PROCESSED = "processed"


class BuyingEventDepartment(StrEnum):
    """Business unit lane."""
    COMAI = "COMAI"
    INOWIX = "INOWIX"


class BuyingEventClassification(StrEnum):
    """6-level classification system.
    
    Every company/event MUST receive exactly ONE classification.
    Never mix ICP with opportunity, pain with buying intent.
    """
    ACTIVE_BUYING_EVENT = "ACTIVE_BUYING_EVENT"    # Explicit commercial requirement exists
    VERIFIED_PAIN = "VERIFIED_PAIN"                 # Verified business problem (no explicit request)
    ICP_OPPORTUNITY = "ICP_OPPORTUNITY"             # Fits ICP but no verified pain
    PARTNER_OPPORTUNITY = "PARTNER_OPPORTUNITY"     # Agency with verified partnership potential
    NURTURE = "NURTURE"                             # Interesting but insufficient evidence
    REJECT = "REJECT"                               # Wrong ICP, competitor, irrelevant


class BusinessType(StrEnum):
    """Whether opportunity is direct customer or partner."""
    DIRECT_CUSTOMER = "DIRECT_CUSTOMER"
    PARTNER = "PARTNER"


class ContactType(StrEnum):
    """Contact quality classification."""
    DECISION_MAKER_DIRECT = "DECISION_MAKER_DIRECT"
    VERIFIED_WORK_EMAIL = "VERIFIED_WORK_EMAIL"
    LINKEDIN_DIRECT = "LINKEDIN_DIRECT"
    PLATFORM_DM = "PLATFORM_DM"
    GENERIC_COMPANY_EMAIL = "GENERIC_COMPANY_EMAIL"
    UNKNOWN = "UNKNOWN"


class FreshnessStatus(StrEnum):
    """Time-based eligibility."""
    CURRENT = "CURRENT"              # 0-7 days - eligible
    NEEDS_RESEARCH = "NEEDS_RESEARCH"  # 8-14 days - needs verification
    REJECT = "REJECT"                # >14 days - rejected


class OutreachChannel(StrEnum):
    """Available outreach channels."""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    REDDIT_DM = "reddit_dm"
    PLATFORM_DM = "platform_dm"


class BuyingEvent(BaseModel):
    """Verified buying event - Two-Lane Architecture.
    
    Two independent lanes: COMAI and INOWIX.
    6-level classification: ACTIVE_BUYING_EVENT, VERIFIED_PAIN, ICP_OPPORTUNITY,
                            PARTNER_OPPORTUNITY, NURTURE, REJECT.
    """
    __tablename__ = "buying_events"
    __table_args__ = (
        Index("ix_buying_events_department_status", "department", "status"),
        Index("ix_buying_events_company_name", "company_name"),
        Index("ix_buying_events_raw_event_id", "raw_event_id"),
        Index("ix_buying_events_created_at", "created_at"),
        Index("ix_buying_events_classification", "classification"),
        Index("ix_buying_events_freshness", "freshness"),
        Index("ix_buying_events_contact_type", "contact_type"),
        Index("ix_buying_events_business_type", "business_type"),
    )

    # Core fields
    raw_event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    department: Mapped[BuyingEventDepartment] = mapped_column(
        Enum(BuyingEventDepartment, name="buying_event_department"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=list)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_info: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    disqualifiers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=list)
    
    # Status
    status: Mapped[BuyingEventStatus] = mapped_column(
        Enum(BuyingEventStatus, name="buying_event_status"),
        default=BuyingEventStatus.DETECTED,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disqualified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disqualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Evidence-based fields
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_now: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_match: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outreach_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Two-Lane Architecture fields
    
    # 6-level classification (replaces old opportunity_type)
    classification: Mapped[BuyingEventClassification] = mapped_column(
        Enum(BuyingEventClassification, name="buying_event_classification"),
        default=BuyingEventClassification.REJECT,
        nullable=False,
    )
    
    # Business type (DIRECT_CUSTOMER or PARTNER)
    business_type: Mapped[BusinessType | None] = mapped_column(
        Enum(BusinessType, name="business_type"),
        nullable=True,
    )
    
    # Production hardening fields
    freshness: Mapped[FreshnessStatus] = mapped_column(
        Enum(FreshnessStatus, name="freshness_status"),
        default=FreshnessStatus.REJECT,
        nullable=False,
    )
    days_old: Mapped[int] = mapped_column(nullable=False, default=999)
    contact_type: Mapped[ContactType] = mapped_column(
        Enum(ContactType, name="contact_type"),
        default=ContactType.UNKNOWN,
        nullable=False,
    )
    is_high_contactability: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Two-lane specific fields
    
    # Pain signals (COMAI: support volume, slow response, etc.)
    pain_signals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=list)
    
    # Buying signals (INOWIX: looking for developers, need MVP, etc.)
    buying_signals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=list)
    
    # Partner signals (agencies, consultants)
    partner_signals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=list)
    
    # ICP match score (0.0-1.0)
    icp_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Outreach preparation (channel-specific drafts)
    outreach_preparation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=dict)
    
    # CTO 15-minute test result
    cto_test_result: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class OutreachDraft(BaseModel):
    """Channel-specific outreach draft for a buying event."""
    __tablename__ = "outreach_drafts"
    __table_args__ = (
        Index("ix_outreach_drafts_buying_event", "buying_event_id"),
        Index("ix_outreach_drafts_channel", "channel"),
        Index("ix_outreach_drafts_status", "status"),
    )

    buying_event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    channel: Mapped[OutreachChannel] = mapped_column(
        Enum(OutreachChannel, name="outreach_channel"),
        nullable=False,
    )
    style: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_points: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=list)
    evidence_chain: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=list)
    quality_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
