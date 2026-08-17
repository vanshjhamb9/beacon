"""Unified Sales Workspace hub — wires Home / Leads / Pipeline / Outreach / Analytics
to Lead Engine pool + persisted pipeline stages (not stale FSW / empty campaigns).
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspace", tags=["workspace-hub"])

# routes → api → app → api → apps → repo root
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPORT_ROOT = ROOT / "exports" / "lead_engine_runs"
STAGES_PATH = EXPORT_ROOT / "_workspace_stages.json"
OUTREACH_PATH = EXPORT_ROOT / "_workspace_outreach.json"
CYBER_WORKSPACE_PATH = EXPORT_ROOT / "_cyber_workspace.json"
ACTIVITY_PATH = EXPORT_ROOT / "_workspace_activity.json"

VALID_STAGES = ("new", "contacted", "replied", "meeting", "won", "lost")
CONTACTED_STAGES = ("contacted", "replied", "meeting", "won")
_NAME_NOISE_RE = re.compile(r"\s+(?:soft\s+)?mid$", re.IGNORECASE)


def _engine():
    try:
        from packages import lead_engine as le
    except ImportError:
        import lead_engine as le  # type: ignore
    return le


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed reading %s: %s", path, exc)
        return default


def _save_json(path: Path, data: Any) -> None:
    """Atomic write with short retries — avoids Windows Errno 22 on locked files."""
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = path.with_suffix(path.suffix + ".tmp")
    last_exc: OSError | None = None
    for attempt in range(4):
        try:
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(path)
            return
        except OSError as exc:
            last_exc = exc
            logger.warning("save_json attempt %s failed for %s: %s", attempt + 1, path, exc)
            time.sleep(0.05 * (attempt + 1))
    if last_exc:
        raise last_exc


def _load_stages() -> dict[str, str]:
    data = _load_json(STAGES_PATH, {"stages": {}})
    stages = data.get("stages") if isinstance(data, dict) else {}
    return {str(k).lower(): str(v).lower() for k, v in (stages or {}).items()}


def _save_stages(stages: dict[str, str]) -> None:
    _save_json(STAGES_PATH, {"updated_at": _now_iso(), "stages": stages})


def _append_activity(event: str, detail: str, meta: dict[str, Any] | None = None) -> None:
    data = _load_json(ACTIVITY_PATH, {"feed": []})
    feed = list(data.get("feed") or [])
    feed.insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "event": event,
            "detail": detail,
            "meta": meta or {},
            "at": _now_iso(),
        },
    )
    _save_json(ACTIVITY_PATH, {"updated_at": _now_iso(), "feed": feed[:80]})


def _lead_id(email: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, (email or "").lower().strip()))


def _product_label(lead: dict[str, Any]) -> str:
    lane = str(lead.get("lane") or lead.get("company_type") or lead.get("department") or "").lower()
    src = str(lead.get("source") or "").lower()
    if "cyber" in lane or "cyber" in src or "vapt" in lane or "pentest" in src:
        return "Cyber"
    if "inowix" in lane or "saas" in lane or "inowix" in src:
        return "Inowix"
    return "COMAI"


def _clean_company_name(name: str) -> str:
    cleaned = _NAME_NOISE_RE.sub("", (name or "").strip()).strip()
    return cleaned or (name or "Unknown")


def _has_contact_data(email: str, phone: str, website: str, why: str, score: float) -> bool:
    return bool(email) and bool(website or phone) and (bool(why) or score >= 58)


def _website_url(raw: dict[str, Any]) -> str:
    site = str(raw.get("website") or "").strip()
    if site:
        return site if site.startswith("http") else f"https://{site}"
    domain = str(raw.get("domain") or "").strip().removeprefix("https://").removeprefix("http://")
    if domain:
        return f"https://{domain}"
    return ""


def _normalize_lead(raw: dict[str, Any], stages: dict[str, str], sent: set[str]) -> dict[str, Any]:
    email = (raw.get("email") or raw.get("to_email") or "").lower().strip()
    company = _clean_company_name(str(raw.get("company") or raw.get("company_name") or "Unknown"))
    score = float(raw.get("intent_score") or raw.get("score") or 0)
    stage = stages.get(email) or "new"
    if email in sent and stage == "new":
        stage = "contacted"
    product = _product_label(raw)
    why = str(raw.get("why") or raw.get("why_now") or raw.get("signal") or "")
    why_l = why.lower()
    whatsapp_already = bool(
        raw.get("whatsapp_already")
        or "whatsapp already present" in why_l
        or ("whatsapp present" in why_l and "no whatsapp" not in why_l)
    )
    if whatsapp_already and score > 70:
        score = max(58.0, score - 12.0)
    phone = str(raw.get("phone") or "").strip()
    website = _website_url(raw)
    founder = str(raw.get("founder_name") or "").strip()
    founder_title = str(raw.get("founder_role") or raw.get("founder_title") or "").strip()
    if not founder_title and founder:
        founder_title = "Founder"
    elif not founder_title and email:
        local = email.split("@", 1)[0]
        if local in ("care", "wecare", "hello", "hi", "info", "contact", "support", "help"):
            founder_title = "Brand inbox"
    created_at = (
        raw.get("created_at")
        or raw.get("pooled_at")
        or raw.get("discovered_at")
        or raw.get("updated_at")
        or _now_iso()
    )
    outreach_raw = str(raw.get("outreach_status") or "").lower().strip()
    if email in sent:
        outreach_status = "sent"
    elif outreach_raw in ("sent", "delivered", "replied", "bounced"):
        outreach_status = outreach_raw
    else:
        # pool stamps like "pooled" / "ready" are still pending outreach
        outreach_status = "pending"
    grade = str(raw.get("grade") or "")
    if whatsapp_already and grade == "SALES_READY":
        grade = "QUALIFIED"
    return {
        "id": raw.get("id") or _lead_id(email or company),
        "company_id": raw.get("id") or _lead_id(email or company),
        "company_name": company,
        "company": company,
        "founder_name": founder,
        "founder_title": founder_title,
        "founder_role": founder_title,
        "email": email,
        "phone": phone,
        "website": website,
        "source_url": raw.get("source_url") or website,
        "domain": raw.get("domain") or "",
        "city": raw.get("city") or "",
        "country": raw.get("country") or ("India" if product != "Cyber" else ""),
        "industry": raw.get("category") or raw.get("industry") or "",
        "category": raw.get("category") or raw.get("industry") or "",
        "stage": stage,
        "status": stage,
        "manual_status": stage,
        "intent_score": score,
        "score": score,
        "confidence": min(1.0, score / 100.0) if score else 0,
        "opportunity_score": score,
        "fit_score": score,
        "grade": grade,
        "service_match": f"{product} — WhatsApp / chat AI" if product == "COMAI" else f"{product} — Product build",
        "department": product,
        "source": raw.get("source") or "lead_engine",
        "source_connector": "lead_engine",
        "trigger": raw.get("signal") or "live_discovery",
        "why_now": why[:240],
        "description": why[:240],
        "requirement": why[:240],
        "buying_signals": raw.get("strong_signals") or raw.get("signal_families") or [],
        "strong_signals": raw.get("strong_signals") or [],
        "signal_families": raw.get("signal_families") or [],
        "subject": raw.get("subject") or "",
        "body": raw.get("body") or "",
        "outreach_status": outreach_status,
        "contacted": stage in CONTACTED_STAGES,
        "not_contacted": stage == "new",
        "has_contact_data": _has_contact_data(email, phone, website, why, score),
        "is_new": stage == "new",
        "tags": [product, grade or "QUALIFIED"],
        "platform": raw.get("platform") or "",
        "size": raw.get("size") or "",
        "employee_estimate": raw.get("employee_estimate"),
        "created_at": created_at,
        "updated_at": raw.get("updated_at") or created_at,
        "whatsapp_already": whatsapp_already,
        "contact_info": {
            "email": email,
            "phone": phone,
            "whatsapp": phone,
        },
    }


def _collect_raw_leads() -> list[dict[str, Any]]:
    le = _engine()
    pool = list(le.load_outreach_pool() or [])
    by_email: dict[str, dict[str, Any]] = {}
    for lead in pool:
        email = (lead.get("email") or "").lower().strip()
        if email:
            by_email[email] = lead

    # Merge recent run CSVs / run.json leads for extra coverage
    if EXPORT_ROOT.exists():
        import csv as _csv

        runs = sorted(
            [p for p in EXPORT_ROOT.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:12]
        for run_dir in runs:
            meta = run_dir / "run.json"
            if meta.exists():
                try:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    for lead in data.get("leads") or []:
                        if not isinstance(lead, dict):
                            continue
                        email = (lead.get("email") or "").lower().strip()
                        if email and email not in by_email:
                            by_email[email] = lead
                except Exception:  # noqa: BLE001
                    pass
            csv_path = run_dir / "leads.csv"
            if not csv_path.exists():
                continue
            try:
                with csv_path.open(encoding="utf-8", newline="") as fh:
                    for row in _csv.DictReader(fh):
                        email = (row.get("email") or "").lower().strip()
                        if email and email not in by_email:
                            by_email[email] = dict(row)
            except Exception:  # noqa: BLE001
                continue
    if CYBER_WORKSPACE_PATH.exists():
        try:
            data = json.loads(CYBER_WORKSPACE_PATH.read_text(encoding="utf-8"))
            for lead in data.get("leads") or []:
                if not isinstance(lead, dict):
                    continue
                email = (lead.get("email") or "").lower().strip()
                key = email or str(lead.get("source_url") or lead.get("id") or "")
                if key and key not in by_email:
                    by_email[key] = lead
        except Exception:  # noqa: BLE001
            pass
    return list(by_email.values())


def _build_workspace_leads() -> list[dict[str, Any]]:
    le = _engine()
    sent = le._load_sent_emails()  # noqa: SLF001
    stages = _load_stages()
    # Ensure sent emails are at least contacted in stage map
    dirty = False
    for email in sent:
        if stages.get(email) in (None, "new"):
            stages[email] = "contacted"
            dirty = True
    if dirty:
        _save_stages(stages)
    leads = [_normalize_lead(raw, stages, sent) for raw in _collect_raw_leads()]
    leads.sort(key=lambda x: (-float(x.get("intent_score") or 0), str(x.get("company_name") or "")))
    return leads


def _stage_counts(leads: list[dict[str, Any]]) -> dict[str, int]:
    counts = {s: 0 for s in VALID_STAGES}
    for lead in leads:
        stage = str(lead.get("stage") or "new").lower()
        if stage not in counts:
            stage = "new"
        counts[stage] += 1
    return counts


def _sync_outreach_from_leads(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build outreach campaign rows from workspace leads (drafts / sent)."""
    existing = _load_json(OUTREACH_PATH, {"campaigns": []})
    by_email = {
        str(c.get("email") or "").lower(): c
        for c in (existing.get("campaigns") or [])
        if isinstance(c, dict) and c.get("email")
    }
    out: list[dict[str, Any]] = []
    for lead in leads:
        email = str(lead.get("email") or "").lower()
        if not email:
            continue
        prev = by_email.get(email) or {}
        prev_status = str(prev.get("status") or "").lower()
        lead_status = str(lead.get("outreach_status") or "").lower()
        status = prev_status if prev_status in ("pending", "draft", "sent", "delivered", "replied", "bounced") else ""
        if not status:
            status = lead_status if lead_status in ("pending", "draft", "sent", "delivered", "replied", "bounced") else "pending"
        if lead.get("stage") in ("contacted", "replied", "meeting", "won") and status in ("pending", "draft"):
            status = "sent"
        if lead.get("stage") == "replied":
            status = "replied"
        subject = lead.get("subject") or prev.get("subject") or f"Quick idea for {lead.get('company_name')}"
        body = lead.get("body") or prev.get("body") or str(lead.get("why_now") or "")[:400]
        row = {
            "id": prev.get("id") or _lead_id(email + ":outreach"),
            "company_id": lead.get("id"),
            "company_name": lead.get("company_name"),
            "email": email,
            "status": status,
            "channel": "email",
            "subject": subject,
            "body": body,
            "created_at": prev.get("created_at") or _now_iso(),
            "sent_at": prev.get("sent_at") or ( _now_iso() if status in ("sent", "delivered", "replied") else None),
            "delivered_at": prev.get("delivered_at") or ( _now_iso() if status in ("delivered", "replied") else None),
            "replied_at": prev.get("replied_at") or (_now_iso() if status == "replied" else None),
            "bounced_at": prev.get("bounced_at"),
            "intent_score": lead.get("intent_score"),
            "grade": lead.get("grade"),
            "department": lead.get("department"),
        }
        out.append(row)
    _save_json(OUTREACH_PATH, {"updated_at": _now_iso(), "campaigns": out})
    return out


