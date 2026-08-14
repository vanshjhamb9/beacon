"""API routes for Beacon Validation & Continuous Learning Platform."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseDep, SettingsDep
from app.services.validation_engine import ValidationService


def get_validation_service(
    database: DatabaseDep,
    settings: SettingsDep,
) -> ValidationService:
    return ValidationService(database, settings=settings)


ServiceDep = Annotated[ValidationService, Depends(get_validation_service)]

router = APIRouter(prefix="/validation", tags=["validation-engine"])


@router.get("/dashboard")
async def dashboard(service: ServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/replies")
async def replies(service: ServiceDep) -> dict[str, Any]:
    return await service.replies()


@router.get("/meetings")
async def meetings(service: ServiceDep) -> dict[str, Any]:
    return await service.meetings()


@router.get("/proposals")
async def proposals(service: ServiceDep) -> dict[str, Any]:
    return await service.proposals()


@router.get("/deals")
async def deals(service: ServiceDep) -> dict[str, Any]:
    return await service.deals()


@router.get("/connectors")
async def connectors(service: ServiceDep) -> dict[str, Any]:
    return await service.connectors()


@router.get("/industries")
async def industries(service: ServiceDep) -> dict[str, Any]:
    return await service.industries()


@router.get("/services")
async def services(service: ServiceDep) -> dict[str, Any]:
    return await service.services()


@router.get("/personas")
async def personas(service: ServiceDep) -> dict[str, Any]:
    return await service.personas()


@router.get("/triggers")
async def triggers(service: ServiceDep) -> dict[str, Any]:
    return await service.triggers()


@router.get("/revenue")
async def revenue(service: ServiceDep) -> dict[str, Any]:
    return await service.revenue()


@router.get("/reports/daily")
async def report_daily(service: ServiceDep) -> dict[str, Any]:
    return await service.report_daily()


@router.get("/reports/weekly")
async def report_weekly(service: ServiceDep) -> dict[str, Any]:
    return await service.report_weekly()


@router.get("/reports/monthly")
async def report_monthly(service: ServiceDep) -> dict[str, Any]:
    return await service.report_monthly()
