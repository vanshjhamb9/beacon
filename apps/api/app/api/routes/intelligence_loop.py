"""Intelligence Loop API routes — analyzes lead outcomes and generates recommendations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.dependencies import DatabaseDep
from app.services.intelligence_loop import IntelligenceLoop

router = APIRouter(prefix="/intelligence-loop", tags=["Intelligence Loop"])


@router.get("/analysis")
async def get_analysis(database: DatabaseDep) -> dict[str, Any]:
    """Get full intelligence analysis with recommendations."""
    loop = IntelligenceLoop(database)
    return await loop.run_full_analysis()


@router.get("/recommendations")
async def get_recommendations(database: DatabaseDep) -> dict[str, Any]:
    """Get recommendations for improving lead quality."""
    loop = IntelligenceLoop(database)
    analysis = await loop.analyze_outcomes()
    recommendations = await loop.generate_recommendations(analysis)
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }


@router.post("/rescore")
async def rescore_leads(database: DatabaseDep) -> dict[str, Any]:
    """Re-score all active leads based on latest intelligence."""
    loop = IntelligenceLoop(database)
    return await loop.update_lead_scores()
