"""Hyperpersonalized ComAI Agency Partner outreach for enriched marketing-agency founders.

Sends individually via vansh@inowix.in with vanshjhamb9@gmail.com on CC.
Skips leads whose enriched domains clearly do not match a marketing agency.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from email_service import send_email  # noqa: E402

CC = "vanshjhamb9@gmail.com"
FROM_NAME = "Vansh Jhamb | Inowix"
OUT_DIR = Path(__file__).resolve().parents[1] / "exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Partnership model (from COMAI ICP + Lane A partner motion):
# - Product: COMAI = AI commerce employee (WhatsApp/chat) — instant replies,
#   product recommendations, lead capture, automated follow-ups, 24/7 support.
# - Motion for agencies: COMAI Agency Partner Program / white-label WhatsApp
#   automation — agency keeps the client relationship and adds a recurring
#   AI-commerce service line for ecommerce/D2C clients without building tech.


def first_name(full: str) -> str:
    parts = (full or "").strip().split()
    if not parts:
        return "there"
    # Skip placeholder-ish names
    if parts[0].lower() in {"kredworks", "yucorp"}:
        return "there"
    return parts[0]


def to_html(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>{p.replace(chr(10), '<br/>')}</p>" for p in paras)


DRAFTS: list[dict] = [
    {
        "founder_name": "Praneeth Reddy",
        "company_name": "Tall Bunny",
        "to_email": "hello@tallbunny.com",
        "angle": "studio that designs/builds/grows brands",
        "subject": "Partnership idea for Tall Bunny’s ecommerce clients — COMAI",
        "body": """Hi Praneeth,

I’ve been looking at Tall Bunny — “designed, built, and grown” as one studio is a rare positioning, especially when you’re already touching SEO, content, and ecommerce for brands.

I’m Vansh from Inowix. We built COMAI — an AI commerce layer that sits on WhatsApp/chat and handles instant replies, product recommendations, lead capture, and follow-ups 24/7 for D2C and ecommerce brands.

For agencies/studios like yours, we run a simple Agency Partner model: you keep the client relationship and offer COMAI white-label (or co-branded) as a recurring service line. You don’t need to build chatbot/WhatsApp automation in-house — we become the tech layer behind the growth work you already do.

If a few of your ecommerce clients are losing sales to slow replies after ads/content drive traffic, this is usually a clean upsell.

Open to a quick 15-minute partnership chat this week?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Rashmi Tewari",
        "company_name": "KredWorks",
        "to_email": "enquiries.rashmigautam@gmail.com",
        "angle": "personal branding",
        "subject": "KredWorks × COMAI — AI conversation layer for your clients",
        "body": """Hi Rashmi,

KredWorks’ focus on personal branding stood out — once a founder/creator brand starts getting inbound on WhatsApp and DM, response speed becomes part of the brand itself.

I’m Vansh from Inowix. COMAI is our AI commerce employee: instant replies, lead capture, recommendations, and automated follow-ups — built for businesses that live on conversations.

Through our Agency Partner Program, branding/marketing partners can offer COMAI to clients as a white-label conversation layer and earn recurring revenue without building the AI stack. You stay the strategic partner; we power the always-on replies behind the scenes.

Would a short call to walk through the partnership model be useful?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Sushmita Guha",
        "company_name": "Dygic",
        "to_email": "bd@dygic.com",
        "angle": "design + development + marketing; WhatsApp already in stack",
        "subject": "Dygic + COMAI white-label — WhatsApp AI for your client roster",
        "body": """Hi Sushmita,

Dygic’s Design + Development + Marketing mix is exactly where client demand for WhatsApp automation usually shows up — and I noticed WhatsApp already surfaces in your public footprint.

I’m Vansh from Inowix. COMAI is an AI commerce layer (WhatsApp + chat) that replies in seconds, recommends products, captures leads, and runs follow-ups 24/7.

Our Agency Partner Program is built for agencies like Dygic: white-label WhatsApp AI you can deploy across ecommerce clients, keep the relationship, and add a recurring line without diverting your build team into chatbot projects.

