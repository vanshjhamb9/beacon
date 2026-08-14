#!/usr/bin/env python3
"""COMAI ICP founder/CEO outreach — small & mid Indian D2C only.

ICP: online store + WhatsApp/IG + Meta ads signal + product Qs before purchase.
Excludes mega brands. Founder/CEO named contacts preferred (public emails only).
CC: vanshjhamb9@gmail.com, ragibali84@gmail.com
"""

from __future__ import annotations

import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from email_service import send_email  # noqa: E402

CC = ["vanshjhamb9@gmail.com", "ragibali84@gmail.com"]
FROM_NAME = "Vansh Jhamb | COMAI"
SLEEP = 12.0

# Already sent successfully in dual-lane wave1 — do not re-blast
ALREADY_SENT = {
    "resolutions@superbottoms.com",
    "care@dotandkey.com",
    "info@foxtale.in",
    "shop@bellavitaorganic.com",
    "care@giva.co",
    "care@palmonas.com",
    "hello@sugarcosmetics.com",
    "support@earthrhythm.com",
    "hello@plumgoodness.com",
    "support@faebeauty.in",
}

# High-intent small/mid D2C — founder/CEO focus
LEADS = [
    {
        "intent_score": 96,
        "company": "Elinor Jewels",
        "founder_name": "Nazneen Mogal",
        "founder_role": "Co-Founder",
        "to_email": "elinorjewels@gmail.com",
        "website": "https://elinorjewels.com",
        "city": "Surat",
        "category": "jewellery",
        "size": "1-10",
        "platform": "Shopify",
        "why": "Shopify jewellery D2C with WhatsApp order support (+91 7096165209) and hiring Customer Service — classic Meta-ad → chat → slow-reply leak",
        "signal": "Hiring CS specialist + WhatsApp support published",
        "email_source": "Founder LinkedIn / public brand gmail",
    },
    {
        "intent_score": 95,
        "company": "Elinor Jewels",
        "founder_name": "Nazneen Mogal",
        "founder_role": "Co-Founder",
        "to_email": "support@elinorjewels.com",
        "website": "https://elinorjewels.com",
        "city": "Surat",
        "category": "jewellery",
        "size": "1-10",
        "platform": "Shopify",
        "why": "Official support inbox; limited hours (12–6) while ads drive night/weekend queries",
        "signal": "support@ + WhatsApp published on site",
        "email_source": "elinorjewels.com/contact",
    },
    {
        "intent_score": 94,
        "company": "C11 Aura",
        "founder_name": "Navjot Kaur",
        "founder_role": "Founder",
        "to_email": "navjotkaurwork@gmail.com",
        "website": "https://www.linkedin.com/company/c11-aura",
        "city": "Chandigarh",
        "category": "skincare",
        "size": "1-10",
        "platform": "D2C ecommerce",
        "why": "Early D2C skincare hiring Customer Experience Executive for post-purchase chats — need 24/7 capacity without a big CS team",
        "signal": "Founder posted CX hire → navjotkaurwork@gmail.com",
        "email_source": "Founder LinkedIn hiring post",
    },
    {
        "intent_score": 93,
        "company": "SEREKO",
        "founder_name": "Malvika Jain",
        "founder_role": "Founder",
        "to_email": "mj@serekoshop.com",
        "website": "https://serekoshop.com",
        "city": "Noida",
        "category": "skincare",
        "size": "20-30 (mid)",
        "platform": "Shopify",
        "why": "Psychodermatology skincare — product questions before purchase; support hours Mon–Fri only = after-hours ad traffic lost",
        "signal": "Founder publicly shares mj@serekoshop.com",
        "email_source": "Founder LinkedIn",
    },
    {
        "intent_score": 92,
        "company": "The Label Jenn",
        "founder_name": "Jinita Sheth",
        "founder_role": "CEO & Founder",
        "to_email": "labeljenn.jinita@gmail.com",
        "website": "https://thelabeljenn.com",
        "city": "Mumbai",
        "category": "fashion",
        "size": "10-20",
        "platform": "Shopify",
        "why": "Bootstrapped women's fashion D2C (150k+ customers) with WhatsApp/call support — size/style queries after Instagram/Meta clicks",
        "signal": "Founder hiring email + site WhatsApp +91 7977424546",
        "email_source": "Founder LinkedIn + labeljenn.com/contact",
    },
    {
        "intent_score": 91,
        "company": "Premkala",
        "founder_name": "Khyati Radadiya",
        "founder_role": "Founder",
        "to_email": "care@premakala.in",
        "website": "https://premkala.in",
        "city": "Surat",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Women's apparel D2C that already pushes WhatsApp (+91 70692 06000) for support — perfect COMAI slot for 24/7 product/order replies",
        "signal": "Site publishes WhatsApp as primary care channel",
        "email_source": "premkala.in about/care",
    },
    {
        "intent_score": 90,
        "company": "Naitra Jewelry",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "collab@naitra.in",
        "website": "https://www.naitra.in",
        "city": "Hyderabad",
        "category": "jewellery",
        "size": "small/mid D2C",
        "platform": "Shopify",
        "why": "Waterproof jewellery D2C — WhatsApp care (+91-9959698855) Mon–Sat only; Meta/IG shoppers ask size & care after hours",
        "signal": "WhatsApp-first support + collab@ for partnerships",
        "email_source": "naitra.in/contact",
    },
    {
        "intent_score": 89,
        "company": "Teejh",
        "founder_name": "Satish Singh",
        "founder_role": "Co-Founder & CEO",
        "to_email": "satish@jokerandwitch.com",
        "website": "https://www.teejh.com",
        "city": "Bengaluru",
        "category": "jewellery",
        "size": "1-10 (Teejh) / mid group",
        "platform": "Shopify",
        "why": "Ethnic jewellery & sarees D2C; CS hours 10–6:30 — performance ads create WhatsApp/IG intent that needs instant product help",
        "signal": "Founder public email + hiring performance marketing for Teejh/Joker",
        "email_source": "Founder LinkedIn (satish@jokerandwitch.com)",
    },
    {
        "intent_score": 88,
        "company": "Teejh",
        "founder_name": "Satish Singh",
        "founder_role": "Co-Founder & CEO",
        "to_email": "support@teejh.com",
        "website": "https://www.teejh.com",
        "city": "Bengaluru",
        "category": "jewellery",
        "size": "1-10",
        "platform": "Shopify",
        "why": "Official Teejh support — 24–48h reply SLA while shoppers decide on jewellery/sarees in chat",
        "signal": "teejh.com contact support@",
        "email_source": "teejh.com/pages/contact",
    },
    {
        "intent_score": 87,
        "company": "ShopSiiri",
        "founder_name": "Meghna Kanumilli",
        "founder_role": "Founder",
        "to_email": "shopsiiri@gmail.com",
        "website": "https://shopsiiri.com",
        "city": "Hyderabad",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "ecommerce + marketplaces",
        "why": "Demi-fine jewellery D2C built on Instagram drops — product/styling questions convert better with instant WhatsApp AI",
        "signal": "Public brand email + phone on site",
        "email_source": "shopsiiri.com about/shipping",
    },
    {
        "intent_score": 86,
        "company": "Frenesi Fashion",
        "founder_name": "Tanvi Pathania",
        "founder_role": "Founder",
        "to_email": "hello@frenesifashion.com",
        "website": "https://frenesifashion.com",
        "city": "India",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Women's fashion + Tawi Jewels — actively connecting Shopify to Meta Ads; need conversation layer after ad click",
        "signal": "Founder hiring Shopify expert for Meta/Google integration",
        "email_source": "Founder LinkedIn hello@frenesifashion.com",
    },
    {
        "intent_score": 85,
        "company": "Sadabahaar Jewelry",
        "founder_name": "Seema",
        "founder_role": "Founder",
        "to_email": "hello@sadabahaarjewelry.com",
        "website": "https://sadabahaarjewelry.com",
        "city": "Delhi",
        "category": "jewellery",
        "size": "small (founder-led)",
        "platform": "Shopify",
        "why": "Bootstrapped silver jewellery Shopify + WhatsApp text support — high-touch product advice before purchase",
        "signal": "hello@ + WhatsApp published; Shopify store",
        "email_source": "sadabahaarjewelry.com FAQs/about",
    },
    {
        "intent_score": 84,
        "company": "Dermalist Skincare",
        "founder_name": "Mayur Bambhaniya",
        "founder_role": "Co-Founder",
        "to_email": "dermalistskincare@gmail.com",
        "website": "https://www.linkedin.com/company/dermalist-skincare",
        "city": "Mumbai",
        "category": "skincare",
        "size": "10-20",
        "platform": "D2C",
        "why": "Growing skincare brand (10–20 team) — ingredient/routine questions stall carts without 24/7 chat agent",
        "signal": "Founder public business gmail for brand ops",
        "email_source": "Founder LinkedIn",
    },
    {
        "intent_score": 83,
        "company": "Mogasu",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@mogasu.com",
        "website": "https://www.mogasu.com",
        "city": "Goa",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Handblock saree D2C — WhatsApp/phone for fit & stock; perfect assisted-sale category",
        "signal": "hello@mogasu.com + WhatsApp +91 7666 297989",
        "email_source": "mogasu.com FAQs",
    },
    {
        "intent_score": 82,
        "company": "Mogasu",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "mogasu.goa@gmail.com",
        "website": "https://www.mogasu.com",
        "city": "Goa",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Secondary founder/ops inbox used for order issues — high-intent WhatsApp commerce brand",
        "signal": "Published on FAQs for order changes",
        "email_source": "mogasu.com FAQs",
    },
    {
        "intent_score": 81,
        "company": "B77 Life",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@b77life.com",
        "website": "https://b77life.com",
        "city": "India",
        "category": "fashion",
        "size": "small/mid",
        "platform": "Shopify",
        "why": "Sustainable fashion D2C with WhatsApp (+91 95995 50779) for order help — conversation converts better than ticket queues",
        "signal": "hello@ + WhatsApp support published",
        "email_source": "b77life.com FAQ",
    },
    {
        "intent_score": 80,
        "company": "Siyoura Natural Care",
        "founder_name": "Nikki Pandey",
        "founder_role": "Founder",
        "to_email": "info@siyouranaturalcare.com",
        "website": "https://www.linkedin.com/in/nikki-pandey-98b93310b",
        "city": "Mumbai",
        "category": "beauty",
        "size": "small",
        "platform": "D2C / marketplaces",
        "why": "Herbal skincare & haircare — product recommendation chats drive conversion; founder lists business email + phone",
        "signal": "Founder LinkedIn business email +91 7977059678",
        "email_source": "Founder LinkedIn",
    },
    {
        "intent_score": 79,
        "company": "Precious Jewels",
        "founder_name": "Priyanka Sethi",
        "founder_role": "Founder",
        "to_email": "preciousjewels265@gmail.com",
        "website": "https://preciousjewels.fashion",
        "city": "Pune",
        "category": "jewellery",
        "size": "small",
        "platform": "ecommerce",
        "why": "Founder-led jewellery & fashion — phone + gmail published; high-touch purchase assistance category",
        "signal": "About page email + phone 9837544802",
        "email_source": "preciousjewels.fashion/about-me",
    },
    {
        "intent_score": 78,
        "company": "Tviya Jewels",
        "founder_name": "Harsh Ghelani",
        "founder_role": "Founder & CEO",
        "to_email": "tviyajewels@gmail.com",
        "website": "https://www.linkedin.com/in/ghelani-harsh",
        "city": "Surat",
        "category": "jewellery",
        "size": "small",
        "platform": "D2C / wholesale",
        "why": "Jewellery brand with public founder mobile — custom & retail inquiries need fast chat conversion",
        "signal": "Founder LinkedIn email +91 86898 90123",
        "email_source": "Founder LinkedIn",
    },
    {
        "intent_score": 77,
        "company": "Fawwnity",
        "founder_name": "Priya Sharma",
        "founder_role": "Co-Founder",
        "to_email": "support@fawwnity.com",
        "website": "https://fawwnity.com",
        "city": "Bengaluru",
        "category": "skincare",
        "size": "1-10",
        "platform": "D2C",
        "why": "Biocompatible skincare startup — ingredient education before purchase is conversation-heavy",
        "signal": "support@fawwnity.com published for order/CS",
        "email_source": "Brand support docs / site",
    },
    {
        "intent_score": 76,
        "company": "Valencia Bodycare",
        "founder_name": "Esha Zad",
        "founder_role": "Founder",
        "to_email": "eshwarizad16@gmail.com",
        "website": "https://www.linkedin.com/in/esha-zad",
        "city": "Pune",
        "category": "beauty",
        "size": "micro D2C",
        "platform": "D2C / pop-ups",
        "why": "Founder-run bath & body brand — direct customer chats; WhatsApp AI scales without hiring night staff",
        "signal": "Founder public gmail",
        "email_source": "Founder LinkedIn",
    },
    {
        "intent_score": 75,
        "company": "Mittal Sarees",
        "founder_name": "",
        "founder_role": "Founding / owner team",
        "to_email": "support@mittalsarees.com",
        "website": "https://mittalsarees.com",
        "city": "Panipat",
        "category": "fashion",
        "size": "small/mid retail D2C",
        "platform": "Shopify",
        "why": "Saree/lehenga ecommerce with live chat + WhatsApp (+91 8930270049) — assisted selling category",
        "signal": "WhatsApp + support@ published",
        "email_source": "mittalsarees.com customer services",
    },
]


