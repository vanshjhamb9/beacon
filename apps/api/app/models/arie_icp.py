"""ARIE: ICP Intelligence Engine - Database Models.

AI-powered Ideal Customer Profile management with versioning,
team sharing, and AI-assisted ICP generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index,
    Integer, JSON, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TimestampMixin


class ICPProfile(BaseModel):
    """Master ICP profile - the brain of the system.
    
    Users can create unlimited ICP profiles. Nothing is discovered
    before ICP matching.
    """
    __tablename__ = "arie_icp_profiles"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Industry & Vertical
    industries = Column(JSON, default=list)  # ["beauty", "skincare", "cosmetics"]
    subcategories = Column(JSON, default=list)  # ["organic beauty", "ayurveda"]
    business_models = Column(JSON, default=list)  # ["d2c", "marketplace", "b2c"]
    
    # Geographic
    countries = Column(JSON, default=list)  # ["India", "UAE", "USA"]
    states = Column(JSON, default=list)
    cities = Column(JSON, default=list)
    
    # Platform & Technology
    platforms = Column(JSON, default=list)  # ["shopify", "woocommerce"]
    required_technologies = Column(JSON, default=list)  # Must have these
    excluded_technologies = Column(JSON, default=list)  # Must NOT have these
    preferred_technologies = Column(JSON, default=list)  # Nice to have
    
    # Company Size
    min_revenue = Column(Float, nullable=True)  # In USD
    max_revenue = Column(Float, nullable=True)
    min_employees = Column(Integer, nullable=True)
    max_employees = Column(Integer, nullable=True)
    min_monthly_traffic = Column(Integer, nullable=True)
    max_monthly_traffic = Column(Integer, nullable=True)
    min_monthly_orders = Column(Integer, nullable=True)
    max_monthly_orders = Column(Integer, nullable=True)
    min_avg_order_value = Column(Float, nullable=True)
    max_avg_order_value = Column(Float, nullable=True)
    min_store_age_months = Column(Integer, nullable=True)
    
    # Growth Signals
    min_growth_rate = Column(Float, nullable=True)  # Monthly %
    min_traffic_growth = Column(Float, nullable=True)
    min_review_growth = Column(Float, nullable=True)
    hiring_signals = Column(JSON, default=list)  # ["marketing", "engineering"]
    funding_signals = Column(JSON, default=list)  # ["series_a", "series_b"]
    
    # Pain Signals
    pain_categories = Column(JSON, default=list)  # ["support", "marketing", "operations"]
    min_pain_score = Column(Float, nullable=True)
    
    # Buying Intent
    intent_signals = Column(JSON, default=list)  # ["technology_migration", "hiring"]
    min_intent_score = Column(Float, nullable=True)
    
    # Decision Makers
    decision_maker_roles = Column(JSON, default=list)  # ["founder", "ceo", "cmo"]
    min_decision_maker_confidence = Column(Float, nullable=True)
    
    # Scoring Weights
    icp_weight = Column(Float, default=0.15)
    technology_weight = Column(Float, default=0.20)
    growth_weight = Column(Float, default=0.10)
    pain_weight = Column(Float, default=0.15)
    intent_weight = Column(Float, default=0.15)
    revenue_weight = Column(Float, default=0.10)
    decision_maker_weight = Column(Float, default=0.10)
    contact_quality_weight = Column(Float, default=0.05)
    
    # Negative ICP (Exclusions)
    negative_industries = Column(JSON, default=list)  # ["government", "bank"]
    negative_platforms = Column(JSON, default=list)
    negative_countries = Column(JSON, default=list)
    negative_company_sizes = Column(JSON, default=list)  # ["enterprise"]
    negative_keywords = Column(JSON, default=list)  # ["amazon", "walmart"]
    
    # Thresholds
    min_score = Column(Float, default=50.0)  # Minimum score to be SALES_READY
    auto_qualify_score = Column(Float, default=80.0)  # Auto-qualify above this
    
    # Settings
    max_results_per_run = Column(Integer, default=100)
    refresh_interval_hours = Column(Integer, default=24)
    enable_auto_discovery = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    
    # Relationships
    versions = relationship("ICPProfileVersion", back_populates="profile", lazy="selectin")
    discoveries = relationship("ICPDiscovery", back_populates="profile", lazy="selectin")
    
    __table_args__ = (
        Index("arie_icp_profiles_owner", "owner_id"),
        Index("arie_icp_profiles_active", "is_active"),
        Index("arie_icp_profiles_industries", "industries", postgresql_using="gin"),
    )


class ICPProfileVersion(BaseModel):
    """Version history for ICP profiles."""
    __tablename__ = "arie_icp_profile_versions"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("arie_icp_profiles.id"), nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)  # Full ICP state at this version
    change_summary = Column(Text, nullable=True)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    
    profile = relationship("ICPProfile", back_populates="versions")
    
    __table_args__ = (
        UniqueConstraint("profile_id", "version", name="uq_icp_profile_version"),
    )


class ICPDiscovery(BaseModel):
    """Discovery jobs triggered by ICP profiles."""
    __tablename__ = "arie_icp_discoveries"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("arie_icp_profiles.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_found = Column(Integer, default=0)
    total_qualified = Column(Integer, default=0)
    total_rejected = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    config = Column(JSON, default=dict)  # Override settings for this run
    
    profile = relationship("ICPProfile", back_populates="discoveries")
    
    __table_args__ = (
        Index("arie_icp_discoveries_profile", "profile_id"),
        Index("arie_icp_discoveries_status", "status"),
    )


class ICPNiche(BaseModel):
    """Niche definitions for discovery."""
    __tablename__ = "arie_icp_niches"

    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("arie_icp_niches.id"), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)  # Search keywords for this niche
    platforms = Column(JSON, default=list)  # Common platforms in this niche
    typical_aov = Column(JSON, default=dict)  # {"min": 500, "max": 5000}
    typical_traffic = Column(JSON, default=dict)
    typical_employees = Column(JSON, default=dict)
    growth_rate = Column(Float, nullable=True)  # Industry growth %
    competition_level = Column(String(50), nullable=True)  # low, medium, high
    comai_fit = Column(Float, nullable=True)  # 0-100 COMAI fit score
    
    parent = relationship("ICPNiche", remote_side="ICPNiche.id", foreign_keys=[parent_id], lazy="raise")
    children = relationship("ICPNiche", back_populates="parent", lazy="raise")
    
    __table_args__ = (
        Index("arie_icp_niches_slug", "slug"),
        Index("arie_icp_niches_parent", "parent_id"),
    )


class ICPAITemplate(BaseModel):
    """AI-generated ICP templates."""
    __tablename__ = "arie_icp_ai_templates"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)  # User's natural language input
    generated_icp = Column(JSON, nullable=False)  # Generated ICP config
    industry = Column(String(255), nullable=True)
    use_case = Column(String(255), nullable=True)  # "whatsapp_automation", "ai_chatbot"
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Float, nullable=True)
    
    __table_args__ = (
        Index("arie_icp_ai_templates_industry", "industry"),
        Index("arie_icp_ai_templates_public", "is_public"),
    )
