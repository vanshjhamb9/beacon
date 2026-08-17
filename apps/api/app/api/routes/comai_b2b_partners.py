"""COMAI B2B Partner Discovery API endpoints."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/b2b-partners", tags=["b2b-partners"])

EXPORT_DIR = Path("/home/ubuntu/beacon/exports/comai_b2b_partners")

# WhatsApp API/BSP/automation providers — these are COMAI competitors, NOT partners
COMPETITOR_DOMAINS = {
    "wati.io", "wati.com", "aisensy.com", "interakt.shop",
    "whatsboost.in", "quickreply.ai", "watease.com",
    "waba.nxccontrols.in", "getitsms.com", "heltar.com",
    "oncloudapi.com", "akestech.com", "gupshup.com",
    "twilio.com", "zoko.io", "delightchat.io", "kepsla.com",
    "whapi.cloud", "respond.io", "simpli.fi",
}

COMPETITOR_NAMES = {
    "wati", "aisensy", "aisensy", "interakt", "jio haptik",
    "whatboost", "quickreply", "watease", "nxcmsg", "nxc controls",
    "getitsms", "heltar", "on cloud api", "akestech",
    "gupshup", "twilio", "zoko", "delightchat", "kepsla",
}


def _get_db():
    from sqlalchemy import create_engine
    return create_engine("postgresql://beacon:beacon_password@127.0.0.1:5432/beacon")


class B2BPartnerResponse(BaseModel):
    id: str | None = None
    agency_name: str = ""
    agency_url: str = ""
    domain: str = ""
    agency_type: str = ""
    country: str = ""
    city: str = ""
    founder_name: str = ""
    founder_role: str = ""
    linkedin_url: str = ""
    services: list = Field(default_factory=list)
    client_count_evidence: int = 0
    client_examples: list = Field(default_factory=list)
    client_industries: list = Field(default_factory=list)
    partner_intent: str = ""
    partner_intent_evidence: list = Field(default_factory=list)
    client_access_score: float = 0.0
    client_access_evidence: list = Field(default_factory=list)
    comai_partner_fit: float = 0.0
    comai_fit_evidence: list = Field(default_factory=list)
    email: str = ""
    email_status: str = ""
    phone: str = ""
    contactability: str = ""
    partner_tier: str = ""
    final_verdict: str = ""
    rejection_reason: str = ""
    recommended_pitch_angle: str = ""
    why_this_agency: str = ""
    client_overlap: str = ""
    comai_fit_reason: str = ""
    partner_opportunity: str = ""
    competitor: bool = False
    safety_clear: bool = True
    source: str = ""
    created_at: str = ""


class B2BPartnersListResponse(BaseModel):
    partners: list[B2BPartnerResponse]
    total: int
    stats: dict[str, Any]


class B2BPartnerStatsResponse(BaseModel):
    total: int
    tier_a: int
    tier_b: int
    tier_c: int
    with_email: int
    with_phone: int
    contactable: int
    avg_client_score: float
    avg_fit_score: int
    explicit_intent: int
    high_potential: int
    by_type: dict[str, int]
    by_country: dict[str, int]
    by_intent: dict[str, int]


@router.get("/all", response_model=B2BPartnersListResponse)
async def get_all_partners(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    tier: str | None = Query(None),
    agency_type: str | None = Query(None),
    country: str | None = Query(None),
    intent: str | None = Query(None),
    verdict: str | None = Query(None),
) -> B2BPartnersListResponse:
    engine = _get_db()
    from sqlalchemy import text

    conditions = ["competitor = false"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if search:
        conditions.append("(agency_name ILIKE :search OR founder_name ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"
    if tier:
        conditions.append("partner_tier = :tier")
        params["tier"] = tier
    if agency_type:
        conditions.append("agency_type = :agency_type")
        params["agency_type"] = agency_type
    if country:
        conditions.append("country = :country")
        params["country"] = country
    if intent:
        conditions.append("partner_intent = :intent")
        params["intent"] = intent
    if verdict:
        conditions.append("final_verdict = :verdict")
        params["verdict"] = verdict

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(*) FROM comai_b2b_partners {where}"),
            params,
        ).scalar() or 0

        rows = conn.execute(
            text(f"""
                SELECT id, agency_name, agency_url, domain, agency_type, country, city,
                       founder_name, founder_role, linkedin_url, services,
                       client_count_evidence, client_examples, client_industries,
                       partner_intent, partner_intent_evidence,
                       client_access_score, client_access_evidence,
                       comai_partner_fit, comai_fit_evidence,
                       email, email_status, phone, contactability,
                       partner_tier, final_verdict, rejection_reason,
                       recommended_pitch_angle, why_this_agency, client_overlap,
                       comai_fit_reason, partner_opportunity, competitor, safety_clear,
                       source, created_at
                FROM comai_b2b_partners
                {where}
                ORDER BY client_access_score DESC, comai_partner_fit DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

        partners = []
        for r in rows:
            def _json_or_list(val):
                if val is None:
                    return []
                if isinstance(val, list):
                    return val
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        return []
                return []

            def _json_or_dict(val):
                if val is None:
                    return {}
                if isinstance(val, dict):
                    return val
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        return {}
                return {}

            partners.append(B2BPartnerResponse(
                id=str(r[0]) if r[0] else "",
                agency_name=r[1] or "",
                agency_url=r[2] or "",
                domain=r[3] or "",
                agency_type=r[4] or "",
                country=r[5] or "",
                city=r[6] or "",
                founder_name=r[7] or "",
                founder_role=r[8] or "",
                linkedin_url=r[9] or "",
                services=_json_or_list(r[10]),
                client_count_evidence=r[11] or 0,
                client_examples=_json_or_list(r[12]),
                client_industries=_json_or_list(r[13]),
                partner_intent=r[14] or "",
                partner_intent_evidence=_json_or_list(r[15]),
                client_access_score=float(r[16] or 0),
                client_access_evidence=_json_or_list(r[17]),
                comai_partner_fit=float(r[18] or 0),
                comai_fit_evidence=_json_or_list(r[19]),
                email=r[20] or "",
                email_status=r[21] or "",
                phone=r[22] or "",
                contactability=r[23] or "",
                partner_tier=r[24] or "",
                final_verdict=r[25] or "",
                rejection_reason=r[26] or "",
                recommended_pitch_angle=r[27] or "",
                why_this_agency=r[28] or "",
                client_overlap=r[29] or "",
                comai_fit_reason=r[30] or "",
                partner_opportunity=r[31] or "",
                competitor=r[32] or False,
                safety_clear=r[33] if r[33] is not None else True,
                source=r[34] or "",
                created_at=str(r[35]) if r[35] else "",
            ))

    stats_obj = await _get_stats()
    stats_dict = stats_obj.model_dump()
    return B2BPartnersListResponse(partners=partners, total=total, stats=stats_dict)


