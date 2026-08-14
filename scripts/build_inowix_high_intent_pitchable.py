#!/usr/bin/env python3
"""Build HIGH-INTENT pitchable Inowix leads (verified emails only).

Intent types:
  CAPACITY_OVERFLOW — tiny/mid SaaS hiring eng = need to ship before hire closes
  PRODUCT_BUILD     — explicit mobile/AI/SaaS product build need
  PARTNER_OVERFLOW  — sells builds / needs white-label eng bench
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from email_service import send_email  # noqa: E402
from send_inowix_saas_fresh_outreach import CC, FROM_NAME, html_body  # noqa: E402

# Ranked by how pitchable for Inowix services (custom software / AI / apps / iOS)
# Bias: mid-size / tiny eng teams + verified CEO/founder emails (no guessed addresses)
PITCHABLE = [
    {
        "pitch_score": 97,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Nessie Labs",
        "size": "3 (tiny eng)",
        "founder_name": "Anna Zhang",
        "founder_role": "CEO",
        "to_email": "founders@nessielabs.com",
        "website": "https://nessielabs.com",
        "hq": "San Francisco",
        "why_pitchable": "YC AI context layer — team of ~3, public founders@, hiring Founding Engineer / FDE while shipping product",
        "requirement": "Founding Engineer / Founding Forward Deployed Engineer",
        "inowix_offer": "AI product + full-stack surge capacity while founding hires close",
        "intent_date": "2026-08 (YC jobs live)",
        "source": "https://www.ycombinator.com/companies/nessie + nessielabs.com/about",
    },
    {
        "pitch_score": 96,
        "intent_type": "PRODUCT_BUILD",
        "company": "Juno",
        "size": "2 (tiny eng)",
        "founder_name": "Marshall Gould",
        "founder_role": "CEO",
        "to_email": "team@juno-chat.com",
        "website": "https://junocompanion.com",
        "hq": "San Francisco",
        "why_pitchable": "YC health AI — 2-person team, 150k users, actively hiring Founding Mobile + AI Engineer; team@ is public founder contact",
        "requirement": "Founding Mobile Engineer + AI Founding Engineer",
        "inowix_offer": "iOS/Android + AI product engineering partner for consumer health app",
        "intent_date": "2026-08 (YC jobs live)",
        "source": "https://www.ycombinator.com/companies/juno-chat",
    },
    {
        "pitch_score": 95,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Prematch",
        "size": "60-70 (mid)",
        "founder_name": "Lukas Röhle",
        "founder_role": "CEO",
        "to_email": "hello@prematchapp.de",
        "website": "https://prematchapp.de",
        "hq": "Cologne, Germany",
        "why_pitchable": "Mid-size sports SaaS hiring Senior Flutter TODAY — roadmap ahead of headcount; overflow Flutter/iOS is a natural buy",
        "requirement": "Senior Mobile/Flutter engineer (posted today)",
        "inowix_offer": "Flutter + iOS/Android delivery capacity under CTO while hire closes",
        "intent_date": "2026-08-14",
        "source": "https://wellfound.com/jobs/4572800-senior-software-engineer-mobile-all-genders",
    },
    {
        "pitch_score": 94,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Prematch",
        "size": "60-70 (mid)",
        "founder_name": "Niklas Brackmann",
        "founder_role": "Co-Founder",
        "to_email": "niklas@prematchapp.de",
        "website": "https://prematchapp.de",
        "hq": "Cologne, Germany",
        "why_pitchable": "Co-founder inbox + same-day Flutter hire signal",
        "requirement": "Mobile eng capacity for grassroots sports SaaS",
        "inowix_offer": "White-label / overflow Flutter + backend sprints",
        "intent_date": "2026-08-14",
        "source": "Wellfound + LinkedIn company email",
    },
    {
        "pitch_score": 93,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Jiga",
        "size": "~25 (mid)",
        "founder_name": "Adar Hay",
        "founder_role": "CEO",
        "to_email": "founders@jiga.io",
        "website": "https://jiga.io",
        "hq": "Tel Aviv / US",
        "why_pitchable": "Series A manufacturing SaaS posted Full Stack Product Engineer ~2h ago; AI already in product — need ship velocity",
        "requirement": "Full Stack Product Engineer (YC jobs ~2h)",
        "inowix_offer": "Custom SaaS features + AI automation overflow for sourcing platform",
        "intent_date": "2026-08-14",
        "source": "https://www.ycombinator.com/companies/jiga",
    },
    {
        "pitch_score": 92,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Runway (runway.team)",
        "size": "~18 (mid)",
        "founder_name": "Gabriel Savit",
        "founder_role": "CEO",
        "to_email": "hello@runway.team",
        "website": "https://www.runway.team",
        "hq": "New York",
        "why_pitchable": "Mobile-release SaaS added Full Stack hire ~9h ago — product company that lives on mobile tooling",
        "requirement": "Full Stack Engineer (YC jobs ~9h)",
        "inowix_offer": "Full-stack SaaS feature delivery / surge capacity",
        "intent_date": "2026-08-14",
        "source": "YC jobs board",
    },
    {
        "pitch_score": 91,
        "intent_type": "PRODUCT_BUILD",
        "company": "ANORIA",
        "size": "5",
        "founder_name": "Michael Belhassen",
        "founder_role": "Founder",
        "to_email": "hello@anoria.com",
        "website": "https://www.anoria.com",
        "hq": "San Francisco",
        "why_pitchable": "YC S26 wearable AI — actively hiring founding iOS/full-stack; companion app + inference pipeline is exact Inowix stack",
        "requirement": "Founding Full-Stack iOS / cloud+ML surface",
        "inowix_offer": "iOS app + AI product engineering partner / parallel build track",
        "intent_date": "2026-08-13/14",
        "source": "YC + anoria.com/contact",
    },
    {
        "pitch_score": 90,
        "intent_type": "PRODUCT_BUILD",
        "company": "Willow Voice",
        "size": "10-20",
        "founder_name": "Allan Guo",
        "founder_role": "CEO",
        "to_email": "allan@willowvoice.com",
        "website": "https://willowvoice.com",
        "hq": "San Francisco",
        "why_pitchable": "YC voice SaaS hiring Founding iOS Engineer — founder email public; mobile is core product surface",
        "requirement": "Founding Engineer (iOS)",
        "inowix_offer": "Native iOS + AI product engineering capacity",
        "intent_date": "2026-08-14 (active YC listing)",
        "source": "YC Willow iOS job + founder podcast email",
    },
    {
        "pitch_score": 89,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "HomeTeams",
        "size": "1-10",
        "founder_name": "Steve White",
        "founder_role": "Founder/CEO",
        "to_email": "katie@hometeams.io",
        "website": "https://www.hometeams.io",
        "hq": "Michigan, USA",
        "why_pitchable": "AI care SaaS posted Senior Full Stack (RN + LLM) yesterday — needs product shipped while hiring",
        "requirement": "Senior Full Stack — React Native + web + LLM",
        "inowix_offer": "Custom SaaS + mobile + AI features (route via Katie EA)",
        "intent_date": "2026-08-13",
        "source": "Wellfound + hometeams.io/about",
    },
    {
        "pitch_score": 89,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Replo",
        "size": "~20 (mid)",
        "founder_name": "Yuxin Zhu",
        "founder_role": "Co-Founder",
        "to_email": "yuxin@replo.app",
        "website": "https://replo.app",
        "hq": "San Francisco",
        "why_pitchable": "YC ecommerce builder — ~20 people, founder publicly shares yuxin@ for hiring; Senior Full-Stack open = capacity gap",
        "requirement": "Senior Software Engineer (Full-Stack)",
        "inowix_offer": "Full-stack SaaS / AI feature overflow under product leadership",
        "intent_date": "Active YC careers",
        "source": "YC Replo + LinkedIn founder email (yuxin AT replo DOT app)",
    },
    {
        "pitch_score": 88,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Sei AI",
        "size": "~17",
        "founder_name": "Pranay Shetty",
        "founder_role": "CEO",
        "to_email": "founders@seiright.com",
        "website": "https://seiright.com",
        "hq": "NYC + Chennai",
        "why_pitchable": "YC AI mortgage/banking ops — GenAI full-stack hire active; regulated AI product needs senior builders fast",
        "requirement": "Full Stack (TS/React/GenAI) Chennai",
        "inowix_offer": "Custom AI agents + full-stack platform hardening overflow",
        "intent_date": "2026-08-14 (active)",
        "source": "FoundersAreHiring + founders@seiright.com",
    },
    {
        "pitch_score": 88,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "vishwa.ai",
        "size": "5-8 (tiny eng)",
        "founder_name": "Sai Sharan Tangeda",
        "founder_role": "CEO",
        "to_email": "hello@vishwa.ai",
        "website": "https://vishwa.ai",
        "hq": "Bangalore / SF",
        "why_pitchable": "India fintech AI SaaS (~5–8 people, ~2 technical) publicly hiring eng via hello@ — classic low-bench overflow buyer",
        "requirement": "Engineering roles (CEO posts hello@vishwa.ai)",
        "inowix_offer": "Custom AI / full-stack SaaS capacity for LendingAI/DocsAI product",
        "intent_date": "Active LinkedIn hiring ask",
        "source": "CEO LinkedIn + vishwa.ai",
    },
    {
        "pitch_score": 87,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Helium",
        "size": "~9",
        "founder_name": "Zach Witzel",
        "founder_role": "CEO",
        "to_email": "founders@tryhelium.com",
        "website": "https://tryhelium.com",
        "hq": "San Francisco",
        "why_pitchable": "YC AI for mobile app monetization — publicly asks for eng intros at founders@; self-improving software = AI build capacity",
        "requirement": "Software engineers (SF); founder asks email founders@/hi@",
        "inowix_offer": "AI product engineering / full-stack surge for mobile growth systems",
        "intent_date": "Active YC + LinkedIn hiring",
        "source": "https://www.ycombinator.com/companies/helium",
    },
    {
        "pitch_score": 86,
        "intent_type": "PRODUCT_BUILD",
        "company": "Boock.ai",
        "size": "1-10",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@boock.ai",
        "website": "https://boock.ai",
        "hq": "US + India remote",
        "why_pitchable": "Hiring founding agentic AI + full-stack — greenfield multi-agent publishing product",
        "requirement": "Founding Agentic AI / Full Stack Engineer",
        "inowix_offer": "Custom AI agents + SaaS MVP build partner",
        "intent_date": "2026-08-14 (Wellfound active)",
        "source": "Wellfound + boock.ai",
    },
    {
        "pitch_score": 85,
        "intent_type": "PRODUCT_BUILD",
        "company": "AIVOA Technology",
        "size": "Early India AI SaaS",
        "founder_name": "Waseem Mulla",
        "founder_role": "Exec contact",
        "to_email": "waseem.mulla@aivoa.ai",
        "phone": "+91 99014 11003",
        "website": "https://aivoa.ai",
        "hq": "Bangalore",
        "why_pitchable": "Agentic QMS SaaS hiring AI full-stack; public exec email + phone — India AI product build",
        "requirement": "Full Stack Developer – AI Applications",
        "inowix_offer": "Custom AI solutions / agentic workflows / SaaS eng capacity",
        "intent_date": "Active Aug 2026",
        "source": "aivoa.ai contact + Shine job",
    },
    {
        "pitch_score": 85,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Cookiy AI",
        "size": "10-20 (mid)",
        "founder_name": "Davin Dong",
        "founder_role": "CEO",
        "to_email": "hiring@cookiy.ai",
        "website": "https://cookiy.ai",
        "hq": "Palo Alto",
        "why_pitchable": "Voice AI research SaaS raised $7M; hiring Full Stack / Voice Agent eng globally — mid team with eng gap (route via hiring@)",
        "requirement": "Full Stack AI / Voice Agent Engineers",
        "inowix_offer": "AI product engineering / full-stack surge (capacity partner, not job app)",
        "intent_date": "Active hiring posts",
        "source": "CEO LinkedIn hiring@cookiy.ai",
    },
    {
        "pitch_score": 84,
        "intent_type": "PRODUCT_BUILD",
        "company": "Songscription",
        "size": "~10",
        "founder_name": "Andrew Carlins",
        "founder_role": "CEO",
        "to_email": "hello@songscription.ai",
        "website": "https://www.songscription.ai",
        "hq": "Palo Alto",
        "why_pitchable": "$5M seed AI music SaaS — founding mobile developer role still live (iOS/Android from zero)",
        "requirement": "Founding Mobile App Developer",
        "inowix_offer": "iOS/Android + AI product MVP build",
        "intent_date": "Careers live (posted Jun 2026, still open)",
        "source": "songscription.ai/careers",
    },
    {
        "pitch_score": 83,
        "intent_type": "PARTNER_OVERFLOW",
        "company": "Apexnova",
        "size": "Early Mumbai tech",
        "founder_name": "Sahil Asopa",
        "founder_role": "Founder",
        "to_email": "hello@apexnova.in",
        "website": "https://apexnova.in",
        "hq": "Mumbai",
        "why_pitchable": "Sells SaaS/OTT/AI builds to clients AND hiring Flutter Aug 2 — classic white-label eng-bench buyer",
        "requirement": "Flutter Developer (on-site) for client product delivery",
        "inowix_offer": "White-label Flutter/iOS/custom software capacity under Apexnova brand",
        "intent_date": "2026-08-02",
        "source": "Founder LinkedIn hiring post",
    },
    {
        "pitch_score": 82,
        "intent_type": "PRODUCT_BUILD",
        "company": "Torkk",
        "size": "1-10",
        "founder_name": "Shivasheesh Kumar",
        "founder_role": "Founder",
        "to_email": "hr@torkk.in",
        "website": "https://torkk.in",
        "hq": "Delhi NCR",
        "why_pitchable": "Mobility platform hiring Flutter + prefers backend skills — building product from ground up",
        "requirement": "Flutter Developer (maps, realtime, payments)",
        "inowix_offer": "Flutter app + Node/Go backend product development",
        "intent_date": "2026-08-03",
        "source": "Founder LinkedIn",
    },
    {
        "pitch_score": 81,
        "intent_type": "PRODUCT_BUILD",
        "company": "UnClaimedX (Pass Down)",
        "size": "Early",
        "founder_name": "Sandeep P Gaonkar",
        "founder_role": "Founder",
        "to_email": "hello@unclaimedx.com",
        "website": "https://unclaimedx.com",
        "hq": "Bengaluru",
        "why_pitchable": "Encrypted inheritance SaaS app hiring Flutter — security-sensitive mobile product",
        "requirement": "Flutter Intern + Jr Flutter Developer",
        "inowix_offer": "Flutter + secure SaaS mobile build partner",
        "intent_date": "Recent LinkedIn",
        "source": "Founder LinkedIn hello@unclaimedx.com",
    },
    {
        "pitch_score": 80,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Helium",
        "size": "~9",
        "founder_name": "Zach Witzel",
        "founder_role": "CEO",
        "to_email": "hi@tryhelium.com",
        "website": "https://tryhelium.com",
        "hq": "San Francisco",
        "why_pitchable": "Public hiring inbox for eng resumes — secondary path to founders@",
        "requirement": "Software engineers SF",
        "inowix_offer": "AI/full-stack capacity partnership (not job application — partner pitch)",
        "intent_date": "Active",
        "source": "LinkedIn Zach Witzel post",
    },
    {
        "pitch_score": 72,
        "intent_type": "CAPACITY_OVERFLOW",
        "company": "Lyzr AI",
        "size": "150-200 (larger — lower priority)",
        "founder_name": "Siva Surendira",
        "founder_role": "CEO",
        "to_email": "contact@lyzr.ai",
        "website": "https://lyzr.ai",
        "hq": "NJ / Bengaluru",
        "why_pitchable": "Series A agent platform hiring GenAI full-stack Bengaluru — partnership/augmentation angle",
        "requirement": "Full Stack Engineer – GenAI",
        "inowix_offer": "AI agent / custom AI delivery partnership or eng augmentation",
        "intent_date": "2026-08-14 active careers",
        "source": "careers.lyzr.ai + contact@lyzr.ai",
    },
]


def draft(lead: dict) -> tuple[str, str]:
    """Hyperpersonalized Inowix draft (shared with Lead Engine)."""
    # EA routing for HomeTeams
    if str(lead.get("to_email") or lead.get("email") or "").startswith("katie@"):
        subject = "For Steve — HomeTeams product capacity (Inowix)"
        body = """Hi Katie,