def html_body(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>{p.replace(chr(10), '<br>')}</p>"
        for p in paras
    )


def draft(lead: dict) -> tuple[str, str]:
    """Premkala-style hyperpersonalized draft (shared with Lead Engine dashboard)."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.outreach_generator.hyperpersonal import draft_comai

    d = draft_comai(lead)
    return d.subject, d.body


def build_queue() -> list[dict]:
    seen: set[str] = set()
    queue: list[dict] = []
    for lead in sorted(LEADS, key=lambda x: -x["intent_score"]):
        email = lead["to_email"].lower().strip()
        if email in seen or email in ALREADY_SENT:
            continue
        seen.add(email)
        subj, body = draft(lead)
        queue.append({**lead, "subject": subj, "body": body})
    return queue


def export(queue: list[dict]) -> None:
    csv_path = ROOT / "exports" / "comai_icp_founder_leads.csv"
    json_path = ROOT / "exports" / "comai_icp_founder_leads.json"
    md_path = ROOT / "exports" / "comai_icp_founder_leads.md"

    fields = [
        "intent_score", "company", "founder_name", "founder_role", "to_email",
        "website", "city", "category", "size", "platform", "why", "signal",
        "email_source", "subject",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for q in queue:
            w.writerow(q)

    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "count": len(queue),
                "cc": CC,
                "icp": "Small/mid Indian ecommerce D2C — fashion/beauty/jewellery/food/home; Meta+WhatsApp; founder/CEO focus",
                "leads": queue,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = [
        "# COMAI ICP Founder/CEO Leads (small & mid)",
        "",
        f"- Count: {len(queue)}",
        f"- CC: {', '.join(CC)}",
        "",
        "| Score | Company | Founder | Email | Category | Why |",
        "|------:|---------|---------|-------|----------|-----|",
    ]
    for q in queue:
        lines.append(
            f"| {q['intent_score']} | {q['company']} | {q.get('founder_name') or '-'} | "
            f"`{q['to_email']}` | {q['category']} | {q['why'][:80]}... |"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(queue)} leads -> {csv_path}")


def send_all(queue: list[dict]) -> None:
    results = []
    for i, item in enumerate(queue, 1):
        print(f"[{i}/{len(queue)}] {item['company']} -> {item['to_email']}")
        res = send_email(
            to_email=item["to_email"],
            subject=item["subject"],
            body_html=html_body(item["body"]),
            body_text=item["body"],
            from_name=FROM_NAME,
            cc=CC,
            retries=2,
            retry_backoff_sec=10,
        )
        print(" ", res)
        results.append({**item, "send_result": res})
        if not res.get("success"):
            print("SMTP blocked/failed — stopping send.")
            break
        time.sleep(SLEEP)

    report = ROOT / "exports" / "comai_icp_founder_outreach_report.json"
    sent = sum(1 for r in results if r.get("send_result", {}).get("success"))
    report.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "from": "vansh@inowix.in",
                "cc": CC,
                "attempted": len(results),
                "sent": sent,
                "failed": len(results) - sent,
                "results": [
                    {
                        "company": r["company"],
                        "founder_name": r.get("founder_name"),
                        "to_email": r["to_email"],
                        "subject": r["subject"],
                        "intent_score": r["intent_score"],
                        "send_result": r.get("send_result"),
                    }
                    for r in results
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Sent {sent}/{len(results)} | Report: {report}")


if __name__ == "__main__":
    q = build_queue()
    export(q)
    if "--send" in sys.argv:
        send_all(q)
    else:
        print("Dry run only. Pass --send to outreach.")
