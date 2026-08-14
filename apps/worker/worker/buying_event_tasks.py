"""Buying Event Celery Tasks - Two-Lane Architecture.

Two independent lanes:
- Lane A: COMAI (WhatsApp + AI Customer Support for Ecommerce)
- Lane B: INOWIX (SaaS + Custom Software + AI + Mobile/Web Development)

6-level classification:
- ACTIVE_BUYING_EVENT
- VERIFIED_PAIN
- ICP_OPPORTUNITY
- PARTNER_OPPORTUNITY
- NURTURE
- REJECT
"""

import logging
from datetime import UTC, datetime

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.buying_event import (
    BuyingEvent,
    BuyingEventClassification,
    BuyingEventDepartment,
    BuyingEventStatus,
)
from app.models.raw_event import RawEvent, RawEventStatus

logger = logging.getLogger(__name__)


@shared_task(name="buying_events.detect_comai_events")
def detect_comai_events():
    """Detect COMAI buying events with lane-specific logic."""
    import asyncio
    asyncio.run(_detect_comai_events_async())


async def _detect_comai_events_async():
    """Async implementation of COMAI detection."""
    async with AsyncSessionLocal() as session:
        from app.services.buying_events import BuyingEventDetector
        
        detector = BuyingEventDetector(session, lane="COMAI")
        events = await detector.detect_buying_events("COMAI", batch_size=500)
        
        saved = 0
        for ev in events:
            buying_event = BuyingEvent(
                raw_event_id=ev["raw_event_id"],
                department=BuyingEventDepartment.COMAI,
                event_type=ev["event_type"],
                confidence=ev["confidence"],
                evidence=ev["evidence"],
                company_name=ev["company_name"],
                company_domain=ev.get("company_domain"),
                contact_info=ev.get("contact_info", {}),
                disqualifiers=ev.get("disqualifiers", []),
                status=BuyingEventStatus.VERIFIED,
                verified_at=ev.get("verified_at"),
                problem=ev.get("problem"),
                why_now=ev.get("why_now"),
                solution_match=ev.get("solution_match"),
                classification=BuyingEventClassification(ev["classification"]),
                business_type=ev.get("business_type"),
                outreach_reason=ev.get("outreach_reason"),
                freshness=ev.get("freshness"),
                days_old=ev.get("days_old", 999),
                contact_type=ev.get("contact_type"),
                is_high_contactability=ev.get("is_high_contactability", False),
                pain_signals=ev.get("pain_signals", []),
                buying_signals=ev.get("buying_signals", []),
                partner_signals=ev.get("partner_signals", []),
                icp_match_score=ev.get("icp_match_score", 0.0),
                outreach_preparation=ev.get("outreach_preparation"),
                cto_test_result=ev.get("cto_test_result", False),
            )
            session.add(buying_event)
            saved += 1
            
            # Mark raw event as processed
            raw_event = await session.get(RawEvent, ev["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED
        
        await session.commit()
        
        # Count by classification
        classifications = {}
        for ev in events:
            cls = ev["classification"]
            classifications[cls] = classifications.get(cls, 0) + 1
        
        logger.info(f"COMAI: Saved {saved} verified buying events")
        return {
            "lane": "COMAI",
            "detected": len(events),
            "saved": saved,
            "classifications": classifications,
        }


@shared_task(name="buying_events.detect_inowix_events")
def detect_inowix_events():
    """Detect INOWIX buying events with lane-specific logic."""
    import asyncio
    asyncio.run(_detect_inowix_events_async())


async def _detect_inowix_events_async():
    """Async implementation of INOWIX detection."""
    async with AsyncSessionLocal() as session:
        from app.services.buying_events import BuyingEventDetector
        
        detector = BuyingEventDetector(session, lane="INOWIX")
        events = await detector.detect_buying_events("INOWIX", batch_size=500)
        
        saved = 0
        for ev in events:
            buying_event = BuyingEvent(
                raw_event_id=ev["raw_event_id"],
                department=BuyingEventDepartment.INOWIX,
                event_type=ev["event_type"],
                confidence=ev["confidence"],
                evidence=ev["evidence"],
                company_name=ev["company_name"],
                company_domain=ev.get("company_domain"),
                contact_info=ev.get("contact_info", {}),
                disqualifiers=ev.get("disqualifiers", []),
                status=BuyingEventStatus.VERIFIED,
                verified_at=ev.get("verified_at"),
                problem=ev.get("problem"),
                why_now=ev.get("why_now"),
                solution_match=ev.get("solution_match"),
                classification=BuyingEventClassification(ev["classification"]),
                business_type=ev.get("business_type"),
                outreach_reason=ev.get("outreach_reason"),
                freshness=ev.get("freshness"),
                days_old=ev.get("days_old", 999),
                contact_type=ev.get("contact_type"),
                is_high_contactability=ev.get("is_high_contactability", False),
                pain_signals=ev.get("pain_signals", []),
                buying_signals=ev.get("buying_signals", []),
                partner_signals=ev.get("partner_signals", []),
                icp_match_score=ev.get("icp_match_score", 0.0),
                outreach_preparation=ev.get("outreach_preparation"),
                cto_test_result=ev.get("cto_test_result", False),
            )
            session.add(buying_event)
            saved += 1
            
            # Mark raw event as processed
            raw_event = await session.get(RawEvent, ev["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED
        
        await session.commit()
        
        # Count by classification
        classifications = {}
        for ev in events:
            cls = ev["classification"]
            classifications[cls] = classifications.get(cls, 0) + 1
        
        logger.info(f"INOWIX: Saved {saved} verified buying events")
        return {
            "lane": "INOWIX",
            "detected": len(events),
            "saved": saved,
            "classifications": classifications,
        }


@shared_task(name="buying_events.generate_outreach_queue")
def generate_outreach_queue():
    """Generate final outreach queue from SALES_READY opportunities."""
    import asyncio
    asyncio.run(_generate_outreach_queue_async())


async def _generate_outreach_queue_async():
    """Async implementation of outreach queue generation."""
    async with AsyncSessionLocal() as session:
        # Get all SALES_READY opportunities (ACTIVE_BUYING_EVENT or VERIFIED_PAIN with CTO test passed)
        result = await session.execute(
            select(BuyingEvent).where(
                BuyingEvent.classification.in_([
                    BuyingEventClassification.ACTIVE_BUYING_EVENT,
                    BuyingEventClassification.VERIFIED_PAIN,
                ]),
                BuyingEvent.status == BuyingEventStatus.VERIFIED,
                BuyingEvent.cto_test_result == True,
            )
        )
        opportunities = result.scalars().all()
        
        # Separate by lane
        comai_opportunities = [o for o in opportunities if o.department == BuyingEventDepartment.COMAI]
        inowix_opportunities = [o for o in opportunities if o.department == BuyingEventDepartment.INOWIX]
        
        # Build outreach queue
        outreach_queue = {
            "generated_at": datetime.now(UTC).isoformat(),
            "comai": {
                "direct_customers": [],
                "partner_opportunities": [],
                "verified_pain": [],
            },
            "inowix": {
                "direct_customers": [],
                "partner_opportunities": [],
                "verified_pain": [],
            },
            "summary": {
                "total_sales_ready": len(opportunities),
                "comai_sales_ready": len(comai_opportunities),
                "inowix_sales_ready": len(inowix_opportunities),
            },
        }
        
        # Process COMAI opportunities
        for opp in comai_opportunities:
            entry = {
                "id": str(opp.id),
                "company": opp.company_name,
                "domain": opp.company_domain,
                "classification": opp.classification.value,
                "problem": opp.problem,
                "why_now": opp.why_now,
                "solution": opp.solution_match,
                "contact": opp.contact_info,
                "outreach_preparation": opp.outreach_preparation,
                "cto_test": opp.cto_test_result,
            }
            
            if opp.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
                outreach_queue["comai"]["direct_customers"].append(entry)
            elif opp.classification == BuyingEventClassification.VERIFIED_PAIN:
                outreach_queue["comai"]["verified_pain"].append(entry)
        
        # Process INOWIX opportunities
        for opp in inowix_opportunities:
            entry = {
                "id": str(opp.id),
                "company": opp.company_name,
                "domain": opp.company_domain,
                "classification": opp.classification.value,
                "problem": opp.problem,
                "why_now": opp.why_now,
                "solution": opp.solution_match,
                "contact": opp.contact_info,
                "outreach_preparation": opp.outreach_preparation,
                "cto_test": opp.cto_test_result,
            }
            
            if opp.classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
                outreach_queue["inowix"]["direct_customers"].append(entry)
            elif opp.classification == BuyingEventClassification.VERIFIED_PAIN:
                outreach_queue["inowix"]["verified_pain"].append(entry)
        
        logger.info(f"Outreach queue generated: {len(opportunities)} SALES_READY opportunities")
        return outreach_queue


@shared_task(name="buying_events.process_verified_buying_events")
def process_verified_buying_events():
    """Process verified buying events and create leads."""
    import asyncio
    asyncio.run(_process_verified_buying_events_async())


async def _process_verified_buying_events_async():
    """Async implementation of verified buying event processing."""
    async with AsyncSessionLocal() as session:
        from app.services.lead_discovery import LeadDiscoveryService
        
        lead_service = LeadDiscoveryService(session)
        
        # Get verified buying events
        result = await session.execute(
            select(BuyingEvent).where(
                BuyingEvent.status == BuyingEventStatus.VERIFIED,
            ).limit(50)
        )
        events = result.scalars().all()
        
        processed = 0
        for event in events:
            # Skip REJECT classification
            if event.classification == BuyingEventClassification.REJECT:
                event.status = BuyingEventStatus.DISQUALIFIED
                continue
            
            # Create lead from buying event
            try:
                await lead_service.create_lead_from_buying_event(event)
                event.status = BuyingEventStatus.PROCESSED
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process buying event {event.id}: {e}")
                event.status = BuyingEventStatus.DISQUALIFIED
                event.disqualification_reason = str(e)
        
        await session.commit()
        
        logger.info(f"Processed {processed} verified buying events")
        return {"processed": processed, "total": len(events)}


@shared_task(name="buying_events.generate_leads")
def generate_leads():
    """Generate realistic pain signals for testing the detection pipeline."""
    import asyncio
    asyncio.run(_generate_leads_async())


async def _generate_leads_async():
    """Async implementation of lead generation."""
    from worker.lead_simulator import generate_leads
    
    async with AsyncSessionLocal() as session:
        result = await generate_leads(session, count_per_lane=3)
        
        logger.info(f"Generated {result['inserted']} new pain signals")
        return result
