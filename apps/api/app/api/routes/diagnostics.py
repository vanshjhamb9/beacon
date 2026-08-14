from fastapi import APIRouter

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.schemas.diagnostics import DiagnosticsResponse
from app.services.diagnostics import DiagnosticsService

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.get("", response_model=DiagnosticsResponse)
async def pipeline_diagnostics(
    database: DatabaseDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> DiagnosticsResponse:
    return await DiagnosticsService(database, redis, settings).snapshot()
