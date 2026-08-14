from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.dependencies import DatabaseDep
from app.services.execution_readiness import ExecutionReadinessService
from execution_readiness.router import build_execution_router


def get_execution_service(database: DatabaseDep) -> ExecutionReadinessService:
    return ExecutionReadinessService(database)


router = build_execution_router(get_execution_service)

# Also expose under /api/v1/execution via package factory — ensure type for OpenAPI
_ServiceDep = Annotated[ExecutionReadinessService, Depends(get_execution_service)]


@router.get("/report-section")
async def report_section(service: _ServiceDep) -> dict[str, Any]:
    snap = await service.snapshot()
    return service.engine.report_section(snap)
