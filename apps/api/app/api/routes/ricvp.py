"""RICVP: Revenue Intelligence Calibration & Validation Platform API."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ricvp", tags=["RICVP"])


# === Request Models ===

class ValidateCompanyRequest(BaseModel):
    """Request to validate a company."""
    company_id: str
    company_data: dict = {}


class CalibrateRequest(BaseModel):
    """Request to calibrate a score."""
    raw_score: float
    evidence_count: int = 0
    verified_count: int = 0
    conflicting_count: int = 0
    source_reliability: float = 0.5


class RevenueEstimateRequest(BaseModel):
    """Request for revenue estimation."""
    company_data: dict


class BuyingWindowRequest(BaseModel):
    """Request for buying window detection."""
    signals: dict = {}


class CompetitiveRequest(BaseModel):
    """Request for competitive analysis."""
    company_data: dict


class ConfidenceRequest(BaseModel):
    """Request for confidence calculation."""
    dimensions: dict = {}


class SalesOutcomeRequest(BaseModel):
    """Request to record a sales outcome."""
    company_id: str
    stage: str
    outcome: str = None
    lost_reason: str = None
    deal_value: float = None
    prediction_at_entry: float = None


class ICPOutcomeRequest(BaseModel):
    """Request to record ICP outcome."""
    company_id: str
    icp_id: str
    matched: bool
    qualified: bool
    meeting: bool = False
    deal: bool = False
    revenue: float = 0.0


# === API Endpoints ===

@router.post("/validate-company", summary="Full RICVP validation")
async def validate_company(request: ValidateCompanyRequest):
    """Perform full RICVP validation for a company."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import RICVPOrchestrator

    orchestrator = RICVPOrchestrator()
    result = orchestrator.validate_company(request.company_id, request.company_data)

    return result


@router.post("/validate", summary="Validate a specific field")
async def validate_field(company_id: str, field_name: str, value: str, sources: list[dict] = []):
    """Validate a specific field across sources."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import CrossSourceValidationEngine

    engine = CrossSourceValidationEngine()
    result = engine.validate_across_sources(field_name, sources)

    return {
        "company_id": company_id,
        "field": field_name,
        "value": value,
        "validation": result,
    }


@router.post("/calibrate", summary="Calibrate a score")
async def calibrate_score(request: CalibrateRequest):
    """Calibrate a raw score based on evidence quality."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import CalibrationEngine

    engine = CalibrationEngine()
    result = engine.calibrate_score(
        raw_score=request.raw_score,
        evidence_count=request.evidence_count,
        verified_count=request.verified_count,
        conflicting_count=request.conflicting_count,
        source_reliability=request.source_reliability,
    )

    return {
        "raw_score": result.raw_score,
        "calibrated_score": result.calibrated_score,
        "calibration_factor": result.calibration_factor,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "evidence_count": result.evidence_count,
    }


@router.post("/confidence", summary="Calculate confidence")
async def calculate_confidence(request: ConfidenceRequest):
    """Calculate multi-dimensional confidence."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import ConfidenceEngine

    engine = ConfidenceEngine()
    result = engine.calculate_confidence(request.dimensions)

    return result


@router.post("/buying-window", summary="Detect buying window")
async def detect_buying_window(request: BuyingWindowRequest):
    """Detect buying window from signals."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import BuyingWindowEngine

    engine = BuyingWindowEngine()
    result = engine.detect_buying_window(request.signals)

    return result


@router.post("/revenue-estimate", summary="Estimate revenue opportunity")
async def estimate_revenue(request: RevenueEstimateRequest):
    """Estimate revenue opportunity for COMAI."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import RevenueEstimationEngine

    engine = RevenueEstimationEngine()
    result = engine.estimate_opportunity(request.company_data)

    return result


@router.post("/competitive-analysis", summary="Analyze competition")
async def analyze_competition(request: CompetitiveRequest):
    """Analyze competitive landscape."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import CompetitiveIntelligenceEngine

    engine = CompetitiveIntelligenceEngine()
    result = engine.analyze_competition(request.company_data)

    return result


