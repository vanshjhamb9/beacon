from typing import Any

from sqlalchemy import Boolean, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ROIPEmailMetricsRow(BaseModel):
    __tablename__ = "roip_email_metrics"
    __table_args__ = (Index("ix_roip_email_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPSubjectPerformanceRow(BaseModel):
    __tablename__ = "roip_subject_performance"
    __table_args__ = (Index("ix_roip_subject_created", "created_at"),)

    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPCTAPerformanceRow(BaseModel):
    __tablename__ = "roip_cta_performance"
    __table_args__ = (Index("ix_roip_cta_created", "created_at"),)

    cta: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPFollowupPatternRow(BaseModel):
    __tablename__ = "roip_followup_patterns"
    __table_args__ = (Index("ix_roip_followup_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPIndustryMetricsRow(BaseModel):
    __tablename__ = "roip_industry_metrics"
    __table_args__ = (Index("ix_roip_industry_created", "created_at"),)

    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPFounderMetricsRow(BaseModel):
    __tablename__ = "roip_founder_metrics"
    __table_args__ = (Index("ix_roip_founder_created", "created_at"),)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPOfferMetricsRow(BaseModel):
    __tablename__ = "roip_offer_metrics"
    __table_args__ = (Index("ix_roip_offer_created", "created_at"),)

    offer: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPCaseStudyMetricsRow(BaseModel):
    __tablename__ = "roip_case_study_metrics"
    __table_args__ = (Index("ix_roip_case_created", "created_at"),)

    asset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPReplyAnalysisRow(BaseModel):
    __tablename__ = "roip_reply_analysis"
    __table_args__ = (Index("ix_roip_reply_created", "created_at"),)

    reply_id: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPLearningEventRow(BaseModel):
    __tablename__ = "roip_learning_events"
    __table_args__ = (Index("ix_roip_learning_created", "created_at"),)

    insight_type: Mapped[str] = mapped_column(String(64), nullable=False)
    modifies_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPRevenueBenchmarkRow(BaseModel):
    __tablename__ = "roip_revenue_benchmarks"
    __table_args__ = (Index("ix_roip_bench_created", "created_at"),)

    period: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")


class ROIPRecommendationRow(BaseModel):
    __tablename__ = "roip_recommendations"
    __table_args__ = (Index("ix_roip_recs_created", "created_at"),)

    recommendation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requires_founder_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    modifies_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(64), nullable=False, default="roip-v1")