def _outreach_stats(campaigns: list[dict[str, Any]]) -> dict[str, int]:
    stats = {"pending": 0, "sent": 0, "delivered": 0, "replied": 0, "bounced": 0}
    for c in campaigns:
        st = str(c.get("status") or "pending").lower()
        if st in ("pending", "draft", "needs_review"):
            stats["pending"] += 1
        elif st == "replied":
            stats["replied"] += 1
            stats["sent"] += 1
            stats["delivered"] += 1
        elif st in ("delivered",):
            stats["delivered"] += 1
            stats["sent"] += 1
        elif st in ("sent", "approved", "scheduled"):
            stats["sent"] += 1
        elif st == "bounced":
            stats["bounced"] += 1
    return stats


class StageBody(BaseModel):
    stage: str = Field(..., description="new|contacted|replied|meeting|won|lost")


class SyncBody(BaseModel):
    archive_stale_fsw: bool = False


@router.post("/sync")
async def sync_workspace(body: SyncBody | None = None) -> dict[str, Any]:
    """Refresh workspace from Lead Engine pool and materialize outreach rows."""
    _ = body
    leads = _build_workspace_leads()
    campaigns = _sync_outreach_from_leads(leads)
    _append_activity(
        "workspace_sync",
        f"Synced {len(leads)} Lead Engine leads into Home / Leads / Pipeline / Outreach",
        {"lead_count": len(leads), "campaign_count": len(campaigns)},
    )
    return {
        "ok": True,
        "lead_count": len(leads),
        "campaign_count": len(campaigns),
        "stage_counts": _stage_counts(leads),
        "synced_at": _now_iso(),
    }


