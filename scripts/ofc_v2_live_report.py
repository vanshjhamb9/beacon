"""OFC v2 live report — sync Revenue Ready → outreach + write operation-first-customer-live-report.json."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "operation-first-customer-live-report.json"
REPORT_MD = ROOT / "docs" / "operation-first-customer-live-report.md"


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.operation_first_customer import OperationFirstCustomerService

    async with AsyncSessionLocal() as session:
        svc = OperationFirstCustomerService(session)
        print("OFC v2: sync Revenue Ready -> Outreach Records...", flush=True)
        sync = await svc.sync_from_revenue_ready()
        report = sync.get("report") or await svc.build_report()
        await session.commit()

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    morning = report.get("vansh_morning_question") or {}
    md = f"""# Sprint 34 — Operation First Customer (OFC v2) Live Report

## Morning question

**What should Vansh do today to close the next customer?**

> {morning.get('answer')}

Why: {morning.get('why')}  
Company: {morning.get('company') or '—'}  
Channel: {morning.get('channel') or '—'}

## Pipeline

| Metric | Value |
| --- | ---: |
| Revenue Ready | {report.get('revenue_ready_companies')} |
| Contacted | {report.get('contacted')} |
| Replies | {report.get('replies')} |
| Meetings | {report.get('meetings')} |
| Proposals | {report.get('proposals')} |
| Won | {report.get('won')} |
| Lost | {report.get('lost')} |
| Pipeline Value | {report.get('pipeline_value')} |
| Reply Rate | {report.get('reply_rate')}% |
| Meeting Rate | {report.get('meeting_rate')}% |
| Win Rate | {report.get('win_rate')}% |
| Avg Sales Cycle (days) | {report.get('average_sales_cycle_days')} |

## Learning

- Most successful industry: **{report.get('most_successful_industry')}**
- Most successful service: **{report.get('most_successful_service')}**
- Most successful DM role: **{report.get('most_successful_decision_maker_role')}**
- Top objections: {', '.join(str(o.get('label')) for o in (report.get('top_objections') or [])[:5]) or '—'}

Can answer morning question: **{report.get('can_answer_morning_question')}**

Raw: `operation-first-customer-live-report.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(morning, indent=2))
    print(f"Synced created={sync.get('created')} refreshed={sync.get('refreshed')}")
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