Please pass to Steve White.

HomeTeams is hiring senior full-stack with LLM/product features — classic overflow slot.

Inowix builds custom SaaS, AI features, and mobile apps for product teams that need senior delivery while hiring. Happy to do a 15-min intro if useful.

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
        return subject, body

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.outreach_generator.hyperpersonal import draft_inowix

    payload = {
        **lead,
        "why": lead.get("why_pitchable") or lead.get("requirement") or lead.get("why"),
        "email": lead.get("to_email") or lead.get("email"),
    }
    d = draft_inowix(payload)
    return d.subject, d.body


def export_and_optionally_send(do_send: bool = False) -> None:
    seen = set()
    queue = []
    for lead in sorted(PITCHABLE, key=lambda x: -x["pitch_score"]):
        email = lead["to_email"].lower()
        if email in seen:
            continue
        seen.add(email)
        subj, body = draft(lead)
        queue.append({**lead, "subject": subj, "body": body})

    csv_path = ROOT / "exports" / "inowix_high_intent_pitchable.csv"
    json_path = ROOT / "exports" / "inowix_high_intent_pitchable.json"
    md_path = ROOT / "exports" / "inowix_high_intent_pitchable.md"

    fields = [
        "pitch_score", "intent_type", "company", "founder_name", "founder_role",
        "to_email", "phone", "website", "hq", "size", "requirement", "why_pitchable",
        "inowix_offer", "intent_date", "source", "subject",
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
                "note": "Verified emails only. Ranked by pitchability for Inowix custom software / AI / apps / iOS.",
                "leads": queue,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Inowix High-Intent Pitchable Leads",
        "",
        f"- Count: {len(queue)}",
        f"- CC planned: {', '.join(CC)}",
        "",
        "| Score | Type | Company | Contact | Email | Why pitchable |",
        "|------:|------|---------|---------|-------|---------------|",
    ]
    for q in queue:
        lines.append(
            f"| {q['pitch_score']} | {q['intent_type']} | {q['company']} | "
            f"{q.get('founder_name') or '-'} | `{q['to_email']}` | {q['why_pitchable'][:90]}... |"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(queue)} leads -> {csv_path}")

    if not do_send:
        return

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
        time.sleep(12)

    report = ROOT / "exports" / "inowix_high_intent_outreach_report.json"
    report.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "sent": sum(1 for r in results if r.get("send_result", {}).get("success")),
                "results": [
                    {
                        "company": r["company"],
                        "to_email": r["to_email"],
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
    print("Report:", report)


if __name__ == "__main__":
    export_and_optionally_send(do_send="--send" in sys.argv)
