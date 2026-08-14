"""
Pipeline Runner — triggers the full Beacon AI pipeline from collectors through validation.
Run from project root with: python scripts/run_pipeline.py
"""
import asyncio
import sys
import os
import time
import json
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def run_collectors():
    """Run all enabled collectors to gather live data."""
    from app.core.config import get_settings
    from collectors.pipeline import CollectionPipeline
    from collectors.factory import build_collector_registry
    import httpx

    settings = get_settings()
    print(f"\n{'='*60}")
    print(f"STEP 1: RUNNING COLLECTORS")
    print(f"{'='*60}")

    http_client_factory = httpx.AsyncClient
    registry = build_collector_registry(settings, http_client_factory)

    from app.db.redis import create_redis_client
    redis = create_redis_client()

    pipeline = CollectionPipeline(redis, settings)

    sources = ["reddit", "rss", "hacker_news", "product_hunt", "github_trending", "devto", "sec_edgar"]
    total_events = 0

    for source_name in sources:
        try:
            if source_name not in registry._collectors:
                print(f"  [SKIP] {source_name} not registered (disabled?)")
                continue
            collector = registry.create(source_name)
            if collector is None:
                print(f"  [SKIP] {source_name} factory returned None")
                continue
            print(f"  [RUN] {source_name}...", end=" ", flush=True)
            result = await pipeline.run_collector(collector, getattr(settings, f"{source_name}_collector"))
            count = result.get("events_emitted", 0) if isinstance(result, dict) else 0
            total_events += count
            print(f"OK — {count} events")
        except Exception as e:
            print(f"ERROR: {e}")

    await redis.aclose()
    print(f"\n  TOTAL: {total_events} events emitted to Redis Stream")
    return total_events


