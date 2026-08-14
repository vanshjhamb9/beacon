"""Premkala-style hyperpersonalized outreach drafts for COMAI and Inowix.

Rules:
- One specific evidence hook (from enrichment only — never invent pain)
- Clear, professional tone — no jargon stacks or salesy filler
- Short: hook → product → outcome → soft CTA
- Never invent contacts
- Sign-off: vansh@inowix.in + https://inowix.in only (no getcomai.com)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


BANNED_PHRASES = (
    "customer conversations still look mostly manual",
    "still look mostly manual",
    "perfect comai slot",
    "password",
    "smtp",
    "credential",
)


@dataclass
class HyperDraft:
    subject: str
    body: str
    product: str
    hook_used: str


def _first_name(name: str | None) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    return name.split()[0]


def _clean_evidence(text: str) -> str:
    t = " ".join((text or "").split())
    low = t.lower()
    for ban in BANNED_PHRASES:
        if ban in low:
            # strip banned clause if embedded; otherwise drop
            t = re.sub(re.escape(ban), "", t, flags=re.I)
            t = " ".join(t.split()).strip(" —,-")
    return t


def _platform_label(platform: str) -> str:
    p = (platform or "").strip()
    if not p:
        return ""
    low = p.lower()
    if low in ("d2c", "d2c ecommerce", "ecommerce", "your store"):
        return ""
    if "shopify" in low:
        return "Shopify"
    return p.split("/")[0].strip()[:40]


def _comai_observation(lead: dict[str, Any]) -> str:
    """One crisp, evidence-based observation — not a pitch."""
    company = lead.get("company") or lead.get("company_name") or "your brand"
    city = (lead.get("city") or lead.get("hq") or "").strip()
    category = (lead.get("category") or lead.get("industry") or "D2C").strip()
    phone = (lead.get("phone") or lead.get("whatsapp") or "").strip()
    platform = _platform_label(str(lead.get("platform") or ""))
    why = _clean_evidence(str(lead.get("why") or lead.get("why_intent") or lead.get("signal") or ""))
    support_hours = str(lead.get("support_hours") or "").strip()
    sla = str(lead.get("support_sla") or "").strip()
    size = str(lead.get("size") or "").strip()

    loc = f" in {city}" if city else ""
    cat = category if category.lower() not in ("d2c", "ecommerce") else "D2C"

    # Prefer concrete why text (founder/wave quality), lightly trimmed
    if why and len(why) > 24:
        observation = why
        if len(observation) > 140:
            observation = observation[:137].rsplit(" ", 1)[0] + "…"
        if observation.lower().startswith(company.lower()):
            observation = observation[len(company) :].lstrip(" —,-:")
        return observation

    # Structured fallbacks from enrichment fields only
    if phone and phone.startswith("+"):
        return (
            f"{company}{loc} already uses WhatsApp ({phone}) for customer care "
            f"— product questions still need instant replies after the ad click"
        )
    if sla or support_hours:
        window = sla or support_hours
        return (
            f"{company}{loc} looks limited to office-hours support ({window}) "
            f"while {cat.lower()} shoppers ask product questions around the clock"
        )
    if platform:
        return (
            f"{company}{loc} runs on {platform} — {cat.lower()} buyers often need "
            f"ingredient, fit, or order answers before they convert"
        )
    if size:
        return (
            f"{company}{loc} is a {size} {cat.lower()} brand where chat quality "
            f"usually decides conversion after Meta/Instagram traffic"
        )
    return (
        f"{company}{loc} — growing {cat.lower()} brand where product questions "
        f"after the click still need a fast reply"
    )


def draft_comai(lead: dict[str, Any]) -> HyperDraft:
    company = lead.get("company") or lead.get("company_name") or "your brand"
    first = _first_name(lead.get("founder_name") or lead.get("contact_name"))
    greet = f"Hi {first}," if first else "Hi there,"
    category = (lead.get("category") or lead.get("industry") or "D2C").strip()
    platform = _platform_label(str(lead.get("platform") or ""))
    observation = _comai_observation(lead)

    store_bit = f" on {platform}" if platform else ""
    category_bit = category if category.lower() not in ("d2c", "ecommerce", "products") else "D2C"

    subject = f"{company} — WhatsApp replies before the cart goes cold"

    # Build a clean observation clause (no stacked "Company — Company — …")
    detail = observation.strip()
    if detail.lower().startswith(company.lower()):
        detail = detail[len(company) :].lstrip(" —,-:")
    detail = detail.replace(" — ", ", ", 1)
    if detail and detail[0].isupper() and not detail.startswith("WhatsApp"):
        detail = detail[0].lower() + detail[1:]
    if detail.lower().startswith("whatsapp"):
        detail = "WhatsApp" + detail[8:]
    # Make fragment grammatical after "that …"
    low = detail.lower()
    if low.startswith("growing ") or low.startswith("small ") or low.startswith("early "):
        detail = "you're a " + detail
        # "…team), ingredient…" → "…team) where ingredient…"
        detail = re.sub(r"\),\s+", ") where ", detail, count=1)
    elif low.startswith("whatsapp support") or low.startswith("whatsapp-heavy"):
        detail = "you already run " + (detail[0].lower() + detail[1:] if detail[:1].isupper() else detail)

    city = (lead.get("city") or lead.get("hq") or "").strip()
    if city:
        open_line = f"I was looking at {company} ({city}). What stood out is that {detail}."
    else:
        open_line = f"I was looking at {company}. What stood out is that {detail}."

    body = f"""{greet}

