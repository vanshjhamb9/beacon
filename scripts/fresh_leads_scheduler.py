"""
Fresh Leads Scheduler - runs every 10 minutes while server is live.
Collects only LAST 4H signals -> OCP -> LOD -> OI -> Validation -> Outputs fresh leads.
No old/duplicate leads. Every run only surfaces NEW leads since last run.

Usage:
  python scripts/fresh_leads_scheduler.py          # single run
  python scripts/fresh_leads_scheduler.py --loop   # loop every 10 min
"""

from __future__ import annotations

import asyncio
import json
import sys
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "apps" / "api"),
    str(ROOT / "apps" / "worker"),
    str(ROOT / "packages"),
    str(ROOT),
]

# ── Freshness SLA: only events ≤ 4 hours old qualify ──
FRESH_WINDOW_HOURS = 4
# ── How often to run in --loop mode ──
LOOP_INTERVAL_SECONDS = 600  # 10 minutes
# ── Track last run to avoid re-processing ──
STATE_FILE = ROOT / "scripts" / ".fresh_leads_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_run_at": None, "seen_hashes": []}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


async def collect_fresh_signals() -> list[dict[str, Any]]:
    """Collect ONLY fresh signals (≤4h) from all live sources."""
    import httpx
    from collectors.factory import build_collector_registry
    from collectors.freshness import filter_fresh_events, FRESH_HOURS
    from app.core.config import get_settings

    settings = get_settings()
    sources = [
        "hacker_news",
        "reddit",
        "rss",
        "github_trending",
        "devto",
        "product_hunt",
        "sec_edgar",
    ]

    all_fresh: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as http_client:
        registry = build_collector_registry(settings, lambda: http_client)
        for source_name in sources:
            try:
                collector = registry.create(source_name)
                if collector is None:
                    continue
                raw_events = await collector.collect()
                # Filter to ONLY events from last 4 hours
                fresh = filter_fresh_events(raw_events, max_age_hours=FRESH_WINDOW_HOURS)
                for ev in fresh:
                    pub = ev.published_at
                    if isinstance(pub, str):
                        pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    all_fresh.append({
                        "source": ev.source,
                        "url": ev.url,
                        "title": ev.title,
                        "content": ev.content,
                        "published_at": pub,
                        "metadata": dict(ev.metadata or {}),
                        "idempotency_key": ev.idempotency_key,
                        "event_hash": ev.event_hash,
                    })
                print(f"  {source_name}: {len(raw_events)} raw -> {len(fresh)} fresh (<={FRESH_WINDOW_HOURS}h)")
            except Exception as exc:
                print(f"  {source_name}: ERROR {exc}")
    return all_fresh


