#!/usr/bin/env python3
"""Inowix SaaS-only fresh opportunities (last ~48h signals) + outreach.

CC: vanshjhamb9@gmail.com, ragibali84@gmail.com
Only includes leads with publicly verified emails + dated intent signals.
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
FROM_NAME = "Vansh Jhamb | Inowix"
SLEEP = 12.0

# Freshness window: signals dated ~Aug 12–14 2026 (today = Aug 14)
LEADS = [
    {
        "company": "Prematch",
        "size": "60-70",
        "stage": "Series / multi-round funded sports SaaS",
        "hq": "Cologne / Berlin, Germany",
        "founder_name": "Lukas Röhle",
        "founder_role": "Co-Founder & CEO",
        "founder_2": "Fiete Grünter (Co-Founder & CTO)",
        "to_email": "hello@prematchapp.de",
        "alt_email": "niklas@prematchapp.de",
        "website": "https://prematchapp.de",
        "linkedin_company": "https://www.linkedin.com/company/prematch/",
        "intent": "Senior Software Engineer – Mobile (Flutter) posted TODAY on Wellfound",
        "intent_date": "2026-08-14 (posted today)",
        "intent_source": "https://wellfound.com/jobs/4572800-senior-software-engineer-mobile-all-genders",
        "service_fit": "iOS/Android Flutter app + full-stack capacity; AI-first mobile delivery",
        "email_source": "Impressum hello@prematchapp.de; LinkedIn lists niklas@prematchapp.de",
        "pitch_type": "mobile_overflow",
    },
    {
        "company": "Prematch",
        "size": "60-70",
        "stage": "Series / multi-round funded sports SaaS",
        "hq": "Cologne / Berlin, Germany",
        "founder_name": "Niklas Brackmann",
        "founder_role": "Co-Founder",
        "to_email": "niklas@prematchapp.de",
        "website": "https://prematchapp.de",
        "intent": "Senior mobile/Flutter hire posted TODAY — eng capacity signal",
        "intent_date": "2026-08-14 (posted today)",
        "intent_source": "https://wellfound.com/jobs/4572800-senior-software-engineer-mobile-all-genders",
        "service_fit": "White-label / overflow Flutter + backend for grassroots sports SaaS",
        "email_source": "LinkedIn company emails: niklas@prematchapp.de",
        "pitch_type": "mobile_overflow",
    },
    {
        "company": "HomeTeams",
        "size": "1-10 (growing)",
        "stage": "Early SaaS — AI care coordination",
        "hq": "Chesterfield, MI, USA",
        "founder_name": "Steve White",
        "founder_role": "Founder & CEO",
        "to_email": "katie@hometeams.io",
        "website": "https://www.hometeams.io",
        "intent": "Senior Full Stack (React Native + web + LLM features) posted 1 day ago",
        "intent_date": "2026-08-13 (posted 1 day ago)",
        "intent_source": "https://wellfound.com/jobs/4574791-senior-software-engineer-full-stack",
        "service_fit": "Custom SaaS + React Native mobile + AI/LLM product features while hiring",
        "email_source": "About page: Katie Clark EA primary contact katie@hometeams.io for Steve",
        "pitch_type": "saas_ai_build",
        "note": "Route via Katie to Steve — published as founder EA channel",
    },
    {
        "company": "ANORIA",
        "size": "5",
        "stage": "YC Spring 2026 — wearable AI SaaS",
        "hq": "San Francisco, CA",
        "founder_name": "Michael Belhassen",
        "founder_role": "Founder",
        "to_email": "hello@anoria.com",
        "website": "https://www.anoria.com",
        "intent": "Founding Full-Stack iOS Engineer actively hiring (Ashby/YC listing live ~hours)",
        "intent_date": "~2026-08-13/14 (role listed ~13h on remote boards; YC jobs live)",
        "intent_source": "https://www.ycombinator.com/companies/anoria/jobs/8J1xbSZ-founding-software-engineer ; Ashby via Clera board",
        "service_fit": "Companion iOS app + cloud pipeline + custom AI inference product engineering",
        "email_source": "https://www.anoria.com/contact → hello@anoria.com",
        "pitch_type": "ios_ai",
    },
    {
        "company": "Sei AI",
        "size": "~17",
        "stage": "YC-backed AI ops for mortgage/banking",
        "hq": "NYC + Chennai eng",
        "founder_name": "Pranay Shetty",
        "founder_role": "Co-Founder & CEO",
        "founder_2": "Ram Venkataraman (Co-Founder & CTO)",
        "to_email": "founders@seiright.com",
        "website": "https://seiright.com",
        "intent": "Full Stack Engineer (Typescript, React, Gen AI) — Chennai hybrid, founder-connect listing active",
        "intent_date": "Active listing verified 2026-08-14 (FoundersAreHiring / company careers)",
        "intent_source": "https://foundersarehiring.com/job/hybrid/full-stack-engineer-typescript-react-gen-ai-689c26853ea1d89ed0c12b08",
        "service_fit": "GenAI full-stack / custom AI agents / platform hardening overflow while scaling V1→V2",
        "email_source": "LinkedIn company emails: founders@seiright.com",
        "pitch_type": "saas_ai_build",
    },
    {
        "company": "AIVOA Technology",
        "size": "Early / directors Mohamed Elyas + Sakthivelan",
        "stage": "AI-native QMS / life-sciences SaaS (Bangalore)",
        "hq": "Bangalore, India",
        "founder_name": "Waseem Mulla",
        "founder_role": "Sales Director / executive contact (public)",
        "decision_makers": "Directors: Mohamed Elyas, Sakthivelan (MCA)",
        "to_email": "waseem.mulla@aivoa.ai",
        "alt_email": "admin@aivoa.ai",
        "phone": "+91 99014 11003",
        "website": "https://aivoa.ai",
        "intent": "Hiring Full Stack Developer – AI Applications (Python + React) — India remote",
        "intent_date": "Listing active as of early Aug 2026 (Shine); product aggressively shipping agentic QMS",
        "intent_source": "https://www.shine.com/jobs/full-stack-developer-ai-applications-python-react-fresher-wfh/aivoa/19203322 ; https://aivoa.ai",
        "service_fit": "Custom AI solutions / agentic workflows / full-stack SaaS build capacity",
        "email_source": "aivoa.ai contact section",
        "pitch_type": "saas_ai_build",
        "freshness_note": "Job may be slightly older than 48h; company is mid-market India AI SaaS with public exec email — include as high-fit India lead",
    },
    {
        "company": "Willow Voice",
        "size": "10-20",
        "stage": "YC X25 — AI voice SaaS ($4.2M)",
        "hq": "San Francisco, CA",
        "founder_name": "Allan Guo",
        "founder_role": "Co-Founder & CEO",
        "founder_2": "Lawrence Liu (Co-Founder & CTO)",
        "to_email": "allan@willowvoice.com",
        "website": "https://willowvoice.com",
        "intent": "Founding Engineer (iOS) — build Willow iOS experience; voice/AI product",
        "intent_date": "Active YC job listing verified 2026-08-14",
        "intent_source": "https://www.ycombinator.com/companies/willow/jobs/fqRS0WJ-founding-engineer-ios",
        "service_fit": "Native iOS + AI product engineering / mobile capacity while hiring founding iOS",
        "email_source": "Founder stated publicly: allan@willowvoice.com (Willow podcast/YouTube)",
        "pitch_type": "ios_ai",
    },
    {
        "company": "Runway (runway.team)",
        "size": "~18",
        "stage": "YC W21 — mobile release management SaaS",
        "hq": "New York, NY",
        "founder_name": "Gabriel Savit",
        "founder_role": "Co-Founder & CEO",
        "founder_2": "David Filion (Co-Founder)",
        "to_email": "hello@runway.team",
        "website": "https://www.runway.team",
        "intent": "Full Stack Engineer role added ~9 hours ago on YC jobs board",
        "intent_date": "2026-08-14 (~9 hours ago on YC jobs)",
        "intent_source": "https://www.ycombinator.com/jobs/role (Runway W21 Full Stack Engineer)",
        "service_fit": "Full-stack SaaS capacity for mobile-devtools platform while hiring",
        "email_source": "LinkedIn company emails: hello@runway.team",
        "pitch_type": "saas_ai_build",
    },
    {
        "company": "Jiga",
        "size": "~25",
        "stage": "YC W21 — manufacturing sourcing SaaS (Series A)",
        "hq": "Tel Aviv / US remote",
        "founder_name": "Adar Hay",
        "founder_role": "Co-Founder & CEO",
        "founder_2": "Yonatan Wolowelsky (CTO)",
        "to_email": "founders@jiga.io",
        "website": "https://jiga.io",
        "intent": "Full Stack Product Engineer — posted ~2 hours ago on YC jobs",
        "intent_date": "2026-08-14 (~2 hours ago)",
        "intent_source": "https://www.ycombinator.com/companies/jiga (Full Stack Product Engineer Remote/US)",
        "service_fit": "Custom SaaS / AI automation on manufacturing platform; full-stack overflow",
        "email_source": "YC company page: founders@jiga.io",
        "pitch_type": "saas_ai_build",
    },
    {
        "company": "Boock.ai",
        "size": "1-10",
        "stage": "Agentic AI publishing SaaS",
        "hq": "US + Remote India",
        "founder_name": "",
        "founder_role": "Founding team",
        "to_email": "hello@boock.ai",
        "website": "https://boock.ai",
        "intent": "Founding Full Stack / Agentic AI Engineer roles open (MERN + multi-agent)",
        "intent_date": "Active Wellfound listing verified 2026-08-14",
        "intent_source": "https://wellfound.com/jobs/3725654-founding-agentic-ai-engineer-boock-ai-remote-india ; https://boock.ai",
        "service_fit": "Custom AI agents / full-stack SaaS MVP capacity for publishing automation",
        "email_source": "boock.ai footer: hello@boock.ai",
        "pitch_type": "saas_ai_build",
    },
    {
        "company": "Songscription",
        "size": "~10",
        "stage": "AI music SaaS ($5M seed)",
        "hq": "Palo Alto / Stanford",
        "founder_name": "Andrew Carlins",
        "founder_role": "Co-Founder & CEO",
        "to_email": "hello@songscription.ai",
        "alt_email": "jobs@songscription.ai",
        "website": "https://www.songscription.ai",
        "intent": "Founding Mobile App Developer — iOS/Android for AI transcription → learning app",
        "intent_date": "Careers page still live (posted Jun 18 2026); active hiring signal",
        "intent_source": "https://www.songscription.ai/careers/founding-mobile-app-developer",
        "service_fit": "iOS/Android + AI product build; mobile MVP capacity",
        "email_source": "songscription.ai/contact hello@ ; careers jobs@",
        "pitch_type": "ios_ai",
        "priority": "secondary",
    },
    {
        "company": "Apexnova",
        "size": "Early (Mumbai)",
        "stage": "Builds SaaS / OTT / AI products (needs Flutter capacity)",
        "hq": "Mumbai, India",
        "founder_name": "Sahil Asopa",
        "founder_role": "Founder / Director",
        "to_email": "hello@apexnova.in",
        "website": "https://apexnova.in",
        "intent": "Hiring Flutter Developer (on-site) — LinkedIn post Aug 2 2026",
        "intent_date": "2026-08-02 (recent India hire; slightly >48h)",
        "intent_source": "https://www.linkedin.com/posts/sahilasopa_hiring-flutter-developer-on-site-full-time-activity-7489676124189265920-6s1c",
        "service_fit": "Flutter/iOS overflow or white-label eng for SaaS/OTT client builds",
        "email_source": "Founder LinkedIn post: hello@apexnova.in",
        "pitch_type": "mobile_overflow",
        "priority": "secondary",
    },
    {
        "company": "Torkk (BlackOriginX)",
        "size": "1-10",
        "stage": "Mobility SaaS / app platform",
        "hq": "Delhi NCR, India",
        "founder_name": "Shivasheesh Kumar",
        "founder_role": "Founder",
        "to_email": "hr@torkk.in",
        "website": "https://torkk.in",
        "intent": "Hiring Flutter Developer for Torkk mobility platform — LinkedIn Aug 3 2026",
        "intent_date": "2026-08-03",
        "intent_source": "https://www.linkedin.com/posts/shivasheeshkumar_hiring-flutterdeveloper-flutterjobs-activity-7490085572129230849-6Y5V",
        "service_fit": "Flutter + Node/Go backend app development capacity",
        "email_source": "Founder LinkedIn post: hr@torkk.in",
        "pitch_type": "mobile_overflow",
        "priority": "secondary",
    },
    {
        "company": "UnClaimedX (Pass Down)",
        "size": "Early",
        "stage": "Encrypted digital inheritance SaaS app",
        "hq": "Bengaluru, India",
        "founder_name": "Sandeep P Gaonkar",
        "founder_role": "Founder",
        "to_email": "hello@unclaimedx.com",
        "website": "https://unclaimedx.com",
        "intent": "Hiring Flutter Intern + Jr Flutter Developer for Pass Down app",
        "intent_date": "Recent LinkedIn hiring post (Bengaluru)",
        "intent_source": "LinkedIn hiring post UnClaimedX / Pass Down → hello@unclaimedx.com",
        "service_fit": "Flutter mobile + secure SaaS app development partner",
        "email_source": "Founder LinkedIn: hello@unclaimedx.com",
        "pitch_type": "mobile_overflow",
        "priority": "secondary",
    },
    {
        "company": "Lyzr AI",
        "size": "150-200 (mid/large — optional)",
        "stage": "Series A agent infrastructure",
        "hq": "Jersey City / Bengaluru",
        "founder_name": "Siva Surendira",
        "founder_role": "Founder & CEO",
        "to_email": "contact@lyzr.ai",
        "alt_email": "reimagine@lyzr.ai",
        "website": "https://lyzr.ai",
        "intent": "Full Stack Engineer – GenAI (Bengaluru hybrid) open on careers",
        "intent_date": "Active careers listing verified 2026-08-14",
        "intent_source": "https://careers.lyzr.ai/jobs/536318-full-stack-engineer-genai",
        "service_fit": "AI agent platform eng augmentation / custom AI delivery partnership",
        "email_source": "lyzr.ai/contact contact@lyzr.ai; LinkedIn posts reimagine@lyzr.ai",
        "pitch_type": "saas_ai_build",
        "freshness_note": "Larger than ideal mid-size; include as secondary",
        "priority": "secondary",
    },
]


def html_body(text: str) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    return "".join(
        f"<p style='margin:0 0 14px;line-height:1.55;font-size:15px;color:#111'>"
        f"{p.replace(chr(10), '<br/>')}</p>"
        for p in paras
    )


def draft(lead: dict) -> tuple[str, str]:
    """Hyperpersonalized Inowix draft (shared with Lead Engine)."""
    if str(lead.get("to_email") or "").startswith("katie@"):
        body = """Hi Katie,

