"""RDRP — Revenue Data Reliability Platform API routes.

Sprint 42.5: 8 REST endpoints for company verification, technology verification,
contact verification, readiness, reliability scoring, batch processing,
company detail, and dashboard.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rdrp", tags=["RDRP"])


# =============================================================================
# Request/Response Models
# =============================================================================
class CompanyVerifyRequest(BaseModel):
    company_id: str = Field(..., description="Canonical company ID")
    website: str = Field(..., description="Company website URL")
    html_content: str = Field("", description="Homepage HTML content")
    headers: dict[str, str] | None = Field(None, description="HTTP response headers")
    dna_data: dict[str, Any] | None = Field(None, description="Company DNA data for validation")
    decision_makers: list[dict[str, Any]] | None = Field(None, description="Decision maker records")
    emails: list[str] | None = Field(None, description="Email addresses to verify")
    phones: list[str] | None = Field(None, description="Phone numbers to verify")


class TechnologyVerifyRequest(BaseModel):
    company_id: str
    website: str
    html_content: str = ""
    headers: dict[str, str] | None = None


class ContactVerifyRequest(BaseModel):
    company_id: str
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)


class ReadinessRequest(BaseModel):
    company_id: str
    target_stage: str
    verification_passed: bool = True
    failure_reason: str | None = None


class ReliabilityRequest(BaseModel):
    company_id: str
    company_verification_score: float = 0.0
    technology_score: float = 0.0
    contact_score: float = 0.0
    evidence_count: int = 0
    evidence_reliability: float = 0.0
    freshness_hours: float = 168.0
    data_completeness: float = 0.0
    verification_checks_passed: int = 0
    verification_checks_total: int = 0


class BatchCompanyInput(BaseModel):
    company_id: str
    website: str
    html_content: str = ""
    headers: dict[str, str] | None = None
    dna_data: dict[str, Any] | None = None
    decision_makers: list[dict[str, Any]] | None = None
    emails: list[str] | None = None
    phones: list[str] | None = None


class BatchRequest(BaseModel):
    companies: list[BatchCompanyInput]


# =============================================================================
# Lazy-loaded orchestrator
# =============================================================================
_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        try:
            from packages.sales_intelligence_platform.engines.rdrp_engines import RDRPOrchestrator
            _orchestrator = RDRPOrchestrator()
        except ImportError:
            from sales_intelligence_platform.engines.rdrp_engines import RDRPOrchestrator
            _orchestrator = RDRPOrchestrator()
    return _orchestrator


def _to_dict(obj: Any) -> Any:
    """Convert dataclass to dict, handling nested dataclasses and datetimes."""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for k in obj.__dataclass_fields__:
            v = getattr(obj, k, None)
            if v is not None:
                result[k] = _to_dict(v)
        return result
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


# =============================================================================
# Endpoints
# =============================================================================
@router.post("/company/verify")
async def verify_company(req: CompanyVerifyRequest):
    """Full company verification: existence, tech, DNA, contacts, integrity, reliability."""
    orch = _get_orchestrator()
    result = orch.verify_company(
        company_id=req.company_id,
        website=req.website,
        html_content=req.html_content,
        headers=req.headers,
        dna_data=req.dna_data,
        decision_makers=req.decision_makers,
        emails=req.emails,
        phones=req.phones,
    )
    return _to_dict(result)


@router.post("/technology/verify")
async def verify_technology(req: TechnologyVerifyRequest):
    """Verify technology stack from website HTML."""
    orch = _get_orchestrator()
    result = orch.technology_verification.verify(
        company_id=req.company_id,
        website=req.website,
        html_content=req.html_content,
        headers=req.headers,
    )
    return _to_dict(result)


@router.post("/contact/verify")
async def verify_contacts(req: ContactVerifyRequest):
    """Verify emails and phones. Detect disposables, duplicates, role-based."""
    orch = _get_orchestrator()
    result = orch.contact_verification.verify(
        company_id=req.company_id,
        emails=req.emails,
        phones=req.phones,
    )
    return _to_dict(result)


@router.post("/readiness")
async def update_readiness(req: ReadinessRequest):
    """Update lead readiness pipeline stage."""
    orch = _get_orchestrator()
    result = orch.readiness.advance(
        company_id=req.company_id,
        target_stage=req.target_stage,
        verification_passed=req.verification_passed,
        failure_reason=req.failure_reason,
    )
    return _to_dict(result)


@router.post("/reliability")
async def calculate_reliability(req: ReliabilityRequest):
    """Calculate revenue reliability score."""
    orch = _get_orchestrator()
    result = orch.reliability_score.calculate(
        company_id=req.company_id,
        company_verification_score=req.company_verification_score,
        technology_score=req.technology_score,
        contact_score=req.contact_score,
        evidence_count=req.evidence_count,
        evidence_reliability=req.evidence_reliability,
        freshness_hours=req.freshness_hours,
        data_completeness=req.data_completeness,
        verification_checks_passed=req.verification_checks_passed,
        verification_checks_total=req.verification_checks_total,
    )
    return _to_dict(result)


@router.post("/batch")
async def batch_verify(req: BatchRequest):
    """Batch verify multiple companies through full RDRP pipeline."""
    orch = _get_orchestrator()
    results = []
    for company in req.companies:
        result = orch.verify_company(
            company_id=company.company_id,
            website=company.website,
            html_content=company.html_content,
            headers=company.headers,
            dna_data=company.dna_data,
            decision_makers=company.decision_makers,
            emails=company.emails,
            phones=company.phones,
        )
        results.append(_to_dict(result))

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("overall_passed")),
        "rejected": sum(1 for r in results if not r.get("overall_passed")),
        "results": results,
    }
    return summary


@router.get("/company/{company_id}")
async def get_company_rdrp(company_id: str):
    """Get RDRP verification state for a company."""
    orch = _get_orchestrator()
    readiness = orch.readiness.get_or_create(company_id)
    evidence = orch.evidence.get_evidence("company", company_id)
    return {
        "company_id": company_id,
        "readiness": _to_dict(orch.readiness._build_result(company_id, readiness)),
        "evidence_count": len(evidence),
        "evidence": _to_dict(evidence),
    }


@router.get("/dashboard")
async def rdrp_dashboard():
    """RDRP dashboard overview."""
    orch = _get_orchestrator()
    dashboard = orch.get_dashboard()
    evidence_all = orch.evidence.get_all()
    return {
        **dashboard,
        "evidence_by_type": {
            "company": sum(1 for e in evidence_all if e.entity_type == "company"),
            "technology": sum(1 for e in evidence_all if e.entity_type == "technology"),
            "contact": sum(1 for e in evidence_all if e.entity_type == "contact"),
            "integrity": sum(1 for e in evidence_all if e.entity_type == "integrity"),
        },
        "engines": {
            "company_verification": "active",
            "technology_verification": "active",
            "dna_validation": "active",
            "decision_maker_reliability": "active",
            "contact_verification": "active",
            "evidence_engine": "active",
            "confidence_engine": "active",
            "data_integrity": "active",
            "lead_readiness": "active",
            "reliability_score": "active",
        },
    }


@router.get("/metrics")
async def rdrp_metrics():
    """RDRP engine metrics."""
    orch = _get_orchestrator()
    return {
        "evidence_collected": orch.evidence.count(),
        "companies_tracked": len(orch.readiness._readiness),
        "engines_active": 10,
        "pipeline_stages": [
            "DISCOVERED", "NORMALIZED", "COMPANY_VERIFIED", "TECH_VERIFIED",
            "DNA_VERIFIED", "CONTACT_VERIFIED", "ICP_VERIFIED", "ARIE_ANALYZED",
            "RICVP_CALIBRATED", "SALES_READY", "OUTREACH_READY",
        ],
    }
