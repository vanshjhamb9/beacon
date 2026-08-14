#!/usr/bin/env python3
"""Fresh dual-lane outreach: COMAI (D2C + agency partners) + INOWIX (white-label / product build).

Sources: buyability engine exports + live public research.
Sends via vansh@inowix.in with vanshjhamb9@gmail.com CC.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from email_service import send_email  # noqa: E402

CC = "vanshjhamb9@gmail.com"
FROM_NAME = "Vansh Jhamb | Inowix"


def html_body(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>"
        f"{p.replace(chr(10), '<br/>')}</p>"
        for p in paras
    )


def load_comai_buyability(limit: int = 18) -> list[dict]:
    path = ROOT / "exports" / "comai_buyability_results.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    exclude = {
        "mamaearth.in", "nykaa.com", "boat-lifestyle.com", "lenskart.com",
        "bewakoof.com", "myntra.com", "ajio.com", "flipkart.com", "amazon.in",
        "wowskinscience.com", "beardo.in", "mcaffeine.com", "snitch.co.in",
        "bombayshavingcompany.com",  # often demo/synthetic in older runs
    }
    # Prefer mid-market: has email, not mega-enterprise support desks only when possible
    ranked = sorted(data, key=lambda x: -(x.get("buyability_score") or 0))
    out = []
    seen = set()
    for L in ranked:
        domain = (L.get("domain") or "").lower()
        email = (L.get("email") or "").lower().strip()
        if not email or not L.get("email_valid"):
            continue
        if domain in exclude or domain in seen:
            continue
        if email.endswith(("@sentry.io", "@example.com")):
            continue
        company = L.get("company") or domain
        seen.add(domain)
        out.append(
            {
                "lane": "COMAI_DIRECT",
                "company_name": company,
                "founder_name": L.get("founder_name") or "",
                "to_email": email,
                "website": L.get("website") or f"https://{domain}",
                "domain": domain,
                "city": L.get("city") or "",
                "industry": L.get("industry") or "D2C / Ecommerce",
                "platform": L.get("platform") or "",
                "score": L.get("buyability_score"),
                "why": L.get("why_buy_comai") or "WhatsApp / support automation gap",
                "phone": L.get("phone") or "",
            }
        )
        if len(out) >= limit:
            break
    return out


# Curated high-fit public leads (researched) — partners + Inowix
CURATED = [
    # ——— COMAI Agency Partners ———
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Resultiq Digital",
        "founder_name": "Akash Saini",
        "to_email": "info@resultiqdigital.com",
        "website": "https://resultiqdigital.com",
        "city": "Delhi NCR",
        "industry": "Performance marketing for D2C",
        "angle": "Already runs Email & WhatsApp marketing for D2C — white-label COMAI deepens conversion layer",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Brandscalez",
        "founder_name": "Rohit Raj",
        "to_email": "info@brandscalez.com",
        "website": "https://brandscalez.com",
        "city": "Noida",
        "industry": "Fashion/lifestyle D2C performance agency",
        "angle": "Scales D2C fashion brands on Meta/Google/WhatsApp Ads — COMAI converts post-click chats",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Per4mance Guru",
        "founder_name": "",
        "to_email": "hello@per4mance.guru",
        "website": "https://per4mance.guru",
        "city": "Delhi",
        "industry": "Performance marketing agency",
        "angle": "D2C Meta/Google agency — add white-label WhatsApp AI as retention/conversion offer",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "PERFORMAKS",
        "founder_name": "",
        "to_email": "growth@performaks.com",
        "website": "https://performaks.com",
        "city": "India",
        "industry": "D2C performance & growth agency",
        "angle": "Shopify + performance stack for D2C — COMAI plugs conversation commerce gap",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "PurpleChalk",
        "founder_name": "",
        "to_email": "hello@purplechalk.in",
        "website": "https://www.purplechalk.in",
        "city": "Chennai",
        "industry": "Shopify + branding + WhatsApp/email automation agency",
        "angle": "Already offers WhatsApp automation — COMAI white-label upgrades to AI commerce employee",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Gravmo",
        "founder_name": "Afzal Anis",
        "to_email": "mail@gravmo.in",
        "website": "https://www.gravmo.in",
        "city": "Delhi / Mumbai / Bangalore",
        "industry": "Performance marketing",
        "angle": "eCommerce performance agency — partner lane for WhatsApp AI conversion",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Mobyink Innovations",
        "founder_name": "Kapil Thakkar",
        "to_email": "info@mobyink.com",
        "website": "https://mobyink.com",
        "city": "Jaipur / UAE",
        "industry": "D2C growth / Shopify partner agency",
        "angle": "150+ D2C brands, Shopify partner — natural reseller for COMAI",
    },
    # ——— Mid D2C direct (public contact pages) ———
    {
        "lane": "COMAI_DIRECT",
        "company_name": "Premkala",
        "founder_name": "Khyati Radadiya",
        "to_email": "care@premakala.in",
        "website": "https://premkala.in",
        "city": "Surat",
        "industry": "Women's apparel D2C",
        "angle": "WhatsApp-heavy support (+91 70692 06000) — COMAI automates order/style queries 24/7",
        "why": "Active WhatsApp support channel; apparel D2C fit",
    },
    {
        "lane": "COMAI_DIRECT",
        "company_name": "Naitra Jewelry",
        "founder_name": "",
        "to_email": "collab@naitra.in",
        "website": "https://www.naitra.in",
        "city": "Hyderabad",
        "industry": "Jewellery D2C",
        "angle": "WhatsApp-first customer care — AI commerce replies for order/size/return questions",
        "why": "Jewellery D2C with WhatsApp support published",
    },
    # ——— INOWIX white-label / product build ———
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Brandscalez",
        "founder_name": "Rohit Raj",
        "to_email": "info@brandscalez.com",
        "website": "https://brandscalez.com",
        "city": "Noida",
        "industry": "Agency offering website + app development",
        "angle": "Lists App Development + Website — Inowix white-label eng capacity without hiring",
        "inowix_note": "partner_app_web",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "PurpleChalk",
        "founder_name": "",
        "to_email": "hello@purplechalk.in",
        "website": "https://www.purplechalk.in",
        "city": "Chennai",
        "industry": "Full-service Shopify / digital agency",
        "angle": "Shopify + custom web for brands — white-label Inowix for heavier builds / apps / AI agents",
        "inowix_note": "partner_shopify_custom",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Resultiq Digital",
        "founder_name": "Akash Saini",
        "to_email": "info@resultiqdigital.com",
        "website": "https://resultiqdigital.com",
        "city": "Delhi NCR",
        "industry": "D2C agency with Shopify/WordPress dev",
        "angle": "Offers Shopify & WordPress builds — Inowix as overflow engineering / custom app partner",
        "inowix_note": "partner_shopify_overflow",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Mobyink Innovations",
        "founder_name": "Kapil Thakkar",
        "to_email": "info@mobyink.com",
        "website": "https://mobyink.com",
        "city": "Jaipur",
        "industry": "Shopify Partner D2C agency",
        "angle": "Official Shopify Partner scaling 150+ brands — white-label Inowix for custom apps/AI features clients ask for",
        "inowix_note": "partner_shopify_ai",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "PERFORMAKS",
        "founder_name": "",
        "to_email": "growth@performaks.com",
        "website": "https://performaks.com",
        "city": "India",
        "industry": "D2C growth + Shopify ecommerce development",
        "angle": "Shopify ecommerce development spotlight — Inowix as white-label build bench",
        "inowix_note": "partner_shopify_dev",
    },
    {
        "lane": "INOWIX_DIRECT",
        "company_name": "Graxi Tech Solutions",
        "founder_name": "Sarankumar M",
        "to_email": "info@graxitechs.com",
        "website": "https://graxitechs.com",
        "city": "Bangalore / Chennai",
        "industry": "Offshore / IT solutions for US-UK startups",
        "angle": "Helps US/UK startups build teams — co-delivery / overflow partnership on AI agents & custom SaaS with Inowix",
        "inowix_note": "co_delivery_partner",
    },
]


def draft_comai_direct(lead: dict) -> tuple[str, str]:
    """Premkala-style hyperpersonalized COMAI direct pitch."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.outreach_generator.hyperpersonal import draft_comai

    payload = {
        "company": lead.get("company_name") or lead.get("company"),
        "founder_name": lead.get("founder_name"),
        "city": lead.get("city"),
        "category": lead.get("industry") or lead.get("category"),
        "platform": lead.get("platform"),
        "phone": lead.get("phone"),
        "why": lead.get("why") or lead.get("angle"),
        "signal": lead.get("signal"),
    }
    d = draft_comai(payload)
    return d.subject, d.body


