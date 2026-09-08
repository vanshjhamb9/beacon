"""Orchestration service for COMAI partner outreach campaigns."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from comai_partner_outreach.config import PartnerOutreachConfig, load_config
from comai_partner_outreach.drafting import draft_for_step
from comai_partner_outreach.ingest import parse_upload
from comai_partner_outreach.rate_limit import RateLimitState, check_send_gate, record_send
from comai_partner_outreach.replies import classify_reply
from comai_partner_outreach.sender import send_partner_email
from comai_partner_outreach.sequence import is_followup_due, next_step_after, schedule_after_step
from comai_partner_outreach.store import PartnerOutreachStore
from comai_partner_outreach.types import (
    PartnerCampaign,
    PartnerEvent,
    PartnerLead,
    PartnerMessage,
    new_id,
    now_iso,
)

logger = logging.getLogger(__name__)


class PartnerOutreachService:
    def __init__(
        self,
        store: PartnerOutreachStore | None = None,
        config: PartnerOutreachConfig | None = None,
    ) -> None:
        self.store = store or PartnerOutreachStore()
        self.config = config or load_config()

    def _event(self, campaign_id: str, event_type: str, lead_id: str | None = None, **detail: Any) -> None:
        self.store.append_event(
            PartnerEvent(
                id=new_id(),
                campaign_id=campaign_id,
                lead_id=lead_id,
                event_type=event_type,
                detail=detail,
            )
        )

    def _draft_leads(self, campaign_id: str, leads: list[PartnerLead]) -> int:
        """Draft intro copy for leads that still need it (uploaded / empty body)."""
        drafted = 0
        events: list[PartnerEvent] = []
        skip_stages = {
            "sent",
            "replied",
            "interested",
            "meeting",
            "partner_onboarded",
            "lost",
            "failed",
            "nurture",
            "killed",
        }
        for lead in leads:
            if lead.stage in skip_stages:
                continue
            if lead.stage == "drafted" and (lead.body_text or "").strip():
                continue
            draft = draft_for_step(lead.sequence_step or "intro", lead.to_dict(), self.config)
            lead.subject = draft.subject
            lead.body_text = draft.body_text
            lead.body_html = draft.body_html
            lead.sequence_step = lead.sequence_step or "intro"
            lead.stage = "drafted"
            lead.error = ""
            lead.updated_at = now_iso()
            drafted += 1
            events.append(
                PartnerEvent(
                    id=new_id(),
                    campaign_id=campaign_id,
                    lead_id=lead.id,
                    event_type="drafted",
                    detail={"subject": draft.subject, "hook": draft.hook_used},
                )
            )
        if drafted:
            self.store.save_leads(campaign_id, leads)
            self.store.append_events(events)
        return drafted

    def create_campaign_from_upload(
        self,
        *,
        filename: str,
        content: bytes,
        name: str | None = None,
    ) -> dict[str, Any]:
        campaign_id = new_id()
        campaign = PartnerCampaign(
            id=campaign_id,
            name=name or f"Partner outreach — {filename}",
            status="validating",
            video_url=self.config.video_url,
            config_snapshot={
                "commission_pct": self.config.commission_pct,
                "trial_days": self.config.trial_days,
                "video_url": self.config.video_url,
                "dry_run": self.config.dry_run,
                "enabled": self.config.enabled,
            },
        )
        self.store.save_campaign(campaign)
        self._event(campaign_id, "uploaded", filename=filename)

        ingested = parse_upload(
            filename=filename,
            content=content,
            campaign_id=campaign_id,
            config=self.config,
            already_sent=self.store.load_sent_emails(),
        )
        campaign.total_rows = ingested.total_rows
        campaign.valid_rows = ingested.valid_rows
        campaign.skipped_rows = ingested.skipped_rows
        campaign.row_errors = ingested.errors
        campaign.status = "drafting"
        self.store.save_campaign(campaign)
        self.store.save_leads(campaign_id, ingested.leads)

        drafted = self._draft_leads(campaign_id, ingested.leads)
        campaign.drafted = drafted
        campaign.status = "sending"
        self.store.save_campaign(campaign)

        # Auto-process immediately so upload → send (or dry-run) without extra clicks
        process_result: dict[str, Any] | None = None
        try:
            process_result = self.process_campaign(campaign_id, max_sends=max(drafted, 1))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Auto-process after upload failed: %s", exc)
            process_result = {"error": str(exc)}

        campaign = self.store.get_campaign(campaign_id) or campaign
        return {
            "campaign": campaign.to_dict(),
            "valid_rows": ingested.valid_rows,
            "skipped_rows": ingested.skipped_rows,
            "errors": ingested.errors[:50],
            "dry_run": self.config.dry_run,
            "enabled": self.config.enabled,
            "process": process_result,
        }

    def get_campaign(self, campaign_id: str) -> dict[str, Any] | None:
        campaign = self.store.get_campaign(campaign_id)
        if not campaign:
            return None
        return campaign.to_dict()

    def list_campaigns(self) -> list[dict[str, Any]]:
        out = []
        for cid in self.store.list_campaign_ids():
            c = self.store.get_campaign(cid)
            if c:
                out.append(c.to_dict())
        return out

    def kill_campaign(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        if not campaign:
            raise KeyError("campaign_not_found")
        campaign.kill_flag = True
        campaign.status = "killed"
        self.store.save_campaign(campaign)
        self._event(campaign_id, "kill_switch", reason="manual_kill")
        return campaign.to_dict()

    def resume_campaign(self, campaign_id: str) -> dict[str, Any]:
        if not self.config.enabled and not self.config.dry_run:
            raise PermissionError("Global kill switch is off")
        campaign = self.store.get_campaign(campaign_id)
        if not campaign:
            raise KeyError("campaign_not_found")
        campaign.kill_flag = False
        campaign.status = "sending"
        self.store.save_campaign(campaign)
        self._event(campaign_id, "resumed")
        return campaign.to_dict()

    def clear_all_campaigns(self) -> dict[str, Any]:
        result = self.store.clear_all_campaigns()
        return {**result, "metrics": self.metrics()}

    def get_leads(self, campaign_id: str, stage: str | None = None) -> list[dict[str, Any]]:
        leads = self.store.get_leads(campaign_id)
        if stage:
            leads = [l for l in leads if l.stage == stage]
        return [l.to_dict() for l in leads]

    def pipeline(self) -> dict[str, Any]:
        buckets: dict[str, list[dict[str, Any]]] = {}
        for lead in self.store.all_leads():
            buckets.setdefault(lead.stage, []).append(
                {
                    "id": lead.id,
                    "campaign_id": lead.campaign_id,
                    "agency_name": lead.agency_name,
                    "email": lead.email,
                    "stage": lead.stage,
                    "sequence_step": lead.sequence_step,
                    "reply_class": lead.reply_class,
                }
            )
        return {"stages": buckets, "counts": {k: len(v) for k, v in buckets.items()}}

    def inbox(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.store.inbox(limit=limit)

    def set_lead_stage(self, lead_id: str, stage: str, note: str = "") -> dict[str, Any]:
        for lead in self.store.all_leads():
            if lead.id != lead_id:
                continue
            lead.stage = stage
            if note:
                lead.notes = (lead.notes + "\n" + note).strip() if lead.notes else note
            lead.updated_at = now_iso()
            if stage in ("interested", "meeting", "partner_onboarded", "lost", "unsubscribed", "bounced"):
                lead.stop_reason = stage
                lead.next_followup_at = None
            self.store.upsert_lead(lead)
            self._event(lead.campaign_id, "stage_changed", lead.id, stage=stage, note=note)
            return lead.to_dict()
        raise KeyError("lead_not_found")

    def _rate_state(self) -> RateLimitState:
        return RateLimitState.from_dict(self.store.load_rate_state())

    def _save_rate(self, state: RateLimitState) -> None:
        self.store.save_rate_state(state.to_dict())

    def process_campaign(self, campaign_id: str, *, max_sends: int = 100) -> dict[str, Any]:
        campaign = self.store.get_campaign(campaign_id)
        if not campaign:
            raise KeyError("campaign_not_found")
        if campaign.kill_flag or campaign.status == "killed":
            return {"campaign_id": campaign_id, "status": "killed", "sent": 0, "held_reason": "killed"}

        leads = self.store.get_leads(campaign_id)
        # Recover stuck uploads (Windows write failures mid-draft, etc.)
        drafted_now = self._draft_leads(campaign_id, leads)
        if drafted_now:
            leads = self.store.get_leads(campaign_id)
            if campaign.status in ("completed", "validating", "drafting"):
                campaign.status = "sending"
                self.store.save_campaign(campaign)

        rate = self._rate_state()
        sent = 0
        failed = 0
        held = 0
        held_reason = ""
        held_code = ""

        for lead in leads:
            if sent >= max_sends:
                break
            if lead.stage not in ("drafted", "queued"):
                continue
            if lead.sequence_step and lead.sequence_step != "intro" and lead.stage == "drafted":
                if lead.last_sent_at:
                    continue

            gate = check_send_gate(self.config, rate, campaign_killed=campaign.kill_flag)
            if not gate.allowed:
                if gate.code == "rate_gap" and gate.retry_after_seconds > 0:
                    import time

                    time.sleep(min(gate.retry_after_seconds, 120))
                    gate = check_send_gate(self.config, rate, campaign_killed=campaign.kill_flag)
                if not gate.allowed:
                    held += 1
                    held_reason = gate.reason
                    held_code = gate.code
                    lead.stage = "queued"
                    lead.error = gate.reason
                    self.store.upsert_lead(lead)
                    self._event(campaign_id, "held", lead.id, reason=gate.reason, code=gate.code)
                    break

            if not lead.body_text:
                draft = draft_for_step(lead.sequence_step or "intro", lead.to_dict(), self.config)
                lead.subject = draft.subject
                lead.body_text = draft.body_text
                lead.body_html = draft.body_html

            lead.stage = "queued"
            lead.send_attempts += 1
            result = send_partner_email(
                to_email=lead.email,
                subject=lead.subject,
                body_text=lead.body_text,
                body_html=lead.body_html,
                config=self.config,
                campaign_id=campaign_id,
            )
            msg = PartnerMessage(
                id=new_id(),
                campaign_id=campaign_id,
                lead_id=lead.id,
                direction="outbound",
                step=lead.sequence_step or "intro",
                subject=lead.subject,
                body_text=lead.body_text,
                body_html=lead.body_html,
                delivery_state="sent" if result.ok else "failed",
                provider_message_id=result.provider_message_id,
                thread_id=result.thread_id,
            )
            self.store.append_message(msg)

            if result.ok:
                lead.stage = "sent"
                lead.last_sent_at = now_iso()
                lead.error = "dry_run" if result.dry_run else ""
                nxt = schedule_after_step(lead.sequence_step or "intro", self.config)
                lead.next_followup_at = nxt.isoformat() if nxt else None
                rate = record_send(rate)
                self._save_rate(rate)
                self.store.mark_sent_email(lead.email)
                sent += 1
                self._event(
                    campaign_id,
                    "sent",
                    lead.id,
                    dry_run=result.dry_run,
                    provider_message_id=result.provider_message_id,
                )
            else:
                lead.error = result.error or "send_failed"
                if lead.send_attempts >= self.config.max_send_retries:
                    lead.stage = "failed"
                    lead.stop_reason = "send_failed"
                    failed += 1
                self._event(campaign_id, "failed", lead.id, error=lead.error)
            self.store.upsert_lead(lead)

        leads = self.store.get_leads(campaign_id)
        campaign.drafted = sum(1 for l in leads if l.stage == "drafted")
        campaign.queued = sum(1 for l in leads if l.stage == "queued")
        campaign.sent = sum(
            1
            for l in leads
            if l.stage in ("sent", "replied", "interested", "meeting", "partner_onboarded", "nurture")
        )
        campaign.failed = sum(1 for l in leads if l.stage == "failed")
        remaining = sum(1 for l in leads if l.stage in ("uploaded", "drafted", "queued"))
        if remaining == 0 and not campaign.kill_flag:
            campaign.status = "completed"
        else:
            campaign.status = "sending" if not campaign.kill_flag else "killed"
        self.store.save_campaign(campaign)
        return {
            "campaign_id": campaign_id,
            "status": campaign.status,
            "sent": sent,
            "failed": failed,
            "held": held,
            "held_reason": held_reason,
            "held_code": held_code,
            "drafted_now": drafted_now,
            "dry_run": self.config.dry_run,
            "enabled": self.config.enabled,
            "remaining": remaining,
            "total_leads": len(leads),
            "message": (
                f"{'Dry-run: simulated' if self.config.dry_run else 'Sent'} {sent} email(s)."
                + (f" Drafted {drafted_now}." if drafted_now else "")
                + (f" Held: {held_reason}" if held_reason else "")
                + (
                    " Enable live send with COMAI_PARTNER_OUTREACH_ENABLED=true and "
                    "COMAI_PARTNER_OUTREACH_DRY_RUN=false."
                    if self.config.dry_run
                    else ""
                )
            ),
        }

    def process_all_sending(self, *, max_sends: int = 25) -> list[dict[str, Any]]:
        results = []
        for cid in self.store.list_campaign_ids():
            c = self.store.get_campaign(cid)
            if not c or c.kill_flag or c.status in ("killed", "completed", "paused"):
                continue
            if c.status in ("sending", "drafting"):
                results.append(self.process_campaign(cid, max_sends=max_sends))
        return results

    def tick_followups(self, *, max_sends: int = 20) -> dict[str, Any]:
        rate = self._rate_state()
        sent = 0
        skipped = 0
        for lead in self.store.all_leads():
            if sent >= max_sends:
                break
            if not is_followup_due(lead.to_dict()):
                continue
            campaign = self.store.get_campaign(lead.campaign_id)
            if not campaign or campaign.kill_flag or campaign.status == "killed":
                skipped += 1
                continue
            nxt = next_step_after(lead.sequence_step or "intro")
            if not nxt:
                lead.stage = "nurture"
                lead.stop_reason = "sequence_exhausted"
                lead.next_followup_at = (
                    datetime.now(UTC) + timedelta(days=self.config.nurture_reentry_days)
                ).isoformat()
                self.store.upsert_lead(lead)
                continue

            gate = check_send_gate(self.config, rate, campaign_killed=campaign.kill_flag)
            if not gate.allowed:
                break

            draft = draft_for_step(nxt, lead.to_dict(), self.config)
            lead.sequence_step = nxt
            lead.subject = draft.subject
            lead.body_text = draft.body_text
            lead.body_html = draft.body_html
            result = send_partner_email(
                to_email=lead.email,
                subject=lead.subject,
                body_text=lead.body_text,
                body_html=lead.body_html,
                config=self.config,
                campaign_id=lead.campaign_id,
            )
            self.store.append_message(
                PartnerMessage(
                    id=new_id(),
                    campaign_id=lead.campaign_id,
                    lead_id=lead.id,
                    direction="outbound",
                    step=nxt,
                    subject=lead.subject,
                    body_text=lead.body_text,
                    body_html=lead.body_html,
                    delivery_state="sent" if result.ok else "failed",
                    provider_message_id=result.provider_message_id,
                    thread_id=result.thread_id,
                )
            )
            if result.ok:
                lead.last_sent_at = now_iso()
                lead.stage = "sent"
                sched = schedule_after_step(nxt, self.config)
                lead.next_followup_at = sched.isoformat() if sched else None
                if nxt == "final":
                    lead.next_followup_at = None
                    # after final, mark nurture if no reply later via tick; keep sent for now
                rate = record_send(rate)
                self._save_rate(rate)
                sent += 1
                self._event(lead.campaign_id, "followup_sent", lead.id, step=nxt, dry_run=result.dry_run)
            else:
                lead.error = result.error
                self._event(lead.campaign_id, "followup_failed", lead.id, error=result.error)
            self.store.upsert_lead(lead)

        return {"sent": sent, "skipped": skipped, "dry_run": self.config.dry_run}

    def ingest_reply(
        self,
        *,
        from_email: str,
        body_text: str,
        subject: str = "",
        provider_message_id: str = "",
        thread_id: str = "",
        in_reply_to: str = "",
    ) -> dict[str, Any] | None:
        email = (from_email or "").lower().strip()
        matched: PartnerLead | None = None
        for lead in self.store.all_leads():
            if lead.email.lower() == email:
                matched = lead
                break
            if thread_id:
                for msg in self.store.get_messages(lead.campaign_id):
                    if msg.lead_id == lead.id and msg.thread_id and msg.thread_id == thread_id:
                        matched = lead
                        break
            if matched:
                break
        if not matched:
            return None

        classification = classify_reply(body_text)
        self.store.append_message(
            PartnerMessage(
                id=new_id(),
                campaign_id=matched.campaign_id,
                lead_id=matched.id,
                direction="inbound",
                step="manual",
                subject=subject,
                body_text=body_text,
                delivery_state="received",
                provider_message_id=provider_message_id,
                thread_id=thread_id or in_reply_to,
                reply_class=classification.label,
            )
        )
        matched.reply_class = classification.label
        matched.reply_snippet = (body_text or "")[:280]
        matched.stage = classification.stage
        if classification.stop_sequence:
            matched.stop_reason = classification.label
            matched.next_followup_at = None
        elif classification.delay_days:
            matched.next_followup_at = (
                datetime.now(UTC) + timedelta(days=classification.delay_days)
            ).isoformat()
        matched.updated_at = now_iso()
        self.store.upsert_lead(matched)
        campaign = self.store.get_campaign(matched.campaign_id)
        if campaign:
            campaign.replied += 1
            self.store.save_campaign(campaign)
        self._event(
            matched.campaign_id,
            "replied",
            matched.id,
            label=classification.label,
            stage=classification.stage,
            evidence=classification.evidence,
        )
        return {
            "lead_id": matched.id,
            "campaign_id": matched.campaign_id,
            "classification": classification.label,
            "stage": classification.stage,
            "stop_sequence": classification.stop_sequence,
        }

    def metrics(self) -> dict[str, Any]:
        leads = self.store.all_leads()
        sent = sum(1 for l in leads if l.last_sent_at)
        replied = sum(1 for l in leads if l.reply_class)
        interested = sum(1 for l in leads if l.stage in ("interested", "meeting", "partner_onboarded"))
        meetings = sum(1 for l in leads if l.stage == "meeting")
        onboarded = sum(1 for l in leads if l.stage == "partner_onboarded")
        return {
            "campaigns": len(self.store.list_campaign_ids()),
            "leads": len(leads),
            "sent": sent,
            "replied": replied,
            "reply_rate": round(replied / sent, 4) if sent else 0.0,
            "interested": interested,
            "interest_rate": round(interested / sent, 4) if sent else 0.0,
            "meetings": meetings,
            "partners_onboarded": onboarded,
            "enabled": self.config.enabled,
            "dry_run": self.config.dry_run,
        }