def _filter_leads(
    leads: list[dict[str, Any]],
    *,
    search: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    out = leads
    if search:
        q = search.lower().strip()
        out = [
            x
            for x in out
            if q in str(x.get("company_name") or "").lower()
            or q in str(x.get("email") or "").lower()
            or q in str(x.get("industry") or "").lower()
            or q in str(x.get("city") or "").lower()
            or q in str(x.get("department") or "").lower()
        ]
    status_key = (status or "all").lower().strip()
    if status_key in ("new", "not_contacted", "not-contacted"):
        out = [x for x in out if x.get("stage") == "new"]
    elif status_key == "contacted":
        out = [x for x in out if x.get("stage") in CONTACTED_STAGES]
    elif status_key in ("with_data", "with-data", "data"):
        out = [x for x in out if x.get("has_contact_data")]
    elif status_key in ("incomplete", "no_data"):
        out = [x for x in out if not x.get("has_contact_data")]
    return out


@router.get("/leads")
async def workspace_leads(
    limit: int = 300,
    search: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    all_leads = _build_workspace_leads()
    leads = _filter_leads(all_leads, search=search, status=status)
    counts = _stage_counts(all_leads)
    with_data = sum(1 for x in all_leads if x.get("has_contact_data"))
    not_contacted = counts["new"]
    contacted = counts["contacted"] + counts["replied"] + counts["meeting"] + counts["won"]
    leads = leads[: max(1, min(limit, 500))]
    return {
        "items": leads,
        "total": len(leads),
        "stage_counts": counts,
        "filter_counts": {
            "all": len(all_leads),
            "new": counts["new"],
            "not_contacted": not_contacted,
            "contacted": contacted,
            "with_data": with_data,
        },
        "source": "lead_engine_workspace",
    }


@router.get("/leads/{lead_id}")
async def workspace_lead(lead_id: str) -> dict[str, Any]:
    for lead in _build_workspace_leads():
        if str(lead.get("id")) == lead_id or str(lead.get("company_id")) == lead_id:
            return lead
    raise HTTPException(status_code=404, detail="Lead not found in workspace")


@router.post("/leads/{lead_id}/stage")
async def set_lead_stage(lead_id: str, body: StageBody) -> dict[str, Any]:
    stage = body.stage.lower().strip()
    if stage in ("rejected", "reject", "garbage"):
        stage = "lost"
    if stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"stage must be one of {VALID_STAGES}")
    leads = _build_workspace_leads()
    target = next((x for x in leads if str(x.get("id")) == lead_id or str(x.get("company_id")) == lead_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Lead not found")
    email = str(target.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Lead has no email key")
    stages = _load_stages()
    stages[email] = stage
    _save_stages(stages)
    target["stage"] = stage
    target["status"] = stage
    _sync_outreach_from_leads(_build_workspace_leads())
    _append_activity("stage_move", f"{target.get('company_name')} → {stage}", {"email": email, "stage": stage})
    return {"ok": True, "lead": target}


class SendBody(BaseModel):
    dry_run: bool = False
    subject: str | None = None
    body: str | None = None


def _find_workspace_lead(lead_id: str) -> dict[str, Any]:
    for lead in _build_workspace_leads():
        if str(lead.get("id")) == lead_id or str(lead.get("company_id")) == lead_id:
            return lead
    raise HTTPException(status_code=404, detail="Lead not found in workspace")


def _persist_draft_on_pool(email: str, subject: str, body: str) -> None:
    """Write subject/body back onto outreach pool + outreach campaigns."""
    le = _engine()
    pool = list(le.load_outreach_pool() or [])
    changed = False
    for lead in pool:
        if (lead.get("email") or "").lower().strip() == email:
            lead["subject"] = subject
            lead["body"] = body
            lead["draft_status"] = "drafted"
            changed = True
    if changed:
        le.save_outreach_pool(pool)

    data = _load_json(OUTREACH_PATH, {"campaigns": []})
    campaigns = list(data.get("campaigns") or [])
    found = False
    for c in campaigns:
        if str(c.get("email") or "").lower() == email:
            c["subject"] = subject
            c["body"] = body
            if str(c.get("status") or "") in ("", "pooled"):
                c["status"] = "pending"
            found = True
    if not found:
        campaigns.append(
            {
                "id": _lead_id(email + ":outreach"),
                "company_id": _lead_id(email),
                "company_name": "",
                "email": email,
                "status": "pending",
                "channel": "email",
                "subject": subject,
                "body": body,
                "created_at": _now_iso(),
            }
        )
    _save_json(OUTREACH_PATH, {"updated_at": _now_iso(), "campaigns": campaigns})


@router.post("/leads/{lead_id}/draft")
async def draft_workspace_lead(lead_id: str) -> dict[str, Any]:
    """Generate COMAI/Inowix outreach draft for a workspace lead."""
    lead = _find_workspace_lead(lead_id)
    email = str(lead.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Lead has no email")
    dept = str(lead.get("department") or "")
    if dept.startswith("Cyber") or "cyber" in dept.lower():
        product = "cyber"
    elif dept.startswith("Inowix"):
        product = "inowix"
    else:
        product = "comai"
    try:
        from packages.outreach_generator.hyperpersonal import draft_for_product
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Draft generator unavailable: {exc}") from exc

    draft_lead = {
        "company": lead.get("company_name") or lead.get("company"),
        "founder_name": lead.get("founder_name") or "",
        "email": email,
        "why": lead.get("why_now") or lead.get("description") or "",
        "category": lead.get("industry") or "",
        "city": lead.get("city") or "",
        "platform": lead.get("platform") or "",
        "website": lead.get("website") or "",
        "intent_score": lead.get("intent_score"),
        "grade": lead.get("grade"),
        "strong_signals": lead.get("strong_signals") or [],
    }
    d = draft_for_product(product, draft_lead)
    _persist_draft_on_pool(email, d.subject, d.body)
    lead["subject"] = d.subject
    lead["body"] = d.body
    _append_activity(
        "draft_generated",
        f"Draft ready for {lead.get('company_name')}",
        {"email": email, "hook": getattr(d, "hook_used", "")},
    )
    return {
        "ok": True,
        "lead_id": lead_id,
        "subject": d.subject,
        "body": d.body,
        "hook_used": getattr(d, "hook_used", ""),
        "lead": lead,
    }


@router.post("/leads/{lead_id}/send")
async def send_workspace_lead(lead_id: str, body: SendBody | None = None) -> dict[str, Any]:
    """Mark outreach sent (and optionally dry-run). Persists stage + sent ledger."""
    body = body or SendBody()
    lead = _find_workspace_lead(lead_id)
    email = str(lead.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Lead has no email")

    subject = (body.subject or lead.get("subject") or "").strip()
    text = (body.body or lead.get("body") or "").strip()
    if not subject or not text:
        # auto-draft if missing
        drafted = await draft_workspace_lead(lead_id)
        subject = str(drafted.get("subject") or subject)
        text = str(drafted.get("body") or text)
        lead = drafted.get("lead") or lead

    if body.dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "to_email": email,
            "subject": subject,
            "body": text,
            "lead": lead,
        }

    le = _engine()
    try:
        le._persist_sent_emails({email})  # noqa: SLF001
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sent ledger update failed: %s", exc)

    stages = _load_stages()
    stages[email] = "contacted"
    _save_stages(stages)

    data = _load_json(OUTREACH_PATH, {"campaigns": []})
    campaigns = list(data.get("campaigns") or [])
    for c in campaigns:
        if str(c.get("email") or "").lower() == email:
            c["status"] = "sent"
            c["subject"] = subject
            c["body"] = text
            c["sent_at"] = _now_iso()
            c["delivered_at"] = _now_iso()
    _save_json(OUTREACH_PATH, {"updated_at": _now_iso(), "campaigns": campaigns})

    # Keep pool draft fields in sync
    _persist_draft_on_pool(email, subject, text)

    lead["stage"] = "contacted"
    lead["status"] = "contacted"
    lead["outreach_status"] = "sent"
    lead["subject"] = subject
    lead["body"] = text
    _append_activity(
        "outreach_sent",
        f"Marked sent to {lead.get('company_name')} <{email}>",
        {"email": email, "subject": subject[:80]},
    )
    return {"ok": True, "dry_run": False, "to_email": email, "subject": subject, "lead": lead}


@router.get("/overview")
async def workspace_overview() -> dict[str, Any]:
    leads = _build_workspace_leads()
    campaigns = _sync_outreach_from_leads(leads)
    counts = _stage_counts(leads)
    contacted_plus = counts["contacted"] + counts["replied"] + counts["meeting"] + counts["won"]
    total = len(leads) or 1
    activity = _load_json(ACTIVITY_PATH, {"feed": []}).get("feed") or []
    le = _engine()
    pool_count = len(le.load_outreach_pool() or [])
    return {
        "generated_at": _now_iso(),
        "kpis": {
            "total_leads": len(leads),
            "new_today": counts["new"],
            "in_pipeline": len(leads),
            "contacted": counts["contacted"],
            "replied": counts["replied"],
            "meeting": counts["meeting"],
            "won": counts["won"],
            "lost": counts["lost"],
            "pool_count": pool_count,
            "conversion_rate": round(counts["won"] / total * 100, 1),
            "contact_rate": round(contacted_plus / total * 100, 1),
        },
        "stage_counts": counts,
        "funnel": [
            {"label": "Discovered", "value": len(leads), "percentage": 100.0},
            {
                "label": "Contacted",
                "value": contacted_plus,
                "percentage": round(contacted_plus / total * 100, 1),
            },
            {
                "label": "Replied",
                "value": counts["replied"] + counts["meeting"] + counts["won"],
                "percentage": round((counts["replied"] + counts["meeting"] + counts["won"]) / total * 100, 1),
            },
            {
                "label": "Meeting",
                "value": counts["meeting"] + counts["won"],
                "percentage": round((counts["meeting"] + counts["won"]) / total * 100, 1),
            },
            {
                "label": "Won",
                "value": counts["won"],
                "percentage": round(counts["won"] / total * 100, 1),
            },
        ],
        "outreach": _outreach_stats(campaigns),
        "revenue": {
            "pipeline_value": int(sum(float(x.get("intent_score") or 0) * 120 for x in leads if x.get("stage") != "lost")),
            "won_revenue": int(counts["won"] * 15000),
            "avg_deal_size": 15000 if counts["won"] else 12000,
            "win_rate": round(counts["won"] / total * 100, 1),
        },
        "top_leads": [x for x in leads if x.get("stage") == "new"][:20] or leads[:12],
        "new_leads": [x for x in leads if x.get("stage") == "new"][:20],
        "department_counts": {
            "COMAI": sum(1 for x in leads if str(x.get("department") or "") == "COMAI"),
            "Inowix": sum(1 for x in leads if str(x.get("department") or "") == "Inowix"),
            "Cyber": sum(1 for x in leads if str(x.get("department") or "") == "Cyber"),
        },
        "filter_counts": {
            "all": len(leads),
            "new": counts["new"],
            "not_contacted": counts["new"],
            "contacted": contacted_plus,
            "with_data": sum(1 for x in leads if x.get("has_contact_data")),
        },
        "feed": activity[:20],
        "source": "lead_engine_workspace",
    }


@router.get("/outreach")
async def workspace_outreach(limit: int = 100) -> dict[str, Any]:
    leads = _build_workspace_leads()
    campaigns = _sync_outreach_from_leads(leads)[: max(1, min(limit, 300))]
    stats = _outreach_stats(campaigns)
    return {
        "campaigns": campaigns,
        "total": len(campaigns),
        "pending": stats["pending"],
        "sent": stats["sent"],
        "delivered": stats["delivered"],
        "replied": stats["replied"],
        "bounced": stats["bounced"],
        "dashboard": {
            **stats,
            "total_campaigns": len(campaigns),
            "needs_review": stats["pending"],
            "approved_or_scheduled": stats["sent"],
            "by_status": {
                "pending": stats["pending"],
                "sent": stats["sent"],
                "delivered": stats["delivered"],
                "replied": stats["replied"],
                "bounced": stats["bounced"],
            },
        },
        "source": "lead_engine_workspace",
    }


@router.post("/outreach/{campaign_id}/approve")
async def approve_outreach(campaign_id: str) -> dict[str, Any]:
    data = _load_json(OUTREACH_PATH, {"campaigns": []})
    campaigns = list(data.get("campaigns") or [])
    found = None
    for c in campaigns:
        if str(c.get("id")) == campaign_id:
            c["status"] = "sent"
            c["sent_at"] = _now_iso()
            c["delivered_at"] = _now_iso()
            found = c
            email = str(c.get("email") or "").lower()
            if email:
                stages = _load_stages()
                if stages.get(email) in (None, "new"):
                    stages[email] = "contacted"
                    _save_stages(stages)
            break
    if not found:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _save_json(OUTREACH_PATH, {"updated_at": _now_iso(), "campaigns": campaigns})
    _append_activity("outreach_approve", f"Approved outreach to {found.get('company_name')}", {"id": campaign_id})
    return {"ok": True, "campaign": found}


@router.post("/outreach/{campaign_id}/reject")
async def reject_outreach(campaign_id: str) -> dict[str, Any]:
    data = _load_json(OUTREACH_PATH, {"campaigns": []})
    campaigns = list(data.get("campaigns") or [])
    found = None
    kept = []
    for c in campaigns:
        if str(c.get("id")) == campaign_id:
            found = c
            email = str(c.get("email") or "").lower()
            if email:
                stages = _load_stages()
                stages[email] = "lost"
                _save_stages(stages)
            continue
        kept.append(c)
    if not found:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _save_json(OUTREACH_PATH, {"updated_at": _now_iso(), "campaigns": kept})
    return {"ok": True, "rejected": campaign_id}


@router.get("/analytics")
async def workspace_analytics() -> dict[str, Any]:
    overview = await workspace_overview()
    return {
        "kpis": overview["kpis"],
        "funnel": overview["funnel"],
        "stage_counts": overview["stage_counts"],
        "revenue": overview["revenue"],
        "pipeline_distribution": overview["stage_counts"],
        "source": "lead_engine_workspace",
    }


@router.get("/activity")
async def workspace_activity(limit: int = 30) -> dict[str, Any]:
    feed = (_load_json(ACTIVITY_PATH, {"feed": []}).get("feed") or [])[:limit]
    return {"feed": feed, "count": len(feed)}
