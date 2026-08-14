"""ARIE: Revenue Intelligence Engine - Database Models.

Replaces one-dimensional lead score with 12+ explainable scores.
Every score has evidence and confidence.
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


class RevenueScore(BaseModel):
    """Comprehensive revenue opportunity scores for a company.
    
    Replaces single account_score with 12+ explainable dimensions.
    """
    __tablename__ = "arie_revenue_scores"

    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    icp_profile_id = Column(UUID(as_uuid=True), ForeignKey("arie_icp_profiles.id"), nullable=True)
    
    # === 12 COMPONENT SCORES (0-100) ===
    
    # 1. ICP Score - How well does this company match our ideal customer?
    icp_score = Column(Float, default=0.0)
    icp_evidence = Column(JSON, default=list)
    icp_confidence = Column(Float, default=0.0)
    
    # 2. Technology Fit - How compatible is their tech stack with COMAI?
    technology_fit = Column(Float, default=0.0)
    technology_evidence = Column(JSON, default=list)
    technology_confidence = Column(Float, default=0.0)
    
    # 3. Growth Score - How fast is this company growing?
    growth_score = Column(Float, default=0.0)
    growth_evidence = Column(JSON, default=list)
    growth_confidence = Column(Float, default=0.0)
    
    # 4. Pain Score - How much pain are they experiencing?
    pain_score = Column(Float, default=0.0)
    pain_evidence = Column(JSON, default=list)
    pain_confidence = Column(Float, default=0.0)
    
    # 5. Intent Score - How likely are they to buy soon?
    intent_score = Column(Float, default=0.0)
    intent_evidence = Column(JSON, default=list)
    intent_confidence = Column(Float, default=0.0)
    
    # 6. Revenue Fit - Do they have budget and revenue potential?
    revenue_fit = Column(Float, default=0.0)
    revenue_evidence = Column(JSON, default=list)
    revenue_confidence = Column(Float, default=0.0)
    
    # 7. Decision Maker Score - Can we reach the right people?
    decision_maker_score = Column(Float, default=0.0)
    decision_maker_evidence = Column(JSON, default=list)
    decision_maker_confidence = Column(Float, default=0.0)
    
    # 8. Contact Quality - How verified and complete are contacts?
    contact_quality = Column(Float, default=0.0)
    contact_evidence = Column(JSON, default=list)
    contact_confidence = Column(Float, default=0.0)
    
    # 9. Urgency Score - How urgent is their need?
    urgency_score = Column(Float, default=0.0)
    urgency_evidence = Column(JSON, default=list)
    urgency_confidence = Column(Float, default=0.0)
    
    # 10. Automation Readiness - How ready are they for automation?
    automation_readiness = Column(Float, default=0.0)
    automation_evidence = Column(JSON, default=list)
    automation_confidence = Column(Float, default=0.0)
    
    # 11. AI Readiness - How ready are they for AI solutions?
    ai_readiness = Column(Float, default=0.0)
    ai_evidence = Column(JSON, default=list)
    ai_confidence = Column(Float, default=0.0)
    
    # 12. Support Complexity - How complex is their support operation?
    support_complexity = Column(Float, default=0.0)
    support_evidence = Column(JSON, default=list)
    support_confidence = Column(Float, default=0.0)
    
    # === COMPOSITE SCORES ===
    
    # Overall opportunity score (weighted average)
    overall_score = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    
    # Expected close probability (0-100%)
    close_probability = Column(Float, default=0.0)
    
    # Expected ARR (Annual Recurring Revenue)
    expected_arr = Column(Float, default=0.0)
    arr_confidence = Column(Float, default=0.0)
    
    # Expected payback period (months)
    expected_payback_months = Column(Integer, nullable=True)
    
    # Classification
    classification = Column(String(50), default="UNSCORED")  # HOT, WARM, COLD, UNSCORED
    
    # Scoring weights used
    weights_used = Column(JSON, default=dict)
    
    # Timestamps
    scored_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Scores decay
    
    __table_args__ = (
        Index("arie_revenue_scores_overall", "overall_score"),
        Index("arie_revenue_scores_classification", "classification"),
        Index("arie_revenue_scores_scored", "scored_at"),
        UniqueConstraint("company_id", "icp_profile_id", name="uq_revenue_score_company_icp"),
    )


class RevenueScoreExplanation(BaseModel):
    """Detailed explanation for each score component."""
    __tablename__ = "arie_revenue_score_explanations"

    score_id = Column(UUID(as_uuid=True), ForeignKey("arie_revenue_scores.id"), nullable=False)
    component = Column(String(100), nullable=False)  # icp_score, technology_fit, etc.
    score = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    weighted_score = Column(Float, nullable=False)
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)  # Human-readable explanation
    
    score_rel = relationship("RevenueScore", lazy="selectin")
    
    __table_args__ = (
        Index("arie_revenue_score_explanations_score", "score_id"),
        Index("arie_revenue_score_explanations_component", "component"),
    )


class RevenueScoreHistory(BaseModel):
    """Historical score changes for tracking improvement."""
    __tablename__ = "arie_revenue_score_history"

    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(255), nullable=False)
    overall_score = Column(Float, nullable=False)
    classification = Column(String(50), nullable=False)
    component_scores = Column(JSON, nullable=False)  # Snapshot of all 12
    change_delta = Column(Float, nullable=True)  # Change from previous
    change_reason = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("arie_revenue_score_history_company", "company_id"),
        Index("arie_revenue_score_history_date", "created_at"),
    )


class NegativeQualification(BaseModel):
    """Tracks why companies were rejected."""
    __tablename__ = "arie_negative_qualifications"

    company_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String(255), nullable=False)
    rejection_reason = Column(String(255), nullable=False)
    rejection_category = Column(String(100), nullable=False)  # enterprise, government, inactive, etc.
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    is_manual = Column(Boolean, default=False)
    
    __table_args__ = (
        Index("arie_negative_qualifications_domain", "domain"),
        Index("arie_negative_qualifications_reason", "rejection_reason"),
    )


class SalesCopilotPackage(BaseModel):
    """Generated sales intelligence for outreach."""
    __tablename__ = "arie_sales_copilot_packages"

    company_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String(255), nullable=False)
    icp_profile_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Why this company?
    why_this_company = Column(Text, nullable=True)
    
    # Why now?
    why_now = Column(Text, nullable=True)
    
    # Pain summary
    pain_summary = Column(JSON, default=list)
    
    # Technology summary
    technology_summary = Column(JSON, default=dict)
    
    # Growth summary
    growth_summary = Column(JSON, default=dict)
    
    # Recommended pitch
    recommended_pitch = Column(Text, nullable=True)
    
    # ROI estimate
    roi_estimate = Column(JSON, default=dict)  # {"monthly_savings": 5000, "roi": "300%"}
    
    # Outreach strategy
    outreach_strategy = Column(JSON, default=dict)
    # {
    #   "primary_channel": "email",
    #   "best_time": "Tuesday 10am IST",
    #   "personalization_angles": ["recent funding", "new product launch"]
    # }
    
    # Generated content
    email_draft = Column(Text, nullable=True)
    whatsapp_message = Column(Text, nullable=True)
    call_script = Column(Text, nullable=True)
    linkedin_message = Column(Text, nullable=True)
    
    # Follow-up plan
    follow_up_plan = Column(JSON, default=list)
    # [
    #   {"day": 1, "channel": "email", "action": "Initial outreach"},
    #   {"day": 3, "channel": "linkedin", "action": "Connection request"},
    #   {"day": 7, "channel": "whatsapp", "action": "Follow-up"}
    # ]
    
    # Competitive talking points
    competitive_points = Column(JSON, default=list)
    
    # Confidence
    confidence_score = Column(Float, default=0.0)
    
    __table_args__ = (
        Index("arie_sales_copilot_packages_company", "company_id"),
        Index("arie_sales_copilot_packages_domain", "domain"),
    )


class CampaignResult(BaseModel):
    """Tracks campaign outcomes for continuous learning."""
    __tablename__ = "arie_campaign_results"

    campaign_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String(255), nullable=False)
    
    # Outreach metrics
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    
    whatsapp_sent = Column(Integer, default=0)
    whatsapp_replied = Column(Integer, default=0)
    
    calls_made = Column(Integer, default=0)
    calls_connected = Column(Integer, default=0)
    
    linkedin_sent = Column(Integer, default=0)
    linkedin_replied = Column(Integer, default=0)
    
    # Outcome
    meetings_booked = Column(Integer, default=0)
    opportunities_created = Column(Integer, default=0)
    deals_won = Column(Integer, default=0)
    deals_lost = Column(Integer, default=0)
    reason_lost = Column(Text, nullable=True)
    
    # Timing
    time_to_first_reply = Column(Integer, nullable=True)  # Hours
    time_to_meeting = Column(Integer, nullable=True)  # Days
    time_to_close = Column(Integer, nullable=True)  # Days
    
    # Learning data
    icp_at_time = Column(JSON, nullable=True)  # ICP when this lead was scored
    score_at_time = Column(JSON, nullable=True)  # Scores when this lead was scored
    what_worked = Column(Text, nullable=True)
    what_didnt_work = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("arie_campaign_results_campaign", "campaign_id"),
        Index("arie_campaign_results_company", "company_id"),
        Index("arie_campaign_results_domain", "domain"),
    )


class LearningEvent(BaseModel):
    """Events that feed the continuous learning engine."""
    __tablename__ = "arie_learning_events"

    event_type = Column(String(100), nullable=False)  # campaign_result, feedback, correction
    entity_type = Column(String(100), nullable=False)  # company, icp, score
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # What was learned
    learning = Column(JSON, nullable=False)
    
    # Impact on scoring
    score_impact = Column(JSON, nullable=True)  # How scores changed
    
    # Source
    source = Column(String(255), nullable=True)  # campaign, manual, feedback
    
    # Applied
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("arie_learning_events_type", "event_type"),
        Index("arie_learning_events_entity", "entity_type", "entity_id"),
        Index("arie_learning_events_applied", "is_applied"),
    )
