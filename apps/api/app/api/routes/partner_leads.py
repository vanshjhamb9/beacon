"""Partner Leads API routes — serves data from partner_leads table to dashboard."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DatabaseDep
from app.db.session import AsyncSessionLocal
from app.models.partner_leads import PartnerLead

router = APIRouter(prefix="/partner-leads", tags=["Partner Leads"])


class UpdatePartnerLeadRequest(BaseModel):
    status: str | None = None
    tier: str | None = None
    outreach_sent: bool | None = None
    response_received: bool | None = None
    meeting_scheduled: bool | None = None
    partner_converted: bool | None = None
    notes: str | None = None


@router.get("")
async def list_partner_leads(
    database: DatabaseDep,
    tier: str | None = None,
    status: str | None = None,
    country: str | None = None,
    agency_type: str | None = None,
    contactability: str | None = None,
    lead_source: str | None = None,
    search: str | None = None,
    has_phone: bool | None = None,
    today_only: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List partner leads from the partner_leads table."""
    query = select(PartnerLead)
    count_query = select(func.count(PartnerLead.id))

    filters = []
    if tier:
        filters.append(PartnerLead.tier == tier)
    if status:
        filters.append(PartnerLead.status == status)
    if country:
        filters.append(PartnerLead.country == country)
    if agency_type:
        filters.append(PartnerLead.agency_type.ilike(f"%{agency_type}%"))
    if contactability:
        filters.append(PartnerLead.contactability == contactability)
    if lead_source:
        filters.append(PartnerLead.lead_source == lead_source)
    if has_phone:
        filters.append(PartnerLead.phone.isnot(None))
        filters.append(PartnerLead.phone != "")
    if today_only:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        filters.append(PartnerLead.created_at >= today_start)
    if search:
        filters.append(
            or_(
                PartnerLead.agency_name.ilike(f"%{search}%"),
                PartnerLead.city.ilike(f"%{search}%"),
                PartnerLead.decision_maker.ilike(f"%{search}%"),
            )
        )

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await database.scalar(count_query)
    results = await database.scalars(
        query.order_by(PartnerLead.final_score.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [r.to_dict() for r in results],
    }


@router.get("/stats")
async def partner_leads_stats(database: DatabaseDep):
    """Get partner leads statistics."""
    total = await database.scalar(select(func.count(PartnerLead.id)))
    tier_a = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.tier == "A")
    )
    tier_b = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.tier == "B")
    )
    tier_c = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.tier == "C")
    )
    contacted = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.outreach_sent == True)
    )
    responded = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.response_received == True)
    )
    meetings = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.meeting_scheduled == True)
    )
    converted = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.partner_converted == True)
    )
    high_contactability = await database.scalar(
        select(func.count(PartnerLead.id)).where(PartnerLead.contactability == "HIGH")
    )

    # By country
    country_query = await database.execute(
        select(PartnerLead.country, func.count(PartnerLead.id))
        .group_by(PartnerLead.country)
        .order_by(func.count(PartnerLead.id).desc())
    )
    by_country = {row[0] or "Unknown": row[1] for row in country_query.all()}

    # By agency type
    type_query = await database.execute(
        select(PartnerLead.agency_type, func.count(PartnerLead.id))
        .group_by(PartnerLead.agency_type)
        .order_by(func.count(PartnerLead.id).desc())
    )
    by_type = {row[0] or "Unknown": row[1] for row in type_query.all()}

    # Average scores
    avg_final = await database.scalar(select(func.avg(PartnerLead.final_score)))
    avg_client = await database.scalar(select(func.avg(PartnerLead.client_access_score)))
    avg_comai = await database.scalar(select(func.avg(PartnerLead.comai_fit_score)))

    return {
        "total": total,
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "contacted": contacted,
        "responded": responded,
        "meetings": meetings,
        "converted": converted,
        "high_contactability": high_contactability,
        "by_country": by_country,
        "by_type": by_type,
        "avg_final_score": round(avg_final, 1) if avg_final else 0,
        "avg_client_access_score": round(avg_client, 1) if avg_client else 0,
        "avg_comai_fit_score": round(avg_comai, 1) if avg_comai else 0,
    }


@router.get("/export/all")
async def export_all_partner_leads(database: DatabaseDep):
    """Export all partner leads as JSON."""
    results = await database.scalars(
        select(PartnerLead).order_by(PartnerLead.final_score.desc().nullslast())
    )
    return [r.to_dict() for r in results]


@router.get("/phone-ready")
async def phone_ready_partner_leads(database: DatabaseDep):
    """Get partner leads ready for cold calling (have phone number, status=NEW)."""
    query = (
        select(PartnerLead)
        .where(
            and_(
                PartnerLead.phone.isnot(None),
                PartnerLead.phone != "",
                PartnerLead.status == "NEW",
            )
        )
        .order_by(PartnerLead.final_score.desc().nullslast())
    )
    results = await database.scalars(query)
    return [r.to_dict() for r in results]


class EnrichRequest(BaseModel):
    lead_ids: list[str] | None = None
    limit: int = 50


@router.post("/enrich")
async def enrich_partner_leads(database: DatabaseDep, body: EnrichRequest):
    """Enrich partner leads missing phone/email. Returns leads needing enrichment."""
    query = select(PartnerLead).where(
        or_(
            PartnerLead.phone.is_(None),
            PartnerLead.phone == "",
            PartnerLead.email.is_(None),
            PartnerLead.email == "",
        )
    )
    if body.lead_ids:
        from uuid import UUID as _UUID
        query = query.where(PartnerLead.id.in_([_UUID(lid) for lid in body.lead_ids]))
    query = query.order_by(PartnerLead.final_score.desc().nullslast()).limit(body.limit)
    results = await database.scalars(query)
    leads = [r.to_dict() for r in results]
    return {
        "count": len(leads),
        "leads": leads,
        "message": f"{len(leads)} leads need enrichment. Use the enrichment script to fill phone/email.",
    }


@router.get("/{lead_id}")
async def get_partner_lead(database: DatabaseDep, lead_id: UUID):
    """Get a single partner lead by ID."""
    result = await database.scalar(
        select(PartnerLead).where(PartnerLead.id == lead_id)
    )
    if not result:
        raise HTTPException(status_code=404, detail="Partner lead not found")
    return result.to_dict()


@router.patch("/{lead_id}")
async def update_partner_lead(
    database: DatabaseDep, lead_id: UUID, body: UpdatePartnerLeadRequest
):
    """Update a partner lead."""
    result = await database.scalar(
        select(PartnerLead).where(PartnerLead.id == lead_id)
    )
    if not result:
        raise HTTPException(status_code=404, detail="Partner lead not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)

    await database.commit()
    await database.refresh(result)
    return result.to_dict()
