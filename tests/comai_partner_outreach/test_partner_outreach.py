"""Tests for COMAI partner outreach: ingest, drafting, gates, replies, follow-ups."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from comai_partner_outreach.config import PartnerOutreachConfig, load_config
from comai_partner_outreach.drafting import draft_for_step, draft_partner_intro
from comai_partner_outreach.ingest import parse_upload
from comai_partner_outreach.rate_limit import RateLimitState, check_send_gate, record_send
from comai_partner_outreach.replies import classify_reply
from comai_partner_outreach.sequence import next_step_after, schedule_after_step
from comai_partner_outreach.service import PartnerOutreachService
from comai_partner_outreach.store import PartnerOutreachStore
from comai_partner_outreach.types import new_id


@pytest.fixture()
def cfg() -> PartnerOutreachConfig:
    return PartnerOutreachConfig(
        video_url="https://example.com/video",
        thumbnail_url="https://example.com/thumb.jpg",
        cta_label="Watch walkthrough",
        commission_pct=15,
        trial_days=10,
        referral_bonus_inr=200,
        referral_bonus_threshold=2,
        partner_page_url="https://comai.in",
        competitor_domains={"wati.io", "aisensy.com"},
        partner_type_angles={
            "video_production_agency": "clients who shoot ads still lose leads on WhatsApp",
            "default": "agencies can offer WhatsApp AI without building tech",
        },
        max_per_hour=5,
        max_per_day=20,
        min_seconds_between_sends=0,
        business_start_hour=0,
        business_end_hour=24,
        weekdays_only=False,
    )


@pytest.fixture()
def tmp_service(tmp_path: Path, cfg: PartnerOutreachConfig, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COMAI_PARTNER_OUTREACH_ENABLED", "false")
    monkeypatch.setenv("COMAI_PARTNER_OUTREACH_DRY_RUN", "true")
    store = PartnerOutreachStore(tmp_path / "store")
    return PartnerOutreachService(store=store, config=cfg)


def test_load_config_reads_yaml():
    config = load_config()
    assert config.commission_pct == 15
    assert config.trial_days == 10
    assert "intro" in [s.get("step") for s in config.sequence_steps]


def test_ingest_aliases_and_competitor(cfg: PartnerOutreachConfig):
    csv = (
        "First Name,Company,Work Email,Type,Notes\n"
        "Asha,Glow Ads,asha@glowads.in,video_production_agency,Runs Meta ads for D2C brands\n"
        "Bot,Wati Clone,sales@wati.io,marketing,competitor\n"
        "Bad,,not-an-email,marketing,\n"
    ).encode("utf-8")
    result = parse_upload(
        filename="leads.csv",
        content=csv,
        campaign_id=new_id(),
        config=cfg,
    )
    assert result.valid_rows == 1
    assert result.leads[0].first_name == "Asha"
    assert result.leads[0].agency_name == "Glow Ads"
    errors = {e["error"] for e in result.errors}
    assert "competitor_excluded" in errors
    assert "invalid_or_missing_email" in errors


def test_draft_includes_economics_and_video(cfg: PartnerOutreachConfig):
    lead = {
        "first_name": "Riya",
        "agency_name": "Frame & Co",
        "agency_type": "video_production_agency",
        "notes": "Produces performance video for Shopify brands",
    }
    draft = draft_partner_intro(lead, cfg)
    assert "15%" in draft.body_text
    assert "10-day" in draft.body_text or "10-day" in draft.body_text.replace("**", "")
    assert "₹200" in draft.body_text
    assert "https://example.com/video" in draft.body_text
    assert "Watch walkthrough" in draft.body_html or "example.com/thumb.jpg" in draft.body_html
    assert "Frame & Co" in draft.subject
    assert "Produces performance video" in draft.body_text


def test_followup_steps_and_schedule(cfg: PartnerOutreachConfig):
    assert next_step_after("intro") == "fu1"
    assert next_step_after("fu1") == "fu2"
    assert next_step_after("fu2") == "final"
    assert next_step_after("final") is None
    now = datetime(2026, 9, 8, 10, 0, tzinfo=UTC)
    nxt = schedule_after_step("intro", cfg, now=now)
    assert nxt == now + timedelta(days=3)
    fu1 = draft_for_step("fu1", {"first_name": "Riya", "agency_name": "X"}, cfg)
    assert fu1.step == "fu1"


def test_kill_switch_and_rate_limit(cfg: PartnerOutreachConfig):
    state = RateLimitState()
    now = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    gate = check_send_gate(cfg, state, campaign_killed=True, now=now)
    assert not gate.allowed
    assert gate.code == "campaign_killed"

    cfg2 = PartnerOutreachConfig(
        max_per_hour=1,
        max_per_day=10,
        min_seconds_between_sends=0,
        business_start_hour=0,
        business_end_hour=24,
        weekdays_only=False,
    )
    # Force enabled path for rate checks (dry_run still ok)
    os.environ["COMAI_PARTNER_OUTREACH_ENABLED"] = "true"
    os.environ["COMAI_PARTNER_OUTREACH_DRY_RUN"] = "true"
    state = record_send(state, now=now)
    gate = check_send_gate(cfg2, state, now=now + timedelta(seconds=1))
    assert not gate.allowed
    assert gate.code == "rate_hour"


def test_reply_classifier_stops_sequence():
    interested = classify_reply("Sounds good — interested in the partnership demo")
    assert interested.label == "interested"
    assert interested.stop_sequence
    assert interested.stage == "interested"
    ooo = classify_reply("I am out of office until Monday")
    assert ooo.label == "ooo"
    assert not ooo.stop_sequence
    assert ooo.delay_days == 5


def test_end_to_end_upload_process_reply(tmp_service: PartnerOutreachService):
    csv = (
        "first_name,agency_name,email,agency_type,notes\n"
        "Kabir,Northlane Media,kabir@northlane.test,performance_marketing_agency,"
        "Runs Meta + WhatsApp lead gen for D2C\n"
    ).encode("utf-8")
    created = tmp_service.create_campaign_from_upload(
        filename="batch.csv",
        content=csv,
        name="Test batch",
    )
    campaign_id = created["campaign"]["id"]
    assert created["valid_rows"] == 1
    leads = tmp_service.get_leads(campaign_id)
    assert leads[0]["stage"] == "drafted"
    assert "15%" in leads[0]["body_text"]

    processed = tmp_service.process_campaign(campaign_id, max_sends=5)
    assert processed["sent"] == 1
    leads = tmp_service.get_leads(campaign_id)
    assert leads[0]["stage"] == "sent"
    assert leads[0]["next_followup_at"]

    reply = tmp_service.ingest_reply(
        from_email="kabir@northlane.test",
        body_text="Interested — can we schedule a call?",
        subject="Re: partnership",
    )
    assert reply is not None
    assert reply["classification"] in ("interested", "meeting")
    leads = tmp_service.get_leads(campaign_id)
    assert leads[0]["stop_reason"]
    assert leads[0]["next_followup_at"] is None

    metrics = tmp_service.metrics()
    assert metrics["sent"] >= 1
    assert metrics["replied"] >= 1
