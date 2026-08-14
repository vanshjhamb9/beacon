"""Live end-to-end: collect fresh signals → full pipeline → top TAI hot leads."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "apps" / "api"),
    str(ROOT / "apps" / "worker"),
    str(ROOT / "packages"),
    str(ROOT),
]


async def main() -> None:
    import httpx
    from sqlalchemy import exists, or_, select

    from app.core.config import get_settings
    from app.db.session import AsyncSessionLocal
    from app.models.quality import QualityReport
    from app.models.raw_event import RawEvent, RawEventStatus
    from app.repositories.context import ContextRepository
    from app.repositories.copilot import SalesCopilotRepository
    from app.repositories.decision import DecisionDiscoveryRepository
    from app.repositories.enrichment import EnrichmentRepository
    from app.repositories.intelligence import IntelligenceRepository
    from app.repositories.opportunity import OpportunityRepository
    from app.repositories.quality import QualityRepository
    from app.repositories.raw_event import RawEventRepository
    from app.repositories.revenue import RevenueRepository
    from app.repositories.target_account import TargetAccountRepository
    from app.repositories.verification import VerificationRepository
    from app.services.context import ContextService
    from app.services.copilot import AISalesCopilotService
    from app.services.decision import DecisionMakerDiscoveryService
    from app.services.enrichment import LeadEnrichmentService
    from app.services.intelligence import IntelligenceService
    from app.services.opportunity import OpportunityService
    from app.services.quality import QualityService
    from app.services.revenue import RevenueService
    from app.services.target_account import TargetAccountPlatformService
    from app.services.verification import DataVerificationService
    from collectors.factory import build_collector_registry

    settings = get_settings()
    report: dict = {"started_at": datetime.now(UTC).isoformat(), "collectors": {}, "stages": {}}

    print("=== 1) Collecting + persisting fresh public signals (direct DB path) ===")
    print("  note: local Redis 3.x lacks Streams; collectors write straight to Postgres for this live run")
    sources = [
        "hacker_news",
        "reddit",
        "rss",
        "github_trending",
        "devto",
        "product_hunt",
        "indie_hackers",
        "sec_edgar",
    ]
    total_persisted = 0
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as http_client:
        registry = build_collector_registry(settings, lambda: http_client)
        async with AsyncSessionLocal() as session:
            raw_repo = RawEventRepository(session)
            for source in sources:
                try:
                    collector = registry.create(source)
                    events = await collector.collect()
                    created = 0
                    duplicates = 0
                    for event in events:
                        ok = await raw_repo.create_if_new(
                            {
                                "source": event.source,
                                "url": event.url,
                                "title": event.title,
                                "content": event.content,
                                "published_at": event.published_at,
                                "event_metadata": dict(event.metadata or {}),
                                "idempotency_key": event.idempotency_key,
                                "event_hash": event.event_hash,
                                "trace_id": f"live-{source}",
                                "stream_id": None,
                            }
                        )
                        if ok:
                            created += 1
                            total_persisted += 1
                        else:
                            duplicates += 1
                    await session.commit()
                    report["collectors"][source] = {
                        "collected": len(events),
                        "persisted": created,
                        "duplicates": duplicates,
                    }
                    print(
                        f"  {source}: collected={len(events)} persisted={created} dupes={duplicates}"
                    )
                except Exception as exc:  # noqa: BLE001
                    report["collectors"][source] = {"error": str(exc)}
                    print(f"  {source}: ERROR {exc}")
    report["stages"]["persist"] = {"persisted": total_persisted}
    print(f"  total newly persisted: {total_persisted}")

    async with AsyncSessionLocal() as session:
        print("=== 3) Quality Engine ===")
        already_reported = exists().where(QualityReport.raw_event_id == RawEvent.id)
        pending = (
            await session.execute(
                select(RawEvent)
                .where(RawEvent.status == RawEventStatus.RECEIVED, ~already_reported)
                .order_by(RawEvent.created_at.desc())
                .limit(250)
            )
        ).scalars().all()
        quality = QualityService(QualityRepository(session))
        await quality.ensure_rules_seeded()
        q_ok = q_accept = q_reject = 0
        for event in pending:
            report_row = await quality.process_raw_event(event)
            q_ok += 1
            q_accept += int(report_row.decision == "accept")
            q_reject += int(report_row.decision == "reject")
        await session.commit()
        report["stages"]["quality"] = {"processed": q_ok, "accepted": q_accept, "rejected": q_reject}
        print(f"  quality processed={q_ok} accepted={q_accept} rejected={q_reject}")

        print("=== 4) Intelligence Engine ===")
        accepted_quality = exists().where(
            QualityReport.raw_event_id == RawEvent.id,
            or_(QualityReport.decision == "accept", QualityReport.decision == "review"),
        )
        intel_events = (
            await session.execute(
                select(RawEvent)
                .where(RawEvent.status == RawEventStatus.RECEIVED, accepted_quality)
                .order_by(RawEvent.published_at.desc())
                .limit(150)
            )
        ).scalars().all()
        intel = IntelligenceService(IntelligenceRepository(session))
        i_ok = 0
        for event in intel_events:
            try:
                await intel.process_raw_event(event)
                i_ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  intelligence skip: {exc}")
        await session.commit()
        report["stages"]["intelligence"] = {"processed": i_ok}
        print(f"  intelligence processed: {i_ok}")

        print("=== 5) Context Engine ===")
        ctx = ContextService(ContextRepository(session))
        c = await ctx.process_pending(limit=80)
        await session.commit()
        report["stages"]["context"] = c
        print(f"  context: {c}")

        print("=== 6) Opportunity Engine ===")
        opp = OpportunityService(OpportunityRepository(session))
        o = await opp.process_pending(limit=60)
        await session.commit()
        report["stages"]["opportunity"] = o
        print(f"  opportunity: {o}")

        print("=== 7) Revenue Engine ===")
        rev = RevenueService(RevenueRepository(session))
        r = await rev.process_pending(limit=50)
        await session.commit()
        report["stages"]["revenue"] = r
        print(f"  revenue: {r}")

        print("=== 8) Lead Enrichment ===")
        enr = LeadEnrichmentService(EnrichmentRepository(session), settings=settings)
        e = await enr.process_pending(limit=40)
        await session.commit()
        report["stages"]["enrichment"] = e
        print(f"  enrichment: {e}")

        print("=== 9) Verification ===")
        ver = DataVerificationService(VerificationRepository(session))
        v = await ver.process_pending(limit=40)
        await session.commit()
        report["stages"]["verification"] = v
        print(f"  verification: {v}")

        print("=== 10) Decision Discovery ===")
        dec = DecisionMakerDiscoveryService(DecisionDiscoveryRepository(session), settings=settings)
        d = await dec.process_pending(limit=30)
        await session.commit()
        report["stages"]["decision"] = d
        print(f"  decision: {d}")

        print("=== 11) Target Account Intelligence (Master Brain) ===")
        tai = TargetAccountPlatformService(TargetAccountRepository(session), settings)
        t = await tai.process_pending(limit=40)
        await session.commit()
        report["stages"]["target_accounts"] = t
        print(f"  target accounts: {t}")

        print("=== 12) Sales Copilot (top-tier gated) ===")
        copilot = AISalesCopilotService(SalesCopilotRepository(session), settings=settings)
        sc = await copilot.process_pending(limit=15)
        await session.commit()
        report["stages"]["copilot"] = sc
        print(f"  copilot: {sc}")

        print("=== HOT LEADS (ranked by Revenue Opportunity Score) ===")
        targets = await tai.list_targets(tier="top", icp_key=None, limit=25, offset=0)
        if not targets:
            targets = await tai.list_targets(tier=None, icp_key=None, limit=25, offset=0)
        report["hot_leads"] = targets
        for idx, row in enumerate(targets[:20], start=1):
            print(
                f"{idx:02d}. {row['company_name']} | ROS={row['revenue_opportunity_score']:.1f} "
                f"| tier={row['tier']} | ICP={row['matched_icp_name'] or '-'} "
                f"| service={row['service_match'] or '-'} | fit={row['fit_score']:.0f} "
                f"intent={row['intent_score']:.0f} urgency={row['urgency_score']:.0f}"
            )
            print(f"    WHY NOW: {row['why_now'][:240]}")

        out = ROOT / "scripts" / "live_hot_leads_report.json"
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nReport written: {out}")
        print(f"Hot leads returned: {len(targets)}")


if __name__ == "__main__":
    asyncio.run(main())
