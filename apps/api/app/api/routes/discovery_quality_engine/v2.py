"""Discovery Quality Engine v2 API router — scoring, grading, and reports."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.services.discovery_quality_engine.v2 import DiscoveryQualityServiceV2

router = APIRouter(prefix="/quality/v2", tags=["discovery-quality-engine-v2"])

_service = DiscoveryQualityServiceV2()


@router.get("/evaluate")
async def evaluate(
    company_id: str,
    company_name: str,
    website: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    signal_type: str = "",
    signal_source: str = "",
    signal_title: str = "",
    signal_timestamp: str | None = None,
    signal_types: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    return await _service.evaluate_v2(
        company_id=company_id,
        company_name=company_name,
        website=website,
        industry=industry,
        country=country,
        signal_type=signal_type,
        signal_source=signal_source,
        signal_title=signal_title,
        signal_timestamp=signal_timestamp,
        signal_types=signal_types,
        domain=domain,
    )


@router.get("/score/{company_id}")
async def get_score(company_id: str) -> dict[str, Any]:
    return await _service.get_quality_score(company_id=company_id)


@router.get("/grade/{company_id}")
async def get_grade(company_id: str) -> dict[str, Any]:
    return await _service.get_quality_grade(company_id=company_id)


@router.get("/report/{company_id}")
async def get_report(company_id: str) -> dict[str, Any]:
    return await _service.get_quality_report(company_id=company_id)


@router.get("/reports")
async def list_reports(
    grade: str | None = None,
    decision: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    return await _service.list_quality_reports(
        grade=grade,
        decision=decision,
        limit=limit,
    )


@router.get("/scores/summary")
async def scores_summary() -> dict[str, Any]:
    return await _service.scores_summary()


@router.get("/grades/summary")
async def grades_summary() -> dict[str, Any]:
    return await _service.grades_summary()


@router.get("/freshness/v2")
async def freshness_v2() -> dict[str, Any]:
    return await _service.freshness_stats_v2()


@router.get("/buying-signals/v2")
async def buying_signals_v2() -> dict[str, Any]:
    return await _service.buying_signals_stats_v2()


@router.get("/audit/{company_id}")
async def audit_trail(company_id: str) -> dict[str, Any]:
    return await _service.get_audit_trail(company_id=company_id)
