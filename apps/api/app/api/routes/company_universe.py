"""Company Universe API routes.

CRITICAL RULES:
1. Company Universe is a DATABASE, not a pipeline
2. Companies here have NOT necessarily shown buying intent
3. ICP match score indicates fit, NOT buying intent
4. Only companies with verified buying events move to sales pipeline
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session as get_db
from app.models.company_universe import CompanyUniverse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company-universe", tags=["company-universe"])


@router.get("")
async def list_companies(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    source: str | None = Query(default=None),
    has_buying_event: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List companies in the universe.
    
    This is NOT a sales pipeline. It's a database of companies we know about.
    Companies only enter the sales pipeline when they have verified buying events.
    """
    query = select(CompanyUniverse).where(CompanyUniverse.deleted_at.is_(None))
    
    if source:
        query = query.where(CompanyUniverse.source == source)
    
    if has_buying_event is not None:
        query = query.where(CompanyUniverse.has_buying_event == has_buying_event)
    
    query = query.order_by(CompanyUniverse.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    companies = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(CompanyUniverse).where(
        CompanyUniverse.deleted_at.is_(None)
    )
    if source:
        count_query = count_query.where(CompanyUniverse.source == source)
    if has_buying_event is not None:
        count_query = count_query.where(CompanyUniverse.has_buying_event == has_buying_event)
    
    total = (await db.execute(count_query)).scalar() or 0
    
    return {
        "items": [company.to_dict() for company in companies],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_universe_stats(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get company universe statistics."""
    total = (
        await db.execute(
            select(func.count()).select_from(CompanyUniverse).where(
                CompanyUniverse.deleted_at.is_(None)
            )
        )
    ).scalar() or 0
    
    with_buying_event = (
        await db.execute(
            select(func.count()).select_from(CompanyUniverse).where(
                CompanyUniverse.deleted_at.is_(None),
                CompanyUniverse.has_buying_event == True,
            )
        )
    ).scalar() or 0
    
    # Source breakdown
    source_counts = {}
    rows = (
        await db.execute(
            select(CompanyUniverse.source, func.count())
            .where(CompanyUniverse.deleted_at.is_(None))
            .group_by(CompanyUniverse.source)
        )
    ).all()
    for source, count in rows:
        source_counts[source] = count
    
    return {
        "total": total,
        "with_buying_event": with_buying_event,
        "without_buying_event": total - with_buying_event,
        "by_source": source_counts,
    }