Could you please pass this to Steve White?

I saw HomeTeams posted a Senior Full Stack role yesterday (React Native + web + LLM features). Inowix builds custom SaaS, AI product features, and mobile apps for teams that need senior delivery capacity while hiring.

Happy to do a short intro with Steve if useful.

Best,
Vansh Jhamb
Founder, Inowix
vansh@inowix.in
https://inowix.in"""
        return "For Steve — HomeTeams full-stack / AI capacity (Inowix)", body

    from packages.outreach_generator.hyperpersonal import draft_inowix

    payload = {
        **lead,
        "why": lead.get("intent") or lead.get("why") or lead.get("service_fit"),
        "inowix_offer": lead.get("service_fit") or lead.get("inowix_offer"),
        "requirement": lead.get("intent"),
        "intent_type": (
            "PRODUCT_BUILD"
            if lead.get("pitch_type") in ("mobile_overflow", "ios_ai")
            else lead.get("intent_type")
        ),
    }
    d = draft_inowix(payload)
    return d.subject, d.body



def build_queue(include_secondary: bool = False) -> list[dict]:
    out = []
    seen = set()
    for lead in LEADS:
        if lead.get("priority") == "secondary" and not include_secondary:
            continue
        email = lead["to_email"].lower()
        if email in seen:
            continue
        seen.add(email)
        subj, body = draft(lead)
        out.append({**lead, "subject": subj, "body": body, "lane": "INOWIX_SAAS"})
    return out


