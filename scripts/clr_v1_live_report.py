"""CLR v1 live report — sync OFC → outcomes, seed contacted for loop coverage, write sprint-35 reports."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "sprint-35-live-revenue-report.json"
REPORT_MD = ROOT / "docs" / "sprint-35-live-revenue-report.md"
WEEKLY_JSON = ROOT / "docs" / "weekly-revenue-review.json"


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.operation_first_customer import OperationFirstCustomerService
    from app.services.revenue_validation import RevenueValidationService

    async with AsyncSessionLocal() as session:
        ofc = OperationFirstCustomerService(session)
        await ofc.sync_from_revenue_ready()
        clr = RevenueValidationService(session)
        # Never seed CONTACTED — execution readiness gate forbids fabricated outreach
        print("CLR v1: sync (truthful — no seed_contacted)...", flush=True)
        sync = await clr.sync_from_ofc(seed_contacted=False)
        report = sync.get("report") or await clr.build_report()
        weekly = await clr.weekly_review()
        await session.commit()

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    WEEKLY_JSON.write_text(json.dumps(weekly, indent=2), encoding="utf-8")

    cto = report.get("cto_morning") or {}
    first = report.get("contact_first_tomorrow") or {}
    md = f"""# Sprint 35 — Closed Loop Revenue Validation Live Report

**Version:** clr-v1  
**Generated:** {report.get('generated_at')}

## CTO morning question

> {cto.get('question')}

**Answer:** {cto.get('answer')}

**Learned yesterday:** {cto.get('learned_yesterday')}

## KPIs

| Metric | Value |
| --- | ---: |
| Revenue Ready | {report.get('revenue_ready_companies')} |
| Contacted | {report.get('contacted')} |
| Replies | {report.get('replies')} |
| Meetings | {report.get('meetings')} |
| Won | {report.get('won')} |
| Revenue | {report.get('revenue')} |
| Pipeline Value | {report.get('pipeline_value')} |
| Reply Rate | {report.get('average_reply_rate')}% |
| Meeting Rate | {report.get('average_meeting_rate')}% |
| Win Rate | {report.get('average_win_rate')}% |
| Prediction Accuracy | {report.get('prediction_accuracy')}% |
| Outcome Tracking Coverage | {report.get('outcome_tracking_coverage')}% |
| Attribution Coverage | {report.get('revenue_attribution_coverage')}% |
| Fabricated Data | {report.get('fabricated_data')} |

## Learning

- Most successful connector: **{report.get('most_successful_connector')}**
- Most successful industry: **{report.get('most_successful_industry')}**
- Most successful service: **{report.get('most_successful_service')}**
- Most successful Why Now: **{report.get('most_successful_why_now')}**
- Biggest blocker: **{report.get('biggest_blocker')}**

## Tomorrow

- Continue outreach? **{report.get('continue_outreach_tomorrow')}**
- Contact first: **{first.get('company')}** — {first.get('why')}
- Channel: {first.get('email')}
- Next step: {first.get('next_step')}

Migration note: alembic revision `20260725_0046` (brief said 0043; 0043 already used by ODU).

Raw: `sprint-35-live-revenue-report.json` · Weekly: `weekly-revenue-review.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(cto, indent=2))
    print(
        f"RR={report.get('revenue_ready_companies')} contacted={report.get('contacted')} "
        f"continue={report.get('continue_outreach_tomorrow')}"
    )
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
