#!/usr/bin/env python3
"""Retry failed dual-lane sends + expand with founder-level fresh leads."""

from __future__ import annotations

import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from email_service import send_email  # noqa: E402
from send_dual_lane_fresh_outreach import (  # noqa: E402
    draft_comai_direct,
    draft_comai_partner,
    draft_inowix_direct,
    draft_inowix_partner,
    html_body,
)

CC = "vanshjhamb9@gmail.com"
FROM_NAME = "Vansh Jhamb | Inowix"
SLEEP_BETWEEN = 7.0


# Fresh curated leads — founder-reachable where possible (public pages)
EXPAND = [
    # ——— COMAI Agency Partners (founder emails) ———
    {
        "lane": "COMAI_PARTNER",
        "company_name": "A3 Mediacom",
        "founder_name": "Aditya Jain",
        "to_email": "aditya@a3mediacom.in",
        "website": "https://a3mediacom.in",
        "city": "Gurugram",
        "industry": "D2C performance + retention marketing",
        "angle": "You scale D2C across Meta/Google/marketplaces and already sell retention + website flows — COMAI white-label turns post-ad WhatsApp into a conversion channel your clients keep asking for",
        "phone": "+91 8384052488",
        "source": "a3mediacom.in/contact",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "A3 Mediacom",
        "founder_name": "Anubhav Mehta",
        "to_email": "anubhav@a3mediacom.in",
        "website": "https://a3mediacom.in",
        "city": "Gurugram",
        "industry": "Growth & retention for D2C",
        "angle": "Your retention/CRO work already owns the post-purchase journey — COMAI Agency Partner lets A3 white-label WhatsApp AI commerce without building the stack",
        "phone": "+91 8384052488",
        "source": "a3mediacom.in/contact",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "SW Cybernetics",
        "founder_name": "Amogh Sachdev",
        "to_email": "contact@swcybernetics.in",
        "website": "https://swcybernetics.in",
        "city": "Noida",
        "industry": "Marketplace / ecommerce growth agency",
        "angle": "You scale 500+ brands on Amazon/Flipkart/quick commerce — COMAI white-label adds WhatsApp AI for brands that also sell D2C and need instant chat conversion",
        "phone": "+91 93544 59066",
        "source": "swcybernetics.in",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "SocioBuffs",
        "founder_name": "Deepanshu Suneja",
        "to_email": "contact@sociobuffs.com",
        "website": "https://sociobuffs.com",
        "city": "New Delhi",
        "industry": "Performance marketing + Shopify builds",
        "angle": "100+ Shopify stores + performance marketing for D2C — perfect Agency Partner fit: keep the client, white-label COMAI for WhatsApp AI commerce revenue",
        "phone": "+91 97736 32772",
        "source": "sociobuffs.com + LinkedIn",
    },
    {
        "lane": "COMAI_PARTNER",
        "company_name": "Baking AI",
        "founder_name": "",
        "to_email": "hello@bakingai.com",
        "website": "https://bakingai.com",
        "city": "Gurugram",
        "industry": "AI-powered marketing agency",
        "angle": "AI-led marketing for brands — COMAI is the natural WhatsApp commerce layer you can white-label into client retainers",
        "source": "public agency directory / site",
    },
    # ——— INOWIX white-label / overflow (agencies that sell builds, not competing WL Shopify mills) ———
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "SocioBuffs",
        "founder_name": "Deepanshu Suneja",
        "to_email": "contact@sociobuffs.com",
        "website": "https://sociobuffs.com",
        "city": "New Delhi",
        "industry": "Perf marketing + website development",
        "angle": "You already ship Shopify/web for D2C — when clients ask for custom apps, AI agents, or multi-sprint builds beyond store setup, Inowix is quiet white-label eng capacity under your brand",
        "inowix_note": "defer_same_email_comai_first",
        "source": "sociobuffs.com",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "A3 Mediacom",
        "founder_name": "Anubhav Mehta",
        "to_email": "anubhav@a3mediacom.in",
        "website": "https://a3mediacom.in",
        "city": "Gurugram",
        "industry": "Growth stack incl. website creation",
        "angle": "A3 sells website creation + growth — Inowix white-label covers custom SaaS/apps/AI features when scopes outgrow a marketing-site build",
        "inowix_note": "defer_same_email_comai_first",
        "source": "a3mediacom.in",
    },
    {
        "lane": "INOWIX_DIRECT",
        "company_name": "SW Cybernetics",
        "founder_name": "Amogh Sachdev",
        "to_email": "contact@swcybernetics.in",
        "website": "https://swcybernetics.in",
        "city": "Noida",
        "industry": "Ecommerce enabler / marketplace tech services",
        "angle": "You already deliver marketplace stack for brands — open to co-delivery with Inowix on custom SaaS, AI agents, or product builds US/UK/IN clients request beyond catalog/PPC?",
        "inowix_note": "defer_same_email_comai_first",
        "source": "swcybernetics.in",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Brandscalez",
        "founder_name": "Rohit Raj",
        "to_email": "info@brandscalez.com",
        "website": "https://brandscalez.com",
        "city": "Noida",
        "industry": "Agency offering website + app development",
        "angle": "Lists App Development + Website — Inowix white-label eng capacity without hiring when app scopes stack up",
        "source": "brandscalez.com (wave2 inowix — comai retry separate)",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "PurpleChalk",
        "founder_name": "",
        "to_email": "hello@purplechalk.in",
        "website": "https://www.purplechalk.in",
        "city": "Chennai",
        "industry": "Shopify / digital agency",
        "angle": "Shopify + custom web for brands — white-label Inowix for heavier builds / apps / AI agents",
        "source": "purplechalk.in",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Mobyink Innovations",
        "founder_name": "Kapil Thakkar",
        "to_email": "info@mobyink.com",
        "website": "https://mobyink.com",
        "city": "Jaipur",
        "industry": "Shopify Partner D2C agency",
        "angle": "Official Shopify Partner scaling 150+ brands — white-label Inowix when clients need custom apps/AI beyond theme work",
        "source": "mobyink.com",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "Resultiq Digital",
        "founder_name": "Akash Saini",
        "to_email": "info@resultiqdigital.com",
        "website": "https://resultiqdigital.com",
        "city": "Delhi NCR",
        "industry": "D2C agency with Shopify/WordPress",
        "angle": "Shopify & WordPress builds in your stack — Inowix as overflow engineering / custom app partner under your brand",
        "source": "resultiqdigital.com",
    },
    {
        "lane": "INOWIX_PARTNER",
        "company_name": "PERFORMAKS",
        "founder_name": "",
        "to_email": "growth@performaks.com",
        "website": "https://performaks.com",
        "city": "India",
        "industry": "D2C growth + Shopify ecommerce development",
        "angle": "Shopify ecommerce development spotlight — Inowix as white-label build bench for custom/AI scopes",
        "source": "performaks.com",
    },
    {
        "lane": "INOWIX_DIRECT",
        "company_name": "Graxi Tech Solutions",
        "founder_name": "Sarankumar M",
        "to_email": "info@graxitechs.com",
        "website": "https://graxitechs.com",
        "city": "Bangalore / Chennai",
        "industry": "Offshore / IT for US-UK startups",
        "angle": "Helps US/UK startups build teams — co-delivery / overflow on AI agents & custom SaaS with Inowix",
        "source": "graxitechs.com",
    },
]


