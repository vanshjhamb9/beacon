#!/usr/bin/env python3
"""COMAI wave2 — ~35-40 NEW small/mid Indian D2C founder/CEO leads + master CSV.

Skips emails already successfully sent. Dual CC.
Also builds exports/comai_all_collected_leads_master.csv with email + phone.
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
SLEEP = 11.0

# --- NEW wave2 leads (not previously sent) ---
LEADS = [
    {
        "company": "Earthly Jewels",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@earthlyjewels.co",
        "phone": "+91 93212 94329",
        "website": "https://earthlyjewels.co",
        "city": "Mumbai",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Lab-grown diamond D2C — sizing/custom queries via WhatsApp; high-ticket assisted sales",
        "signal": "hello@ + WhatsApp published",
        "email_source": "earthlyjewels.co/contact",
    },
    {
        "company": "Tiny Jewels",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@tinyjewels.in",
        "phone": "+91 91120 20009",
        "website": "https://www.tinyjewels.in",
        "city": "Pune",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Kids fine gold jewellery — Mon–Fri care hours only; parents message nights/weekends after ads",
        "signal": "Care hours Mon–Fri + WhatsApp",
        "email_source": "tinyjewels.in contact/FAQs",
    },
    {
        "company": "Purecarat",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@purecarat.in",
        "phone": "+91 81609 49270",
        "website": "https://purecarat.in",
        "city": "Surat",
        "category": "jewellery",
        "size": "small/mid D2C",
        "platform": "ecommerce",
        "why": "Lab-grown diamond jewellery — consultant WhatsApp for custom/urgent orders",
        "signal": "hello@ + jewellery consultant WhatsApp",
        "email_source": "purecarat.in FAQs",
    },
    {
        "company": "Mridah",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@mridah.com",
        "phone": "+91 97043 33588",
        "website": "https://mridah.com",
        "city": "Hyderabad",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Custom jewellery D2C — WhatsApp for customisation; limited shop hours",
        "signal": "hello@ + WhatsApp on FAQs/contact",
        "email_source": "mridah.com contact",
    },
    {
        "company": "Mridah",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "help@mridah.com",
        "phone": "+91 97043 33588",
        "website": "https://mridah.com",
        "city": "Hyderabad",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Secondary help inbox for custom jewellery chats",
        "signal": "help@mridah.com on FAQs",
        "email_source": "mridah.com FAQs",
    },
    {
        "company": "TINCH Jewels",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@tinch.co.in",
        "phone": "+91 77188 29472",
        "website": "https://www.tinch.co.in",
        "city": "India",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Custom jewellery via call/WhatsApp — conversation converts before checkout",
        "signal": "hello@ + WhatsApp on FAQs",
        "email_source": "tinch.co.in FAQs",
    },
    {
        "company": "Svaraa Jewels",
        "founder_name": "Chahat Shah",
        "founder_role": "Founder",
        "to_email": "care@svaraa.com",
        "phone": "+91 70694 56456",
        "website": "https://svaraa.com",
        "city": "Surat",
        "category": "jewellery",
        "size": "small/mid D2C",
        "platform": "Shopify",
        "why": "Lab-grown/natural diamond D2C with WhatsApp Business — high-intent product Qs",
        "signal": "care@ + phones + WhatsApp Business stack",
        "email_source": "LinkedIn company + site",
    },
    {
        "company": "Azga",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@azga.in",
        "phone": "+91 87796 66047",
        "website": "https://www.azga.in",
        "city": "India",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Designer jewellery — care Mon–Fri 12–5; urgent requests go to WhatsApp",
        "signal": "Limited hours + WhatsApp for urgent",
        "email_source": "azga.in product care footer",
    },
    {
        "company": "Culturati",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@culturati.in",
        "phone": "+91 72042 36809",
        "website": "https://culturati.in",
        "city": "India",
        "category": "jewellery",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Ethnic jewellery + sarees — WhatsApp chat for product assistance",
        "signal": "hello@ + WhatsApp chat published",
        "email_source": "culturati.in product pages",
    },
    {
        "company": "Ciceroni",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "customercare@ciceroni.in",
        "phone": "+91 99040 45564",
        "website": "https://ciceroni.in",
        "city": "India",
        "category": "jewellery",
        "size": "small/mid D2C",
        "platform": "Shopify",
        "why": "Temple jewellery — stylist WhatsApp before order; Mon–Fri care hours",
        "signal": "WhatsApp stylist + limited hours",
        "email_source": "ciceroni.in product FAQs",
    },
    {
        "company": "Ciceroni",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@ciceroni.in",
        "phone": "+91 99040 45564",
        "website": "https://ciceroni.in",
        "city": "India",
        "category": "jewellery",
        "size": "small/mid D2C",
        "platform": "Shopify",
        "why": "International/urgent jewellery requests via hello@",
        "signal": "hello@ciceroni.in published",
        "email_source": "ciceroni.in",
    },
    {
        "company": "Amama",
        "founder_name": "",
        "founder_role": "Founding / leadership",
        "to_email": "customercare@amama.in",
        "phone": "+91 79821 90311",
        "website": "https://www.amama.in",
        "city": "Delhi NCR",
        "category": "jewellery",
        "size": "mid D2C",
        "platform": "Shopify",
        "why": "Handmade jewellery — Mon–Fri care; WhatsApp styling booking = conversation commerce gap",
        "signal": "Office-hours care + WhatsApp styling",
        "email_source": "amama.in/contact",
    },
    {
        "company": "Kalki Millets",
        "founder_name": "Santhi TJ",
        "founder_role": "Founder",
        "to_email": "hello@kalkimillets.in",
        "phone": "+91 63815 92082",
        "website": "https://kalkimillets.in",
        "city": "Madurai",
        "category": "food",
        "size": "small family D2C",
        "platform": "ecommerce",
        "why": "Millet snacks D2C — product/diet questions before repeat purchase",
        "signal": "hello@ + phone on homepage",
        "email_source": "kalkimillets.in",
    },
    {
        "company": "Samasta Foods",
        "founder_name": "Sushant Kalra",
        "founder_role": "Founder",
        "to_email": "hello@samastafoods.com",
        "phone": "",
        "website": "https://www.samastafoods.com",
        "city": "India",
        "category": "food",
        "size": "small D2C",
        "platform": "ecommerce",
        "why": "Healthy snacks/premixes — founder pushes hello@ on every post; repeat-order chat opportunity",
        "signal": "Founder LinkedIn hello@samastafoods.com",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "Satvikveda",
        "founder_name": "Vimal Navapariya",
        "founder_role": "Co-Founder & CEO",
        "to_email": "vimal@satvikveda.in",
        "phone": "",
        "website": "https://satvikveda.in",
        "city": "Bhavnagar",
        "category": "food",
        "size": "1-10",
        "platform": "D2C",
        "why": "Clean millet snacks for kids — CEO email public; product advice drives conversion",
        "signal": "CEO LinkedIn vimal@satvikveda.in",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "Lunévra Beauty",
        "founder_name": "Zuber Rao",
        "founder_role": "Founder & CEO",
        "to_email": "zuber@lunevra.in",
        "phone": "",
        "website": "https://lunevra.in",
        "city": "India",
        "category": "skincare",
        "size": "early D2C",
        "platform": "D2C",
        "why": "Luxury skincare launch — ingredient/routine Qs convert on WhatsApp",
        "signal": "CEO public zuber@lunevra.in",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "Koshah Cosmetics",
        "founder_name": "Poonam Joshi",
        "founder_role": "Founder",
        "to_email": "koshahcosmetics@gmail.com",
        "phone": "",
        "website": "https://koshah.in",
        "city": "India",
        "category": "beauty",
        "size": "1-10",
        "platform": "ecommerce + WhatsApp",
        "why": "Handmade custom cosmetics — WhatsApp-first sales; AI agent scales customisation Qs",
        "signal": "Founder lists gmail + WhatsApp Business",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "D'Moraa",
        "founder_name": "Brinda Vaja",
        "founder_role": "Founder & CEO",
        "to_email": "dmoraa.personalcare@gmail.com",
        "phone": "",
        "website": "https://www.linkedin.com/in/brinda-vaja-757a2431a",
        "city": "Ahmedabad",
        "category": "skincare",
        "size": "small D2C",
        "platform": "D2C",
        "why": "Skincare D2C founder email public — product education chats before purchase",
        "signal": "Founder LinkedIn business gmail",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "VeraMoss",
        "founder_name": "Shriram Deshpande",
        "founder_role": "CEO",
        "to_email": "veramossglobal@gmail.com",
        "phone": "+91 96997 94249",
        "website": "https://www.linkedin.com/company/veramoss-car-perfumes",
        "city": "Pune",
        "category": "lifestyle",
        "size": "1-10",
        "platform": "D2C",
        "why": "Fragrance D2C (25k+ customers) — founder WhatsApp for sales; 24/7 agent lifts conversion",
        "signal": "CEO phone + gmail public",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "Reborn Naturals",
        "founder_name": "Smit Daredia",
        "founder_role": "Founder & CEO",
        "to_email": "smitdworks@gmail.com",
        "phone": "",
        "website": "https://www.linkedin.com/in/smitdaredia",
        "city": "Vadodara",
        "category": "beauty",
        "size": "small D2C",
        "platform": "D2C",
        "why": "Hair/skin/wellness D2C scaling — founder email for partnerships; chat converts product advice",
        "signal": "Founder smitdworks@gmail.com",
        "email_source": "Founder LinkedIn",
    },
    {
        "company": "SVARASYA",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "contact@svarasya.com",
        "phone": "+91 99713 21001",
        "website": "https://www.svarasya.com",
        "city": "India",
        "category": "skincare",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Ayurveda skincare — product education before purchase; phone published for care",
        "signal": "contact@ + phone on contact page",
        "email_source": "svarasya.com/contact-us",
    },
    {
        "company": "Prathaa",
        "founder_name": "Sukanya Bhattacharya",
        "founder_role": "Founder",
        "to_email": "hello@prathaa.in",
        "phone": "+91 90823 40500",
        "website": "https://prathaa.in",
        "city": "Mumbai",
        "category": "fashion",
        "size": "small/mid",
        "platform": "Shopify",
        "why": "Handloom fashion — Mon–Fri care; fit/fabric Qs after Instagram/Meta traffic",
        "signal": "hello@ + phones; office hours only",
        "email_source": "prathaa.in/contact-us",
    },
    {
        "company": "Kreation by KJ",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello.kreationbykj@zohomail.in",
        "phone": "+91 62906 56219",
        "website": "https://kreationbykj.in",
        "city": "India",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Ethnic saree D2C — WhatsApp-first customer service for orders/exchanges",
        "signal": "WhatsApp primary + Zoho mail",
        "email_source": "kreationbykj.in help center",
    },
    {
        "company": "Summer by Priyanka Gupta",
        "founder_name": "Priyanka Gupta",
        "founder_role": "Founder",
        "to_email": "info@lovesummer.in",
        "phone": "+91 98990 70899",
        "website": "https://www.lovesummer.in",
        "city": "New Delhi",
        "category": "fashion",
        "size": "small/mid",
        "platform": "ecommerce + IG",
        "why": "Women's clothing label with strong IG — size/style Qs convert on chat",
        "signal": "info@ + founder phone published",
        "email_source": "Brand directory / lovesummer.in",
    },
    {
        "company": "The Ethnic Label",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@theethniclabel.com",
        "phone": "+91 70219 91231",
        "website": "https://theethniclabel.com",
        "city": "India",
        "category": "fashion",
        "size": "small D2C",
        "platform": "ecommerce",
        "why": "Ethnic wear D2C — product assistance via phone/email before purchase",
        "signal": "hello@ + phone published",
        "email_source": "theethniclabel.com",
    },
    {
        "company": "ODE THE LABEL",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "thelabelode@gmail.com",
        "phone": "",
        "website": "https://odethelabel.in",
        "city": "Kolkata",
        "category": "fashion",
        "size": "small",
        "platform": "ecommerce",
        "why": "Boutique fashion label — founder-led; IG-driven traffic needs instant chat replies",
        "signal": "Public brand gmail on site",
        "email_source": "odethelabel.in",
    },
    {
        "company": "PR LABEL",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@prthelabel.com",
        "phone": "",
        "website": "https://prthelabel.com",
        "city": "India",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Fashion label — exchange/size chats within 48h; WhatsApp AI prevents bounce",
        "signal": "hello@prthelabel.com on policies",
        "email_source": "prthelabel.com exchange policy",
    },
    {
        "company": "PR LABEL",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "theprlabel@gmail.com",
        "phone": "",
        "website": "https://prthelabel.com",
        "city": "India",
        "category": "fashion",
        "size": "small D2C",
        "platform": "Shopify",
        "why": "Secondary founder/ops gmail for exchanges — chat-heavy apparel ops",
        "signal": "theprlabel@gmail.com published",
        "email_source": "prthelabel.com",
    },
    {
        "company": "Rajasvi Decor",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "rajasvidecor@gmail.com",
        "phone": "+91 88023 76186",
        "website": "https://rajasvidecor.com",
        "city": "India",
        "category": "home",
        "size": "small D2C",
        "platform": "ecommerce",
        "why": "Luxury candles / home décor gifting — custom & bulk Qs via WhatsApp",
        "signal": "Brand gmail + phone",
        "email_source": "Public brand listings / site",
    },
    {
        "company": "Jaivik Store",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "jaivikstore24@gmail.com",
        "phone": "+91 99874 05367",
        "website": "",
        "city": "India",
        "category": "home",
        "size": "small",
        "platform": "D2C / WhatsApp",
        "why": "Natural home/haircare products — WhatsApp commerce; product advice before buy",
        "signal": "Public gmail + phone",
        "email_source": "Public supplier listings",
    },
    {
        "company": "Spark Soul",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "econnsparksoul@gmail.com",
        "phone": "+91 92745 08929",
        "website": "",
        "city": "India",
        "category": "home",
        "size": "small",
        "platform": "WhatsApp D2C",
        "why": "Scented soy candles — gifting queries convert on WhatsApp",
        "signal": "Public gmail + WhatsApp",
        "email_source": "Public brand listings",
    },
    {
        "company": "Greeniecan India",
        "founder_name": "Dhirender",
        "founder_role": "Founder contact",
        "to_email": "dhirender@greeniecan.com",
        "phone": "+91 99106 28263",
        "website": "https://www.greeniecan.com",
        "city": "New Delhi",
        "category": "personal care",
        "size": "small",
        "platform": "D2C / B2B",
        "why": "Natural haircare & home products — product education chats before purchase",
        "signal": "Founder email + phones on company PDF",
        "email_source": "Company profile PDF",
    },
    {
        "company": "Greeniecan India",
        "founder_name": "Dhirender",
        "founder_role": "Founder contact",
        "to_email": "greeniecan@gmail.com",
        "phone": "+91 99116 35443",
        "website": "https://www.greeniecan.com",
        "city": "New Delhi",
        "category": "personal care",
        "size": "small",
        "platform": "D2C / B2B",
        "why": "Secondary brand inbox for natural personal care",
        "signal": "greeniecan@gmail.com published",
        "email_source": "Company profile PDF",
    },
    {
        "company": "Amama",
        "founder_name": "",
        "founder_role": "Marketing / PR",
        "to_email": "marketing@amama.in",
        "phone": "+91 98185 23953",
        "website": "https://www.amama.in",
        "city": "Delhi NCR",
        "category": "jewellery",
        "size": "mid D2C",
        "platform": "Shopify",
        "why": "Marketing inbox — Meta/IG growth team that feels WhatsApp conversion gap",
        "signal": "marketing@ + WhatsApp published",
        "email_source": "amama.in/contact",
    },
    {
        "company": "Svaraa Jewels",
        "founder_name": "Chahat Shah",
        "founder_role": "Founder",
        "to_email": "care@svaraa.com",
        "phone": "+91 74360 00826",
        "website": "https://svaraa.com",
        "city": "Surat",
        "category": "jewellery",
        "size": "small/mid",
        "platform": "Shopify",
        "why": "Alt phone path — same brand (dedupe by email in builder)",
        "signal": "Secondary phone on LinkedIn company",
        "email_source": "LinkedIn company",
    },
]


def load_already_sent() -> set[str]:
    sent: set[str] = set()
    for name in (
        "dual_lane_fresh_outreach_report.json",
        "comai_icp_founder_outreach_report.json",
        "comai_agency_partner_outreach_report.json",
        "comai_icp_wave2_outreach_report.json",
    ):
        path = ROOT / "exports" / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("results", []):
            email = (r.get("to_email") or "").lower().strip()
            ok = r.get("send_result") or {}
            if email and isinstance(ok, dict) and ok.get("success"):
                sent.add(email)
            elif email and r.get("success"):
                sent.add(email)
    return sent


def html_body(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>{p.replace(chr(10), '<br>')}</p>"
        for p in paras
    )


def draft(lead: dict) -> tuple[str, str]:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.outreach_generator.hyperpersonal import draft_comai

    d = draft_comai(lead)
    return d.subject, d.body


def build_queue(already: set[str]) -> list[dict]:
    seen: set[str] = set()
    queue: list[dict] = []
    for lead in LEADS:
        email = lead["to_email"].lower().strip()
        if email in seen or email in already:
            continue
        seen.add(email)
        subj, body = draft(lead)
        queue.append({**lead, "subject": subj, "body": body, "wave": "wave2"})
    return queue


def export_wave(queue: list[dict]) -> None:
    csv_path = ROOT / "exports" / "comai_icp_wave2_leads.csv"
    fields = [
        "company", "founder_name", "founder_role", "to_email", "phone",
        "website", "city", "category", "size", "platform", "why", "signal",
        "email_source", "subject",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for q in queue:
            w.writerow(q)
    print(f"Wave2 queue: {len(queue)} -> {csv_path}")


def send_all(queue: list[dict]) -> list[dict]:
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
        results.append({**item, "send_result": res, "outreach_status": "sent" if res.get("success") else "failed"})
        if not res.get("success"):
            print("SMTP failed — stopping.")
            break
        time.sleep(SLEEP)

    report = ROOT / "exports" / "comai_icp_wave2_outreach_report.json"
    sent_n = sum(1 for r in results if r.get("send_result", {}).get("success"))
    report.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "from": "vansh@inowix.in",
                "cc": CC,
                "attempted": len(results),
                "sent": sent_n,
                "failed": len(results) - sent_n,
                "results": [
                    {
                        "company": r["company"],
                        "founder_name": r.get("founder_name"),
                        "to_email": r["to_email"],
                        "phone": r.get("phone"),
                        "subject": r["subject"],
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
    print(f"Sent {sent_n}/{len(results)} | {report}")
    return results


def build_master_csv() -> Path:
    """Merge all known ComAI brand leads (direct + prior waves) with email + phone."""
    rows: dict[str, dict] = {}

    def upsert(row: dict) -> None:
        email = (row.get("email") or row.get("to_email") or "").lower().strip()
        if not email or "@" not in email:
            return
        cur = rows.get(email, {})
        merged = {**cur, **{k: v for k, v in row.items() if v not in (None, "")}}
        merged["email"] = email
        rows[email] = merged

    # Wave2 LEADS
    for L in LEADS:
        upsert(
            {
                "company": L["company"],
                "founder_name": L.get("founder_name"),
                "founder_role": L.get("founder_role"),
                "email": L["to_email"],
                "phone": L.get("phone"),
                "website": L.get("website"),
                "city": L.get("city"),
                "category": L.get("category"),
                "size": L.get("size"),
                "platform": L.get("platform"),
                "why_intent": L.get("why"),
                "signal": L.get("signal"),
                "source": L.get("email_source"),
                "lane": "COMAI_DIRECT",
                "wave": "wave2",
            }
        )

    # Wave1 founder ICP
    p = ROOT / "exports" / "comai_icp_founder_leads.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        for L in data.get("leads", []):
            upsert(
                {
                    "company": L.get("company"),
                    "founder_name": L.get("founder_name"),
                    "founder_role": L.get("founder_role"),
                    "email": L.get("to_email"),
                    "phone": L.get("phone") or "",
                    "website": L.get("website"),
                    "city": L.get("city"),
                    "category": L.get("category"),
                    "size": L.get("size"),
                    "platform": L.get("platform"),
                    "why_intent": L.get("why"),
                    "signal": L.get("signal"),
                    "source": L.get("email_source"),
                    "lane": "COMAI_DIRECT",
                    "wave": "wave1_founder",
                }
            )

    # Enrich phones for wave1 known phones
    phone_enrich = {
        "care@premakala.in": "+91 70692 06000",
        "collab@naitra.in": "+91 99596 98855",
        "elinorjewels@gmail.com": "+91 76006 12814",
        "support@elinorjewels.com": "+91 70961 65209",
        "labeljenn.jinita@gmail.com": "+91 79774 24546",
        "shopsiiri@gmail.com": "+91 79953 09284",
        "hello@mogasu.com": "+91 76662 97989",
        "mogasu.goa@gmail.com": "+91 76662 97989",
        "hello@b77life.com": "+91 95995 50779",
        "info@siyouranaturalcare.com": "+91 79770 59678",
        "preciousjewels265@gmail.com": "+91 98375 44802",
        "tviyajewels@gmail.com": "+91 86898 90123",
        "support@mittalsarees.com": "+91 89302 70049",
        "hello@sadabahaarjewelry.com": "",
    }
    for email, phone in phone_enrich.items():
        if email in rows and phone and not rows[email].get("phone"):
            rows[email]["phone"] = phone

    # Dual-lane master / pending for more ComAI directs
    for fname in ("dual_lane_fresh_leads_master.csv", "dual_lane_pending_queue.csv", "comai_icp_founder_leads.csv"):
        path = ROOT / "exports" / fname
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                lane = (r.get("lane") or "").upper()
                if lane and not lane.startswith("COMAI"):
                    continue
                email = r.get("to_email") or r.get("email") or ""
                upsert(
                    {
                        "company": r.get("company") or r.get("company_name"),
                        "founder_name": r.get("founder_name"),
                        "founder_role": r.get("founder_role"),
                        "email": email,
                        "phone": r.get("phone"),
                        "website": r.get("website"),
                        "city": r.get("city"),
                        "category": r.get("category") or r.get("industry"),
                        "size": r.get("size"),
                        "platform": r.get("platform"),
                        "why_intent": r.get("why") or r.get("angle"),
                        "signal": r.get("signal") or r.get("intent"),
                        "source": r.get("source") or r.get("email_source") or fname,
                        "lane": lane or "COMAI_DIRECT",
                        "wave": fname,
                    }
                )

    # Outreach status from reports
    status_map: dict[str, str] = {}
    for name in (
        "dual_lane_fresh_outreach_report.json",
        "comai_icp_founder_outreach_report.json",
        "comai_agency_partner_outreach_report.json",
        "comai_icp_wave2_outreach_report.json",
    ):
        path = ROOT / "exports" / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("results", []):
            email = (r.get("to_email") or "").lower().strip()
            ok = r.get("send_result") or {}
            if email and isinstance(ok, dict) and ok.get("success"):
                status_map[email] = "sent"
            elif email and isinstance(ok, dict) and ok.get("success") is False:
                status_map.setdefault(email, "failed")

    for email, row in rows.items():
        row["outreach_status"] = status_map.get(email, row.get("outreach_status") or "collected")

    out = ROOT / "exports" / "comai_all_collected_leads_master.csv"
    fields = [
        "company", "founder_name", "founder_role", "email", "phone",
        "website", "city", "category", "size", "platform", "lane",
        "outreach_status", "why_intent", "signal", "source", "wave",
    ]
    ordered = sorted(rows.values(), key=lambda x: (x.get("company") or "", x.get("email") or ""))
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in ordered:
            w.writerow(r)
    print(f"Master CSV: {len(ordered)} rows -> {out}")
    return out


if __name__ == "__main__":
    already = load_already_sent()
    print(f"Already sent (skip): {len(already)}")
    queue = build_queue(already)
    export_wave(queue)
    if "--send" in sys.argv:
        send_all(queue)
    build_master_csv()
    if "--send" not in sys.argv:
        print("Dry run. Pass --send to outreach.")