@router.get("/stats", response_model=B2BPartnerStatsResponse)
async def get_stats() -> B2BPartnerStatsResponse:
    return await _get_stats()


async def _get_stats() -> B2BPartnerStatsResponse:
    engine = _get_db()
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN partner_tier = 'A' THEN 1 END) as tier_a,
                COUNT(CASE WHEN partner_tier = 'B' THEN 1 END) as tier_b,
                COUNT(CASE WHEN partner_tier = 'C' THEN 1 END) as tier_c,
                COUNT(CASE WHEN email != '' AND email IS NOT NULL THEN 1 END) as with_email,
                COUNT(CASE WHEN phone != '' AND phone IS NOT NULL THEN 1 END) as with_phone,
                COUNT(CASE WHEN contactability IN ('HIGH', 'MEDIUM') THEN 1 END) as contactable,
                AVG(client_access_score) as avg_client_score,
                AVG(comai_partner_fit) as avg_fit_score,
                COUNT(CASE WHEN partner_intent = 'EXPLICIT' THEN 1 END) as explicit_intent,
                COUNT(CASE WHEN partner_intent = 'HIGH_POTENTIAL' THEN 1 END) as high_potential
            FROM comai_b2b_partners
            WHERE competitor = false
        """)).fetchone()

        types = conn.execute(text("""
            SELECT agency_type, COUNT(*) FROM comai_b2b_partners
            WHERE competitor = false
            GROUP BY agency_type ORDER BY COUNT(*) DESC
        """)).fetchall()

        countries = conn.execute(text("""
            SELECT country, COUNT(*) FROM comai_b2b_partners
            WHERE competitor = false
            GROUP BY country ORDER BY COUNT(*) DESC
        """)).fetchall()

        intents = conn.execute(text("""
            SELECT partner_intent, COUNT(*) FROM comai_b2b_partners
            WHERE competitor = false
            GROUP BY partner_intent ORDER BY COUNT(*) DESC
        """)).fetchall()

    return B2BPartnerStatsResponse(
        total=row[0] or 0,
        tier_a=row[1] or 0,
        tier_b=row[2] or 0,
        tier_c=row[3] or 0,
        with_email=row[4] or 0,
        with_phone=row[5] or 0,
        contactable=row[6] or 0,
        avg_client_score=round(float(row[7] or 0), 1),
        avg_fit_score=round(float(row[8] or 0)),
        explicit_intent=row[9] or 0,
        high_potential=row[10] or 0,
        by_type={r[0]: r[1] for r in types},
        by_country={r[0]: r[1] for r in countries},
        by_intent={r[0]: r[1] for r in intents},
    )


@router.get("/tiers")
async def get_tiers() -> dict[str, Any]:
    engine = _get_db()
    from sqlalchemy import text

    with engine.connect() as conn:
        tier_a = conn.execute(text("""
            SELECT agency_name, agency_url, agency_type, country, city,
                   client_access_score, comai_partner_fit, partner_intent,
                   founder_name, email, why_this_agency
            FROM comai_b2b_partners WHERE partner_tier = 'A' AND competitor = false
            ORDER BY client_access_score DESC
        """)).fetchall()

        tier_b = conn.execute(text("""
            SELECT agency_name, agency_url, agency_type, country, city,
                   client_access_score, comai_partner_fit, partner_intent,
                   founder_name, email, why_this_agency
            FROM comai_b2b_partners WHERE partner_tier = 'B' AND competitor = false
            ORDER BY client_access_score DESC LIMIT 50
        """)).fetchall()

        tier_c = conn.execute(text("""
            SELECT agency_name, agency_url, agency_type, country, city,
                   client_access_score, comai_partner_fit, partner_intent,
                   founder_name, email, why_this_agency
            FROM comai_b2b_partners WHERE partner_tier = 'C' AND competitor = false
            ORDER BY client_access_score DESC LIMIT 20
        """)).fetchall()

    def row_to_dict(r):
        return {
            "agency_name": r[0],
            "agency_url": r[1],
            "agency_type": r[2],
            "country": r[3],
            "city": r[4],
            "client_access_score": float(r[5] or 0),
            "comai_partner_fit": float(r[6] or 0),
            "partner_intent": r[7],
            "founder_name": r[8],
            "email": r[9],
            "why_this_agency": r[10],
        }

    return {
        "tier_a": [row_to_dict(r) for r in tier_a],
        "tier_b": [row_to_dict(r) for r in tier_b],
        "tier_c": [row_to_dict(r) for r in tier_c],
    }


@router.get("/export")
async def export_partners() -> dict[str, Any]:
    report_path = EXPORT_DIR / "comai_b2b_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text())
    return {"error": "No report found. Run extraction first."}


@router.post("/discover")
async def trigger_discovery() -> dict[str, Any]:
    """Trigger B2B partner discovery."""
    try:
        import subprocess
        result = subprocess.run(
            ["/home/ubuntu/beacon/.venv/bin/python",
             "/home/ubuntu/beacon/apps/api/app/scripts/comai_b2b_partner_extraction.py"],
            capture_output=True, text=True, timeout=600,
            cwd="/home/ubuntu/beacon",
        )
        if result.returncode == 0:
            output = json.loads(result.stdout) if result.stdout else {}
            return {"status": "completed", "result": output}
        else:
            return {"status": "error", "error": result.stderr[:500]}
    except Exception as e:
        logger.error(f"B2B discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
