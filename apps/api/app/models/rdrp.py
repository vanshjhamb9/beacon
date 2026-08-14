"""RDRP — Revenue Data Reliability Platform database models.

Sprint 42.5: 10 tables for company verification, technology verification,
contact verification, DNA validation, evidence, confidence, integrity,
readiness pipeline, reliability scoring, and verification history.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# 1. Company Verification
# =============================================================================
class RdrpCompanyVerification(BaseModel):
    __tablename__ = "rdrp_company_verification"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    website_alive = Column(Boolean, default=False)
    https_valid = Column(Boolean, default=False)
    homepage_loads = Column(Boolean, default=False)
    about_page_exists = Column(Boolean, default=False)
    contact_page_exists = Column(Boolean, default=False)
    products_exist = Column(Boolean, default=False)
    collection_pages_exist = Column(Boolean, default=False)
    checkout_exists = Column(Boolean, default=False)
    privacy_policy_exists = Column(Boolean, default=False)
    refund_policy_exists = Column(Boolean, default=False)
    terms_exists = Column(Boolean, default=False)
    shipping_policy_exists = Column(Boolean, default=False)
    gst_info_present = Column(Boolean, default=False)
    country_detected = Column(String(100), nullable=True)
    active_ecommerce_store = Column(Boolean, default=False)
    domain_age_days = Column(Integer, nullable=True)
    last_website_update = Column(DateTime(timezone=True), nullable=True)
    store_language = Column(String(50), nullable=True)
    store_currency = Column(String(10), nullable=True)
    mobile_responsive = Column(Boolean, default=False)
    verification_score = Column(Float, default=0.0)
    verification_confidence = Column(Float, default=0.0)
    verification_failures = Column(JSONB, nullable=True)
    checks_passed = Column(Integer, default=0)
    checks_total = Column(Integer, default=0)
    evidence = Column(JSONB, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    record_version = Column(Integer, default=1)


# =============================================================================
# 2. Technology Verification
# =============================================================================
class RdrpTechnologyVerification(BaseModel):
    __tablename__ = "rdrp_technology_verification"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    technology = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    tech_version = Column(String(50), nullable=True)
    detected = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    evidence_type = Column(String(50), nullable=True)
    evidence_url = Column(String(1000), nullable=True)
    evidence_snapshot = Column(Text, nullable=True)
    script_pattern = Column(String(500), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    detection_method = Column(String(50), nullable=True)
    version_detected = Column(Boolean, default=False)
    source_id = Column(String(100), nullable=True)
    record_version = Column(Integer, default=1)


# =============================================================================
# 3. Company DNA Validation
# =============================================================================
class RdrpCompanyDnaValidation(BaseModel):
    __tablename__ = "rdrp_company_dna_validation"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text, nullable=True)
    value_numeric = Column(Float, nullable=True)
    confidence = Column(Float, default=0.0)
    evidence = Column(JSONB, nullable=True)
    source = Column(String(100), nullable=True)
    source_url = Column(String(1000), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=False)
    previous_value = Column(Text, nullable=True)
    value_changed = Column(Boolean, default=False)
    record_version = Column(Integer, default=1)


# =============================================================================
# 4. Contact Verification (Decision Makers + Contacts)
# =============================================================================
class RdrpContactVerification(BaseModel):
    __tablename__ = "rdrp_contact_verification"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contact_type = Column(String(50), nullable=False)  # decision_maker, email, phone
    full_name = Column(String(255), nullable=True)
    designation = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    phone_country = Column(String(10), nullable=True)
    phone_type = Column(String(50), nullable=True)  # mobile, landline, business
    is_whatsapp = Column(Boolean, default=False)
    linkedin_url = Column(String(500), nullable=True)
    evidence_url = Column(String(1000), nullable=True)
    evidence_snapshot = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50), nullable=True)
    is_disposable = Column(Boolean, default=False)
    is_role_based = Column(Boolean, default=False)
    is_catch_all = Column(Boolean, default=False)
    is_corporate = Column(Boolean, default=False)
    deliverability = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=True)
    reachability_score = Column(Float, default=0.0)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(UUID(as_uuid=True), nullable=True)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    last_verified = Column(DateTime(timezone=True), nullable=False)
    record_version = Column(Integer, default=1)


# =============================================================================
# 5. Evidence
# =============================================================================
class RdrpEvidence(BaseModel):
    __tablename__ = "rdrp_evidence"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # company, technology, contact, dna
    entity_id = Column(String(100), nullable=True)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=False)  # html, header, script, screenshot, url
    evidence_url = Column(String(1000), nullable=True)
    evidence_snapshot = Column(Text, nullable=True)
    evidence_hash = Column(String(64), nullable=True)
    source_id = Column(String(100), nullable=True)
    source_reliability = Column(Float, default=0.5)
    confidence = Column(Float, default=0.0)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    record_version = Column(Integer, default=1)


# =============================================================================
# 6. Confidence
# =============================================================================
class RdrpConfidence(BaseModel):
    __tablename__ = "rdrp_confidence"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True)
    field_name = Column(String(100), nullable=False)
    confidence = Column(Float, default=0.0)
    confidence_grade = Column(String(5), nullable=True)
    factors = Column(JSONB, nullable=True)
    source_count = Column(Integer, default=0)
    source_reliability_avg = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    verification_success = Column(Boolean, default=False)
    historical_consistency = Column(Float, default=0.0)
    evidence_quality = Column(Float, default=0.0)
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    record_version = Column(Integer, default=1)


# =============================================================================
# 7. Data Integrity
# =============================================================================
class RdrpIntegrity(BaseModel):
    __tablename__ = "rdrp_integrity"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    check_type = Column(String(100), nullable=False)
    check_name = Column(String(255), nullable=False)
    passed = Column(Boolean, default=False)
    severity = Column(String(20), nullable=False)  # critical, warning, info
    details = Column(JSONB, nullable=True)
    affected_fields = Column(JSONB, nullable=True)
    recommendation = Column(Text, nullable=True)
    auto_fixable = Column(Boolean, default=False)
    auto_fixed = Column(Boolean, default=False)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    record_version = Column(Integer, default=1)


# =============================================================================
# 8. Lead Readiness Pipeline
# =============================================================================
class RdrpReadiness(BaseModel):
    __tablename__ = "rdrp_readiness"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    current_stage = Column(String(50), nullable=False, default="DISCOVERED")
    stage_history = Column(JSONB, nullable=True)
    discovered_at = Column(DateTime(timezone=True), nullable=True)
    normalized_at = Column(DateTime(timezone=True), nullable=True)
    company_verified_at = Column(DateTime(timezone=True), nullable=True)
    tech_verified_at = Column(DateTime(timezone=True), nullable=True)
    dna_verified_at = Column(DateTime(timezone=True), nullable=True)
    contact_verified_at = Column(DateTime(timezone=True), nullable=True)
    icp_verified_at = Column(DateTime(timezone=True), nullable=True)
    arie_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    ricvp_calibrated_at = Column(DateTime(timezone=True), nullable=True)
    sales_ready_at = Column(DateTime(timezone=True), nullable=True)
    outreach_ready_at = Column(DateTime(timezone=True), nullable=True)
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    block_reason = Column(String(255), nullable=True)
    stages_passed = Column(Integer, default=0)
    stages_total = Column(Integer, default=12)
    readiness_score = Column(Float, default=0.0)
    record_version = Column(Integer, default=1)


# =============================================================================
# 9. Revenue Reliability Score
# =============================================================================
class RdrpReliabilityScore(BaseModel):
    __tablename__ = "rdrp_reliability_score"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    overall_score = Column(Float, default=0.0)
    overall_grade = Column(String(20), nullable=True)  # Reliable, Likely Reliable, Needs Review, Reject
    company_trust = Column(Float, default=0.0)
    technology_trust = Column(Float, default=0.0)
    contact_trust = Column(Float, default=0.0)
    evidence_trust = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    data_completeness = Column(Float, default=0.0)
    verification_success = Column(Float, default=0.0)
    historical_stability = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    component_details = Column(JSONB, nullable=True)
    score_breakdown = Column(JSONB, nullable=True)
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    model_version = Column(String(20), default="v1")
    record_version = Column(Integer, default=1)


# =============================================================================
# 10. Verification History
# =============================================================================
class RdrpVerificationHistory(BaseModel):
    __tablename__ = "rdrp_verification_history"

    canonical_company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    verification_type = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)  # started, passed, failed, updated
    previous_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)
    score_delta = Column(Float, nullable=True)
    details = Column(JSONB, nullable=True)
    triggered_by = Column(String(50), nullable=True)  # auto, manual, schedule
    triggered_by_user = Column(String(100), nullable=True)
    record_version = Column(Integer, default=1)
