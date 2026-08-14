"""RRP live audit — perfect Sales Ready → Revenue Ready. No new companies."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "revenue-ready-live-audit.json"
REPORT_MD = ROOT / "docs" / "revenue-ready-live-audit.md"


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.revenue_readiness_perfection import RevenueReadinessPerfectionService

    async with AsyncSessionLocal() as session:
        svc = RevenueReadinessPerfectionService(session)
        print("RRP perfect: Sales Ready -> Revenue Ready...", flush=True)
        audit = await svc.perfect(crawl_dm=True)

    before = audit.get("before") or {}
    after = audit.get("after") or {}
    promoted = audit.get("promoted") or []
    blocked = audit.get("still_blocked") or []

    report = {
        "mission": "Phase 2 — Revenue Readiness Perfection live audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "impact_statement": audit.get("impact_statement"),
        "before": before,
        "after": after,
        "promoted": promoted,
        "still_blocked": blocked,
        "blocker_counts": audit.get("blocker_counts"),
        "confidence_distribution": audit.get("confidence_distribution"),
        "trust_distribution": audit.get("trust_distribution"),
        "cto_answers": {
            "1_revenue_ready": after.get("revenue_ready"),
            "2_verified_decision_makers": after.get("decision_makers"),
            "3_decision_maker_contact_methods": after.get("decision_maker_contact_methods"),
            "3b_decision_maker_emails_name_matched": after.get("decision_maker_emails"),
            "4_why_now_count": len([p for p in promoted if p.get("why_now")]),
            "5_promoted_today": [p.get("company") for p in promoted],
            "6_still_blocked": [
                {"company": b.get("company"), "blockers": b.get("blockers")} for b in blocked
            ],
            "7_vansh_contact_10": audit.get("vansh_ready_answer"),
        },
        "acceptance": {
            "sales_ready": {"target": 13, "actual": after.get("sales_ready")},
            "revenue_ready": {"target": 10, "actual": after.get("revenue_ready")},
            "decision_makers": {"target": 24, "actual": after.get("decision_makers")},
            "decision_maker_contact_methods": {
                "target": 10,
                "actual": after.get("decision_maker_contact_methods"),
            },
            "decision_maker_emails_name_matched": {
                "target": "public evidence only (no fabrication)",
                "actual": after.get("decision_maker_emails"),
            },
            "confidence_ge_90": {"target": 10, "actual": after.get("confidence_ge_90")},
            "trust_ge_95": {"target": 10, "actual": after.get("trust_ge_95")},
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    promoted_lines = "\n".join(
        f"| {p.get('company')} | {p.get('website')} | {p.get('decision_maker')} | {p.get('business_email')} | {str(p.get('why_now') or '')[:50]} |"
        for p in promoted[:15]
    ) or "| — | — | — | — | — |"
    blocked_lines = "\n".join(
        f"| {b.get('company')} | {', '.join(b.get('blockers') or [])} |" for b in blocked
    ) or "| — | — |"

    md = f"""# Phase 2 — Revenue Readiness Perfection Live Audit

**Impact:** {audit.get('impact_statement')}

## Before → After

| KPI | Before | After | Target |
| --- | ---: | ---: | ---: |
| Sales Ready | {before.get('sales_ready')} | {after.get('sales_ready')} | ≥13 |
| Revenue Ready | {before.get('revenue_ready')} | {after.get('revenue_ready')} | ≥10 |
| Decision Makers | {before.get('decision_makers')} | {after.get('decision_makers')} | ≥24 |
| Decision Maker Contact Methods | {before.get('decision_maker_contact_methods')} | {after.get('decision_maker_contact_methods')} | ≥10 |
| Decision Maker Emails (name-matched) | {before.get('decision_maker_emails')} | {after.get('decision_maker_emails')} | evidence-only |
| Confidence ≥90 | {before.get('confidence_ge_90')} | {after.get('confidence_ge_90')} | ≥10 |
| Trust ≥95 | {before.get('trust_ge_95')} | {after.get('trust_ge_95')} | ≥10 |

## CTO answers

1. Revenue Ready: **{after.get('revenue_ready')}**
2. Verified decision makers: **{after.get('decision_makers')}**
3. Decision-maker contact methods: **{after.get('decision_maker_contact_methods')}** (name-matched DM emails: {after.get('decision_maker_emails')})
4. Evidence-backed Why Now (promoted): **{len([p for p in promoted if p.get('why_now')])}**
5. Promoted today: **{', '.join(p.get('company') or '' for p in promoted) or 'none'}**
6. Still blocked: see table
7. Can Vansh start outreach to 10 companies today? **{audit.get('vansh_ready_answer')}**

## Promoted

| Company | Website | Decision Maker | Email | Why Now |
| --- | --- | --- | --- | --- |
{promoted_lines}

## Still blocked

| Company | Blockers |
| --- | --- |
{blocked_lines}

Raw: `revenue-ready-live-audit.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(report["cto_answers"], indent=2))
    print(audit.get("impact_statement"))
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
