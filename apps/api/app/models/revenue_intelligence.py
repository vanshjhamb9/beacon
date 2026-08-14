from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RevenueIntelligenceRow(BaseModel):
    """Revenue intelligence analysis result for an ecommerce lead."""

    __tablename__ = "revenue_intelligence"
    __table_args__ = (
        Index("ix_revenue_intelligence_domain", "domain", unique=True),
        Index("ix_revenue_intelligence_priority", "priority"),
        Index("ix_revenue_intelligence_probability", "probability_to_buy"),
        Index("ix_revenue_intelligence_icp", "icp_match"),
        Index("ix_revenue_intelligence_ecommerce_lead", "ecommerce_lead_id"),
    )

    ecommerce_lead_id: Mapped[str] = mapped_column(String(64), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(128), default="India", nullable=False)

    # Pain
    pain_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pain_signals: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Growth
    growth_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    growth_signals: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Buying Intent
    buying_intent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    intent_signals: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Technology Gap
    technology_gap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tech_gaps: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Support Gap
    support_gap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    support_gaps: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # ICP
    icp_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icp_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    icp_reasons: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    rejection_reasons: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Revenue & Probability
    revenue_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probability_to_buy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probability_reasons: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Summary
    why_comai: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recommended_pitch: Mapped[str] = mapped_column(Text, default="", nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="REJECT", nullable=False)

    # Signal Scores
    traffic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    review_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    social_growth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    whatsapp_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    founder_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Evidence
    evidence_json: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
