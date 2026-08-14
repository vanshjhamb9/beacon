from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RrpCompanyProfile(BaseModel):
    __tablename__ = "rrp_company_profiles"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    revenue_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sales_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trust: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    blockers: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    opportunity: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    decision_maker: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    contacts: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rrp-v1", nullable=False)


class RrpFounderReview(BaseModel):
    __tablename__ = "rrp_founder_reviews"

    company_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RrpDailyReport(BaseModel):
    __tablename__ = "rrp_daily_reports"

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    revenue_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vansh_ready_answer: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), default="rrp-v1", nullable=False)
