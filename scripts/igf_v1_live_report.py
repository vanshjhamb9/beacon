"""IGF v1 live report — collect GitHub identity sources + rebuild + contact recovery."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "igf-v1-live-report.json"
REPORT_MD = ROOT / "docs" / "igf-v1-engineering-report.md"


async def _ingest_github(session, max_items: int = 80) -> int:
    import httpx
    from app.models.raw_event import RawEvent
    from collectors.sources.github_trending import GitHubTrendingCollector
    from sqlalchemy import select

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            collector = GitHubTrendingCollector(
                client,
                max_items=max_items,
                topics=["saas", "startup", "artificial-intelligence", "automation"],
            )
            events = await collector.collect()
    except Exception as exc:  # noqa: BLE001
        print(f"GitHub collect skipped: {exc}", flush=True)
        return 0

    inserted = 0
    for event in events:
        exists = (
            await session.execute(
                select(RawEvent.id).where(
                    RawEvent.idempotency_key == event.idempotency_key,
                    RawEvent.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(
            RawEvent(
                id=uuid4(),
                source=event.source,
                url=event.url,
                title=event.title,
                content=event.content or event.title,
                published_at=event.published_at,
                idempotency_key=event.idempotency_key,
                event_hash=event.event_hash,
                event_metadata=dict(event.metadata or {}),
            )
        )
        inserted += 1
    await session.commit()
    return inserted


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.identity_graph import IdentityGraphService
    from collectors.extraction.public_contacts import recover_from_official_website
    from app.models.intelligence import Company
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    async with AsyncSessionLocal() as session:
        print("Collecting GitHub identity candidates…", flush=True)
        inserted = await _ingest_github(session, 80)
        print(f"Inserted raw events: {inserted}", flush=True)

        svc = IdentityGraphService(session)
        rebuild = await svc.rebuild(limit=1500, fetch_official=False)
        print(json.dumps({k: rebuild.get(k) for k in (
            "signals", "candidates", "official_websites", "verified_companies",
            "merged", "rejected", "companies_created_or_linked", "seeded_from_existing_companies",
        )}, indent=2), flush=True)

        # Contact recovery on ACTIVE canonical domains
        companies = (
            await session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        emails = 0
        dms = 0
        for company in companies:
            website = f"https://{company.primary_domain}"
            contacts = await asyncio.to_thread(recover_from_official_website, website)
            attrs = dict(company.attributes or {})
            if contacts.get("emails"):
                attrs["ofc_business_email"] = contacts["emails"][0]
                attrs["business_email"] = contacts["emails"][0]
                emails += 1
            if contacts.get("decision_makers"):
                top = contacts["decision_makers"][0]
                attrs["decision_maker"] = f"{top['name']} ({top['role']})"
                attrs["ofc_decision_makers"] = contacts["decision_makers"]
                dms += 1
            if contacts.get("linkedin"):
                attrs["ofc_linkedin"] = contacts["linkedin"]
            attrs["igf_contact_recovery_at"] = datetime.now(UTC).isoformat()
            company.attributes = attrs
            flag_modified(company, "attributes")
        await session.commit()

        dash = await svc.dashboard()

    payload = {
        "mission": "IGF v1 — Identity Graph Foundation",
        "generated_at": datetime.now(UTC).isoformat(),
        "github_events_inserted": inserted,
        "rebuild": rebuild,
        "contact_recovery": {
            "companies_scanned": len(companies),
            "with_business_email": emails,
            "with_decision_makers": dms,
        },
        "dashboard": dash,
        "acceptance": {
            "target_official_websites": 100,
            "target_business_emails": 50,
            "target_decision_makers": 30,
            "target_revenue_ready": 20,
            "official_websites": rebuild.get("official_websites") or dash.get("official_websites"),
            "verified_companies": rebuild.get("verified_companies") or dash.get("active_canonical"),
            "business_emails": emails,
            "decision_makers": dms,
            "revenue_ready": 0,
            "production_locked": True,
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = f"""# IGF v1 — Identity Graph Foundation

## Philosophy

```
Signal → Identity Candidate → Identity Graph → Official Website → Verified Company → Enrichment → Revenue Ready
```

A company **does not exist** until Identity Graph admits it.

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/identity_graph/` (`igf-v1`) |
| Migration | `20260724_0040` |
| API | `/api/v1/identity-graph/*` |
| Dashboard | `/identity-graph` |
| Gate | `IntelligenceService` requires IGF admit after EROWD |

## Live funnel

| Metric | Value |
| --- | ---: |
| Signals evaluated | {rebuild.get("signals")} |
| Candidates | {rebuild.get("candidates")} |
| Official websites | {rebuild.get("official_websites")} |
| Verified companies | {rebuild.get("verified_companies")} |
| Companies created/linked | {rebuild.get("companies_created_or_linked")} |
| Business emails (same-domain) | {emails} |
| Named decision makers | {dms} |
| Revenue Ready | 0 (downstream; production LOCKED) |

## Source roles

- **Identity:** Product Hunt, GitHub (org/homepage), Crunchbase, LinkedIn Company, Official Website
- **Conversation (never create):** Reddit, HN, RSS, Dev.to, Twitter
- **Intent (never create):** Hiring/Funding/Press/SEC

## Honest blockers

Product Hunt HTML still Cloudflare-blocked — PH signals become candidates without websites until redirects resolve.
GitHub repos **with homepage** are the primary live identity source this run.

## CTO acceptance

Targets: 100 websites · 50 emails · 30 DMs · 20 Revenue Ready · zero fabricated · zero duplicate canonicals.

Raw: `igf-v1-live-report.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {REPORT_JSON}", flush=True)
    print(f"Wrote {REPORT_MD}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
