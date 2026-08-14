from __future__ import annotations

from app.api.dependencies import DatabaseDep
from opportunity_intelligence.router import OpportunityReadService, build_opportunity_router


def get_opportunity_intelligence(database: DatabaseDep) -> OpportunityReadService:
    return OpportunityReadService(database)


router = build_opportunity_router(get_opportunity_intelligence)
