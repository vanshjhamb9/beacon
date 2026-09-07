"""Hyperpersonalized COMAI partner outreach drafts with hosted video CTA."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

from comai_partner_outreach.config import PartnerOutreachConfig


@dataclass
class PartnerDraft:
    subject: str
    body_text: str
    body_html: str
    step: str
    hook_used: str


def _first_name(lead: dict[str, Any]) -> str:
    name = (lead.get("first_name") or "").strip()
    if not name:
        full = (lead.get("founder_name") or "").strip()
        name = full.split()[0] if full else ""
    if not name or len(name) < 2 or re.search(r"\d", name):
        return ""
    return name[:24]


def _agency(lead: dict[str, Any]) -> str:
    return (
        lead.get("agency_name")
        or lead.get("company_name")
        or lead.get("company")
        or lead.get("domain")
        or "your agency"
    ).strip()


def _observation(lead: dict[str, Any], config: PartnerOutreachConfig) -> str:
    notes = " ".join(str(lead.get("notes") or "").split()).strip()
    services = " ".join(str(lead.get("services") or "").split()).strip()
    clients = " ".join(str(lead.get("client_examples") or "").split()).strip()
    agency_type = str(lead.get("agency_type") or "").strip()
    city = str(lead.get("city") or "").strip()
    agency = _agency(lead)

    # Never invent client names — only use provided evidence.
    if notes:
        return notes[:220]
    if clients:
        return f"{agency} works with clients such as {clients[:120]}"
    if services:
        return f"{agency} focuses on {services[:140]}"
    angle = config.angle_for(agency_type)
    loc = f" in {city}" if city else ""
    type_label = agency_type.replace("_", " ") if agency_type else "agency / consulting"
    return f"As a {type_label}{loc}, {angle}"


def _packaging_line(agency_type: str) -> str:
    key = (agency_type or "").lower()
    if "freelance" in key:
        return (
            "You can package COMAI as a recurring add-on for clients you already serve — "
            "you introduce, we demo & onboard, you earn commission."
        )
    if "video" in key or "content" in key or "creative" in key:
        return (
            "Offer COMAI alongside creative/production retainers: your clients get WhatsApp "
            "lead management and automated follow-ups without you building the tech."
        )
    if "web" in key or "shopify" in key or "development" in key:
        return (
            "Bundle COMAI with site/store builds as a managed WhatsApp commerce layer — "
            "you keep the client relationship; we run the product."
        )
    if "consult" in key:
        return (
            "Recommend COMAI as an implementation partner for clients who need WhatsApp "
            "sales/support automation — you stay advisory; recurring commission follows."
        )
    return (
        "Resell or white-label COMAI into your existing client book: introduce → we demo & onboard → "
        "client subscribes → you earn recurring commission."
    )


def _video_html_block(config: PartnerOutreachConfig) -> str:
    url = html.escape(config.video_url or config.partner_page_with_utm())
    label = html.escape(config.cta_label or "Watch partner walkthrough")
    thumb = (config.thumbnail_url or "").strip()
    if thumb:
        thumb_tag = (
            f'<a href="{url}" style="display:inline-block;text-decoration:none">'
            f'<img src="{html.escape(thumb)}" alt="{label}" width="480" '
            f'style="max-width:100%;border-radius:8px;display:block;border:0"/>'
            f"</a>"
        )
    else:
        thumb_tag = (
            f'<a href="{url}" style="display:inline-block;background:#111;color:#fff;'
            f'padding:14px 22px;border-radius:8px;text-decoration:none;font-weight:600">'
            f"▶ {label}</a>"
        )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        'style="margin:18px 0;width:100%"><tr><td style="padding:0">'
        f"{thumb_tag}"
        f'<p style="margin:10px 0 0;font-size:13px;color:#555">'
        f'<a href="{url}" style="color:#0b57d0;text-decoration:underline">{label}</a>'
        f"</p></td></tr></table>"
    )


def _video_text_line(config: PartnerOutreachConfig) -> str:
    return f"{config.cta_label}: {config.video_url or config.partner_page_with_utm()}"


def _economics_bullets(config: PartnerOutreachConfig) -> list[str]:
    return [
        f"**{config.commission_pct}% recurring commission** every month after the client subscribes",
        f"**{config.trial_days}-day free trial** for your clients",
        f"**₹{config.referral_bonus_inr} bonus** after successfully bringing {config.referral_bonus_threshold} businesses",
        "Product, demo & onboarding support from our team",
        "A new recurring-revenue service to offer your existing clients",
    ]


def _text_to_html(text: str, config: PartnerOutreachConfig) -> str:
    """Convert plain draft text to simple HTML and inject video block before sign-off."""
    parts = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    blocks: list[str] = []
    video_injected = False
    for p in parts:
        # Detect sign-off start
        if not video_injected and p.lower().startswith("best,"):
            blocks.append(_video_html_block(config))
            video_injected = True
        escaped = html.escape(p).replace("\n", "<br/>")
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        blocks.append(
            f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>{escaped}</p>"
        )
    if not video_injected:
        # Insert before last paragraph if possible
        if len(blocks) >= 2:
            blocks.insert(-1, _video_html_block(config))
        else:
            blocks.append(_video_html_block(config))
    unsub = (
        "<p style='margin:24px 0 0;font-size:12px;color:#888'>"
        "If this isn’t relevant, reply “unsubscribe” and we won’t follow up."
        "</p>"
    )
    return "".join(blocks) + unsub


def draft_partner_intro(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    hook = _observation(lead, config)
    bullets = "\n".join(f"• {b}" for b in _economics_bullets(config))
    packaging = _packaging_line(str(lead.get("agency_type") or ""))
    partner_url = config.partner_page_with_utm()
    video_line = _video_text_line(config)

    subject = f"{agency} × COMAI Partner Program — recurring WhatsApp AI revenue"
    body = f"""{greet}

