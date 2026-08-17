"""Unified Leads API — serves all leads from ecommerce_leads table."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-leads", tags=["unified-leads"])


class UnifiedLead(BaseModel):
    id: str | None = None
    company_name: str = ""
    founder_name: str = ""
    decision_maker_role: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    domain: str = ""
    platform: str = ""
    category: str = ""
    industry: str = ""
    city: str = ""
    country: str = "India"
    lead_priority: str = "LOW"
    comai_score: float = 0.0
    sales_reason: str = ""
    source: str = ""
    linkedin_url: str = ""
    created_at: str = ""
    stage: str = "new"
    status: str = "active"


class UnifiedLeadsResponse(BaseModel):
    leads: list[UnifiedLead]
    total: int
    stats: dict[str, Any]


def _get_db():
    from sqlalchemy import create_engine, text
    engine = create_engine("postgresql://beacon:beacon_password@127.0.0.1:5432/beacon")
    return engine


def _row_to_lead(row) -> UnifiedLead:
    return UnifiedLead(
        id=str(row[0]) if row[0] else "",
        company_name=str(row[1] or ""),
        founder_name=str(row[2] or ""),
        decision_maker_role=str(row[3] or ""),
        email=str(row[4] or ""),
        phone=str(row[5] or ""),
        website=str(row[6] or ""),
        domain=str(row[7] or ""),
        platform=str(row[8] or ""),
        category=str(row[9] or ""),
        industry=str(row[10] or ""),
        city=str(row[11] or ""),
        country=str(row[12] or "India"),
        lead_priority=str(row[13] or "LOW"),
        comai_score=float(row[14] or 0),
        sales_reason=str(row[15] or ""),
        source=str(row[16] or ""),
        linkedin_url=str(row[17] or ""),
        created_at=str(row[18] or ""),
        stage="new",
        status="active",
    )


@router.get("/all", response_model=UnifiedLeadsResponse)
async def get_all_leads(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    priority: str | None = Query(None),
    source: str | None = Query(None),
    category: str | None = Query(None),
    has_phone: bool | None = Query(None),
    has_email: bool | None = Query(None),
) -> UnifiedLeadsResponse:
    engine = _get_db()
    from sqlalchemy import text

    conditions = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if search:
        conditions.append("(company_name ILIKE :search OR founder_name ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"
    if priority:
        conditions.append("lead_priority = :priority")
        params["priority"] = priority
    if source:
        conditions.append("source = :source")
        params["source"] = source
    if category:
        conditions.append("category = :category")
        params["category"] = category
    if has_phone:
        conditions.append("phone != '' AND phone IS NOT NULL")
    if has_email:
        conditions.append("email != '' AND email IS NOT NULL")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(*) FROM ecommerce_leads {where}"),
            params,
        ).scalar() or 0

        rows = conn.execute(
            text(f"""
                SELECT id, company_name, founder_name, decision_maker_role,
                       email, phone, website, domain, platform, category,
                       industry, city, country, lead_priority, comai_score,
                       sales_reason, source, linkedin_url, created_at
                FROM ecommerce_leads
                {where}
                ORDER BY comai_score DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

        leads = [_row_to_lead(r) for r in rows]

        stats_rows = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN phone != '' AND phone IS NOT NULL THEN 1 END) as with_phone,
                COUNT(CASE WHEN email != '' AND email IS NOT NULL THEN 1 END) as with_email,
                COUNT(CASE WHEN phone != '' AND email != '' THEN 1 END) as with_both,
                COUNT(CASE WHEN lead_priority = 'HOT' THEN 1 END) as hot,
                COUNT(CASE WHEN lead_priority = 'WARM' THEN 1 END) as warm,
                COUNT(CASE WHEN lead_priority = 'LOW' THEN 1 END) as low,
                COUNT(CASE WHEN founder_name != '' THEN 1 END) as with_founder,
                COUNT(CASE WHEN decision_maker_role != '' THEN 1 END) as with_role,
                AVG(comai_score) as avg_score
            FROM ecommerce_leads
        """)).fetchone()

        stats = {
            "total": stats_rows[0] or 0,
            "with_phone": stats_rows[1] or 0,
            "with_email": stats_rows[2] or 0,
            "with_both": stats_rows[3] or 0,
            "hot": stats_rows[4] or 0,
            "warm": stats_rows[5] or 0,
            "low": stats_rows[6] or 0,
            "with_founder": stats_rows[7] or 0,
            "with_role": stats_rows[8] or 0,
            "avg_score": round(float(stats_rows[9] or 0), 1),
        }

    return UnifiedLeadsResponse(leads=leads, total=total, stats=stats)


@router.get("/stats")
async def get_lead_stats() -> dict[str, Any]:
    engine = _get_db()
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN phone != '' AND phone IS NOT NULL THEN 1 END) as with_phone,
                COUNT(CASE WHEN email != '' AND email IS NOT NULL THEN 1 END) as with_email,
                COUNT(CASE WHEN phone != '' AND email != '' THEN 1 END) as with_both,
                COUNT(CASE WHEN lead_priority = 'HOT' THEN 1 END) as hot,
                COUNT(CASE WHEN lead_priority = 'WARM' THEN 1 END) as warm,
                COUNT(CASE WHEN lead_priority = 'LOW' THEN 1 END) as low,
                COUNT(CASE WHEN founder_name != '' THEN 1 END) as with_founder,
                COUNT(CASE WHEN decision_maker_role != '' THEN 1 END) as with_role,
                COUNT(CASE WHEN source = 'mega_extraction' THEN 1 END) as mega_extracted,
                AVG(comai_score) as avg_score
            FROM ecommerce_leads
        """)).fetchone()

        categories = conn.execute(text("""
            SELECT category, COUNT(*) as cnt
            FROM ecommerce_leads
            WHERE category != ''
            GROUP BY category
            ORDER BY cnt DESC
        """)).fetchall()

        roles = conn.execute(text("""
            SELECT decision_maker_role, COUNT(*) as cnt
            FROM ecommerce_leads
            WHERE decision_maker_role != ''
            GROUP BY decision_maker_role
            ORDER BY cnt DESC
        """)).fetchall()

        sources = conn.execute(text("""
            SELECT source, COUNT(*) as cnt
            FROM ecommerce_leads
            WHERE source != ''
            GROUP BY source
            ORDER BY cnt DESC
        """)).fetchall()

    return {
        "total": row[0] or 0,
        "with_phone": row[1] or 0,
        "with_email": row[2] or 0,
        "with_both": row[3] or 0,
        "hot": row[4] or 0,
        "warm": row[5] or 0,
        "low": row[6] or 0,
        "with_founder": row[7] or 0,
        "with_role": row[8] or 0,
        "mega_extracted": row[9] or 0,
        "avg_score": round(float(row[10] or 0), 1),
        "categories": {r[0]: r[1] for r in categories},
        "roles": {r[0]: r[1] for r in roles},
        "sources": {r[0]: r[1] for r in sources},
    }