If helpful, I can share how the partner model works in a focused 15-minute call.

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Vijaya Kumar B",
        "company_name": "Adsspace",
        "to_email": "connect@adsspace.in",
        "angle": "performance + digital marketing Chennai",
        "subject": "Adsspace — turn paid traffic into WhatsApp revenue with COMAI",
        "body": """Hi Vijaya,

Adsspace’s performance and digital marketing work (SEO, social, branding) creates the hard part — traffic and intent. The leak I keep seeing with agencies like yours: WhatsApp/DM replies after the click are still manual, so ad spend doesn’t fully convert.

I’m Vansh from Inowix. COMAI automates those commerce conversations — instant replies, product pushes, lead capture, follow-ups — so the traffic you generate actually gets answered 24/7.

Under our Agency Partner Program, performance agencies offer COMAI white-label to clients as a conversion layer on top of media. You own the client; we power the AI.

Worth a quick partnership chat this week?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Nischal Reddy",
        "company_name": "Anirva Resources Private Limited",
        "to_email": "info@anirvaresources.com",
        "angle": "Telangana marketing-services founder",
        "subject": "Anirva × COMAI Agency Partner Program",
        "body": """Hi Nischal,

I’m reaching out because Anirva came up in our India marketing-services founder map, and we’re selectively opening COMAI’s Agency Partner Program.

COMAI is Inowix’s AI commerce layer for WhatsApp/chat — instant replies, recommendations, lead capture, and follow-ups for ecommerce and service brands. Partners can white-label it for their clients and create a recurring revenue line without building AI tooling in-house.

If Anirva’s clients include growing brands that lose leads to slow replies, this tends to be a natural add-on to existing retainers.

Open to a brief intro call on the partnership model?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Abhay Mandloi",
        "company_name": "LBI Media",
        "to_email": "anmol@lbimedia.in",
        "angle": "Karnataka media agency",
        "subject": "LBI Media — COMAI partnership for client WhatsApp automation",
        "body": """Hi Abhay (and Anmol),

I’m Vansh from Inowix. LBI Media came through in our marketing/media agency founder list out of Karnataka, and I wanted to share a partnership lane — not a generic product pitch.

COMAI is our AI commerce employee for WhatsApp and chat: 24/7 replies, lead capture, product recommendations, and follow-ups. Through the Agency Partner Program, media/marketing agencies white-label COMAI for their clients and keep the account relationship while we run the tech.

If any of LBI’s brand clients are drowning in unread WhatsApp enquiries after campaigns, this is usually a clean expansion offer.

Would a 15-minute partner intro work?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Mohammad",
        "company_name": "Clickwave Solution",
        "to_email": "asad@clickwavesolution.com",
        "angle": "Indore digital agency",
        "subject": "Clickwave × COMAI — white-label WhatsApp AI for your clients",
        "body": """Hi Mohammad (and Asad),

Clickwave Solution in Indore looks like the kind of digital agency whose clients increasingly ask for WhatsApp automation — and most teams don’t want to staff a chatbot project.

I’m Vansh from Inowix. COMAI is an AI commerce layer that replies instantly, captures leads, recommends products, and follows up automatically.

Our Agency Partner Program lets agencies like Clickwave offer this white-label: you sell and own the client; we deliver the AI WhatsApp stack. It’s meant to become a recurring service line next to your existing digital work.

Happy to walk through the model in 15 minutes if useful.

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Jitesh Jaiswal",
        "company_name": "Denken Technologies",
        "to_email": "info@denken.co.in",
        "angle": "research consulting with WhatsApp/social footprint",
        "subject": "Denken — COMAI partner lane for client conversation automation",
        "body": """Hi Jitesh,

I came across Denken Research Consulting and noticed your public presence already touches social/WhatsApp-style engagement — which is usually where client conversation volume starts breaking manual processes.

I’m Vansh from Inowix. We built COMAI to automate commerce conversations (instant replies, lead capture, recommendations, follow-ups). For agencies and consultancies, we run an Agency Partner Program: white-label deployment for your clients, you keep the relationship and margin on a recurring AI service.

If Denken’s clients include brands that need always-on enquiry handling, I’d love to show how the partnership works.

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Nishi Makkar",
        "company_name": "Light Buzz Media",
        "to_email": "contact@lightbuzzmedia.com",
        "angle": "top digital marketing agency India; ecommerce",
        "subject": "Light Buzz Media × COMAI Agency Partner — AI for your ecommerce clients",
        "body": """Hi Nishi,

Light Buzz Media’s digital marketing footprint (SEO, PPC, social, ecommerce) is a strong fit for what we’re opening with select Indian agencies.

I’m Vansh from Inowix. COMAI is an AI commerce employee on WhatsApp/chat — 2-second replies, product recommendations, lead capture, automated follow-ups — so brands stop losing revenue to unread messages after campaigns.

Agency Partner model: Light Buzz white-labels COMAI for clients, keeps the retainer relationship, and adds a recurring AI/WhatsApp line without building the product. Your media work creates demand; COMAI converts the conversations.

