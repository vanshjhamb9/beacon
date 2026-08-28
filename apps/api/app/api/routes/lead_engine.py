"""Lead Engine API — ICP filters → extract/enrich/score → draft → approve send."""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lead-engine", tags=["lead-engine"])

# routes → api → app → api → apps → repo root
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Per-run send lock to prevent concurrent sends for the same run
_send_locks: dict[str, asyncio.Lock] = {}


def _engine():
    try:
        from packages import lead_engine as le
    except ImportError:
        import lead_engine as le  # type: ignore
    return le


class LeadEngineICP(BaseModel):
    key: str | None = None
    name: str | None = None
    service_match: str | None = None
    employee_count_min: int | None = None
    employee_count_max: int | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    industries: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    headquarters_cities: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)
    company_types: list[str] = Field(default_factory=list)
    year_founded_min: int | None = None
    year_founded_max: int | None = None
    linkedin_url_required: bool = False
    company_name_contains: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    lists: list[str] = Field(default_factory=list)
    funding_stages: list[str] = Field(default_factory=list)
    hiring_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)


class StartRunBody(BaseModel):
    product: str = Field(default="comai", description="comai | inowix | cyber | comai_b2b")
    limit: int = Field(default=80, ge=1, le=150)
    icp: LeadEngineICP = Field(default_factory=LeadEngineICP)


class EnrichBody(BaseModel):
    lead_ids: list[str] = Field(default_factory=list)


class DraftsBody(BaseModel):
    lead_ids: list[str] | None = None


class SendBody(BaseModel):
    lead_ids: list[str] = Field(default_factory=list)
    dry_run: bool = False


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    leads = job.get("leads") or []
    top = []
    for lead in leads[:8]:
        top.append(
            {
                "company": lead.get("company"),
                "email": lead.get("email"),
                "intent_score": lead.get("intent_score"),
                "grade": lead.get("grade"),
                "signal_families": lead.get("signal_families") or [],
                "icp_tier": lead.get("icp_tier"),
            }
        )
    return {
        "run_id": job["run_id"],
        "product": job["product"],
        "rejects": job.get("rejects") or {},
        "soft_flags": job.get("soft_flags") or {},
        "status": job["status"],
        "stage": job["stage"],
        "progress_pct": job.get("progress_pct") or 0,
        "stage_label": job.get("stage_label") or job.get("stage"),
        "counts": job.get("counts") or {},
        "error": job.get("error"),
        "limit": job.get("limit"),
        "icp": job.get("icp") or {},
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "elapsed_seconds": (
            (job.get("finished_at") or time.time()) - job["started_at"]
            if job.get("started_at")
            else None
        ),
        "export_csv": job.get("export_csv"),
        "lead_count": len(leads),
        "top_leads": top,
        "enrich_status": job.get("enrich_status") or "idle",
        "enrich_progress_pct": job.get("enrich_progress_pct") or 0,
        "enrich_label": job.get("enrich_label") or "",
        "auto": None,
    }


class AutoStartBody(BaseModel):
    product: str = Field(default="comai")
    limit: int = Field(default=40, ge=1, le=150)
    interval_sec: int = Field(default=600, ge=120, le=3600)
    icp: LeadEngineICP = Field(default_factory=LeadEngineICP)


@router.get("/auto")
async def auto_status() -> dict[str, Any]:
    le = _engine()
    return le.get_auto_status()


@router.post("/auto/start")
async def auto_start(body: AutoStartBody) -> dict[str, Any]:
    le = _engine()
    product = body.product.lower().strip()
    if product not in ("comai", "inowix", "cyber", "comai_b2b"):
        raise HTTPException(status_code=400, detail="product must be comai, inowix, cyber, or comai_b2b")
    return le.start_auto_scheduler(
        product=product,
        icp=body.icp.model_dump(),
        limit=body.limit,
        interval_sec=body.interval_sec,
    )


@router.post("/auto/stop")
async def auto_stop() -> dict[str, Any]:
    le = _engine()
    return le.stop_auto_scheduler()


@router.get("/pool")
async def outreach_pool(limit: int = 100) -> dict[str, Any]:
    le = _engine()
    sent = le._load_sent_emails()  # noqa: SLF001
    leads = [
        x
        for x in le.load_outreach_pool()
        if (x.get("email") or "").lower() not in sent
    ][:limit]
    return {"count": len(leads), "leads": leads}


