"""Persist cyber opportunities into the founder workspace.

Sales-ready rows with a public email enter the human outreach queue as pending.
Needs-research rows appear on Leads / Pipeline. Partners never enter outreach.
This module never sends email.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packages.cybersecurity_discovery.pipeline import PipelineResult
from packages.cybersecurity_discovery.schema import CyberOpportunity, OpportunityType

ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = ROOT / "exports" / "lead_engine_runs"
CYBER_WORKSPACE_PATH = EXPORT_ROOT / "_cyber_workspace.json"
POOL_PATH = EXPORT_ROOT / "_outreach_pool.json"


def sync_to_workspace(result: PipelineResult) -> dict[str, int]:
    """Write cyber rows the dashboard already consumes. No SMTP."""
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    leads: list[dict[str, Any]] = []
    for opp in result.sales_ready:
        leads.append(opportunity_to_workspace_lead(opp, outreach=True))
    for opp in result.needs_research:
        if opp.opportunity_type == OpportunityType.SECURITY_PARTNER.value:
            continue
        leads.append(opportunity_to_workspace_lead(opp, outreach=False))

    payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "lane": "CYBER",
        "sales_ready": len(result.sales_ready),
        "needs_research": len(result.needs_research),
        "leads": leads,
    }
    CYBER_WORKSPACE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    pool_added = 0
    sales_ready_rows = [lead for lead in leads if lead.get("grade") == "SALES_READY"]
    if sales_ready_rows:
        pool_added = _merge_sales_ready_into_pool(sales_ready_rows)
    return {"workspace_leads": len(leads), "pool_added": pool_added}


def opportunity_to_workspace_lead(opp: CyberOpportunity, *, outreach: bool) -> dict[str, Any]:
    email = (opp.email or "").lower().strip()
    company = opp.company or (f"u/{opp.buyer_name}" if opp.buyer_name else None) or (opp.title or "Unknown")[:80]
    is_partner = opp.opportunity_type == OpportunityType.SECURITY_PARTNER.value
    if outreach and (not is_partner) and opp.final_verdict == "SALES_READY":
        grade = "SALES_READY"
    elif opp.final_verdict and opp.final_verdict != "SALES_READY":
        grade = opp.final_verdict
    else:
        grade = "NEEDS_RESEARCH"
    score = 92.0 if grade == "SALES_READY" else 74.0 if opp.buying_event_verified else 55.0
    lead_key = email or (opp.source_url or opp.opportunity_id)
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"cyber:{lead_key}")),
        "company": company,
        "company_name": company,
        "email": email,
        "to_email": email,
        "website": opp.company_url or "",
        "domain": _domain(opp.company_url),
        "founder_name": opp.buyer_name or "",
        "founder_role": opp.buyer_role or "",
        "linkedin": opp.linkedin_url or "",
        "intent_score": score,
        "score": score,
        "grade": grade,
        "lane": "cyber",
        "source": "cyber_discovery",
        "why": opp.why_now or opp.security_problem or opp.buying_event or opp.title,
        "why_now": opp.why_now or opp.security_problem,
        "service_match": opp.service_match or "Penetration Testing",
        "department": "Cyber",
        "country": opp.country or "",
        "industry": opp.industry or "saas",
        "source_url": opp.source_url,
        "opportunity_id": opp.opportunity_id,
        "outreach_status": "pending" if grade == "SALES_READY" else "",
        "subject": f"Security help for {company}" if grade == "SALES_READY" else "",
        "body": _draft_body(opp) if grade == "SALES_READY" else "",
        "strong_signals": [opp.buying_event] if opp.buying_event else [],
    }


def _draft_body(opp: CyberOpportunity) -> str:
    company = opp.company or "your team"
    problem = opp.security_problem or opp.buying_event or "a security testing need"
    service = opp.service_match or "penetration testing"
    return (
        f"Hi{' ' + (opp.buyer_name or '').split()[0] if opp.buyer_name else ''},\n\n"
        f"Saw the public note that {company} is dealing with {problem}. "
        f"Inowix can run {service} and hand back a commercial report your team can act on.\n\n"
        "Would a 15-minute scoping call this week be useful?\n\n"
        "Vansh Jhamb\nFounder, Inowix\nvansh@inowix.in\nhttps://inowix.in"
    )


def _domain(url: str | None) -> str:
    if not url:
        return ""
    text = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return text.split("/")[0].strip()


def _merge_sales_ready_into_pool(leads: list[dict[str, Any]]) -> int:
    existing: dict[str, Any] = {"leads": []}
    if POOL_PATH.exists():
        try:
            loaded = json.loads(POOL_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
            elif isinstance(loaded, list):
                existing = {"leads": loaded}
        except json.JSONDecodeError:
            existing = {"leads": []}
    pool = list(existing.get("leads") or [])
    seen = {
        (str(x.get("email") or x.get("source_url") or x.get("id") or "")).lower()
        for x in pool
        if x.get("email") or x.get("source_url") or x.get("id")
    }
    added = 0
    for lead in leads:
        key = str(lead.get("email") or lead.get("source_url") or lead.get("id") or "").lower()
        if not key or key in seen:
            continue
        pool.append(lead)
        seen.add(key)
        added += 1
    POOL_PATH.write_text(
        json.dumps({"updated_at": datetime.now(UTC).isoformat(), "leads": pool}, indent=2),
        encoding="utf-8",
    )
    return added