Open to a short partnership call this week?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Karthik Dass",
        "company_name": "Digitell Evolution",
        "to_email": "info@digitellevolution.com",
        "angle": "digital marketing, Google ads, Shopify",
        "subject": "Digitell Evolution — COMAI white-label for Shopify/D2C clients",
        "body": """Hi Karthik,

Digitell Evolution’s mix of digital marketing, Google Ads, and Shopify support is exactly where WhatsApp AI becomes a natural next offer — ads and storefronts create questions; slow replies kill conversion.

I’m Vansh from Inowix. COMAI automates those commerce chats 24/7 (replies, recommendations, lead capture, follow-ups).

Through our Agency Partner Program, agencies like Digitell offer COMAI white-label to ecommerce clients as a conversion/support layer on top of existing retainers. You stay the growth partner; we power the AI.

Would a 15-minute walkthrough of the partnership model help?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Arun S",
        "company_name": "Startyfy",
        "to_email": "Info@startyfy.com",
        "angle": "Bengaluru marketing-services founder",
        "subject": "Startyfy × COMAI Agency Partner Program",
        "body": """Hi Arun,

I’m Vansh from Inowix. Startyfy showed up in our Bengaluru marketing-services founder set, and we’re introducing COMAI’s Agency Partner Program to a small set of agencies.

COMAI is an AI commerce layer for WhatsApp and chat — instant replies, product recommendations, lead capture, and follow-ups. Partners can white-label it for clients and create recurring revenue without standing up an AI engineering team.

If Startyfy’s clients include growing brands with high enquiry volume, this is usually a clean add-on conversation.

Open to a quick intro call?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Keval Thakar",
        "company_name": "Conversifyit",
        "to_email": "info@conversifyit.in",
        "angle": "conversation-named digital marketing + web Ahmedabad",
        "subject": "Conversifyit × COMAI — partnership on AI conversations",
        "body": """Hi Keval,

Conversifyit’s name already says it — digital marketing and web that lives in conversations. That’s precisely where COMAI sits.

I’m Vansh from Inowix. COMAI is our AI commerce employee: WhatsApp/chat automation for instant replies, lead capture, recommendations, and follow-ups for ecommerce and local brands.

Agency Partner Program: you white-label COMAI for Ahmedabad (and pan-India) clients, keep the relationship, and add a recurring conversation-AI service next to your marketing and development work — without building the AI yourself.

Would love a short call if this direction fits Conversifyit’s roadmap.

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Neha Gupta",
        "company_name": "BHeard",
        "to_email": "hello@bheard.in",
        "angle": "integrated branding & tech agency Mumbai",
        "subject": "BHeard × COMAI — AI commerce layer for your branding clients",
        "body": """Hi Neha,

BHeard’s “integrated branding & tech agency” positioning in Mumbai is a strong fit for a white-label AI conversation product — brand experience increasingly includes how fast a business replies on WhatsApp.

I’m Vansh from Inowix. COMAI handles 24/7 commerce conversations: replies, product recommendations, lead capture, follow-ups.

Our Agency Partner model lets agencies like BHeard offer COMAI under their brand (or co-branded), keep client ownership, and add recurring revenue on top of branding/tech retainers.

If useful, I can walk you through the partnership structure in 15 minutes.

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Harsh Verma",
        "company_name": "Command Ads - Performance Marketing Agency",
        "to_email": "hello@commandads.com",
        "angle": "performance marketing for D2C — perfect ICP",
        "subject": "Command Ads × COMAI — D2C WhatsApp conversion partner",
        "body": """Hi Harsh,

Command Ads’ focus on performance marketing for D2C brands is the cleanest fit I’ve seen for COMAI’s Agency Partner Program.

You already do the expensive job — Meta/Google traffic for D2C. The gap most D2C brands still have: WhatsApp and chat replies after the click are slow or inconsistent, so CAC rises while conversion leaks.

COMAI is Inowix’s AI commerce employee — instant replies, product recommendations, lead capture, automated follow-ups, 24/7. For agencies, we white-label it so Command Ads can offer a conversion layer on top of media, keep the client relationship, and add recurring revenue without building AI in-house.

Would you be open to a 15-minute partnership call this week?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
    {
        "founder_name": "Abhishek Patil",
        "company_name": "Wings on Fire Marketing",
        "to_email": "Hello@wingsonfire.in",
        "angle": "Noida marketing agency, 6 people",
        "subject": "Wings on Fire × COMAI Agency Partner Program",
        "body": """Hi Abhishek,

Wings on Fire Marketing (Noida) came through in our enriched marketing-agency founder list, and I wanted to reach out on a partnership — not a cold SaaS blast.

I’m Vansh from Inowix. COMAI is an AI commerce layer for WhatsApp/chat that replies instantly, captures leads, recommends products, and follows up automatically for brand clients.

