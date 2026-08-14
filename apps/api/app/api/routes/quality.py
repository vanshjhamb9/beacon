from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.models.quality import QualityMetric, QualityReport
from app.repositories.quality import QualityRepository
from app.schemas.quality import (
    QualityDashboardResponse,
    QualityEventsResponse,
    QualityMetricResponse,
    QualityReportResponse,
    QualityReviewRequest,
    QualityReviewResponse,
    QualityRulesResponse,
    QualitySourcesResponse,
    QualityStatisticsResponse,
)
from app.services.quality import QualityService

router = APIRouter(prefix="/quality", tags=["quality"])


def get_quality_service(database: DatabaseDep) -> QualityService:
    return QualityService(QualityRepository(database))


QualityServiceDep = Annotated[QualityService, Depends(get_quality_service)]


@router.get("/events", response_model=QualityEventsResponse)
async def list_quality_events(
    service: QualityServiceDep,
    decision: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> QualityEventsResponse:
    reports = await service.list_reports(decision=decision, limit=limit, offset=offset)
    return QualityEventsResponse(events=[_report_response(report, []) for report in reports])


@router.get("/events/{event_id}", response_model=QualityReportResponse)
async def get_quality_event(event_id: UUID, service: QualityServiceDep) -> QualityReportResponse:
    report, metrics = await service.latest_event_report(event_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Quality report not found for event.")
    return _report_response(report, metrics)


@router.get("/sources", response_model=QualitySourcesResponse)
async def quality_sources(service: QualityServiceDep) -> QualitySourcesResponse:
    return QualitySourcesResponse(sources=await service.sources())


@router.get("/statistics", response_model=QualityStatisticsResponse)
async def quality_statistics(service: QualityServiceDep) -> QualityStatisticsResponse:
    return QualityStatisticsResponse(statistics=await service.statistics())


@router.get("/report", response_model=QualityReportResponse)
async def quality_report(report_id: UUID, service: QualityServiceDep) -> QualityReportResponse:
    report, metrics = await service.report_detail(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Quality report not found.")
    return _report_response(report, metrics)


@router.get("/rules", response_model=QualityRulesResponse)
async def quality_rules(service: QualityServiceDep) -> QualityRulesResponse:
    rules = await service.rules()
    return QualityRulesResponse(
        rules=[
            {
                "id": rule.id,
                "rule_key": rule.rule_key,
                "name": rule.name,
                "category": rule.category,
                "version": rule.version,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "threshold": rule.threshold,
                "weight": rule.weight,
                "parameters": rule.parameters,
            }
            for rule in rules
        ]
    )


@router.post("/review", response_model=QualityReviewResponse)
async def review_quality_event(
    payload: QualityReviewRequest,
    service: QualityServiceDep,
) -> QualityReviewResponse:
    try:
        feedback = await service.review(
            quality_report_id=payload.quality_report_id,
            reviewer=payload.reviewer,
            review_outcome=payload.review_outcome,
            corrected_decision=payload.corrected_decision,
            corrected_reason_codes=payload.corrected_reason_codes,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return QualityReviewResponse(
        id=feedback.id,
        quality_report_id=feedback.quality_report_id,
        raw_event_id=feedback.raw_event_id,
        reviewer=feedback.reviewer,
        review_outcome=feedback.review_outcome,
        corrected_decision=feedback.corrected_decision,
        corrected_reason_codes=feedback.corrected_reason_codes,
        notes=feedback.notes,
        created_at=feedback.created_at,
    )


@router.get("/dashboard", response_model=QualityDashboardResponse)
async def quality_dashboard(service: QualityServiceDep) -> QualityDashboardResponse:
    return QualityDashboardResponse(dashboard=await service.dashboard())


def _report_response(report: QualityReport, metrics: list[QualityMetric]) -> QualityReportResponse:
    return QualityReportResponse(
        id=report.id,
        raw_event_id=report.raw_event_id,
        source=report.source,
        decision=report.decision,
        grade=report.grade,
        schema_score=report.schema_score,
        spam_score=report.spam_score,
        trust_score=report.trust_score,
        freshness_score=report.freshness_score,
        completeness_score=report.completeness_score,
        entity_confidence_score=report.entity_confidence_score,
        duplicate_probability=report.duplicate_probability,
        overall_quality_score=report.overall_quality_score,
        processing_time_ms=report.processing_time_ms,
        queue_time_ms=report.queue_time_ms,
        reason_codes=report.reason_codes,
        explanation=report.explanation,
        created_at=report.created_at,
        metrics=[
            QualityMetricResponse(
                id=metric.id,
                stage=metric.stage,
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                passed=metric.passed,
                duration_ms=metric.duration_ms,
                reason_codes=metric.reason_codes,
                details=metric.details,
            )
            for metric in metrics
        ],
    )
