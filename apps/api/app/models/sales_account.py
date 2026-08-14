from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SalesAccountRow(BaseModel):
    """Sales-ready account built from ecommerce lead."""

    __tablename__ = "sales_accounts"
    __table_args__ = (
        Index("ix_sales_accounts_domain", "domain", unique=True),
        Index("ix_sales_accounts_status", "status"),
        Index("ix_sales_accounts_score", "account_score"),
        Index("ix_sales_accounts_ecommerce_lead", "ecommerce_lead_id"),
    )

    ecommerce_lead_id: Mapped[str] = mapped_column(String(64), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(128), default="India", nullable=False)
    city: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    state: Mapped[str] = mapped_column(String(128), default="", nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="NEEDS_ENRICHMENT", nullable=False)
    primary_decision_maker: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    primary_email: Mapped[str] = mapped_column(String(320), default="", nullable=False)
    primary_phone: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    primary_linkedin: Mapped[str] = mapped_column(String(512), default="", nullable=False)

    shopify_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    woocommerce_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chatbot_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    crm_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    pain_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    growth_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    buying_intent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probability_to_buy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_potential: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    account_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completeness_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    decision_makers_json: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    contact_channels_json: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    buying_committee_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    health_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    score_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    organization_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Sprint 39: Full intelligence data
    technology_profile_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    pain_analysis_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    opportunity_score_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sales_summary_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    call_preparation_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    website_data_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    @property
    def technology_profile(self) -> dict:
        return self.technology_profile_json or {}

    @property
    def pain_analysis(self) -> dict:
        return self.pain_analysis_json or {}

    @property
    def opportunity_score(self) -> dict:
        return self.opportunity_score_json or {}

    @property
    def sales_summary(self) -> dict:
        return self.sales_summary_json or {}

    @property
    def call_preparation(self) -> dict:
        return self.call_preparation_json or {}
