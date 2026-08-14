from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.schemas.runtime_ops import RuntimeOpsReportsResponse, RuntimeOpsResponse
from app.services.dataset_unlock import DatasetUnlockService
from app.services.runtime_ops import RuntimeOpsService

router = APIRouter(prefix="/operations", tags=["operations"])


def get_odu_service(database: DatabaseDep) -> DatasetUnlockService:
    return DatasetUnlockService(database)


OduServiceDep = Annotated[DatasetUnlockService, Depends(get_odu_service)]


def _celery_inspect_payload() -> dict:
    try:
        from worker.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=1.0)
        if inspector is None:
            return {}
        return {
            "ping": inspector.ping() or {},
            "stats": inspector.stats() or {},
            "active": inspector.active() or {},
            "scheduled": inspector.scheduled() or {},
            "registered": inspector.registered() or {},
        }
    except Exception:  # noqa: BLE001 — ops probe must not crash API
        return {}


@router.get("", response_model=RuntimeOpsResponse)
async def operations_snapshot(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> RuntimeOpsResponse:
    snap = await RuntimeOpsService(database, redis, settings).snapshot(
        inspect_payload=_celery_inspect_payload()
    )
    return RuntimeOpsResponse(**snap.model_dump(mode="json"))


@router.get("/reports", response_model=RuntimeOpsReportsResponse)
async def operations_reports(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> RuntimeOpsReportsResponse:
    reports = await RuntimeOpsService(database, redis, settings).reports()
    return RuntimeOpsReportsResponse(generated_at=datetime.now(UTC), reports=reports)


# ODU endpoints live under /operations/odu/* so BOC v1 owns /operations/connectors
# and /operations/health without route collisions.
@router.get("/odu/connectors")
async def odu_connectors(service: OduServiceDep) -> dict[str, Any]:
    return await service.connectors()


@router.get("/odu/health")
async def odu_health(service: OduServiceDep) -> dict[str, Any]:
    return await service.health()


@router.get("/odu/dashboard")
async def odu_dashboard(service: OduServiceDep) -> dict[str, Any]:
    return await service.dashboard()


@router.get("/odu/recovery")
async def odu_recovery(service: OduServiceDep, limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    return await service.recovery(limit=limit)


@router.get("/odu/report")
async def odu_report(service: OduServiceDep) -> dict[str, Any]:
    return await service.report()


@router.post("/odu/unlock")
async def odu_unlock(
    service: OduServiceDep,
    collect_new: bool = Query(default=True),
    recover_contacts: bool = Query(default=True),
    recover_dms: bool = Query(default=True),
) -> dict[str, Any]:
    return await service.unlock(
        collect_new=collect_new,
        recover_contacts=recover_contacts,
        recover_dms=recover_dms,
    )


@router.get("/production-gate")
async def production_gate(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> dict:
    snap = await RuntimeOpsService(database, redis, settings).snapshot(
        inspect_payload=_celery_inspect_payload()
    )
    gate = snap.production_gate
    if settings.environment == "production" and not gate.allow_production:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Production mode blocked by runtime ops gate",
                "blockers": gate.blockers,
                "score": gate.score,
            },
        )
    return gate.model_dump(mode="json")
