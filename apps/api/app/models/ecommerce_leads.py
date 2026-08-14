from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EcommerceLeadRow(BaseModel):
    """Ecommerce lead database table."""

    __tablename__ = "ecommerce_leads"
    __table_args__ = (
        Index("ix_ecommerce_leads_domain", "domain", unique=True),
        Index("ix_ecommerce_leads_country_state", "country", "state"),
        Index("ix_ecommerce_leads_platform", "platform"),
        Index("ix_ecommerce_leads_score", "comai_score"),
        Index("ix_ecommerce_leads_priority", "lead_priority"),
        Index("ix_ecommerce_leads_category", "category"),
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    industry: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(128), default="India", nullable=False)
    city: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    state: Mapped[str] = mapped_column(String(128), default="", nullable=False)

    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_size: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    social_links: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    instagram_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    facebook_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)

    owner_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    founder_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    decision_maker_role: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(320), default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    contact_source: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    contact_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    shopify_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    woocommerce_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    magento_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chatbot_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    crm_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    comai_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lead_priority: Mapped[str] = mapped_column(String(32), default="LOW", nullable=False)
    sales_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pain_points: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    source: Mapped[str] = mapped_column(String(64), default="", nullable=False)
