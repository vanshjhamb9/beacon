"""ARIE: Company DNA Engine - Database Models.

Every company receives permanent memory with historical snapshots
and change logs. DNA updates continuously.
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


class CompanyDNA(BaseModel):
    """Permanent memory for every company.
    
    Stores business model, industry, revenue, employees, products,
    technology, pain, growth, AI maturity, and more.
    """
    __tablename__ = "arie_company_dna"

    company_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    domain = Column(String(255), nullable=False, index=True)
    
    # Business Model
    business_model = Column(String(100), nullable=True)  # d2c, b2c, b2b, marketplace
    industry = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    
    # Company Size
    revenue_estimate = Column(Float, nullable=True)
    revenue_currency = Column(String(10), default="USD")
    employee_estimate = Column(Integer, nullable=True)
    monthly_traffic = Column(Integer, nullable=True)
    monthly_orders = Column(Integer, nullable=True)
    avg_order_value = Column(Float, nullable=True)
    store_age_months = Column(Integer, nullable=True)
    
    # Products & Collections
    product_count = Column(Integer, nullable=True)
    collection_count = Column(Integer, nullable=True)
    price_range = Column(JSON, nullable=True)  # {"min": 100, "max": 5000}
    top_categories = Column(JSON, default=list)
    
    # Reviews & Reputation
    review_count = Column(Integer, nullable=True)
    review_growth_rate = Column(Float, nullable=True)  # Monthly %
    avg_rating = Column(Float, nullable=True)
    
    # Traffic & Growth
    traffic_trend = Column(String(50), nullable=True)  # growing, stable, declining
    traffic_growth_rate = Column(Float, nullable=True)
    traffic_sources = Column(JSON, default=dict)  # {"organic": 0.4, "paid": 0.3}
    
    # Social Media
    social_media = Column(JSON, default=dict)  # {"instagram": "url", "facebook": "url"}
    social_followers = Column(JSON, default=dict)
    social_growth_rate = Column(Float, nullable=True)
    
    # Geographic
    countries = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    international_presence = Column(Boolean, default=False)
    
    # Competitors
    competitors = Column(JSON, default=list)  # ["competitor1.com", "competitor2.com"]
    
    # Technology Stack
    technology_stack = Column(JSON, default=dict)  # {"shopify": true, "klaviyo": true}
    
    # Maturity Scores (0-100)
    ai_maturity = Column(Float, default=0.0)
    marketing_maturity = Column(Float, default=0.0)
    support_maturity = Column(Float, default=0.0)
    automation_maturity = Column(Float, default=0.0)
    ecommerce_maturity = Column(Float, default=0.0)
    
    # Expansion Stage
    expansion_stage = Column(String(50), nullable=True)  # startup, growth, scale, mature
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0)  # 0-100 (higher = more risk)
    risk_factors = Column(JSON, default=list)
    
    # Buying Probability
    buying_probability = Column(Float, default=0.0)  # 0-100
    buying_signals = Column(JSON, default=list)
    
    # ICP Match
    icp_match_score = Column(Float, default=0.0)  # 0-100
    icp_match_details = Column(JSON, default=dict)
    
    # Quality Metrics
    data_completeness = Column(Float, default=0.0)  # 0-100
    data_freshness = Column(DateTime, nullable=True)
    confidence_score = Column(Float, default=0.0)  # 0-100
    
    # Historical
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_enriched = Column(DateTime, nullable=True)
    enrichment_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index("arie_company_dna_domain", "domain"),
        Index("arie_company_dna_industry", "industry"),
        Index("arie_company_dna_icp_score", "icp_match_score"),
        Index("arie_company_dna_buying_prob", "buying_probability"),
    )


class CompanyDNASnapshot(BaseModel):
    """Historical snapshots of company DNA for change tracking."""
    __tablename__ = "arie_company_dna_snapshots"

    dna_id = Column(UUID(as_uuid=True), ForeignKey("arie_company_dna.id"), nullable=False)
    snapshot = Column(JSON, nullable=False)  # Full DNA state
    changes = Column(JSON, default=dict)  # What changed from previous
    change_type = Column(String(50), nullable=True)  # enrichment, update, correction
    
    dna = relationship("CompanyDNA", lazy="selectin")
    
    __table_args__ = (
        Index("arie_company_dna_snapshots_dna", "dna_id"),
        Index("arie_company_dna_snapshots_created", "created_at"),
    )


class CompanyDNAChangeLog(BaseModel):
    """Detailed change log for company DNA."""
    __tablename__ = "arie_company_dna_change_logs"

    dna_id = Column(UUID(as_uuid=True), ForeignKey("arie_company_dna.id"), nullable=False)
    field = Column(String(255), nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    source = Column(String(255), nullable=True)  # web_scraper, search_engine, manual
    confidence = Column(Float, nullable=True)
    
    dna = relationship("CompanyDNA", lazy="selectin")
    
    __table_args__ = (
        Index("arie_company_dna_change_logs_dna", "dna_id"),
        Index("arie_company_dna_change_logs_field", "field"),
    )


class CompanySignal(BaseModel):
    """Raw signals detected for a company."""
    __tablename__ = "arie_company_signals"

    company_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String(255), nullable=False)
    signal_type = Column(String(100), nullable=False)  # growth, pain, intent, technology
    signal_category = Column(String(100), nullable=True)  # hiring, funding, migration
    signal_value = Column(JSON, nullable=False)
    evidence = Column(JSON, default=list)  # URLs, snippets
    confidence = Column(Float, default=0.0)
    source = Column(String(255), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Intent signals decay
    is_verified = Column(Boolean, default=False)
    
    __table_args__ = (
        Index("arie_company_signals_company", "company_id"),
        Index("arie_company_signals_domain", "domain"),
        Index("arie_company_signals_type", "signal_type"),
        Index("arie_company_signals_detected", "detected_at"),
    )
