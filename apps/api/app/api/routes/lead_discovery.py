"""Lead Discovery API routes — triggers discovery for COMAI and Inowix departments."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.dependencies import DatabaseDep
from app.services.lead_discovery import LeadDiscoveryService

router = APIRouter(prefix="/leads", tags=["Lead Discovery"])


@router.post("/discover")
async def discover_leads(database: DatabaseDep) -> dict[str, Any]:
    """Run a full discovery cycle for both COMAI and Inowix departments."""
    service = LeadDiscoveryService(database)
    result = await service.run_full_cycle()
    return {
        "status": "completed",
        "result": result,
    }


@router.post("/seed")
async def seed_leads(database: DatabaseDep) -> dict[str, Any]:
    """Seed initial leads for both departments (idempotent)."""
    service = LeadDiscoveryService(database)
    result = await service.seed_initial_leads()
    return {
        "status": "completed",
        "result": result,
    }


@router.get("/stats")
async def pipeline_stats(database: DatabaseDep) -> dict[str, Any]:
    """Get pipeline statistics by department."""
    service = LeadDiscoveryService(database)
    return await service.get_pipeline_stats()