def export_queue(queue: list[dict]) -> None:
    path_json = ROOT / "exports" / "inowix_saas_fresh_opportunities.json"
    path_csv = ROOT / "exports" / "inowix_saas_fresh_opportunities.csv"
    path_md = ROOT / "exports" / "inowix_saas_fresh_opportunities.md"

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "window": "signals ~ last 48h where dated; verified public emails only",
        "from": "vansh@inowix.in",
        "cc": CC,
        "count": len(queue),
        "leads": queue,
    }
    path_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = [
        "company", "founder_name", "founder_role", "to_email", "phone", "website",
        "hq", "size", "intent", "intent_date", "intent_source", "service_fit",
        "email_source", "subject",
    ]
    with path_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for q in queue:
            w.writerow(q)

    lines = [
        "# Inowix SaaS Fresh Opportunities (last ~48h)",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- From: vansh@inowix.in | CC: {', '.join(CC)}",
        f"- Count: {len(queue)}",
        "",
        "## Strict rules applied",
        "- SaaS / product companies with real eng demand (custom software, AI, apps, iOS)",
        "- Publicly verified emails only (no guessed founder emails)",
        "- Prefer mid-size; include early SaaS when intent is strong and dated",
        "",
    ]
    for q in queue:
        lines.append(f"### {q['company']} — {q['founder_name']} ({q.get('founder_role','')})")
        lines.append(f"- To: `{q['to_email']}`")
        lines.append(f"- Intent: {q['intent']}")
        lines.append(f"- When: {q['intent_date']}")
        lines.append(f"- Source: {q['intent_source']}")
        lines.append(f"- Fit: {q['service_fit']}")
        lines.append(f"- Subject: {q['subject']}")
        lines.append("")
    path_md.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", path_csv)