def load_failed_from_report() -> list[dict]:
    path = ROOT / "exports" / "dual_lane_fresh_outreach_report.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    failed = []
    for r in data.get("results", []):
        if r.get("send_result", {}).get("success"):
            continue
        # re-draft from stored subject/body if present
        failed.append(
            {
                "lane": r["lane"],
                "company_name": r["company_name"],
                "founder_name": r.get("founder_name") or "",
                "to_email": r["to_email"],
                "website": r.get("website") or "",
                "city": r.get("city") or "",
                "industry": r.get("industry") or "",
                "subject": r["subject"],
                "body": r["body"],
                "why": r.get("why"),
                "angle": r.get("angle"),
                "source": "retry_failed_wave1",
            }
        )
    return failed


def draft_item(lead: dict) -> dict:
    if lead.get("subject") and lead.get("body"):
        return lead
    lane = lead["lane"]
    if lane == "COMAI_DIRECT":
        subj, body = draft_comai_direct(lead)
    elif lane == "COMAI_PARTNER":
        subj, body = draft_comai_partner(lead)
    elif lane == "INOWIX_PARTNER":
        subj, body = draft_inowix_partner(lead)
    else:
        subj, body = draft_inowix_direct(lead)
    return {**lead, "subject": subj, "body": body}


def build_queue() -> list[dict]:
    queue: list[dict] = []
    seen: set[tuple[str, str]] = set()

    # 1) Retry failures first
    for lead in load_failed_from_report():
        key = (lead["to_email"].lower(), lead["lane"])
        if key in seen:
            continue
        seen.add(key)
        queue.append(draft_item(lead))

    # 2) Expand — skip emails already successfully sent in wave1
    report = ROOT / "exports" / "dual_lane_fresh_outreach_report.json"
    already_ok: set[str] = set()
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
        for r in data.get("results", []):
            if r.get("send_result", {}).get("success"):
                already_ok.add(r["to_email"].lower())

    for lead in EXPAND:
        email = lead["to_email"].lower()
        key = (email, lead["lane"])
        if key in seen:
            continue
        # If this email already getting a COMAI_* in this queue, skip INOWIX_* same blast
        if lead["lane"].startswith("INOWIX"):
            if any(
                q["to_email"].lower() == email and q["lane"].startswith("COMAI")
                for q in queue
            ):
                continue
            if lead.get("inowix_note") == "defer_same_email_comai_first":
                # still add if no COMAI for this email in queue and not already_ok as partner
                if any(
                    q["to_email"].lower() == email and q["lane"].startswith("COMAI")
                    for q in queue
                ):
                    continue
        # Don't re-send identical email+lane already OK
        if email in already_ok and lead["lane"].startswith("COMAI"):
            # wave1 may have succeeded on different brands; only skip exact prior success same email
            # already_ok is email-level — skip COMAI expand if email already got any success
            pass
        if email in already_ok:
            # allow INOWIX if only COMAI was sent before — wave1 had no INOWIX success
            prior_lanes = []
            if report.exists():
                data = json.loads(report.read_text(encoding="utf-8"))
                prior_lanes = [
                    r["lane"]
                    for r in data.get("results", [])
                    if r["to_email"].lower() == email and r.get("send_result", {}).get("success")
                ]
            if lead["lane"] in prior_lanes:
                continue
            if any(l.startswith("COMAI") for l in prior_lanes) and lead["lane"].startswith("COMAI"):
                continue

        seen.add(key)
        queue.append(draft_item(lead))

    return queue