Agency Partner Program: Wings on Fire can white-label COMAI for clients, keep the relationship, and add a recurring AI/WhatsApp service next to your marketing retainers — we handle the tech.

Open to a quick 15-minute intro on how the model works?

Best,
Vansh Jhamb
Founder, Inowix | COMAI
vansh@inowix.in
https://inowix.in""",
    },
]

SKIPPED = [
    {"company": "By Gen.", "reason": "enriched domain bygentlemen.com is unrelated dating site"},
    {"company": "Tea Rose", "reason": "enriched domain tearosegarden.com is a garden site, not agency"},
    {"company": "Social Corner", "reason": "enriched domain socialcorner.com is Michelin restaurant, not agency"},
    {"company": "Tale A Weave", "reason": "enriched domain taleweave.in is saree ecommerce, not agency"},
    {"company": "InstantAppointment AI", "reason": "SaaS product, not marketing agency partner ICP"},
    {"company": "Better Collab", "reason": "video-conferencing SaaS, not marketing agency"},
]


def main() -> None:
    results = []
    for i, draft in enumerate(DRAFTS, 1):
        html = to_html(draft["body"])
        print(f"[{i}/{len(DRAFTS)}] Sending to {draft['to_email']} ({draft['company_name']})...")
        result = send_email(
            to_email=draft["to_email"],
            subject=draft["subject"],
            body_html=html,
            body_text=draft["body"],
            from_name=FROM_NAME,
            cc=CC,
        )
        entry = {
            "founder_name": draft["founder_name"],
            "company_name": draft["company_name"],
            "to_email": draft["to_email"],
            "cc": CC,
            "subject": draft["subject"],
            "angle": draft["angle"],
            "body": draft["body"],
            "send_result": result,
            "sent_at": datetime.now(UTC).isoformat(),
        }
        results.append(entry)
        print("  ->", result)
        if i < len(DRAFTS):
            time.sleep(2.5)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "from": "vansh@inowix.in",
        "cc": CC,
        "partnership_model_summary": {
            "program": "COMAI Agency Partner Program",
            "offer": "White-label WhatsApp / chat AI commerce automation",
            "value_to_agency": [
                "Keep client relationship",
                "Add recurring AI service line",
                "No need to build chatbot stack in-house",
                "Converts post-ad WhatsApp/DM traffic for ecommerce & D2C clients",
            ],
            "product_capabilities": [
                "Instant replies",
                "Product recommendations",
                "Lead capture",
                "Automated follow-ups",
                "24/7 support coverage",
            ],
            "sources": [
                "config/icps/comai.yaml",
                "apps/api/app/services/lead_discovery.py (COMAI -- Agency Partner Program)",
                "apps/api/app/services/lane_a_comai_detector.py (white-label WhatsApp automation)",
                "Inowix LinkedIn COMAI product messaging",
            ],
        },
        "sent_count": sum(1 for r in results if r["send_result"].get("success")),
        "failed_count": sum(1 for r in results if not r["send_result"].get("success")),
        "skipped": SKIPPED,
        "results": results,
    }
    out_path = OUT_DIR / "comai_agency_partner_outreach_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = OUT_DIR / "comai_agency_partner_outreach_report.md"
    lines = [
        "# COMAI Agency Partner Outreach Report",
        "",
        f"- From: vansh@inowix.in",
        f"- CC: {CC}",
        f"- Sent: {report['sent_count']}/{len(DRAFTS)}",
        f"- Failed: {report['failed_count']}",
        f"- Skipped (bad domain / non-agency): {len(SKIPPED)}",
        "",
        "## Partnership model pitched",
        "",
        "COMAI Agency Partner Program — white-label WhatsApp/chat AI commerce automation for marketing agencies serving ecommerce/D2C clients. Agency keeps the client; COMAI powers instant replies, recommendations, lead capture, and follow-ups.",
        "",
        "## Sends",
        "",
    ]
    for r in results:
        status = "OK" if r["send_result"].get("success") else f"FAIL: {r['send_result'].get('error')}"
        lines.append(f"### {r['company_name']} — {r['founder_name']}")
        lines.append(f"- To: {r['to_email']}")
        lines.append(f"- Subject: {r['subject']}")
        lines.append(f"- Status: {status}")
        lines.append("")
    lines.append("## Skipped")
    lines.append("")
    for s in SKIPPED:
        lines.append(f"- **{s['company']}**: {s['reason']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\nReport:", out_path)
    print("Markdown:", md_path)
    print(f"Done. sent={report['sent_count']} failed={report['failed_count']} skipped={len(SKIPPED)}")


if __name__ == "__main__":
    main()
