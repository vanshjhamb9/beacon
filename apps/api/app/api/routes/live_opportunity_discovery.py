from __future__ import annotations

from app.api.dependencies import DatabaseDep
from live_opportunity_discovery.router import LiveOpportunityReadService, build_live_opportunity_router


def get_live_opportunity_discovery(database: DatabaseDep) -> LiveOpportunityReadService:
    return LiveOpportunityReadService(database)


router = build_live_opportunity_router(get_live_opportunity_discovery)
