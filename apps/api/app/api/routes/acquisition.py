from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import DatabaseDep, SettingsDep
from app.repositories.acquisition import AcquisitionRepository
from app.schemas.acquisition import (
    AcquisitionAlertsResponse,
    AcquisitionAuditResponse,
    AcquisitionBenchmarksResponse,
    AcquisitionDailyReportResponse,
    AcquisitionDashboardResponse,
    ConnectorAuditResponse,
    ConnectorBenchmarkResponse,
)
from app.services.acquisition import AcquisitionService

router = APIRouter(prefix="/acquisition", tags=["acquisition"])


def get_acquisition_service(database: DatabaseDep, settings: SettingsDep) -> AcquisitionService:
    return AcquisitionService(AcquisitionRepository(database, settings), settings=settings)


AcquisitionServiceDep = Annotated[AcquisitionService, Depends(get_acquisition_service)]


@router.get("/dashboard", response_model=AcquisitionDashboardResponse)
async def acquisition_dashboard(service: AcquisitionServiceDep) -> AcquisitionDashboardResponse:
    dashboard = await service.dashboard()
    return AcquisitionDashboardResponse(
        overall_coverage_score=dashboard.overall_coverage_score,
        active_connectors=dashboard.active_connectors,
        healthy_connectors=dashboard.healthy_connectors,
        degraded_connectors=dashboard.degraded_connectors,
        down_connectors=dashboard.down_connectors,
        signals_24h=dashboard.signals_24h,
        companies_24h=dashboard.companies_24h,
        opportunities_24h=dashboard.opportunities_24h,
        high_value_opportunities_24h=dashboard.high_value_opportunities_24h,
        average_duplicate_rate=dashboard.average_duplicate_rate,
        average_failure_rate=dashboard.average_failure_rate,
        open_alerts=dashboard.open_alerts,
        connectors=[_audit_response(item.model_dump(mode="json")) for item in dashboard.connectors],
        leaderboard=[
            ConnectorBenchmarkResponse(**item.model_dump(mode="json")) for item in dashboard.leaderboard
        ],
        latest_daily_report=(
            dashboard.latest_daily_report.model_dump(mode="json") if dashboard.latest_daily_report else None
        ),
    )


@router.get("/audit", response_model=AcquisitionAuditResponse)
async def acquisition_audit(service: AcquisitionServiceDep) -> AcquisitionAuditResponse:
    payload = await service.audit()
    return AcquisitionAuditResponse(**payload)


@router.get("/benchmarks", response_model=AcquisitionBenchmarksResponse)
async def acquisition_benchmarks(service: AcquisitionServiceDep) -> AcquisitionBenchmarksResponse:
    payload = await service.benchmarks()
    return AcquisitionBenchmarksResponse(**payload)


@router.get("/alerts", response_model=AcquisitionAlertsResponse)
async def acquisition_alerts(service: AcquisitionServiceDep) -> AcquisitionAlertsResponse:
    payload = await service.alerts()
    return AcquisitionAlertsResponse(**payload)


@router.get("/reports/daily", response_model=AcquisitionDailyReportResponse)
async def acquisition_daily_report(service: AcquisitionServiceDep) -> AcquisitionDailyReportResponse:
    payload = await service.latest_report()
    if payload is None:
        raise HTTPException(status_code=404, detail="No daily acquisition report available yet.")
    return AcquisitionDailyReportResponse(report=payload)


@router.post("/reports/daily/generate", response_model=AcquisitionDailyReportResponse)
async def generate_daily_report(service: AcquisitionServiceDep) -> AcquisitionDailyReportResponse:
    report = await service.generate_daily_report()
    return AcquisitionDailyReportResponse(report=report.model_dump(mode="json"))


def _audit_response(item: dict[str, Any]) -> ConnectorAuditResponse:
    return ConnectorAuditResponse(
        source=str(item["source"]),
        enabled=bool(item["enabled"]),
        health_status=str(item["health_status"]),
        consecutive_failures=int(item["consecutive_failures"]),
        average_latency_ms=item.get("average_latency_ms"),
        last_success_at=item.get("last_success_at"),
        last_failure_at=item.get("last_failure_at"),
        last_error=item.get("last_error"),
        signals_collected_24h=int(item["signals_collected_24h"]),
        companies_discovered_24h=int(item["companies_discovered_24h"]),
        opportunities_produced_24h=int(item["opportunities_produced_24h"]),
        high_value_opportunities_24h=int(item["high_value_opportunities_24h"]),
        duplicate_rate_24h=float(item["duplicate_rate_24h"]),
        failure_rate_24h=float(item["failure_rate_24h"]),
        coverage_score=float(item["coverage_score"]),
        extraction_quality_avg=float(item["extraction_quality_avg"]),
    )