def write_leads_csv(queue: list[dict]) -> Path:
    path = ROOT / "exports" / "dual_lane_fresh_leads_enriched.csv"
    fields = [
        "lane", "company_name", "founder_name", "to_email", "website",
        "city", "industry", "phone", "angle", "why", "source", "subject",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for q in queue:
            w.writerow(q)
    return path


def main() -> None:
    queue = build_queue()
    csv_path = write_leads_csv(queue)
    print(f"Queue size: {len(queue)} | leads CSV: {csv_path}")

    results = []
    for i, item in enumerate(queue, 1):
        print(f"[{i}/{len(queue)}] {item['lane']} -> {item['to_email']} ({item['company_name']})")
        res = send_email(
            to_email=item["to_email"],
            subject=item["subject"],
            body_html=html_body(item["body"]),
            body_text=item["body"],
            from_name=FROM_NAME,
            cc=CC,
            retries=4,
            retry_backoff_sec=10.0,
        )
        results.append(
            {
                **{k: item.get(k) for k in (
                    "lane", "company_name", "founder_name", "to_email", "website",
                    "city", "industry", "subject", "body", "why", "angle", "source", "phone",
                )},
                "send_result": res,
                "sent_at": datetime.now(UTC).isoformat(),
            }
        )
        print("  ->", res)
        time.sleep(SLEEP_BETWEEN)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "from": "vansh@inowix.in",
        "cc": CC,
        "wave": "retry_expand",
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

    path = ROOT / "exports" / "dual_lane_retry_expand_outreach_report.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ROOT / "exports" / "dual_lane_retry_expand_outreach_report.md"
    lines = [
        "# Dual-Lane Retry + Expand Outreach (COMAI + INOWIX)",
        "",
        f"- From: vansh@inowix.in | CC: {CC}",
        f"- Sent: {out['sent']}/{out['total']} | Failed: {out['failed']}",
        f"- By lane: {json.dumps(out['by_lane'])}",
        "",
    ]
    for r in results:
        st = "OK" if r["send_result"].get("success") else f"FAIL {r['send_result'].get('error')}"
        lines.append(f"### [{r['lane']}] {r['company_name']}")
        lines.append(f"- To: {r['to_email']} | Founder: {r.get('founder_name') or '-'}")
        lines.append(f"- Subject: {r['subject']}")
        lines.append(f"- Status: {st}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    print("Report:", path)
    print(f"Done sent={out['sent']} failed={out['failed']}")


if __name__ == "__main__":
    main()