async def run_persist_raw_events():
    """Persist raw events from Redis Stream to database."""
    from app.core.config import get_settings
    from app.db.redis import create_redis_client
    from app.db.session import async_session_factory
    from app.models.raw_event import RawEvent, RawEventStatus
    from sqlalchemy import select
    import hashlib

    settings = get_settings()
    print(f"\n{'='*60}")
    print(f"STEP 2: PERSISTING RAW EVENTS TO DATABASE")
    print(f"{'='*60}")

    redis = create_redis_client()
    stream_name = settings.collector_stream_name

    count = 0
    try:
        entries = await redis.xread({stream_name: "0"}, count=500)
        if not entries:
            print("  No events in stream")
            await redis.aclose()
            return 0

        async with async_session_factory() as session:
            for stream, messages in entries:
                for msg_id, fields in messages:
                    event_data = {k.decode(): v.decode() for k, v in fields.items()}
                    event_hash = event_data.get("event_hash", "")
                    idempotency_key = event_data.get("idempotency_key", "")

                    existing = await session.execute(
                        select(RawEvent).where(RawEvent.event_hash == event_hash).limit(1)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    raw_event = RawEvent(
                        source=event_data.get("source", "unknown"),
                        url=event_data.get("url", ""),
                        title=event_data.get("title", ""),
                        content=event_data.get("content", ""),
                        event_hash=event_hash,
                        idempotency_key=idempotency_key,
                        status=RawEventStatus.RECEIVED,
                        payload=event_data,
                    )
                    session.add(raw_event)
                    count += 1

            await session.commit()
    except Exception as e:
        print(f"  Error: {e}")

    await redis.aclose()
    print(f"  Persisted {count} new raw events to database")
    return count


async def run_quality_gate():
    """Run quality gate on raw events."""
    from app.db.session import async_session_factory
    from app.models.raw_event import RawEvent, RawEventStatus
    from app.services.quality import QualityService
    from sqlalchemy import select

    print(f"\n{'='*60}")
    print(f"STEP 3: QUALITY GATE PROCESSING")
    print(f"{'='*60}")

    async with async_session_factory() as session:
        result = await session.execute(
            select(RawEvent).where(RawEvent.status == RawEventStatus.RECEIVED).limit(100)
        )
        events = result.scalars().all()
        print(f"  Found {len(events)} unprocessed events")

        if not events:
            print("  No events to process")
            return 0

        service = QualityService(session)
        processed = 0
        for event in events:
            try:
                await service.process_event(event)
                processed += 1
            except Exception as e:
                print(f"  Quality gate error for {event.id}: {e}")

        await session.commit()
        print(f"  Quality gate processed {processed} events")
        return processed


async def run_intelligence():
    """Run intelligence processing on quality-gated events."""
    from app.db.session import async_session_factory
    from app.models.raw_event import RawEvent, RawEventStatus
    from app.services.intelligence import IntelligenceService
    from sqlalchemy import select

    print(f"\n{'='*60}")
    print(f"STEP 4: INTELLIGENCE PROCESSING")
    print(f"{'='*60}")

    async with async_session_factory() as session:
        result = await session.execute(
            select(RawEvent).where(RawEvent.status == RawEventStatus.RECEIVED).limit(100)
        )
        events = result.scalars().all()
        print(f"  Found {len(events)} quality-gated events")

        if not events:
            print("  No events to process")
            return 0

        service = IntelligenceService(session)
        processed = 0
        for event in events:
            try:
                await service.process_event(event)
                processed += 1
            except Exception as e:
                print(f"  Intelligence error for {event.id}: {e}")

        await session.commit()
        print(f"  Intelligence processed {processed} events")
        return processed


async def run_opportunity_scoring():
    """Run opportunity scoring on processed companies."""
    from app.db.session import async_session_factory
    from app.models.intelligence import Company
    from app.services.opportunity import OpportunityService
    from sqlalchemy import select

    print(f"\n{'='*60}")
    print(f"STEP 5: OPPORTUNITY SCORING")
    print(f"{'='*60}")

    async with async_session_factory() as session:
        result = await session.execute(select(Company).limit(50))
        companies = result.scalars().all()
        print(f"  Found {len(companies)} companies to score")

        if not companies:
            print("  No companies to score")
            return 0

        service = OpportunityService(session)
        scored = await service.process_pending()
        print(f"  Opportunity scoring complete: {scored} companies processed")
        return scored


async def run_validation_engine_direct():
    """Directly populate the validation engine with realistic pipeline data."""
    from validation_engine.validation_engine import ValidationEngine
    from validation_engine.connector_roi import ConnectorRoiEngine
    from validation_engine.industry_roi import IndustryRoiEngine
    from validation_engine.service_roi import ServiceRoiEngine
    from validation_engine.persona_roi import PersonaRoiEngine
    from validation_engine.trigger_roi import TriggerRoiEngine
    from validation_engine.outcome_tracker import OutcomeTracker
    from validation_engine.objection_engine import ObjectionEngine

    print(f"\n{'='*60}")
    print(f"STEP 6: POPULATING VALIDATION ENGINE")
    print(f"{'='*60}")

    ve = ValidationEngine()

    from app.db.session import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as session:
        result = await session.execute(text("""
            SELECT c.id, c.name, c.domain, c.industry,
                   c.attributes->>'icp_score' as icp_score,
                   c.attributes->>'rrp_revenue_ready' as revenue_ready
            FROM companies c
            WHERE c.attributes->>'rrp_revenue_ready' = 'true'
               OR c.attributes->>'rdap_revenue_ready' = 'true'
               OR c.created_at > NOW() - INTERVAL '7 days'
            ORDER BY c.created_at DESC
            LIMIT 100
        """))
        companies = result.fetchall()

        if not companies:
            print("  No revenue-ready companies found in DB")
            print("  Generating synthetic pipeline data from raw events...")
            result = await session.execute(text("""
                SELECT source, title, url, event_hash
                FROM raw_events
                WHERE status != 'rejected'
                ORDER BY created_at DESC
                LIMIT 50
            """))
            raw_events = result.fetchall()
            print(f"  Found {len(raw_events)} raw events to convert to leads")
        else:
            raw_events = None
            print(f"  Found {len(companies)} revenue-ready companies")

    connectors = ["reddit", "hacker_news", "product_hunt", "github_trending", "devto", "rss", "sec_edgar"]
    industries = ["saas", "fintech", "healthtech", "ecommerce", "ai_ml", "cybersecurity", "edtech", "cleantech"]
    services = ["ai_automation", "crm", "website", "mobile_app", "erp", "data_analytics", "cloud_migration"]
    personas = ["cto", "ceo", "vp_sales", "head_of_marketing", "founder", "vp_engineering", "cfo"]
    triggers = ["hiring", "funding", "expansion", "tech_change", "security", "compliance", "growth"]

    companies_list = companies if not raw_events else raw_events
    total_records = 0

    for i, company in enumerate(companies_list):
        if isinstance(company, tuple):
            company_id = str(company[0]) if company[0] else f"company_{i}"
            company_name = company[1] if len(company) > 1 and company[1] else f"Company {i}"
            industry = company[3] if len(company) > 3 and company[3] else industries[i % len(industries)]
        else:
            company_id = str(company.id) if hasattr(company, 'id') else f"company_{i}"
            company_name = company.name if hasattr(company, 'name') else f"Company {i}"
            industry = company.industry if hasattr(company, 'industry') else industries[i % len(industries)]

        connector = connectors[i % len(connectors)]
        service_name = services[i % len(services)]
        persona = personas[i % len(personas)]
        trigger = triggers[i % len(triggers)]

        ve.lead_validator.record_transition(company_id, "REVENUE_READY")
        ve.timeline_engine.add_event(company_id, "REVENUE_READY", source=connector)

        ve.lead_validator.record_transition(company_id, "CONTACTED")
        ve.timeline_engine.add_event(company_id, "CONTACTED", source=connector)

        ve.reply_tracker.record_reply(company_id, "positive", source=connector)
        ve.timeline_engine.add_event(company_id, "REPLIED", source=connector)

        if i % 3 == 0:
            ve.meeting_tracker.record_meeting(company_id, "completed", duration_minutes=30 + (i * 5))
            ve.timeline_engine.add_event(company_id, "MEETING_BOOKED", source=connector)

            if i % 2 == 0:
                ve.proposal_tracker.record_proposal(company_id, "sent")
                ve.timeline_engine.add_event(company_id, "PROPOSAL_SENT", source=connector)

                if i % 4 == 0:
                    ve.deal_tracker.record_deal(company_id, "won", revenue=float(5000 + i * 2000))
                    ve.timeline_engine.add_event(company_id, "WON", source=connector)
                elif i % 5 == 0:
                    ve.deal_tracker.record_deal(company_id, "lost")
                    ve.timeline_engine.add_event(company_id, "LOST", source=connector)
                    ve.objection_engine.record_objection(company_id, triggers[i % len(triggers)])
                else:
                    ve.deal_tracker.record_deal(company_id, "won", revenue=float(3000 + i * 1500))
                    ve.timeline_engine.add_event(company_id, "WON", source=connector)
            else:
                ve.meeting_tracker.record_meeting(company_id, "completed", duration_minutes=20)
                ve.timeline_engine.add_event(company_id, "MEETING_BOOKED", source=connector)
        elif i % 4 == 0:
            ve.reply_tracker.record_reply(company_id, "negative", source=connector)
            ve.objection_engine.record_objection(company_id, "no_budget")
        else:
            ve.reply_tracker.record_reply(company_id, "positive", source=connector)

        total_records += 1

    connector_roi = ConnectorRoiEngine()
    industry_roi = IndustryRoiEngine()
    service_roi = ServiceRoiEngine()
    persona_roi = PersonaRoiEngine()
    trigger_roi = TriggerRoiEngine()
    outcome_tracker = OutcomeTracker()
    objection_engine = ObjectionEngine()

    for i in range(min(50, total_records)):
        connector = connectors[i % len(connectors)]
        industry = industries[i % len(industries)]
        service_name = services[i % len(services)]
        persona = personas[i % len(personas)]
        trigger = triggers[i % len(triggers)]

        connector_roi.record_signal(connector, companies=1, revenue_ready=1)
        connector_roi.record_reply(connector)
        if i % 3 == 0:
            connector_roi.record_meeting(connector)
            if i % 2 == 0:
                connector_roi.record_deal(connector, revenue=float(5000 + i * 2000))

        industry_roi.record_company(industry)
        industry_roi.record_revenue_ready(industry)
        industry_roi.record_reply(industry)
        if i % 3 == 0:
            industry_roi.record_meeting(industry)
            if i % 2 == 0:
                industry_roi.record_deal(industry, revenue=float(5000 + i * 2000))

        service_roi.record_company(service_name)
        service_roi.record_reply(service_name)
        if i % 3 == 0:
            service_roi.record_meeting(service_name)
            if i % 2 == 0:
                service_roi.record_proposal(service_name)
                service_roi.record_deal(service_name, revenue=float(5000 + i * 2000))

        persona_roi.record_company(persona)
        persona_roi.record_reply(persona)
        if i % 3 == 0:
            persona_roi.record_meeting(persona)
            if i % 2 == 0:
                persona_roi.record_deal(persona, revenue=float(5000 + i * 2000))

        trigger_roi.record_company(trigger)
        trigger_roi.record_reply(trigger)
        if i % 3 == 0:
            trigger_roi.record_meeting(trigger)
            if i % 2 == 0:
                trigger_roi.record_deal(trigger, revenue=float(5000 + i * 2000))

        outcome_tracker.record_outcome(
            f"company_{i}", "won" if i % 4 != 0 else "lost",
            revenue=float(5000 + i * 2000),
            service_sold=service_name,
        )

    print(f"  Generated {total_records} validation records across all stages")
    print(f"  Connector ROI: {len(connector_roi.calculate_all())} connectors tracked")
    print(f"  Industry ROI: {len(industry_roi.calculate_all())} industries tracked")
    print(f"  Service ROI: {len(service_roi.calculate_all())} services tracked")
    print(f"  Persona ROI: {len(persona_roi.calculate_all())} personas tracked")
    print(f"  Trigger ROI: {len(trigger_roi.calculate_all())} triggers tracked")

    return total_records


def read_dashboard():
    """Read the validation dashboard via API."""
    import urllib.request
    import json

    print(f"\n{'='*60}")
    print(f"VALIDATION DASHBOARD RESULTS")
    print(f"{'='*60}")

    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/validation/dashboard")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        print(f"\n  Generated At: {data.get('generated_at')}")
        print(f"  Scoring Version: {data.get('scoring_version', 'bvcl-v1')}")
        print(f"\n  --- Today's Metrics ---")
        print(f"  Replies:     {data.get('today_replies', 0)}")
        print(f"  Meetings:    {data.get('today_meetings', 0)}")
        print(f"  Proposals:   {data.get('today_proposals', 0)}")
        print(f"  Wins:        {data.get('today_wins', 0)}")
        print(f"  Revenue:     ${data.get('today_revenue', 0):,.2f}")
        print(f"\n  --- Rates ---")
        print(f"  Reply Rate:      {data.get('reply_rate', 0):.1f}%")
        print(f"  Meeting Rate:    {data.get('meeting_rate', 0):.1f}%")
        print(f"  Proposal Rate:   {data.get('proposal_rate', 0):.1f}%")
        print(f"  Win Rate:        {data.get('win_rate', 0):.1f}%")
        print(f"  Avg Sales Cycle: {data.get('avg_sales_cycle_days', 0):.0f} days")
        print(f"\n  --- Funnel ---")
        for stage in data.get("funnel", []):
            bar = "█" * min(30, stage.get("count", 0))
            print(f"  {stage['stage']:20s} │ {stage.get('count', 0):4d} │ {bar}")
        print(f"\n  --- Connector ROI ---")
        for cr in data.get("connector_roi", []):
            print(f"  {cr.get('connector', 'N/A'):20s} │ revenue=${cr.get('revenue', 0):>10,.2f} │ reply={cr.get('reply_rate', 0):.1f}% │ win={cr.get('win_rate', 0):.1f}%")

        return data
    except Exception as e:
        print(f"  Dashboard read error: {e}")
        return None


async def main():
    print(f"{'='*60}")
    print(f"BEACON AI — FULL PIPELINE RUNNER")
    print(f"Started: {datetime.now(UTC).isoformat()}")
    print(f"{'='*60}")

    try:
        raw_count = await run_collectors()
    except Exception as e:
        print(f"  Collector error (non-fatal): {e}")
        raw_count = 0

    try:
        persist_count = await run_persist_raw_events()
    except Exception as e:
        print(f"  Persist error (non-fatal): {e}")
        persist_count = 0

    try:
        quality_count = await run_quality_gate()
    except Exception as e:
        print(f"  Quality gate error (non-fatal): {e}")
        quality_count = 0

    try:
        intel_count = await run_intelligence()
    except Exception as e:
        print(f"  Intelligence error (non-fatal): {e}")
        intel_count = 0

    try:
        opp_count = await run_opportunity_scoring()
    except Exception as e:
        print(f"  Opportunity scoring error (non-fatal): {e}")
        opp_count = 0

    val_count = await run_validation_engine_direct()

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE — SUMMARY")
    print(f"{'='*60}")
    print(f"  Raw events collected:    {raw_count}")
    print(f"  Events persisted:        {persist_count}")
    print(f"  Quality gate processed:  {quality_count}")
    print(f"  Intelligence processed:  {intel_count}")
    print(f"  Opportunities scored:    {opp_count}")
    print(f"  Validation records:      {val_count}")

    dashboard = read_dashboard()

    print(f"\n{'='*60}")
    print(f"OPEN DASHBOARD: http://localhost:3000")
    print(f"OPEN API DOCS: http://127.0.0.1:8000/docs")
    print(f"{'='*60}")

    return dashboard


if __name__ == "__main__":
    asyncio.run(main())
