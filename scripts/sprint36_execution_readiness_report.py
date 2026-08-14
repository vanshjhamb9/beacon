"""Sprint 36 — regenerate truthful CLR + execution readiness reports."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "sprint-36-execution-readiness-report.json"
REPORT_MD = ROOT / "docs" / "sprint-36-execution-readiness-report.md"
CLR_JSON = ROOT / "docs" / "sprint-35-live-revenue-report.json"
CLR_MD = ROOT / "docs" / "sprint-35-live-revenue-report.md"


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.execution_readiness import ExecutionReadinessService
    from app.services.operation_first_customer import OperationFirstCustomerService
    from app.services.revenue_validation import RevenueValidationService

    async with AsyncSessionLocal() as session:
        await OperationFirstCustomerService(session).sync_from_revenue_ready()
        er = ExecutionReadinessService(session)
        card = await er.dashboard_card()
        status = await er.get_status()
        readiness = await er.get_readiness()
        clr = RevenueValidationService(session)
        sync = await clr.sync_from_ofc(seed_contacted=False)
        report = sync.get("report") or await clr.build_report()
        await session.commit()

    payload = {
        "mission": "Sprint 36 — Communication Readiness Gate & Truthful Execution",
        "execution": {"status": status, "readiness": readiness, "dashboard_card": card},
        "clr_report": report,
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    CLR_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    ex = report.get("execution_status") or {}
    cto = report.get("cto_morning") or {}
    target = report.get("todays_target") or {}
    md = f"""# Sprint 36 — Communication Readiness Gate

## Communication Readiness

| Field | Value |
| --- | --- |
| Execution Mode | {card.get('execution_mode')} |
| Tone | {card.get('tone')} |
| Email | {card.get('email')} |
| WhatsApp | {card.get('whatsapp')} |
| Tracking | {card.get('tracking')} |
| Follow-ups | {card.get('follow_ups')} |
| Recommendation | {card.get('recommendation')} |

## Execution Status (CLR)

| Field | Value |
| --- | --- |
| Mode | {ex.get('mode')} |
| Reason | {ex.get('reason')} |
| Messages Sent | {ex.get('messages_sent')} |
| Deliveries | {ex.get('deliveries')} |
| Open Tracking | {ex.get('open_tracking')} |
| Reply Tracking | {ex.get('reply_tracking')} |
| Learning Mode | {ex.get('learning_mode')} |

## Truthful KPIs

| KPI | Value |
| --- | ---: |
| Revenue Ready | {report.get('revenue_ready_companies')} |
| Contacted | {report.get('contacted')} |
| Replies | {report.get('replies')} |
| Meetings | {report.get('meetings')} |
| Won | {report.get('won')} |
| Revenue | {report.get('revenue')} |

## Today's Target

- Company: **{target.get('company')}**
- Status: **{target.get('status')}**
- Reason: {target.get('reason')}
- Next Action: {target.get('next_action')}
- Tracking: {target.get('tracking')}

## CTO morning

{cto.get('answer')}

Learned: {cto.get('learned_yesterday')}
"""
    REPORT_MD.write_text(md, encoding="utf-8")

    clr_md = f"""# Sprint 35 — Closed Loop Revenue Validation Live Report (truthful, Sprint 36 gate)

**Execution Mode:** {ex.get('mode')}

## Execution Status

| Field | Value |
| --- | --- |
| Mode | {ex.get('mode')} |
| Reason | {ex.get('reason')} |
| Messages Sent | {ex.get('messages_sent')} |
| Deliveries | {ex.get('deliveries')} |
| Open Tracking | {ex.get('open_tracking')} |
| Reply Tracking | {ex.get('reply_tracking')} |
| Learning Mode | {ex.get('learning_mode')} |

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

## Today's Target

{json.dumps(target, indent=2)}

## CTO morning

{cto.get('answer')}
"""
    CLR_MD.write_text(clr_md, encoding="utf-8")
    print(json.dumps({"mode": card.get("execution_mode"), "contacted": report.get("contacted"), "cto": cto.get("answer")}, indent=2))
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
