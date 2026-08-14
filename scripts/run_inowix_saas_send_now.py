#!/usr/bin/env python3
"""One-shot sender for Inowix SaaS fresh queue (no probe)."""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from email_service import send_email
from send_inowix_saas_fresh_outreach import (
    CC,
    FROM_NAME,
    build_queue,
    export_queue,
    html_body,
)

queue = build_queue(include_secondary=True)
export_queue(queue)
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
        retries=1,
        retry_backoff_sec=5,
    )
    print(" ", res)
    results.append(
        {
            "company": item["company"],
            "founder_name": item.get("founder_name"),
            "to_email": item["to_email"],
            "subject": item["subject"],
            "intent_date": item.get("intent_date"),
            "send_result": res,
            "sent_at": datetime.now(UTC).isoformat(),
        }
    )
    if not res.get("success"):
        err = str(res.get("error") or "")
        print("Stopping on failure:", err[:200])
        for rest in queue[i:]:
            results.append(
                {
                    "company": rest["company"],
                    "to_email": rest["to_email"],
                    "subject": rest["subject"],
                    "send_result": {"success": False, "error": "skipped_after_failure"},
                }
            )
        break
    time.sleep(20)

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
print("Report", path, "sent=", out["sent"], "failed=", out["failed"])
