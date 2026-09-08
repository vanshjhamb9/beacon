"""Hyperpersonalized COMAI partner outreach drafts with branded HTML + video CTA."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from comai_partner_outreach.config import PartnerOutreachConfig

# Public brand assets (hosted — works in Gmail/Outlook img tags)
DEFAULT_LOGO_URL = (
    "https://res.cloudinary.com/drxu02bbp/image/upload/v1785956926/"
    "2-removebg-preview_2_v8czqo.png"
)
DEFAULT_OG_IMAGE = "https://comai.in/opengraph-image?a8d5ca28a145d97f"

# Brand palette — charcoal + emerald (email-safe inline CSS)
_INK = "#0f172a"
_MUTED = "#64748b"
_LINE = "#e2e8f0"
_SURFACE = "#f8fafc"
_ACCENT = "#059669"
_ACCENT_DARK = "#047857"
_WHITE = "#ffffff"


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
    if "marketing" in key or "performance" in key or "growth" in key:
        return (
            "When your ads create WhatsApp / DM intent, package COMAI as the conversion layer: "
            "you keep media + strategy; COMAI answers, qualifies, and follows up 24/7 — "
            "you earn recurring commission on every subscribed client."
        )
    return (
        "Resell or white-label COMAI into your existing client book: introduce → we demo & onboard → "
        "client subscribes → you earn recurring commission."
    )


def _youtube_id(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "youtu.be" in host:
        vid = parsed.path.strip("/").split("/")[0]
        return vid or None
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return qs["v"][0]
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in ("embed", "shorts", "live"):
            return parts[1]
    return None


def _logo_url(config: PartnerOutreachConfig) -> str:
    raw = getattr(config, "logo_url", "") or ""
    raw = str(raw).strip()
    return raw or DEFAULT_LOGO_URL


def _thumb_url(config: PartnerOutreachConfig) -> str:
    thumb = (config.thumbnail_url or "").strip()
    if thumb:
        return thumb
    yt = _youtube_id(config.video_url or "")
    if yt:
        return f"https://img.youtube.com/vi/{yt}/hqdefault.jpg"
    return DEFAULT_OG_IMAGE


def _video_text_line(config: PartnerOutreachConfig) -> str:
    return f"{config.cta_label}: {config.video_url or config.partner_page_with_utm()}"


def _video_card(config: PartnerOutreachConfig) -> str:
    url = html.escape(config.video_url or config.partner_page_with_utm())
    label = html.escape(config.cta_label or "Watch the 2-min partner walkthrough")
    thumb = html.escape(_thumb_url(config))
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:20px 0;border-collapse:collapse">
  <tr>
    <td style="border:1px solid {_LINE};border-radius:12px;overflow:hidden;background:{_INK}">
      <a href="{url}" style="display:block;text-decoration:none" target="_blank">
        <img src="{thumb}" alt="{label}" width="552"
             style="display:block;width:100%;max-width:552px;height:auto;border:0"/>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:14px 18px">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:{_ACCENT};color:{_WHITE};font-family:Arial,Helvetica,sans-serif;
                             font-weight:700;font-size:13px;padding:10px 16px;border-radius:8px">
                    ▶ Watch now
                  </td>
                  <td style="padding-left:14px;font-family:Arial,Helvetica,sans-serif;
                             font-size:14px;color:#e2e8f0;line-height:1.45">
                    {label}<br/>
                    <span style="font-size:12px;color:#94a3b8">Opens in browser · ~2 minutes</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </a>
    </td>
  </tr>
</table>
""".strip()


def _cta_button(url: str, label: str) -> str:
    safe_url = html.escape(url)
    safe_label = html.escape(label)
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px">
  <tr>
    <td style="background:{_ACCENT};border-radius:8px">
      <a href="{safe_url}" target="_blank"
         style="display:inline-block;padding:12px 22px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;font-weight:700;color:{_WHITE};text-decoration:none">
        {safe_label}
      </a>
    </td>
  </tr>
</table>
""".strip()


def _economics_row(config: PartnerOutreachConfig) -> str:
    cells = [
        (f"{config.commission_pct}%", "recurring commission"),
        (f"{config.trial_days}-day", "client free trial"),
        (f"₹{config.referral_bonus_inr}", f"after {config.referral_bonus_threshold} wins"),
    ]
    parts: list[str] = []
    for i, (v, l) in enumerate(cells):
        border = f"border-right:1px solid {_LINE};" if i < len(cells) - 1 else ""
        parts.append(
            f"""<td width="33%" valign="top" style="padding:12px 10px;text-align:center;{border}">
          <div style="font-family:Arial,Helvetica,sans-serif;font-size:18px;font-weight:700;
                      color:{_ACCENT_DARK};line-height:1.2">{html.escape(v)}</div>
          <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;color:{_MUTED};
                      margin-top:4px;line-height:1.35">{html.escape(l)}</div>
        </td>"""
        )
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="margin:18px 0;background:{_SURFACE};border:1px solid {_LINE};border-radius:10px">
  <tr>{''.join(parts)}</tr>
</table>
""".strip()


