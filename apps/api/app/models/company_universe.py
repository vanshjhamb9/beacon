"""Company Universe model — Database of all known companies (not sales leads).

CRITICAL RULES:
1. Company Universe is a DATABASE, not a pipeline
2. Companies here have NOT necessarily shown buying intent
3. ICP match score indicates fit, NOT buying intent
4. Only companies with verified buying events move to sales pipeline
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CompanyUniverse(BaseModel):
    """Database of all known companies.
    
    This is NOT a sales pipeline. It's a database of companies we know about.
    Companies only enter the sales pipeline when they have verified buying events.
    """
    __tablename__ = "company_universe"
    __table_args__ = (
        Index("ix_company_universe_domain", "domain"),
        Index("ix_company_universe_industry", "industry"),
        Index("ix_company_universe_country", "country"),
        Index("ix_company_universe_source", "source"),
        Index("ix_company_universe_has_buying_event", "has_buying_event"),
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    icp_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    has_buying_event: Mapped[bool] = mapped_column(nullable=False, default=False)
    buying_event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