{open_line}

I'm Vansh, founder of Inowix. We built COMAI to handle WhatsApp and Instagram commerce chat for Indian {category_bit} brands — product questions, order updates, and follow-ups in seconds, including after hours.

For a team like yours{store_bit}, that usually means more conversions from the same ad spend without adding another support shift.

Would a short 15-minute walkthrough of how COMAI could sit on {company}'s WhatsApp be useful?

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
    return HyperDraft(subject=subject, body=body.strip(), product="comai", hook_used=observation)


def _inowix_hook(lead: dict[str, Any]) -> str:
    company = lead.get("company") or lead.get("company_name") or "your team"
    size = lead.get("size") or ""
    req = lead.get("requirement") or lead.get("why") or lead.get("signal") or ""
    req = _clean_evidence(str(req))
    if req:
        return f"{company}{' (' + size + ')' if size else ''} — {req[:160]}"
    return f"{company}{' (' + size + ')' if size else ''} — product roadmap ahead of eng headcount"


def draft_inowix(lead: dict[str, Any]) -> HyperDraft:
    company = lead.get("company") or lead.get("company_name") or "your team"
    first = _first_name(lead.get("founder_name") or lead.get("contact_name"))
    greet = f"Hi {first}," if first else "Hi there,"
    offer = lead.get("inowix_offer") or "custom SaaS / AI / mobile delivery capacity"
    hook = _inowix_hook(lead)
    intent = (lead.get("intent_type") or "").upper()

    if intent == "PARTNER_OVERFLOW":
        subject = f"{company} × Inowix — white-label engineering capacity"
        body = f"""{greet}

{hook}.

I'm Vansh, founder of Inowix. We act as a quiet engineering bench for agencies and product studios: you keep the client relationship; we ship Flutter/iOS, custom SaaS, and AI features under your brand.

Would 15 minutes to walk through how the model works be useful?

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
    else:
        subject = f"{company} — {offer.split('/')[0].strip()[:40]} (Inowix)"
        body = f"""{greet}

{hook}.

I'm Vansh from Inowix. We build custom software, AI features, SaaS MVPs, and mobile apps (Flutter / React Native / native iOS) for product teams that need senior delivery without waiting on a hire cycle.

Concrete fit: {offer}.

Open to a short 15-minute call this week?

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
    return HyperDraft(subject=subject, body=body.strip(), product="inowix", hook_used=hook)


def draft_for_product(product: str, lead: dict[str, Any]) -> HyperDraft:
    p = (product or "comai").lower().strip()
    if p in ("inowix", "inowix_direct", "inowix_partner"):
        return draft_inowix(lead)
    return draft_comai(lead)


def html_body(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>"
        f"{p.replace(chr(10), '<br>')}</p>"
        for p in paras
    )
