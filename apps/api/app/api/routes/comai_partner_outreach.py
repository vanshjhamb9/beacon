"""COMAI Partner Outreach API — upload Excel → draft → auto-send → pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages"))

from comai_partner_outreach.service import PartnerOutreachService  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partner-outreach", tags=["partner-outreach"])


def _svc() -> PartnerOutreachService:
    return PartnerOutreachService()


class StageUpdateRequest(BaseModel):
    stage: str
    note: str = ""


class ReplyIngestRequest(BaseModel):
    from_email: str
    body_text: str
    subject: str = ""
    provider_message_id: str = ""
    thread_id: str = ""
    in_reply_to: str = ""


class ProcessRequest(BaseModel):
    max_sends: int = Field(default=100, ge=1, le=500)


@router.get("/health")
def health() -> dict[str, Any]:
    svc = _svc()
    return {
        "ok": True,
        "enabled": svc.config.enabled,
        "dry_run": svc.config.dry_run,
        "video_url": svc.config.video_url,
        "commission_pct": svc.config.commission_pct,
    }


@router.get("/metrics")
def metrics() -> dict[str, Any]:
    return _svc().metrics()


@router.get("/campaigns")
def list_campaigns() -> dict[str, Any]:
    return {"campaigns": _svc().list_campaigns()}


@router.post("/campaigns/clear")
def clear_campaigns() -> dict[str, Any]:
    """Wipe all partner outreach campaign history (uploads, drafts, dry-run sends)."""
    return _svc().clear_all_campaigns()


@router.post("/campaigns/upload")
async def upload_campaign(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(400, "filename required")
    content = await file.read()
    if not content:
        raise HTTPException(400, "empty file")
    try:
        result = _svc().create_campaign_from_upload(
            filename=file.filename,
            content=content,
            name=name,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Auto-process runs inside create_campaign_from_upload; Celery continues later.
    try:
        from worker.comai_partner_outreach_tasks import process_partner_campaign

        process_partner_campaign.delay(result["campaign"]["id"])
        result["queued_celery"] = True
    except Exception:  # noqa: BLE001
        result["queued_celery"] = False
    return result


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str) -> dict[str, Any]:
    data = _svc().get_campaign(campaign_id)
    if not data:
        raise HTTPException(404, "campaign not found")
    return data


@router.post("/campaigns/{campaign_id}/kill")
def kill_campaign(campaign_id: str) -> dict[str, Any]:
    try:
        return _svc().kill_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(404, "campaign not found") from exc


@router.post("/campaigns/{campaign_id}/resume")
def resume_campaign(campaign_id: str) -> dict[str, Any]:
    try:
        return _svc().resume_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(404, "campaign not found") from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc


@router.post("/campaigns/{campaign_id}/process")
def process_campaign(campaign_id: str, body: ProcessRequest | None = None) -> dict[str, Any]:
    max_sends = body.max_sends if body else 100
    try:
        return _svc().process_campaign(campaign_id, max_sends=max_sends)
    except KeyError as exc:
        raise HTTPException(404, "campaign not found") from exc


@router.get("/campaigns/{campaign_id}/leads")
def campaign_leads(
    campaign_id: str,
    stage: str | None = Query(default=None),
) -> dict[str, Any]:
    return {"leads": _svc().get_leads(campaign_id, stage=stage)}


@router.get("/pipeline")
def pipeline() -> dict[str, Any]:
    return _svc().pipeline()


@router.get("/inbox")
def inbox(limit: int = Query(default=100, ge=1, le=500)) -> dict[str, Any]:
    return {"items": _svc().inbox(limit=limit)}


@router.post("/leads/{lead_id}/stage")
def update_lead_stage(lead_id: str, body: StageUpdateRequest) -> dict[str, Any]:
    try:
        return _svc().set_lead_stage(lead_id, body.stage, body.note)
    except KeyError as exc:
        raise HTTPException(404, "lead not found") from exc


@router.post("/replies/ingest")
def ingest_reply(body: ReplyIngestRequest) -> dict[str, Any]:
    result = _svc().ingest_reply(
        from_email=body.from_email,
        body_text=body.body_text,
        subject=body.subject,
        provider_message_id=body.provider_message_id,
        thread_id=body.thread_id,
        in_reply_to=body.in_reply_to,
    )
    if not result:
        raise HTTPException(404, "no matching partner lead")
    return result


@router.post("/followups/tick")
def tick_followups(body: ProcessRequest | None = None) -> dict[str, Any]:
    max_sends = body.max_sends if body else 20
    return _svc().tick_followups(max_sends=max_sends)