async def run_ocp_lod_oi_pipeline(fresh_signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Run fresh signals through OCP -> LOD -> OI -> Validation."""
    from app.db.session import AsyncSessionLocal
    from app.models.raw_event import RawEvent, RawEventStatus
    from app.models.quality import QualityReport
    from sqlalchemy import exists, or_, select
    from app.services.quality import QualityService
    from app.repositories.quality import QualityRepository
    from app.services.intelligence import IntelligenceService
    from app.repositories.intelligence import IntelligenceRepository
    from app.services.context import ContextService
    from app.repositories.context import ContextRepository
    from app.services.opportunity import OpportunityService
    from app.repositories.opportunity import OpportunityRepository
    from app.services.revenue import RevenueService
    from app.repositories.revenue import RevenueRepository
    from app.services.enrichment import LeadEnrichmentService
    from app.repositories.enrichment import EnrichmentRepository
    from app.services.verification import DataVerificationService
    from app.repositories.verification import VerificationRepository
    from app.services.target_account import TargetAccountPlatformService
    from app.repositories.target_account import TargetAccountRepository
    from app.core.config import get_settings
    from datetime import UTC, datetime

    settings = get_settings()
    results: dict[str, Any] = {"fresh_signals_in": len(fresh_signals), "stages": {}}

    # OCP: Persist fresh signals
    persisted = 0
    async with AsyncSessionLocal() as session:
        raw_repo = None
        from app.repositories.raw_event import RawEventRepository
        raw_repo = RawEventRepository(session)
        for sig in fresh_signals:
            ok = await raw_repo.create_if_new({
                "source": sig["source"],
                "url": sig["url"],
                "title": sig["title"],
                "content": sig["content"],
                "published_at": sig["published_at"],
                "event_metadata": sig["metadata"],
                "idempotency_key": sig["idempotency_key"],
                "event_hash": sig["event_hash"],
                "trace_id": f"fresh-{sig['source']}",
                "stream_id": None,
            })
            if ok:
                persisted += 1
        await session.commit()
    results["stages"]["ocp_persist"] = persisted
    print(f"  OCP persisted: {persisted} new fresh events")

    async with AsyncSessionLocal() as session:
        # LOD: Quality gate (only fresh pending)
        from datetime import UTC, datetime, timedelta
        cutoff = datetime.now(UTC) - timedelta(hours=FRESH_WINDOW_HOURS)
        already_reported = exists().where(QualityReport.raw_event_id == RawEvent.id)
        pending = (
            await session.execute(
                select(RawEvent)
                .where(
                    RawEvent.status == RawEventStatus.RECEIVED,
                    RawEvent.created_at >= cutoff,
                    ~already_reported,
                )
                .order_by(RawEvent.created_at.desc())
                .limit(200)
            )
        ).scalars().all()
        quality = QualityService(QualityRepository(session))
        await quality.ensure_rules_seeded()
        q_accept = 0
        q_reject = 0
        for event in pending:
            report_row = await quality.process_raw_event(event)
            if report_row.decision == "accept":
                q_accept += 1
            else:
                q_reject += 1
        await session.commit()
        results["stages"]["lod_quality"] = {"accepted": q_accept, "rejected": q_reject}
        print(f"  LOD quality: accept={q_accept} reject={q_reject}")

        # OI: Intelligence -> Context -> Opportunity (fresh only)
        accepted_quality = exists().where(
            QualityReport.raw_event_id == RawEvent.id,
            QualityReport.created_at >= cutoff,
            or_(QualityReport.decision == "accept", QualityReport.decision == "review"),
        )
        intel_events = (
            await session.execute(
                select(RawEvent)
                .where(RawEvent.status == RawEventStatus.RECEIVED, accepted_quality)
                .order_by(RawEvent.published_at.desc())
                .limit(100)
            )
        ).scalars().all()
        intel = IntelligenceService(IntelligenceRepository(session))
        i_ok = 0
        for event in intel_events:
            try:
                await intel.process_raw_event(event)
                i_ok += 1
            except Exception:
                pass
        await session.commit()
        results["stages"]["oi_intelligence"] = i_ok
        print(f"  OI intelligence: {i_ok}")

        ctx = ContextService(ContextRepository(session))
        c = await ctx.process_pending(limit=50)
        await session.commit()
        results["stages"]["oi_context"] = c
        print(f"  OI context: {c}")

        opp = OpportunityService(OpportunityRepository(session))
        o = await opp.process_pending(limit=40)
        await session.commit()
        results["stages"]["oi_opportunity"] = o
        print(f"  OI opportunity: {o}")

        rev = RevenueService(RevenueRepository(session))
        r = await rev.process_pending(limit=30)
        await session.commit()
        results["stages"]["revenue"] = r
        print(f"  Revenue: {r}")

        enr = LeadEnrichmentService(EnrichmentRepository(session), settings=settings)
        e = await enr.process_pending(limit=20)
        await session.commit()
        results["stages"]["enrichment"] = e
        print(f"  Enrichment: {e}")

        ver = DataVerificationService(VerificationRepository(session))
        v = await ver.process_pending(limit=20)
        await session.commit()
        results["stages"]["verification"] = v
        print(f"  Verification: {v}")

        # Validation: Get ONLY fresh targets (created in last 4h)
        tai = TargetAccountPlatformService(TargetAccountRepository(session), settings)
        t = await tai.process_pending(limit=20)
        await session.commit()
        results["stages"]["target_accounts"] = t
        print(f"  Target accounts: {t}")

        # Query fresh-only targets (created after cutoff)
        from app.models.target_account import TargetAccount as TargetAccountRow
        fresh_targets = (
            await session.execute(
                select(TargetAccountRow)
                .where(TargetAccountRow.created_at >= cutoff)
                .order_by(TargetAccountRow.created_at.desc())
                .limit(15)
            )
        ).scalars().all()

        # Convert to list format for output
        fresh_leads = []
        for tgt in fresh_targets:
            fresh_leads.append({
                "company_name": tgt.company_name,
                "revenue_opportunity_score": tgt.revenue_opportunity_score,
                "tier": tgt.tier,
                "matched_icp_name": tgt.matched_icp_name,
                "service_match": tgt.service_match,
                "why_now": tgt.why_now,
                "fit_score": tgt.fit_score,
                "intent_score": tgt.intent_score,
                "urgency_score": tgt.urgency_score,
                "buying_signals": tgt.buying_signals or [],
            })
        results["fresh_hot_leads"] = fresh_leads

    return results


def print_fresh_leads(results: dict[str, Any]) -> None:
    """Print only the NEW fresh leads from this run."""
    leads = results.get("fresh_hot_leads", [])
    print("")
    print("=" * 60)
    print(f"FRESH LEADS -- {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    if not leads:
        print("  No fresh leads found this cycle.")
        return
    for idx, row in enumerate(leads[:15], start=1):
        print(
            f"  {idx:02d}. {row['company_name']} | ROS={row['revenue_opportunity_score']:.1f} "
            f"| tier={row['tier']} | ICP={row['matched_icp_name'] or '-'} "
            f"| service={row['service_match'] or '-'}"
        )
        why = row.get('why_now', '')
        if why:
            print(f"      WHY: {why[:180]}")


async def run_once() -> dict[str, Any]:
    """Single fresh-lead pipeline run."""
    state = _load_state()
    started = datetime.now(UTC)
    print("")
    print("=" * 60)
    print(f"FRESH LEADS RUN -- {started.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Window: last {FRESH_WINDOW_HOURS}h only | Last run: {state.get('last_run_at', 'never')}")
    print("=" * 60)

    print("\n[1/2] Collecting fresh signals...")
    fresh = await collect_fresh_signals()
    print(f"  Total fresh signals: {len(fresh)}")

    if not fresh:
        print("  No fresh signals. Skipping pipeline.")
        state["last_run_at"] = started.isoformat()
        _save_state(state)
        return {"fresh_signals_in": 0, "stages": {}, "fresh_hot_leads": []}

    print("\n[2/2] Running OCP -> LOD -> OI -> Validation...")
    results = await run_ocp_lod_oi_pipeline(fresh)

    print_fresh_leads(results)

    # Save state
    state["last_run_at"] = started.isoformat()
    state["last_run_signals"] = len(fresh)
    state["last_run_leads"] = len(results.get("fresh_hot_leads", []))
    _save_state(state)

    # Write report
    out = ROOT / "scripts" / f"fresh_leads_{started.strftime('%Y%m%d_%H%M')}.json"
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nReport: {out}")

    return results


async def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Fresh leads scheduler")
    parser.add_argument("--loop", action="store_true", help="Run every 10 minutes")
    args = parser.parse_args()

    if args.loop:
        print(f"Starting fresh leads loop -- every {LOOP_INTERVAL_SECONDS}s")
        while True:
            try:
                await run_once()
            except Exception as exc:
                print(f"  Run error: {exc}")
            print(f"\n  Next run in {LOOP_INTERVAL_SECONDS}s...")
            await asyncio.sleep(LOOP_INTERVAL_SECONDS)
    else:
        await run_once()


if __name__ == "__main__":
    asyncio.run(main())