def draft_comai_partner(lead: dict) -> tuple[str, str]:
    first = (lead.get("founder_name") or "").split()[0] if lead.get("founder_name") else ""
    greet = f"Hi {first}," if first and len(first) > 1 else "Hi there,"
    company = lead["company_name"]
    angle = lead.get("angle") or "you already help D2C brands grow on Meta and Shopify"
    subject = f"{company} × COMAI Agency Partner — white-label WhatsApp AI"
    body = f"""{greet}

{angle}.

I'm Vansh from Inowix. COMAI is our AI commerce layer (WhatsApp + chat) — instant replies, product recommendations, lead capture, automated follow-ups for ecommerce/D2C clients.

Through the Agency Partner Program, agencies like {company} white-label COMAI: you keep the client relationship and add a recurring AI/WhatsApp revenue line — we run the tech. Especially strong when your ads already create WhatsApp intent that currently goes cold.

Worth a 15-minute partner intro this week?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in"""
    return subject, body


def draft_inowix_partner(lead: dict) -> tuple[str, str]:
    first = (lead.get("founder_name") or "").split()[0] if lead.get("founder_name") else ""
    greet = f"Hi {first}," if first and len(first) > 1 else "Hi there,"
    company = lead["company_name"]
    angle = lead.get("angle") or "you ship digital work for clients"
    subject = f"{company} — white-label engineering capacity from Inowix"
    body = f"""{greet}

{angle}.

I'm Vansh, founder of Inowix — we build SaaS MVPs, custom software, mobile apps, and AI agents for product teams. For agencies, we run a simple white-label partnership: you own the client and delivery relationship; we are the engineering bench behind the scenes when scope gets heavy (custom apps, AI features, backend, multi-sprint builds).

No poaching clients. Clear SLAs. You keep margin.

If {company} is turning down or stretching builds for capacity reasons, happy to share how the model works in 15 minutes.

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
    return subject, body


def draft_inowix_direct(lead: dict) -> tuple[str, str]:
    first = (lead.get("founder_name") or "").split()[0] if lead.get("founder_name") else ""
    greet = f"Hi {first}," if first and len(first) > 1 else "Hi there,"
    company = lead["company_name"]
    angle = lead.get("angle") or "you're building product for global clients"
    subject = f"{company} × Inowix — co-delivery on AI & custom SaaS"
    body = f"""{greet}