@router.post("/pool/load")
async def load_pool_into_run(limit: int = 40, product: str = "comai") -> dict[str, Any]:
    """Create a synthetic completed run from the accumulated NEW outreach pool."""
    le = _engine()
    # Create run first so if take_from_outreach_pool fails, no leads are lost
    job = le.create_run(product=product, icp={}, limit=limit)
    try:
        leads = le.take_from_outreach_pool(limit=limit)
    except Exception:
        # If pool take fails, clean up the empty run
        le._JOBS.pop(job["run_id"], None)
        raise HTTPException(status_code=500, detail="failed to take leads from outreach pool")
    if not leads:
        le._JOBS.pop(job["run_id"], None)
        raise HTTPException(status_code=404, detail="outreach pool empty — start Auto-run or Start Engine first")
    for lead in leads:
        email = (lead.get("email") or "").lower().strip()
        lead["email"] = email
        lead["to_email"] = email
        if not lead.get("id"):
            import uuid as _uuid

            lead["id"] = str(_uuid.uuid5(_uuid.NAMESPACE_URL, email))
    job["leads"] = leads
    job["status"] = "completed"
    job["stage"] = "ready"
    job["progress_pct"] = 100
    job["stage_label"] = f"Loaded {len(leads)} pooled NEW high-intent leads"
    job["counts"]["scored"] = len(leads)
    job["counts"]["ready"] = len(leads)
    job["counts"]["new_unique"] = len(leads)
    job["finished_at"] = time.time()
    le._export_run(job["run_id"], job)  # noqa: SLF001
    return _public_job(job)


@router.get("/presets")
async def lead_engine_presets() -> dict[str, Any]:
    """Return YAML ICP presets for COMAI / Inowix / COMAI B2B."""
    try:
        from packages.qualification_engine.icp_loader import load_icp
    except ImportError:
        from qualification_engine.icp_loader import load_icp  # type: ignore

    out: dict[str, Any] = {}
    for key in ("comai", "inowix", "cyber", "comai_b2b"):
        try:
            icp = load_icp(key)
            out[key] = {
                "key": key,
                "name": icp.name,
                "description": icp.description,
                "employee_count_min": icp.min_employees,
                "employee_count_max": icp.max_employees,
                "industries": list(icp.target_industries),
                "specialties": list(icp.target_industries),
                "countries": list(icp.target_countries),
                "headquarters_cities": list(icp.target_cities),
                "technology_stack": list(icp.target_platforms),
                "company_types": (
                    ["d2c_brand"] if key == "comai" else ["saas_product"] if key == "inowix" else ["agency_partner"] if key == "comai_b2b" else ["saas_product"]
                ),
                "lists": [icp.name],
            }
        except Exception as exc:  # noqa: BLE001
            out[key] = {"key": key, "error": str(exc)}
    return {"presets": out}


@router.post("/runs")
async def start_run(body: StartRunBody) -> dict[str, Any]:
    le = _engine()
    product = body.product.lower().strip()
    if product not in ("comai", "inowix", "cyber", "comai_b2b"):
        raise HTTPException(status_code=400, detail="product must be comai, inowix, cyber, or comai_b2b")
    job = le.create_run(product=product, icp=body.icp.model_dump(), limit=body.limit)
    asyncio.create_task(le.run_pipeline(job["run_id"]))
    return _public_job(job)


@router.get("/runs")
async def list_runs(limit: int = 20) -> dict[str, Any]:
    le = _engine()
    return {"runs": [_public_job(j) for j in le.list_jobs(limit=limit)]}


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    return _public_job(job)


@router.get("/runs/{run_id}/leads")
async def get_leads(run_id: str, min_score: float = 0) -> dict[str, Any]:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    leads = [x for x in (job.get("leads") or []) if float(x.get("intent_score") or 0) >= min_score]
    return {"run_id": run_id, "count": len(leads), "leads": leads}


@router.post("/runs/{run_id}/enrich")
async def enrich_leads(run_id: str, body: EnrichBody) -> dict[str, Any]:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    if job.get("status") not in ("completed", "running"):
        raise HTTPException(status_code=400, detail="run not ready for enrichment")
    if not body.lead_ids:
        raise HTTPException(status_code=400, detail="lead_ids required")
    if job.get("enrich_status") == "running":
        return _public_job(job)

    job["enrich_status"] = "running"
    job["enrich_progress_pct"] = 1
    job["enrich_label"] = "Starting enrichment…"
    asyncio.create_task(le.run_enrichment(run_id, body.lead_ids))
    return _public_job(job)


