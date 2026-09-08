#!/usr/bin/env python3
"""Live practical test: draft + send partner emails to vanshjhamb9@gmail.com + pipeline tracking."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages"))

from comai_partner_outreach.config import load_config
from comai_partner_outreach.drafting import draft_partner_intro
from comai_partner_outreach.service import PartnerOutreachService
from comai_partner_outreach.store import PartnerOutreachStore
from email_service import send_email

TO = "vanshjhamb9@gmail.com"
STORE = PartnerOutreachStore(ROOT / "exports" / "comai_partner_outreach" / "_live_test_store")
PREVIEWS = ROOT / "exports" / "comai_partner_outreach" / "_live_test_previews"
PREVIEWS.mkdir(parents=True, exist_ok=True)

LEADS = [
    {
        "first_name": "Vansh",
        "agency_name": "VJ Growth Studio",
        "agency_type": "performance_marketing_agency",
        "city": "Delhi NCR",
        "services": "Meta ads, Google ads, WhatsApp lead gen for D2C brands",
        "notes": (
            "As a digital marketer running performance campaigns for D2C brands, "
            "your ads already create WhatsApp and inbound intent that often goes cold "
            "without a fast reply + follow-up layer"
        ),
        "email": TO,
        "client_examples": "fashion and beauty D2C brands",
    },
    {
        "first_name": "Vansh",
        "agency_name": "Frame & Pulse Films",
        "agency_type": "video_production_agency",
        "city": "Mumbai",
        "services": "Performance video ads, brand films, UGC-style creatives",
        "notes": (
            "Your video creatives win attention on Meta and YouTube — but clients still lose "
            "enquiries on WhatsApp after the ad click when nobody replies instantly"
        ),
        "email": TO,
        "client_examples": "D2C brands commissioning ad films",
    },
]


def main() -> int:
    cfg = load_config()
    # Ensure brand assets even if env empty
    if not cfg.logo_url:
        cfg.logo_url = (
            "https://res.cloudinary.com/drxu02bbp/image/upload/v1785956926/"
            "2-removebg-preview_2_v8czqo.png"
        )
    if not cfg.thumbnail_url:
        cfg.thumbnail_url = "https://comai.in/opengraph-image?a8d5ca28a145d97f"
    if not cfg.video_url or cfg.video_url.strip() in ("", "https://comai.in"):
        # Hosted product page acts as walkthrough until a dedicated Loom/YouTube is set
        cfg.video_url = "https://comai.in/?utm_source=beacon&utm_medium=email&utm_campaign=partner_test"

    print("CONFIG")
    print("  video:", cfg.video_url)
    print("  thumb:", cfg.thumbnail_url)
    print("  logo:", cfg.logo_url)
    print("  commission:", cfg.commission_pct)

    svc = PartnerOutreachService(store=STORE, config=cfg)
    csv_lines = [
        "first_name,agency_name,email,agency_type,city,services,notes,client_examples",
    ]
    for lead in LEADS:
        # unique emails for pipeline dedupe within campaign — both still deliver to same inbox via +tag
        # Gmail ignores +tags for delivery to same mailbox
        tag = "marketing" if "marketing" in lead["agency_type"] else "video"
        lead_email = f"vanshjhamb9+comai{tag}@gmail.com"
        csv_lines.append(
            ",".join(
                [
                    lead["first_name"],
                    f'"{lead["agency_name"]}"',
                    lead_email,
                    lead["agency_type"],
                    lead["city"],
                    f'"{lead["services"]}"',
                    f'"{lead["notes"]}"',
                    f'"{lead.get("client_examples","")}"',
                ]
            )
        )

    # Also send directly to exact address for easy find in inbox
    results = []
    for lead in LEADS:
        draft = draft_partner_intro(lead, cfg)
        slug = "marketing" if "marketing" in lead["agency_type"] else "video"
        (PREVIEWS / f"{slug}_body.txt").write_text(draft.body_text, encoding="utf-8")
        (PREVIEWS / f"{slug}_body.html").write_text(draft.body_html, encoding="utf-8")
        print("\n===", slug.upper(), "===")
        print("SUBJECT:", draft.subject)
        print("HOOK:", draft.hook_used)
        print("HAS_LOGO_IMG:", "<img" in draft.body_html and "COMAI" in draft.body_html)
        print("HAS_PLAY_CTA:", "Play video" in draft.body_html)
        print("HAS_VIDEO_LINK:", cfg.video_url.split("?")[0] in draft.body_html)

        send_res = send_email(
            to_email=TO,
            subject=f"[TEST {slug.upper()}] {draft.subject}",
            body_html=draft.body_html,
            body_text=draft.body_text,
            from_name="Vansh | COMAI Partner Program",
        )
        print("SEND:", send_res)
        results.append({"persona": slug, "subject": draft.subject, "send": send_res})
        time.sleep(2)

    # Pipeline: upload → draft → process (dry) → simulate reply
    created = svc.create_campaign_from_upload(
        filename="vansh_personas.csv",
        content=("\n".join(csv_lines) + "\n").encode("utf-8"),
        name="Live test — Vansh personas",
    )
    cid = created["campaign"]["id"]
    # Force process with open hours for this test config
    cfg.business_start_hour = 0
    cfg.business_end_hour = 24
    cfg.weekdays_only = False
    cfg.min_seconds_between_sends = 0
    svc.config = cfg
    processed = svc.process_campaign(cid, max_sends=10)
    leads = svc.get_leads(cid)
    # Simulate interested reply from marketing persona
    reply = None
    if leads:
        reply = svc.ingest_reply(
            from_email=leads[0]["email"],
            body_text="Sounds interesting — tell me more about the 15% commission and demo for my D2C clients.",
            subject="Re: partnership",
        )
    pipeline = svc.pipeline()
    metrics = svc.metrics()

    report = {
        "sends": results,
        "campaign_id": cid,
        "created": {
            "valid_rows": created.get("valid_rows"),
            "skipped_rows": created.get("skipped_rows"),
            "errors": created.get("errors"),
        },
        "processed": processed,
        "leads": [
            {
                "email": l["email"],
                "agency_name": l["agency_name"],
                "stage": l["stage"],
                "sequence_step": l["sequence_step"],
                "reply_class": l.get("reply_class"),
                "subject": l.get("subject"),
            }
            for l in leads
        ],
        "reply": reply,
        "pipeline_counts": pipeline.get("counts"),
        "metrics": metrics,
        "previews_dir": str(PREVIEWS),
        "notes": {
            "logo": "Yes — COMAI logo image in email header",
            "video_plays_inline": (
                "No — Gmail/Outlook block autoplay video. Email shows branded thumbnail "
                "+ Play button that opens the hosted video/page."
            ),
            "video_url_used": cfg.video_url,
        },
    }
    out = ROOT / "exports" / "comai_partner_outreach" / "_live_test_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nPIPELINE stages:", pipeline.get("counts"))
    print("REPORT:", out)
    ok = all(r["send"].get("success") for r in results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
