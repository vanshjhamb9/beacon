"""DSIP: API Routes.

Endpoints for the Discovery & Source Intelligence Platform.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/dsip", tags=["DSIP"])


# === Request/Response Models ===

class DiscoveryRequestModel(BaseModel):
    """Request for discovery."""
    icp_name: str = ""
    icp_profile: dict = {}
    country: str = ""
    industry: str = ""
    platform: str = ""
    revenue_min: float | None = None
    revenue_max: float | None = None
    max_sources: int = 10
    max_results_per_source: int = 100


class CSVUploadRequest(BaseModel):
    """CSV upload request."""
    csv_data: str
    icp_name: str = ""
    country: str = ""


class ManualCompanyRequest(BaseModel):
    """Manual company addition."""
    company_name: str
    domain: str
    industry: str = ""
    country: str = ""


# === Source Registry Endpoints ===

@router.get("/sources", summary="List all sources")
async def list_sources(
    category: str | None = Query(None),
    enabled_only: bool = Query(True),
):
    """List all registered discovery sources."""
    from packages.sales_intelligence_platform.engines.dsip_source_registry import SourceRegistry
    registry = SourceRegistry()
    sources = registry.list_sources(category=category, enabled_only=enabled_only)
    return {
        "sources": [
            {
                "source_id": s.source_id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "connector_type": s.connector_type,
                "priority": s.priority,
                "average_confidence": s.average_confidence,
                "cost_per_request": s.cost_per_request,
                "supported_countries": s.supported_countries,
                "supported_industries": s.supported_industries,
                "supported_platforms": s.supported_platforms,
                "status": s.status,
                "enabled": s.enabled,
            }
            for s in sources
        ],
        "total": len(sources),
    }


@router.get("/sources/{source_id}/health", summary="Get source health")
async def get_source_health(source_id: str):
    """Get health status of a source."""
    from packages.sales_intelligence_platform.engines.dsip_source_registry import SourceRegistry
    registry = SourceRegistry()
    health = registry.get_source_health(source_id)
    if not health:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {
        "source_id": health.source_id,
        "health_status": health.health_status,
        "health_score": health.health_score,
        "last_health_check": health.last_health_check.isoformat() if health.last_health_check else None,
        "last_successful_crawl": health.last_successful_crawl.isoformat() if health.last_successful_crawl else None,
        "consecutive_failures": health.consecutive_failures,
    }


@router.get("/sources/stats", summary="Get source statistics")
async def get_source_stats():
    """Get overall source registry statistics."""
    from packages.sales_intelligence_platform.engines.dsip_source_registry import SourceRegistry
    registry = SourceRegistry()
    return registry.get_registry_stats()


# === Discovery Endpoints ===

@router.post("/discover", summary="Run discovery")
async def run_discovery(request: DiscoveryRequestModel):
    """Run company discovery with ICP criteria."""
    from packages.sales_intelligence_platform.engines.dsip_orchestrator import DiscoveryOrchestrator, DiscoveryRequest

    orchestrator = DiscoveryOrchestrator()

    discovery_request = DiscoveryRequest(
        icp_name=request.icp_name,
        icp_profile=request.icp_profile,
        country=request.country,
        industry=request.industry,
        platform=request.platform,
        revenue_min=request.revenue_min,
        revenue_max=request.revenue_max,
        max_sources=request.max_sources,
        max_results_per_source=request.max_results_per_source,
    )

    result = await orchestrator.run_discovery(discovery_request)

    return {
        "total_discovered": result.total_discovered,
        "total_accepted": result.total_accepted,
        "total_rejected": result.total_rejected,
        "duration_ms": result.duration_ms,
        "sources_used": list(result.source_results.keys()),
        "companies": [
            {
                "company_name": c.company_name,
                "primary_domain": c.primary_domain,
                "industry": c.industry,
                "country": c.country,
                "confidence": c.confidence,
            }
            for c in result.accepted_companies[:50]
        ],
        "errors": result.errors,
    }


@router.post("/discover/preview", summary="Preview discovery plan")
async def preview_discovery(request: DiscoveryRequestModel):
    """Preview which sources would be selected without running discovery."""
    from packages.sales_intelligence_platform.engines.dsip_orchestrator import DiscoveryOrchestrator, DiscoveryRequest

    orchestrator = DiscoveryOrchestrator()

    discovery_request = DiscoveryRequest(
        icp_name=request.icp_name,
        icp_profile=request.icp_profile,
        country=request.country,
        industry=request.industry,
        platform=request.platform,
        revenue_min=request.revenue_min,
        revenue_max=request.revenue_max,
        max_sources=request.max_sources,
    )

    return orchestrator.preview_discovery(discovery_request)


@router.post("/discover/csv", summary="Upload CSV for discovery")
async def upload_csv(request: CSVUploadRequest):
    """Upload CSV data for company discovery."""
    from packages.sales_intelligence_platform.engines.connectors.connector_csv_upload import CSVUploadConnector

    connector = CSVUploadConnector(source_id="csv_upload")
    result = await connector.discover()

    # Parse CSV
    import csv
    import io
    reader = csv.DictReader(io.StringIO(request.csv_data))
    rows = list(reader)

    companies = await connector.extract(rows)

    return {
        "total_uploaded": len(rows),
        "total_extracted": len(companies),
        "companies": [
            {
                "company_name": c.company_name,
                "primary_domain": c.primary_domain,
                "industry": c.industry,
                "country": c.country,
                "confidence": c.confidence,
            }
            for c in companies
        ],
    }


@router.post("/discover/manual", summary="Add company manually")
async def add_manual_company(request: ManualCompanyRequest):
    """Manually add a company for analysis."""
    return {
        "status": "added",
        "company": {
            "company_name": request.company_name,
            "primary_domain": request.domain,
            "industry": request.industry,
            "country": request.country,
            "source": "manual",
            "confidence": 1.0,
        },
    }


# === Quality Endpoints ===

@router.post("/quality/check", summary="Run quality checks")
async def run_quality_checks(company_data: dict):
    """Run quality checks on a company."""
    from packages.sales_intelligence_platform.engines.dsip_quality_engine import DiscoveryQualityEngine

    engine = DiscoveryQualityEngine()
    report = engine.run_quality_checks(company_data)

    return {
        "company_id": report.company_id,
        "overall_score": report.overall_score,
        "quality_grade": report.quality_grade,
        "is_qualified": report.is_qualified,
        "checks": [
            {
                "name": c.check_name,
                "passed": c.passed,
                "score": c.score,
                "severity": c.severity,
                "message": c.message,
            }
            for c in report.checks
        ],
        "disqualification_reasons": report.disqualification_reasons,
        "recommendations": report.recommendations,
    }


# === Scoring Endpoints ===

@router.post("/score", summary="Calculate discovery score")
async def calculate_score(company_data: dict, context: dict = {}):
    """Calculate composite discovery score for a company."""
    from packages.sales_intelligence_platform.engines.dsip_scoring_engine import DiscoveryScoringEngine

    engine = DiscoveryScoringEngine()
    score = engine.calculate_score(company_data, context)

    return {
        "company_id": score.company_id,
        "discovery_score": score.discovery_score,
        "classification": score.classification,
        "qualified": score.qualified,
        "components": {
            "source_quality": score.source_quality,
            "evidence_quality": score.evidence_quality,
            "website_quality": score.website_quality,
            "technology_detection": score.technology_detection,
            "freshness": score.freshness,
            "company_completeness": score.company_completeness,
            "confidence": score.confidence,
            "activity": score.activity,
            "canonical_confidence": score.canonical_confidence,
        },
    }


# === Duplicate Detection Endpoints ===

class DuplicateDetectionRequest(BaseModel):
    """Request for duplicate detection."""
    companies: list[dict]
    threshold: float = 0.7


@router.post("/duplicates/detect", summary="Detect duplicates")
async def detect_duplicates(request: DuplicateDetectionRequest):
    """Detect duplicate companies."""
    from packages.sales_intelligence_platform.engines.dsip_duplicate_engine import DuplicateEngine

    engine = DuplicateEngine()
    matches = engine.find_duplicates(request.companies, request.threshold)

    return {
        "total_companies": len(request.companies),
        "duplicates_found": len(matches),
        "matches": [
            {
                "company_a": m.company_a_id,
                "company_b": m.company_b_id,
                "match_type": m.match_type,
                "confidence": m.confidence,
            }
            for m in matches
        ],
    }


# === Queue Endpoints ===

@router.get("/queue/stats", summary="Get queue statistics")
async def get_queue_stats():
    """Get queue statistics."""
    from packages.sales_intelligence_platform.engines.dsip_queue_manager import QueueManager

    manager = QueueManager()
    return manager.get_queue_stats()


@router.get("/queue/{queue_name}", summary="Get queue items")
async def get_queue_items(queue_name: str, limit: int = 10):
    """Get items from a queue."""
    from packages.sales_intelligence_platform.engines.dsip_queue_manager import QueueManager

    manager = QueueManager()
    items = manager.get_priority_items(queue_name, limit)
    return {
        "queue": queue_name,
        "items": [
            {
                "item_id": i.item_id,
                "priority": i.priority,
                "status": i.status,
                "queued_at": i.queued_at.isoformat(),
            }
            for i in items
        ],
    }


# === Observability Endpoints ===

@router.get("/metrics", summary="Get DSIP metrics")
async def get_metrics():
    """Get DSIP observability metrics."""
    from packages.sales_intelligence_platform.engines.dsip_observability import ObservabilityEngine

    engine = ObservabilityEngine()
    metrics = engine.get_metrics()
    health = engine.get_health()

    return {
        "health": health,
        "metrics": {
            "discovery_time_ms": metrics.discovery_time_ms,
            "companies_discovered": metrics.companies_discovered,
            "companies_accepted": metrics.companies_accepted,
            "companies_rejected": metrics.companies_rejected,
            "avg_quality_score": metrics.avg_quality_score,
            "qualification_rate": metrics.qualification_rate,
            "total_errors": metrics.total_errors,
            "total_cost": metrics.total_cost,
        },
    }


@router.get("/analytics", summary="Get discovery analytics")
async def get_analytics():
    """Get discovery analytics and trends."""
    return {
        "total_companies_discovered": 0,
        "total_companies_accepted": 0,
        "total_companies_rejected": 0,
        "avg_discovery_score": 0,
        "top_sources": [],
        "recent_jobs": [],
        "quality_distribution": {
            "A": 0, "B": 0, "C": 0, "D": 0, "F": 0,
        },
    }
