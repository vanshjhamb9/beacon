"""Celery tasks for COMAI Partner Outreach."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from celery import shared_task

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages"))

logger = logging.getLogger(__name__)


def _service():
    from comai_partner_outreach.service import PartnerOutreachService

    return PartnerOutreachService()


@shared_task(name="comai_partner_outreach.process_campaign", bind=True, max_retries=3)
def process_partner_campaign(self, campaign_id: str, max_sends: int = 25):
    try:
        return _service().process_campaign(campaign_id, max_sends=max_sends)
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_partner_campaign failed: %s", exc)
        raise self.retry(exc=exc, countdown=60) from exc


@shared_task(name="comai_partner_outreach.process_sending_queue")
def process_sending_queue(max_sends: int = 25):
    return _service().process_all_sending(max_sends=max_sends)


@shared_task(name="comai_partner_outreach.tick_followups")
def tick_partner_followups(max_sends: int = 20):
    return _service().tick_followups(max_sends=max_sends)


@shared_task(name="comai_partner_outreach.ingest_gmail_replies")
def ingest_gmail_replies():
    """Best-effort bridge: classify any recent reply payloads dumped for the program.

    Primary reply path is POST /partner-outreach/replies/ingest (wired from
    communication sync or manual). This task scans a lightweight inbox file if present.
    """
    svc = _service()
    inbox_path = ROOT / "exports" / "comai_partner_outreach" / "pending_replies.json"
    if not inbox_path.exists():
        return {"ingested": 0, "scanned": 0}
    try:
        import json

        payload = json.loads(inbox_path.read_text(encoding="utf-8"))
        replies = payload if isinstance(payload, list) else payload.get("replies") or []
        ingested = 0
        remaining = []
        for item in replies:
            from_email = item.get("from_address") or item.get("from_email") or item.get("from") or ""
            body = item.get("body_text") or item.get("snippet") or ""
            if not from_email or not body:
                remaining.append(item)
                continue
            matched = svc.ingest_reply(
                from_email=str(from_email),
                body_text=str(body),
                subject=str(item.get("subject") or ""),
                provider_message_id=str(item.get("provider_message_id") or ""),
                thread_id=str(item.get("thread_id") or ""),
                in_reply_to=str(item.get("in_reply_to") or ""),
            )
            if matched:
                ingested += 1
            else:
                remaining.append(item)
        inbox_path.write_text(json.dumps(remaining, indent=2), encoding="utf-8")
        return {"ingested": ingested, "scanned": len(replies), "remaining": len(remaining)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("ingest_gmail_replies failed: %s", exc)
        return {"ingested": 0, "error": str(exc)}
