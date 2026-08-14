"""ARIE: API Routes.

Endpoints for the AI Revenue Intelligence Engine.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DatabaseDep
from app.repositories.sales_account import SalesAccountRepository

router = APIRouter(prefix="/arie", tags=["ARIE"])


# === Request/Response Models ===

class ICPProfileCreate(BaseModel):
    """Request to create an ICP profile."""
    name: str
    description: Optional[str] = None
    industries: list[str] = []
    subcategories: list[str] = []
    business_models: list[str] = []
    countries: list[str] = []
    platforms: list[str] = []
    required_technologies: list[str] = []
    excluded_technologies: list[str] = []
    min_revenue: Optional[float] = None
    max_revenue: Optional[float] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    min_monthly_traffic: Optional[int] = None
    min_monthly_orders: Optional[int] = None
    min_avg_order_value: Optional[float] = None
    pain_categories: list[str] = []
    intent_signals: list[str] = []
    decision_maker_roles: list[str] = []
    negative_industries: list[str] = []
    negative_platforms: list[str] = []
    negative_countries: list[str] = []
    negative_keywords: list[str] = []
    min_score: float = 50.0


class ICPFromNaturalLanguage(BaseModel):
    """Request to generate ICP from natural language."""
    description: str = Field(..., description="Natural language description of ideal customer")
    industry: Optional[str] = None
    country: Optional[str] = None


class CompanyAnalysisRequest(BaseModel):
    """Request to analyze a company."""
    domain: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    platform: Optional[str] = None
    traffic: Optional[int] = None
    revenue: Optional[float] = None
    employees: Optional[int] = None
    icp_profile_id: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis."""
    domains: list[str]
    icp_profile_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response for company analysis."""
    domain: str
    company_name: str
    final_classification: str
    overall_score: float
    confidence: float
    icp_match: Optional[dict] = None
    growth_analysis: Optional[dict] = None
    intent_analysis: Optional[dict] = None
    revenue_score: Optional[dict] = None
    verified_contacts: Optional[dict] = None
    quality_report: Optional[dict] = None
    sales_package: Optional[dict] = None
    analysis_duration_ms: float = 0.0
    errors: list[str] = []


# === ICP Endpoints ===

@router.post("/icp/generate", summary="Generate ICP from natural language")
async def generate_icp(request: ICPFromNaturalLanguage):
    """Generate an ICP profile from natural language description.
    
    Example:
        "I sell AI WhatsApp automation for beauty brands in India"
    """
    from packages.sales_intelligence_platform.engines.arie_icp_engine import ARIEICPEngine
    
    engine = ARIEICPEngine()
    icp = engine.create_icp_from_natural_language(request.description)
    
    return {
        "name": icp.name,
        "description": icp.description,
        "industries": icp.industries,
        "subcategories": icp.subcategories,
        "business_models": icp.business_models,
        "countries": icp.countries,
        "platforms": icp.platforms,
        "pain_categories": icp.pain_categories,
        "intent_signals": icp.intent_signals,
        "decision_maker_roles": icp.decision_maker_roles,
        "min_monthly_traffic": icp.min_monthly_traffic,
        "min_monthly_orders": icp.min_monthly_orders,
        "min_avg_order_value": icp.min_avg_order_value,
    }


@router.get("/icp/templates", summary="Get ICP templates")
async def get_icp_templates():
    """Get pre-defined ICP templates for common niches."""
    from packages.sales_intelligence_platform.engines.arie_icp_engine import ARIEICPEngine
    
    engine = ARIEICPEngine()
    
    templates = []
    for key, template in engine.NICHE_TEMPLATES.items():
        templates.append({
            "id": f"template_{key}",
            "name": template.name,
            "industries": template.industries,
            "countries": template.countries,
            "platforms": template.platforms,
        })
    
    return {"templates": templates}


@router.post("/icp/match", summary="Match company against ICP")
async def match_company_icp(request: CompanyAnalysisRequest):
    """Match a company against an ICP profile."""
    from packages.sales_intelligence_platform.engines.arie_icp_engine import ARIEICPEngine, ICPProfileData
    
    engine = ARIEICPEngine()
    
    # Create ICP from request or use default
    icp = ICPProfileData(
        industries=request.industry.split(",") if request.industry else [],
        countries=[request.country] if request.country else [],
        platforms=[request.platform] if request.platform else [],
    )
    
    company_data = {
        "domain": request.domain,
        "industry": request.industry or "",
        "country": request.country or "",
        "platform": request.platform or "",
        "traffic": request.traffic or 0,
        "revenue_estimate": request.revenue or 0,
        "employees": request.employees or 0,
    }
    
    result = engine.match_company_against_icp(company_data, icp)
    
    return {
        "domain": result.company_domain,
        "icp_score": result.icp_score,
        "classification": result.classified_as,
        "confidence": result.confidence,
        "matched_criteria": result.matched_criteria,
        "unmatched_criteria": result.unmatched_criteria,
        "negative_match": result.negative_match,
        "negative_reason": result.negative_reason,
        "match_details": result.match_details,
    }


# === Analysis Endpoints ===

@router.post("/analyze", summary="Complete ARIE analysis")
async def analyze_company(request: CompanyAnalysisRequest):
    """Perform complete ARIE analysis for a company.
    
    Returns comprehensive analysis including:
    - ICP match score
    - Growth analysis
    - Intent analysis
    - Revenue opportunity score (12 components)
    - Contact verification
    - Quality assessment
    - Sales copilot package
    """
    from packages.sales_intelligence_platform.engines.arie_orchestrator import ARIEOrchestrator
    
    orchestrator = ARIEOrchestrator()
    
    company_data = {
        "domain": request.domain,
        "company_name": request.company_name or "",
        "industry": request.industry or "",
        "country": request.country or "",
        "platform": request.platform or "",
        "monthly_traffic": request.traffic or 0,
        "revenue_estimate": request.revenue or 0,
        "employee_estimate": request.employees or 0,
    }
    
    result = orchestrator.analyze_company(company_data)
    
    return {
        "domain": result.domain,
        "company_name": result.company_name,
        "final_classification": result.final_classification,
        "overall_score": result.overall_score,
        "confidence": result.confidence,
        "icp_match": result.icp_match.__dict__ if result.icp_match else None,
        "growth_analysis": result.growth_analysis.__dict__ if result.growth_analysis else None,
        "intent_analysis": result.intent_analysis.__dict__ if result.intent_analysis else None,
        "revenue_score": result.revenue_score.__dict__ if result.revenue_score else None,
        "verified_contacts": result.verified_contacts.__dict__ if result.verified_contacts else None,
        "quality_report": result.quality_report.__dict__ if result.quality_report else None,
        "sales_package": result.sales_package.__dict__ if result.sales_package else None,
        "analysis_duration_ms": result.analysis_duration_ms,
        "errors": result.errors,
    }


@router.post("/analyze/batch", summary="Batch analyze companies")
async def batch_analyze(request: BatchAnalysisRequest):
    """Analyze multiple companies at once."""
    from packages.sales_intelligence_platform.engines.arie_orchestrator import ARIEOrchestrator
    
    orchestrator = ARIEOrchestrator()
    
    companies = [{"domain": d} for d in request.domains]
    results = orchestrator.batch_analyze(companies)
    summary = orchestrator.get_summary(results)
    
    return {
        "summary": summary,
        "results": [
            {
                "domain": r.domain,
                "company_name": r.company_name,
                "classification": r.final_classification,
                "score": r.overall_score,
                "confidence": r.confidence,
            }
            for r in results
        ],
    }


# === Growth Endpoints ===

@router.post("/growth/analyze", summary="Analyze company growth")
async def analyze_growth(request: CompanyAnalysisRequest):
    """Analyze growth signals for a company."""
    from packages.sales_intelligence_platform.engines.arie_growth_engine import ARIEGrowthEngine
    
    engine = ARIEGrowthEngine()
    
    company_data = {
        "domain": request.domain,
        "monthly_traffic": request.traffic or 0,
        "revenue_estimate": request.revenue or 0,
        "employee_estimate": request.employees or 0,
    }
    
    result = engine.analyze_growth(company_data)
    
    return {
        "domain": result.domain,
        "growth_score": result.growth_score,
        "growth_rate": result.growth_rate,
        "growth_trend": result.growth_trend,
        "expansion_stage": result.expansion_stage,
        "confidence": result.confidence,
        "signals": [
            {
                "type": s.signal_type,
                "category": s.signal_category,
                "value": s.signal_value,
                "impact": s.impact_score,
            }
            for s in result.signals
        ],
        "recommendations": result.recommendations,
    }


# === Intent Endpoints ===

@router.post("/intent/analyze", summary="Analyze buying intent")
async def analyze_intent(request: CompanyAnalysisRequest):
    """Analyze buying intent for a company."""
    from packages.sales_intelligence_platform.engines.arie_intent_engine import ARIEIntentEngine
    
    engine = ARIEIntentEngine()
    
    company_data = {
        "domain": request.domain,
    }
    
    result = engine.analyze_intent(company_data)
    
    return {
        "domain": result.domain,
        "intent_score": result.intent_score,
        "intent_level": result.intent_level,
        "buying_timeframe": result.buying_timeframe,
        "confidence": result.confidence,
        "signals": [
            {
                "type": s.signal_type,
                "category": s.signal_category,
                "value": s.signal_value,
                "impact": s.impact_score,
            }
            for s in result.signals
        ],
        "recommendations": result.recommendations,
    }


# === Revenue Score Endpoints ===

@router.post("/revenue/score", summary="Calculate revenue score")
async def calculate_revenue_score(request: CompanyAnalysisRequest):
    """Calculate comprehensive revenue opportunity score."""
    from packages.sales_intelligence_platform.engines.arie_revenue_engine import ARIERevenueEngine
    
    engine = ARIERevenueEngine()
    
    company_data = {
        "domain": request.domain,
        "company_name": request.company_name or "",
        "revenue_estimate": request.revenue or 0,
        "monthly_traffic": request.traffic or 0,
        "employee_estimate": request.employees or 0,
    }
    
    result = engine.calculate_revenue_score(company_data)
    
    return {
        "domain": result.company_domain,
        "overall_score": result.overall_score,
        "classification": result.classification,
        "close_probability": result.close_probability,
        "expected_arr": result.expected_arr,
        "expected_payback_months": result.expected_payback_months,
        "components": {
            "icp": {"score": result.icp_score.score, "weighted": result.icp_score.weighted_score},
            "technology": {"score": result.technology_fit.score, "weighted": result.technology_fit.weighted_score},
            "growth": {"score": result.growth_score.score, "weighted": result.growth_score.weighted_score},
            "pain": {"score": result.pain_score.score, "weighted": result.pain_score.weighted_score},
            "intent": {"score": result.intent_score.score, "weighted": result.intent_score.weighted_score},
            "revenue": {"score": result.revenue_fit.score, "weighted": result.revenue_fit.weighted_score},
            "decision_maker": {"score": result.decision_maker_score.score, "weighted": result.decision_maker_score.weighted_score},
            "contact": {"score": result.contact_quality.score, "weighted": result.contact_quality.weighted_score},
        },
        "explanations": result.explanations,
    }


# === Quality Endpoints ===

@router.post("/quality/check", summary="Run quality checks")
async def run_quality_checks(request: CompanyAnalysisRequest):
    """Run quality checks on a company."""
    from packages.sales_intelligence_platform.engines.arie_quality_engine import ARIEQualityEngine
    
    engine = ARIEQualityEngine()
    
    company_data = {
        "domain": request.domain,
        "company_name": request.company_name or "",
        "industry": request.industry or "",
        "platform": request.platform or "",
        "monthly_traffic": request.traffic or 0,
        "product_count": 0,
    }
    
    result = engine.run_quality_checks(company_data)
    
    return {
        "domain": result.domain,
        "overall_quality_score": result.overall_quality_score,
        "quality_grade": result.quality_grade,
        "is_qualified": result.is_qualified,
        "disqualification_reasons": result.disqualification_reasons,
        "data_freshness": result.data_freshness,
        "confidence": result.confidence,
        "checks": [
            {
                "name": c.check_name,
                "passed": c.passed,
                "score": c.score,
                "severity": c.severity,
                "message": c.message,
            }
            for c in result.checks
        ],
        "recommendations": result.recommendations,
    }


# === Sales Copilot Endpoints ===

@router.post("/copilot/generate", summary="Generate sales package")
async def generate_sales_package(request: CompanyAnalysisRequest):
    """Generate comprehensive sales intelligence package."""
    from packages.sales_intelligence_platform.engines.arie_sales_copilot import ARIESalesCopilot
    
    copilot = ARIESalesCopilot()
    
    company_data = {
        "domain": request.domain,
        "company_name": request.company_name or "",
        "industry": request.industry or "",
        "monthly_traffic": request.traffic or 0,
        "revenue_estimate": request.revenue or 0,
    }
    
    result = copilot.generate_sales_package(company_data)
    
    return {
        "domain": result.domain,
        "company_name": result.company_name,
        "why_this_company": result.why_this_company,
        "why_now": result.why_now,
        "pain_summary": result.pain_summary,
        "technology_summary": result.technology_summary,
        "growth_summary": result.growth_summary,
        "recommended_pitch": result.recommended_pitch,
        "roi_estimate": result.roi_estimate,
        "outreach_strategy": result.outreach_strategy,
        "email_draft": result.email_draft,
        "whatsapp_message": result.whatsapp_message,
        "call_script": result.call_script,
        "linkedin_message": result.linkedin_message,
        "follow_up_plan": result.follow_up_plan,
        "competitive_points": result.competitive_points,
        "confidence_score": result.confidence_score,
    }


# === Dashboard Endpoints ===

@router.get("/dashboard/summary", summary="Get ARIE dashboard summary")
async def get_dashboard_summary():
    """Get summary statistics for the ARIE dashboard."""
    return {
        "total_companies": 0,
        "hot_leads": 0,
        "warm_leads": 0,
        "cold_leads": 0,
        "rejected": 0,
        "avg_score": 0,
        "avg_confidence": 0,
        "qualification_rate": 0,
        "top_icps": [],
        "recent_analyses": [],
    }


@router.get("/dashboard/pipeline", summary="Get pipeline view")
async def get_pipeline():
    """Get company pipeline grouped by classification."""
    return {
        "hot": [],
        "warm": [],
        "cold": [],
        "rejected": [],
        "unscored": [],
    }