def _render_partner_html(
    *,
    greeting: str,
    headline: str,
    paragraphs: list[str],
    config: PartnerOutreachConfig,
    agency: str,
    include_video: bool = True,
    include_economics: bool = True,
    cta_label: str = "See how the partner offer works",
) -> str:
    logo = html.escape(_logo_url(config))
    partner_url = html.escape(config.partner_page_with_utm())
    video_url = config.video_url or config.partner_page_with_utm()

    body_bits: list[str] = []
    for p in paragraphs:
        if not p.strip():
            continue
        # Skip raw video URL lines — replaced by visual card / button
        if _video_text_line(config) in p or (
            config.video_url and config.video_url in p and p.lower().startswith("watch")
        ):
            continue
        if p.startswith(config.cta_label):
            continue
        escaped = html.escape(p).replace("\n", "<br/>")
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:" + _INK + r"'>\1</strong>", escaped)
        body_bits.append(
            f"<p style='margin:0 0 14px;line-height:1.65;font-size:15px;"
            f"font-family:Arial,Helvetica,sans-serif;color:{_INK}'>{escaped}</p>"
        )

    video_block = _video_card(config) if include_video else ""
    econ_block = _economics_row(config) if include_economics else ""
    cta_block = _cta_button(video_url, cta_label)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>COMAI Partner</title>