@router.get("/pipeline")
async def get_pipeline_leads() -> dict[str, Any]:
    engine = _get_db()
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, company_name, founder_name, decision_maker_role,
                   email, phone, website, domain, category, industry,
                   city, lead_priority, comai_score, sales_reason, source
            FROM ecommerce_leads
            ORDER BY comai_score DESC
        """)).fetchall()

        leads = []
        for r in rows:
            score = float(r[12] or 0)
            if score >= 80:
                stage = "new"
            elif score >= 65:
                stage = "contacted"
            elif score >= 50:
                stage = "replied"
            else:
                stage = "lost"

            leads.append({
                "id": str(r[0]),
                "company_name": r[1],
                "founder_name": r[2],
                "decision_maker_role": r[3],
                "email": r[4],
                "phone": r[5],
                "website": r[6],
                "domain": r[7],
                "category": r[8],
                "industry": r[9],
                "city": r[10],
                "lead_priority": r[11],
                "intent_score": score,
                "sales_reason": r[13],
                "source": r[14],
                "stage": stage,
            })

    return {"leads": leads, "total": len(leads)}


@router.get("/extraction-status")
async def get_extraction_status() -> dict[str, Any]:
    seen_path = Path("/home/ubuntu/beacon/exports/lead_engine_runs/_mega_seen_domains.json")
    seen_count = 0
    if seen_path.exists():
        try:
            seen_count = len(json.loads(seen_path.read_text()))
        except Exception:
            pass

    engine = _get_db()
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT COUNT(*) as total,
                   MAX(created_at) as last_extraction
            FROM ecommerce_leads
            WHERE source = 'mega_extraction'
        """)).fetchone()

    return {
        "active": True,
        "schedule": "every 20 minutes",
        "seen_domains": seen_count,
        "total_mega_extracted": row[0] or 0,
        "last_extraction": str(row[1] or ""),
        "cron_job": "*/20 * * * * /home/ubuntu/beacon/scripts/run_mega_extraction.sh",
    }