{angle}.

I'm Vansh from Inowix. We ship SaaS MVPs, AI agents/automation, and custom product engineering for startups and growth teams — often as a co-delivery partner for firms that already have client relationships but need extra senior build capacity.

If there's interest in a quiet co-delivery or overflow partnership (India/US/UK scopes), I'd love a short intro call.

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
    return subject, body


def build_queue() -> list[dict]:
    queue: list[dict] = []
    # Buyability D2C directs
    for lead in load_comai_buyability(16):
        subj, body = draft_comai_direct(lead)
        queue.append({**lead, "subject": subj, "body": body})

    # Curated — skip duplicate emails already in queue for same lane product conflict carefully
    seen_email_lane: set[tuple[str, str]] = {(q["to_email"].lower(), q["lane"]) for q in queue}
    # Also avoid sending BOTH ComAI partner + Inowix partner to same email in same blast — pick ComAI partner first, Inowix next day ideally
    # For capacity: send ComAI partner, and Inowix partner only if different email OR mark as separate with slight delay
    for lead in CURATED:
        key = (lead["to_email"].lower(), lead["lane"])
        if key in seen_email_lane:
            continue
        # If same email already getting ComAI_PARTNER and this is INOWIX_PARTNER, still allow but tag
        if lead["lane"] == "COMAI_DIRECT":
            subj, body = draft_comai_direct(lead)
        elif lead["lane"] == "COMAI_PARTNER":
            subj, body = draft_comai_partner(lead)
        elif lead["lane"] == "INOWIX_PARTNER":
            # skip if same email already queued for COMAI_PARTNER in this run (avoid double pitch same day)
            if any(q["to_email"].lower() == lead["to_email"].lower() and q["lane"] == "COMAI_PARTNER" for q in queue):
                continue
            subj, body = draft_inowix_partner(lead)
        else:
            subj, body = draft_inowix_direct(lead)
        seen_email_lane.add(key)
        queue.append({**lead, "subject": subj, "body": body})
    return queue