@router.post("/explain", summary="Generate explanation")
async def explain_score(company_data: dict, scores: dict):
    """Generate explainable intelligence for a score."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import ExplainableIntelligenceEngine

    engine = ExplainableIntelligenceEngine()
    result = engine.explain_score(company_data, scores)

    return result


@router.post("/sales-outcome", summary="Record sales outcome")
async def record_sales_outcome(request: SalesOutcomeRequest):
    """Record a sales outcome for learning."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import SalesOutcomeLearningEngine

    engine = SalesOutcomeLearningEngine()
    engine.record_outcome(
        company_id=request.company_id,
        stage=request.stage,
        outcome=request.outcome,
        lost_reason=request.lost_reason,
        deal_value=request.deal_value,
        prediction_at_entry=request.prediction_at_entry,
    )

    return {"status": "recorded", "company_id": request.company_id}


@router.post("/icp-outcome", summary="Record ICP outcome")
async def record_icp_outcome(request: ICPOutcomeRequest):
    """Record an ICP outcome for calibration."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import ICPCalibrationEngine

    engine = ICPCalibrationEngine()
    engine.record_outcome(
        company_id=request.company_id,
        icp_id=request.icp_id,
        matched=request.matched,
        qualified=request.qualified,
        meeting=request.meeting,
        deal=request.deal,
        revenue=request.revenue,
    )

    return {"status": "recorded", "company_id": request.company_id}


@router.get("/dashboard", summary="Get RICVP dashboard")
async def get_dashboard():
    """Get RICVP validation dashboard."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import (
        SalesOutcomeLearningEngine,
        ICPCalibrationEngine,
    )

    sales_engine = SalesOutcomeLearningEngine()
    icp_engine = ICPCalibrationEngine()

    return {
        "overall_data_quality": 0,
        "revenue_accuracy": 0,
        "confidence": 0,
        "calibration_accuracy": 0,
        "source_reliability": 0,
        "evidence_coverage": 0,
        "discovery_health": 0,
        "technology_accuracy": 0,
        "decision_maker_accuracy": 0,
        "contact_quality": 0,
        "buying_window": 0,
        "revenue_opportunity": 0,
        "icp_performance": icp_engine.get_icp_performance("default"),
        "conversion_metrics": sales_engine.get_conversion_metrics(),
    }


@router.get("/metrics", summary="Get RICVP metrics")
async def get_metrics():
    """Get RICVP accuracy metrics."""
    return {
        "precision": 0,
        "recall": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "calibration_error": 0,
        "prediction_accuracy": 0,
        "technology_accuracy": 0,
        "decision_maker_accuracy": 0,
        "contact_accuracy": 0,
        "icp_accuracy": 0,
        "revenue_prediction_accuracy": 0,
    }


@router.get("/calibration-history", summary="Get calibration history")
async def get_calibration_history(company_id: str = None, limit: int = 50):
    """Get calibration history."""
    return {"history": [], "total": 0}


@router.get("/evidence/{company_id}", summary="Get evidence for company")
async def get_evidence(company_id: str):
    """Get evidence trail for a company."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import EvidenceValidationEngine

    engine = EvidenceValidationEngine()
    result = engine.validate_company(company_id)

    return result


@router.get("/freshness/{company_id}", summary="Get freshness for company")
async def get_freshness(company_id: str):
    """Get data freshness for a company."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import FreshnessIntelligenceEngine

    engine = FreshnessIntelligenceEngine()
    result = engine.get_company_freshness(company_id)

    return result


@router.get("/drift/{company_id}", summary="Get data drift for company")
async def get_drift(company_id: str):
    """Get data drift for a company."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import DataDriftEngine

    engine = DataDriftEngine()
    result = engine.get_drift_summary(company_id)

    return result


@router.get("/learning", summary="Get learning summary")
async def get_learning():
    """Get continuous learning summary."""
    from packages.sales_intelligence_platform.engines.ricvp_engines import ContinuousLearningEngine

    engine = ContinuousLearningEngine()
    return engine.get_learning_summary()
