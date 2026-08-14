#!/usr/bin/env python3
"""Build pending dual-lane queue (no send) + optional resume send after SMTP quota resets."""

from __future__ import annotations

import argparse
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
from send_dual_lane_retry_expand import EXPAND, load_failed_from_report  # noqa: E402

CC = "vanshjhamb9@gmail.com"
FROM_NAME = "Vansh Jhamb | Inowix"
PENDING_JSON = ROOT / "exports" / "dual_lane_pending_queue.json"
PENDING_CSV = ROOT / "exports" / "dual_lane_pending_queue.csv"
MASTER_CSV = ROOT / "exports" / "dual_lane_fresh_leads_master.csv"
RESUME_REPORT = ROOT / "exports" / "dual_lane_resume_outreach_report.json"


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


def already_sent_emails() -> set[str]:
    sent: set[str] = set()
    for name in (
        "dual_lane_fresh_outreach_report.json",
        "dual_lane_retry_expand_outreach_report.json",
        "dual_lane_resume_outreach_report.json",
        "comai_agency_partner_outreach_report.json",
    ):
        path = ROOT / "exports" / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("results", []):
            if r.get("send_result", {}).get("success"):
                sent.add(r["to_email"].lower())
    return sent


def build_pending() -> list[dict]:
    sent = already_sent_emails()
    queue: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for lead in load_failed_from_report():
        email = lead["to_email"].lower()
        key = (email, lead["lane"])
        if email in sent or key in seen:
            continue
        seen.add(key)
        queue.append(draft_item({**lead, "status": "pending_retry"}))

    for lead in EXPAND:
        email = lead["to_email"].lower()
        key = (email, lead["lane"])
        if key in seen:
            continue
        if email in sent and lead["lane"].startswith("COMAI"):
            continue
        # avoid same-email COMAI + INOWIX same wave — prefer COMAI first
        if lead["lane"].startswith("INOWIX"):
            if any(q["to_email"].lower() == email and q["lane"].startswith("COMAI") for q in queue):
                continue
            if email in sent:
                # allow Inowix only if prior success was ComAI (different product pitch)
                # still skip if we already sent anything to avoid mailbox spam same day
                continue
        seen.add(key)
        queue.append(draft_item({**lead, "status": "pending_new"}))

    return queue


def write_outputs(queue: list[dict], wave1_ok: list[dict]) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "from": "vansh@inowix.in",
        "cc": CC,
        "note": "SMTP quota hit (550 too many emails). Resume with --send when limit resets.",
        "already_sent_count": len(wave1_ok),
        "pending_count": len(queue),
        "pending": queue,
        "already_sent": wave1_ok,
    }
    PENDING_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = [
        "status", "lane", "company_name", "founder_name", "to_email", "website",
        "city", "industry", "phone", "angle", "why", "source", "subject",
    ]
    with PENDING_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for q in queue:
            w.writerow(q)

    with MASTER_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=fields + ["send_status"],
            extrasaction="ignore",
        )
        w.writeheader()
        for r in wave1_ok:
            w.writerow({**r, "status": "sent_wave1", "send_status": "OK"})
        for q in queue:
            w.writerow({**q, "send_status": "PENDING"})


def load_wave1_ok() -> list[dict]:
    path = ROOT / "exports" / "dual_lane_fresh_outreach_report.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for r in data.get("results", []):
        if r.get("send_result", {}).get("success"):
            out.append(
                {
                    "lane": r["lane"],
                    "company_name": r["company_name"],
                    "founder_name": r.get("founder_name") or "",
                    "to_email": r["to_email"],
                    "website": r.get("website") or "",
                    "city": r.get("city") or "",
                    "industry": r.get("industry") or "",
                    "subject": r.get("subject") or "",
                    "angle": r.get("angle"),
                    "why": r.get("why"),
                    "source": "wave1_sent",
                }
            )
    return out


def send_pending(delay: float = 12.0) -> None:
    if not PENDING_JSON.exists():
        queue = build_pending()
        write_outputs(queue, load_wave1_ok())
    else:
        data = json.loads(PENDING_JSON.read_text(encoding="utf-8"))
        queue = data.get("pending", [])

    # probe
    probe = send_email(
        to_email=CC,
        subject="SMTP probe — resume dual-lane outreach",
        body_html="<p>Probe before pending queue.</p>",
        body_text="Probe",
        from_name=FROM_NAME,
        retries=1,
        retry_backoff_sec=5.0,
    )
    print("Probe:", probe)
    if not probe.get("success"):
        err = str(probe.get("error") or "")
        if "too many emails" in err.lower() or "550" in err:
            print("SMTP still quota-blocked. Not sending. Queue kept at", PENDING_JSON)
            return
        print("Probe failed — aborting send to avoid burning quota.")
        return

    results = []
    remaining = []
    for i, item in enumerate(queue, 1):
        print(f"[{i}/{len(queue)}] {item['lane']} -> {item['to_email']}")
        res = send_email(
            to_email=item["to_email"],
            subject=item["subject"],
            body_html=html_body(item["body"]),
            body_text=item["body"],
            from_name=FROM_NAME,
            cc=CC,
            retries=2,
            retry_backoff_sec=20.0,
        )
        row = {**item, "send_result": res, "sent_at": datetime.now(UTC).isoformat()}
        results.append(row)
        print("  ->", res)
        if not res.get("success"):
            remaining.append(item)
            err = str(res.get("error") or "")
            if "too many emails" in err.lower():
                remaining.extend(queue[i:])
                print("Quota hit mid-run — stopping.")
                break
        time.sleep(delay)

    # refresh pending to remaining only
    write_outputs(remaining, load_wave1_ok() + [
        {k: r.get(k) for k in (
            "lane", "company_name", "founder_name", "to_email", "website",
            "city", "industry", "subject", "angle", "why", "source",
        )}
        for r in results if r.get("send_result", {}).get("success")
    ])

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "sent": sum(1 for r in results if r["send_result"].get("success")),
        "failed": sum(1 for r in results if not r["send_result"].get("success")),
        "remaining": len(remaining),
        "results": results,
    }
    RESUME_REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Resume report:", RESUME_REPORT)
    print(f"Done sent={out['sent']} failed={out['failed']} remaining={out['remaining']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="Send pending after SMTP probe")
    ap.add_argument("--delay", type=float, default=12.0)
    args = ap.parse_args()

    queue = build_pending()
    wave1 = load_wave1_ok()
    write_outputs(queue, wave1)
    print(f"Already sent: {len(wave1)} | Pending: {len(queue)}")
    print("Pending CSV:", PENDING_CSV)
    print("Master CSV:", MASTER_CSV)
    if args.send:
        send_pending(delay=args.delay)


if __name__ == "__main__":
    main()