def main() -> None:
    queue = build_queue()
    results = []
    print(f"Queue size: {len(queue)}")
    for i, item in enumerate(queue, 1):
        print(f"[{i}/{len(queue)}] {item['lane']} -> {item['to_email']} ({item['company_name']})")
        res = send_email(
            to_email=item["to_email"],
            subject=item["subject"],
            body_html=html_body(item["body"]),
            body_text=item["body"],
            from_name=FROM_NAME,
            cc=CC,
        )
        results.append(
            {
                **{k: item.get(k) for k in (
                    "lane", "company_name", "founder_name", "to_email", "website",
                    "city", "industry", "subject", "body", "score", "why", "angle",
                )},
                "send_result": res,
                "sent_at": datetime.now(UTC).isoformat(),
            }
        )
        print("  ->", res)
        time.sleep(2.0)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "from": "vansh@inowix.in",
        "cc": CC,
        "total": len(results),
        "sent": sum(1 for r in results if r["send_result"].get("success")),
        "failed": sum(1 for r in results if not r["send_result"].get("success")),
        "by_lane": {},
        "results": results,
    }
    for r in results:
        lane = r["lane"]
        out["by_lane"].setdefault(lane, {"sent": 0, "failed": 0})
        if r["send_result"].get("success"):
            out["by_lane"][lane]["sent"] += 1
        else:
            out["by_lane"][lane]["failed"] += 1

    path = ROOT / "exports" / "dual_lane_fresh_outreach_report.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ROOT / "exports" / "dual_lane_fresh_outreach_report.md"
    lines = [
        "# Dual-Lane Fresh Outreach Report (COMAI + INOWIX)",
        "",
        f"- From: vansh@inowix.in | CC: {CC}",
        f"- Sent: {out['sent']}/{out['total']} | Failed: {out['failed']}",
        f"- By lane: {json.dumps(out['by_lane'])}",
        "",
    ]
    for r in results:
        st = "OK" if r["send_result"].get("success") else f"FAIL {r['send_result'].get('error')}"
        lines.append(f"### [{r['lane']}] {r['company_name']}")
        lines.append(f"- To: {r['to_email']}")
        lines.append(f"- Subject: {r['subject']}")
        lines.append(f"- Status: {st}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    print("Report:", path)
    print(f"Done sent={out['sent']} failed={out['failed']}")


if __name__ == "__main__":
    main()
