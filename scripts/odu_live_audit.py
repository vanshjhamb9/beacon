"""Operation Dataset Unlock — live operational audit (business outcomes only)."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "dataset-unlock-live-report.json"
REPORT_MD = ROOT / "docs" / "dataset-unlock-live-audit.md"


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.dataset_unlock import DatasetUnlockService

    async with AsyncSessionLocal() as session:
        svc = DatasetUnlockService(session)
        print("ODU unlock: YC + App Store + Play + PH GraphQL + GitHub expand…", flush=True)
        result = await svc.unlock(
            collect_new=True,
            recover_contacts=True,
            recover_dms=True,
            company_crawl_cap=80,
            github_fetch_cap=30,
        )

    before = result.get("before") or {}
    after = result.get("after") or {}
    audit = result.get("audit") or {}
    answers = audit.get("audit_answers") or {}
    connectors = audit.get("connectors") or []
    top = audit.get("top_companies") or []
    failures = audit.get("top_failures") or {}

    payload = {
        "mission": "Operation Dataset Unlock — live operational audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "impact_statement": (
            f"This change increased Revenue Ready companies from "
            f"{before.get('revenue_ready')} to {after.get('revenue_ready')}."
        ),
        "before": before,
        "after": after,
        "created": result.get("created"),
        "websites_recovered": result.get("websites_recovered"),
        "emails_recovered": result.get("emails_recovered"),
        "dms_recovered": result.get("dms_recovered"),
        "audit": audit,
        "cto_answers": {
            "1_official_websites_recovered": answers.get("official_websites_recovered")
            or result.get("websites_recovered"),
            "2_highest_revenue_yield_connector": answers.get("highest_revenue_yield_connector"),
            "3_disable_connectors": answers.get("disable_connectors"),
            "4_business_emails_recovered": answers.get("business_emails_recovered")
            or result.get("emails_recovered"),
            "5_decision_makers_recovered": answers.get("decision_makers_recovered")
            or result.get("dms_recovered"),
            "6_sales_ready": answers.get("sales_ready") or after.get("sales_ready"),
            "7_revenue_ready": answers.get("revenue_ready") or after.get("revenue_ready"),
            "8_vansh_contact_10": answers.get("vansh_contact_10") or audit.get("vansh_ready_answer"),
        },
        "acceptance": {
            "verified_companies": {"target": 100, "actual": after.get("verified_companies")},
            "business_emails": {"target": 50, "actual": after.get("business_emails")},
            "decision_makers": {"target": 25, "actual": after.get("decision_makers")},
            "sales_ready": {"target": 15, "actual": after.get("sales_ready")},
            "revenue_ready": {"target": 10, "actual": after.get("revenue_ready")},
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    conn_lines = "\n".join(
        f"| {c.get('connector')} | {c.get('signals')} | {c.get('websites')} | {c.get('companies')} | {c.get('emails')} | {c.get('decision_makers')} | {c.get('revenue_ready')} | {c.get('yield_pct')} |"
        for c in connectors[:15]
    ) or "| — | — | — | — | — | — | — | — |"
    fail_lines = "\n".join(f"| {k} | {v} |" for k, v in list(failures.items())[:12]) or "| — | 0 |"
    top_lines = "\n".join(
        f"| {t.get('company')} | {t.get('website')} | {t.get('email')} | {t.get('decision_maker')} | {t.get('why_today')} | {t.get('revenue_ready')} |"
        for t in top[:20]
    ) or "| — | — | — | — | — | — |"

    md = f"""# Operation Dataset Unlock — Live Operational Audit

**Impact:** {payload['impact_statement']}

## Before → After

| KPI | Before | After | Target |
| --- | ---: | ---: | ---: |
| Verified Companies | {before.get('verified_companies')} | {after.get('verified_companies')} | ≥100 |
| Business Emails | {before.get('business_emails')} | {after.get('business_emails')} | ≥50 |
| Decision Makers | {before.get('decision_makers')} | {after.get('decision_makers')} | ≥25 |
| Sales Ready | {before.get('sales_ready')} | {after.get('sales_ready')} | ≥15 |
| Revenue Ready | {before.get('revenue_ready')} | {after.get('revenue_ready')} | ≥10 |

Companies created this run: **{result.get('created')}** · Websites recovered: **{result.get('websites_recovered')}** · Emails recovered: **{result.get('emails_recovered')}** · DMs recovered: **{result.get('dms_recovered')}**

## CTO answers

1. Official websites recovered: **{payload['cto_answers']['1_official_websites_recovered']}**
2. Highest Revenue Yield connector: **{payload['cto_answers']['2_highest_revenue_yield_connector']}**
3. Connectors to disable: **{', '.join(payload['cto_answers']['3_disable_connectors'] or []) or 'none'}**
4. Verified business emails recovered: **{payload['cto_answers']['4_business_emails_recovered']}**
5. Named decision makers recovered: **{payload['cto_answers']['5_decision_makers_recovered']}**
6. Sales Ready: **{payload['cto_answers']['6_sales_ready']}**
7. Revenue Ready: **{payload['cto_answers']['7_revenue_ready']}**
8. Can Vansh contact ≥10 real companies today? **{payload['cto_answers']['8_vansh_contact_10']}**

## Connector comparison

| Connector | Signals | Websites | Companies | Emails | DMs | RR | Yield % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{conn_lines}

## Top failures

| Failure | Count |
| --- | ---: |
{fail_lines}

## Top 20 companies

| Company | Website | Email | Decision Maker | Why Today | Revenue Ready |
| --- | --- | --- | --- | --- | --- |
{top_lines}

Raw: `dataset-unlock-live-report.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(payload["cto_answers"], indent=2))
    print(payload["impact_statement"])
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