</head>
<body style="margin:0;padding:0;background:#eef2f7">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef2f7;padding:28px 12px">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="width:100%;max-width:600px;background:{_WHITE};border-radius:14px;
                    overflow:hidden;border:1px solid {_LINE};box-shadow:0 8px 24px rgba(15,23,42,0.06)">
        <!-- Header -->
        <tr>
          <td style="background:{_INK};padding:20px 28px">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <a href="{partner_url}" style="text-decoration:none">
                    <img src="{logo}" alt="COMAI" height="34"
                         style="display:block;height:34px;width:auto;border:0;max-width:150px"/>
                  </a>
                </td>
                <td align="right" style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                                        color:#94a3b8;letter-spacing:0.08em;font-weight:600">
                  PARTNER PROGRAM
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Accent bar -->
        <tr><td style="height:3px;background:{_ACCENT};font-size:0;line-height:0">&nbsp;</td></tr>
        <!-- Body -->
        <tr>
          <td style="padding:28px 28px 8px">
            <p style="margin:0 0 6px;font-family:Arial,Helvetica,sans-serif;font-size:12px;
                      color:{_MUTED};letter-spacing:0.04em;text-transform:uppercase">
              For {html.escape(agency)}
            </p>
            <p style="margin:0 0 18px;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                      color:{_INK};line-height:1.5">{html.escape(greeting)}</p>
            <h1 style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:22px;
                       font-weight:700;color:{_INK};line-height:1.35">
              {html.escape(headline)}
            </h1>
            {''.join(body_bits)}
            {video_block}
            {econ_block}
            <p style="margin:4px 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:14px;
                      color:{_MUTED}">Ready when you are:</p>
            {cta_block}
            <p style="margin:22px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                      color:{_INK};line-height:1.55">
              Best,<br/>
              <strong>{html.escape(config.from_name)}</strong><br/>
              <span style="color:{_MUTED};font-size:13px">{html.escape(config.signoff_title or "COMAI")}</span>
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:18px 28px 24px;border-top:1px solid {_LINE}">
            <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;
                      color:#94a3b8;line-height:1.5">
              If this isn’t relevant, reply “unsubscribe” and we won’t follow up.<br/>
              <a href="{partner_url}" style="color:{_ACCENT_DARK};text-decoration:none">comai.in</a>
              · Partner economics · Demo &amp; onboarding handled by us
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def draft_partner_intro(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    hook = _observation(lead, config)
    partner_url = config.partner_page_with_utm()
    agency_type = str(lead.get("agency_type") or "")

    hook_short = hook.rstrip(".")
    if len(hook_short) > 150:
        hook_short = hook_short[:147].rstrip() + "…"

    # Attention-grabbing but professional subjects
    if "video" in agency_type.lower() or "creative" in agency_type.lower():
        subject = f"{agency}: turn creative demand into WhatsApp revenue"
    elif "marketing" in agency_type.lower() or "performance" in agency_type.lower():
        subject = f"{agency} — close more of the leads your ads already create"
    elif "shopify" in agency_type.lower() or "web" in agency_type.lower():
        subject = f"A recurring WhatsApp layer for {agency}'s clients"
    else:
        subject = f"Partner idea for {agency}: {config.commission_pct}% recurring"

    headline = f"Give {agency}'s clients a WhatsApp closer — earn {config.commission_pct}% recurring"
    packaging = _packaging_line(agency_type)

    body_text = f"""{greet}

{hook_short}.

COMAI is the WhatsApp AI layer agencies package for clients: instant replies, qualification, and follow-ups — without building or maintaining the tech.

{packaging}

Partner economics: {config.commission_pct}% recurring · {config.trial_days}-day client trial · ₹{config.referral_bonus_inr} after {config.referral_bonus_threshold} businesses · we handle demo & onboarding.

Worth a 2-minute look?
{_video_text_line(config)}

Best,
{config.from_name}
{config.signoff_title or "COMAI"}
{partner_url}"""

    body_html = _render_partner_html(
        greeting=greet,
        headline=headline,
        paragraphs=[
            f"{hook_short}.",
            (
                f"COMAI is the WhatsApp AI layer agencies like **{agency}** package for clients: "
                "instant replies, qualification, and follow-ups — without building the tech."
            ),
            packaging,
            "You introduce → we demo & onboard → client subscribes → you earn every month.",
        ],
        config=config,
        agency=agency,
        include_video=True,
        include_economics=True,
        cta_label="Watch the 2-min partner walkthrough",
    )

    return PartnerDraft(
        subject=subject,
        body_text=body_text.strip(),
        body_html=body_html,
        step="intro",
        hook_used=hook[:160],
    )


def draft_partner_fu1(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    video_line = _video_text_line(config)
    subject = f"Re: {agency} × COMAI — still worth a look?"
    body = f"""{greet}

Quick follow-up on the COMAI Partner note for {agency}.

If useful, this short walkthrough shows how agencies resell WhatsApp AI and earn {config.commission_pct}% recurring:
{video_line}

Happy to map 2–3 of {agency}'s clients who could trial it ({config.trial_days}-day free trial).

Best,
{config.from_name}
{config.signoff_title}"""
    body_html = _render_partner_html(
        greeting=greet,
        headline=f"Still thinking about a WhatsApp offer for {agency}'s clients?",
        paragraphs=[
            (
                f"This short walkthrough shows how agencies resell WhatsApp AI and earn "
                f"**{config.commission_pct}% recurring** — we handle demo and onboarding."
            ),
            f"Happy to map 2–3 of {agency}'s clients who could start a {config.trial_days}-day trial.",
        ],
        config=config,
        agency=agency,
        include_video=True,
        include_economics=True,
        cta_label="Watch the walkthrough",
    )
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=body_html,
        step="fu1",
        hook_used="followup_bump",
    )


def draft_partner_fu2(lead: dict[str, Any], config: PartnerOutreachConfig) -> PartnerDraft:
    first = _first_name(lead)
    greet = f"Hi {first}," if first else "Hi there,"
    agency = _agency(lead)
    packaging = _packaging_line(str(lead.get("agency_type") or ""))
    subject = f"{agency}: one clean way to package COMAI"
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
    body_html = _render_partner_html(
        greeting=greet,
        headline=f"Package COMAI as a recurring line for {agency}",
        paragraphs=[
            packaging,
            (
                f"Economics stay simple: **{config.commission_pct}% recurring**, "
                f"{config.trial_days}-day client trial, and ₹{config.referral_bonus_inr} after "
                f"{config.referral_bonus_threshold} successful referrals. We handle demo and onboarding."
            ),
            "Open to a 15-minute partner intro this week?",
        ],
        config=config,
        agency=agency,
        include_video=True,
        include_economics=True,
        cta_label="Book a quick partner intro",
    )
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=body_html,
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
    body_html = _render_partner_html(
        greeting=greet,
        headline="Closing the loop for now",
        paragraphs=[
            (
                f"If later you want a WhatsApp AI offer for {agency}'s clients with "
                f"**{config.commission_pct}% recurring commission**, just reply — no pressure."
            ),
        ],
        config=config,
        agency=agency,
        include_video=False,
        include_economics=False,
        cta_label="Visit comai.in",
    )
    return PartnerDraft(
        subject=subject,
        body_text=body.strip(),
        body_html=body_html,
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
