"""Reset dry-run partner campaign and send real SMTP emails."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages"))

# Live mode — must be set before config load
os.environ["COMAI_PARTNER_OUTREACH_ENABLED"] = "true"
os.environ["COMAI_PARTNER_OUTREACH_DRY_RUN"] = "false"

from comai_partner_outreach.config import load_config
from comai_partner_outreach.drafting import draft_for_step
from comai_partner_outreach.service import PartnerOutreachService
from comai_partner_outreach.store import PartnerOutreachStore
from comai_partner_outreach.types import now_iso


def main() -> int:
    store = PartnerOutreachStore()
    cfg = load_config()
    cfg = cfg.with_overrides(min_seconds_between_sends=5, max_per_hour=60, max_per_day=200)
    assert cfg.enabled and not cfg.dry_run, "live flags not active"
    svc = PartnerOutreachService(store=store, config=cfg)

    ids = store.list_campaign_ids()
    if not ids:
        print("NO_CAMPAIGNS")
        return 1
    campaign_id = ids[0]
    campaign = store.get_campaign(campaign_id)
    assert campaign
    print("CAMPAIGN", campaign_id, campaign.name)

    # Clear dry-run send tracking / rate state so leads can go live
    store.save_rate_state({})
    store._write_json(store._sent_path, {"emails": []})

    leads = store.get_leads(campaign_id)
    # Only reset leads that were never truly SMTP-sent (dry_run marker or empty provider)
    for lead in leads:
        if lead.stage == "sent" and lead.error != "dry_run" and lead.last_sent_at:
            # Keep already-live-sent leads
            continue
        draft = draft_for_step("intro", lead.to_dict(), cfg)
        lead.subject = draft.subject
        lead.body_text = draft.body_text
        lead.body_html = draft.body_html
        lead.sequence_step = "intro"
        lead.stage = "drafted"
        lead.error = ""
        lead.last_sent_at = None
        lead.next_followup_at = None
        lead.send_attempts = 0
        lead.stop_reason = None
        lead.updated_at = now_iso()
    store.save_leads(campaign_id, leads)

    campaign.status = "sending"
    campaign.kill_flag = False
    live_sent = sum(1 for l in leads if l.stage == "sent")
    campaign.sent = live_sent
    campaign.failed = 0
    campaign.drafted = sum(1 for l in leads if l.stage == "drafted")
    campaign.queued = sum(1 for l in leads if l.stage == "queued")
    campaign.config_snapshot = {
        **(campaign.config_snapshot or {}),
        "dry_run": False,
        "enabled": True,
    }
    store.save_campaign(campaign)
    print("RESET pending", campaign.drafted, "already_live", live_sent, "enabled", cfg.enabled, "dry_run", cfg.dry_run, flush=True)

    total_sent = 0
    for round_i in range(40):
        pending = sum(1 for l in store.get_leads(campaign_id) if l.stage in ("drafted", "queued"))
        if pending == 0:
            break
        print(f"START_ROUND {round_i+1} pending={pending}", flush=True)
        result = svc.process_campaign(campaign_id, max_sends=pending + 5)
        total_sent += int(result.get("sent") or 0)
        print(
            f"ROUND {round_i+1} sent={result.get('sent')} held={result.get('held_code')} "
            f"remaining={result.get('remaining')} msg={result.get('message')}",
            flush=True,
        )
        if result.get("held_code") and result.get("held_code") not in ("rate_gap",):
            print("STOP", result, flush=True)
            break
        if int(result.get("sent") or 0) == 0 and result.get("held_code") == "rate_gap":
            import time

            time.sleep(8)
    final = store.get_campaign(campaign_id)
    leads = store.get_leads(campaign_id)
    real = sum(1 for l in leads if l.stage == "sent" and l.error != "dry_run")
    failed = sum(1 for l in leads if l.stage == "failed")
    print(
        "RESULT",
        {
            "total_sent_this_run": total_sent,
            "live_sent_leads": real,
            "failed": failed,
            "status": final.status if final else None,
            "dry_run": cfg.dry_run,
            "enabled": cfg.enabled,
        },
        flush=True,
    )
    return 0 if real > 0 and not cfg.dry_run else 3


if __name__ == "__main__":
    raise SystemExit(main())