def send_queue(queue: list[dict], delay: float = SLEEP) -> dict:
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
            retry_backoff_sec=15.0,
        )
        results.append({**item, "send_result": res, "sent_at": datetime.now(UTC).isoformat()})
        print("  ->", res)
        if not res.get("success"):
            err = str(res.get("error") or "")
            if "too many emails" in err.lower() or "550" in err:
                print("Quota blocked — stopping.")
                # keep remaining unsent
                for rest in queue[i:]:
                    results.append({**rest, "send_result": {"success": False, "error": "skipped_quota"}, "sent_at": datetime.now(UTC).isoformat()})
                break
        time.sleep(delay)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "from": "vansh@inowix.in",
        "cc": CC,
        "sent": sum(1 for r in results if r.get("send_result", {}).get("success")),
        "failed": sum(1 for r in results if not r.get("send_result", {}).get("success")),
        "results": results,
    }
    path = ROOT / "exports" / "inowix_saas_fresh_outreach_report.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ROOT / "exports" / "inowix_saas_fresh_outreach_report.md"
    lines = [
        "# Inowix SaaS Fresh Outreach Report",
        "",
        f"- Sent: {out['sent']} | Failed/skipped: {out['failed']}",
        f"- CC: {', '.join(CC)}",
        "",
    ]
    for r in results:
        st = "OK" if r.get("send_result", {}).get("success") else f"FAIL {r.get('send_result', {}).get('error')}"
        lines.append(f"### {r['company']} → {r['to_email']}")
        lines.append(f"- {st}")
        lines.append(f"- {r['subject']}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    print("Report:", path)
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--include-secondary", action="store_true", default=True)
    ap.add_argument("--primary-only", action="store_true", help="Skip secondary leads")
    ap.add_argument("--delay", type=float, default=SLEEP)
    args = ap.parse_args()

    include_secondary = not args.primary_only
    queue = build_queue(include_secondary=include_secondary)
    export_queue(queue)
    print(f"Queue: {len(queue)} leads")
    if not args.send:
        print("Dry-run only. Pass --send when SMTP quota is clear.")
        return
    # probe
    probe = send_email(
        to_email=CC[0],
        subject="SMTP probe — Inowix SaaS fresh wave",
        body_html="<p>probe</p>",
        body_text="probe",
        from_name=FROM_NAME,
        cc=[CC[1]],
        retries=1,
        retry_backoff_sec=5,
    )
    print("Probe:", probe)
    if not probe.get("success"):
        print("SMTP blocked — queue exported, not sent.")
        # still write empty/failed report marker
        (ROOT / "exports" / "inowix_saas_fresh_outreach_report.json").write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "status": "smtp_quota_blocked",
                    "probe": probe,
                    "pending_count": len(queue),
                    "cc": CC,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return
    send_queue(queue, delay=args.delay)


if __name__ == "__main__":
    main()