{hook}.

We're inviting agencies, consultants and business partners like {agency} to join the **COMAI Partner Program**.

With COMAI, you can offer your clients an AI-powered solution for **WhatsApp lead management, customer support, automated follow-ups, product recommendations and sales automation**—without building or maintaining the technology yourself.

**How it works:**
You introduce COMAI → We demo & onboard the client → Client subscribes → **You earn {config.commission_pct}% recurring commission every month.**

{packaging}

You also get:
{bullets}

{video_line}

If you already work with businesses that receive leads or customer enquiries on WhatsApp, COMAI can be a simple add-on to your existing services.

Would be happy to discuss the partnership and identify a few potential clients together.

Best,
{config.from_name}
{config.signoff_title}
{partner_url}"""

    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=_text_to_html(body, config),
        step="intro",
        hook_used=hook[:160],
    )


def draft_partner_fu1(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    video_line = _video_text_line(config)
    subject = f"Re: {agency} × COMAI Partner Program"
    body = f"""{greet}

Quick follow-up on the COMAI Partner Program note.

If helpful, this short walkthrough shows how agencies resell WhatsApp AI to their clients and earn {config.commission_pct}% recurring commission:
{video_line}

Happy to map 2–3 of {agency}'s clients who could trial it ({config.trial_days}-day free trial).

Best,
{config.from_name}
{config.signoff_title}"""
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=_text_to_html(body, config),
        step="fu1",
        hook_used="followup_bump",
    )


def draft_partner_fu2(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    packaging = _packaging_line(str(lead.get("agency_type") or ""))
    subject = f"{agency} — packaging COMAI as a recurring service line"
    body = f"""{greet}

One practical way partners use COMAI:

{packaging}

Economics stay simple: **{config.commission_pct}% recurring**, {config.trial_days}-day client trial, and ₹{config.referral_bonus_inr} after {config.referral_bonus_threshold} successful referrals. We handle demo and onboarding.

{_video_text_line(config)}

Open to a 15-minute partner intro this week?

Best,
{config.from_name}
{config.signoff_title}
{config.partner_page_with_utm()}"""
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=_text_to_html(body, config),
        step="fu2",
        hook_used="value_packaging",
    )


def draft_partner_final(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    subject = f"Closing the loop — {agency} × COMAI"
    body = f"""{greet}

I'll close the loop on the COMAI Partner Program for now.

If later you want a WhatsApp AI offer for clients (lead management, support, follow-ups) with **{config.commission_pct}% recurring commission**, just reply and we'll pick it up — no pressure.

Best,
{config.from_name}
{config.signoff_title}
{config.partner_page_with_utm()}"""
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=_text_to_html(body, config),
        step="final",
        hook_used="breakup",
    )


def draft_for_step(step: str, lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    step = (step or "intro").lower().strip()
    if step == "fu1":
        return draft_partner_fu1(lead, config)
    if step == "fu2":
        return draft_partner_fu2(lead, config)
    if step == "final":
        return draft_partner_final(lead, config)
    return draft_partner_intro(lead, config)