@router.post("/runs/{run_id}/drafts")
async def create_drafts(run_id: str, body: DraftsBody) -> dict[str, Any]:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="run must be completed before drafting")
    drafts = le.generate_drafts(run_id, body.lead_ids)
    return {"run_id": run_id, "count": len(drafts), "drafts": drafts}


@router.post("/runs/{run_id}/send")
async def send_approved(run_id: str, body: SendBody) -> dict[str, Any]:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    if not body.lead_ids:
        raise HTTPException(status_code=400, detail="lead_ids required")

    # Per-run lock to prevent concurrent sends
    lock = _send_locks.setdefault(run_id, asyncio.Lock())
    if lock.locked():
        raise HTTPException(status_code=409, detail="send already in progress for this run")

    async with lock:
        result = await asyncio.to_thread(_send_loop, le, job, body)

    sent_emails = [
        str(r.get("to_email") or "")
        for r in result["results"]
        if r.get("success") and r.get("to_email")
    ]
    if sent_emails:
        try:
            le._persist_sent_emails(sent_emails)  # noqa: SLF001
        except Exception:  # noqa: BLE001
            pass

    job["counts"]["sent"] = result["sent"]
    le._export_run(run_id, job)  # noqa: SLF001
    return {
        "run_id": run_id,
        "sent": result["sent"],
        "attempted": result["attempted"],
        "results": result["results"],
        "cc": result["cc"],
    }


def _send_loop(le, job: dict, body: SendBody) -> dict[str, Any]:
    """Blocking send loop — runs in a thread via asyncio.to_thread."""
    try:
        from packages.outreach_generator.hyperpersonal import draft_for_product, html_body
    except ImportError:
        from outreach_generator.hyperpersonal import draft_for_product, html_body  # type: ignore

    sys.path.insert(0, str(ROOT))
    try:
        from email_service import send_email
    except ImportError as exc:
        return {"sent": 0, "attempted": 0, "results": [{"error": f"email_service unavailable: {exc}"}], "cc": []}

    cc = ["vanshjhamb9@gmail.com", "ragibali84@gmail.com"]
    product = job["product"]
    idset = set(body.lead_ids)
    results: list[dict[str, Any]] = []
    sent = 0

    for lead in job.get("leads") or []:
        if lead.get("id") not in idset:
            continue
        if not lead.get("subject") or not lead.get("body"):
            d = draft_for_product(product, lead)
            lead["subject"] = d.subject
            lead["body"] = d.body
        email = lead.get("email")
        if not email:
            results.append({"lead_id": lead.get("id"), "success": False, "error": "no email"})
            continue
        if lead.get("already_contacted"):
            results.append(
                {
                    "lead_id": lead.get("id"),
                    "to_email": email,
                    "success": False,
                    "error": "already_contacted — skipped to avoid duplicate outreach",
                }
            )
            continue
        if body.dry_run:
            results.append(
                {
                    "lead_id": lead["id"],
                    "to_email": email,
                    "subject": lead["subject"],
                    "success": True,
                    "dry_run": True,
                }
            )
            lead["outreach_status"] = "dry_run"
            continue

        res = send_email(
            to_email=email,
            subject=lead["subject"],
            body_html=html_body(lead["body"]),
            body_text=lead["body"],
            from_name=(
                "Vansh Jhamb | COMAI"
                if product == "comai"
                else "Vansh Jhamb | Inowix"
            ),
            cc=cc,
            retries=2,
            retry_backoff_sec=8,
        )
        ok = bool(res.get("success"))
        if ok:
            sent += 1
            lead["outreach_status"] = "sent"
        else:
            lead["outreach_status"] = "failed"
        results.append(
            {
                "lead_id": lead["id"],
                "to_email": email,
                "subject": lead["subject"],
                "success": ok,
                "error": res.get("error"),
            }
        )
        # Continue processing all leads — don't break on failure
        time.sleep(10)

    return {"sent": sent, "attempted": len(results), "results": results, "cc": cc}


@router.get("/runs/{run_id}/export")
async def export_csv(run_id: str) -> FileResponse:
    le = _engine()
    job = le.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="run not found")
    path = job.get("export_csv")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="export not ready")
    return FileResponse(path, filename=f"lead_engine_{run_id}.csv", media_type="text/csv")
