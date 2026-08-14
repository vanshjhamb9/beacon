"""Buying Event Contact Enrichment Task - Auto-enriches contact info for buying events.

Runs every 10 minutes via Celery Beat.
For each buying event with missing contact info:
1. Scrapes company website (homepage, /about, /team, /contact)
2. Searches DuckDuckGo + Bing for contact data
3. Extracts emails, founder names, phones, LinkedIn
4. Updates BuyingEvent.contact_info
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from celery import shared_task
from sqlalchemy import select, and_, or_

from app.db.session import AsyncSessionLocal
from app.models.buying_event import BuyingEvent, ContactType

logger = logging.getLogger(__name__)


async def _enrich_single_event(event_id: str, domain: str, company_name: str) -> dict[str, Any]:
    """Enrich a single buying event with contact information."""
    result: dict[str, Any] = {
        "event_id": event_id,
        "domain": domain,
        "company_name": company_name,
        "enriched": False,
        "email_found": False,
        "founder_found": False,
        "phone_found": False,
        "linkedin_found": False,
        "error": None,
    }

    try:
        from packages.sales_intelligence_platform.engines.real_contact_enricher import RealContactEnricher

        enricher = RealContactEnricher(timeout=10.0, delay=1.0, max_concurrent=2)
        enrichment_result = await enricher.enrich(domain=domain, company_name=company_name)

        contact_info: dict[str, Any] = {}

        if enrichment_result.founder_email:
            contact_info["email"] = enrichment_result.founder_email
            contact_info["email_type"] = "founder"
            result["email_found"] = True
        elif enrichment_result.general_email:
            contact_info["email"] = enrichment_result.general_email
            contact_info["email_type"] = "general"
            result["email_found"] = True
        elif enrichment_result.support_email:
            contact_info["email"] = enrichment_result.support_email
            contact_info["email_type"] = "support"
            result["email_found"] = True
        elif enrichment_result.sales_email:
            contact_info["email"] = enrichment_result.sales_email
            contact_info["email_type"] = "sales"
            result["email_found"] = True
        elif enrichment_result.emails:
            best_email = max(enrichment_result.emails, key=lambda e: e.confidence)
            contact_info["email"] = best_email.value
            contact_info["email_type"] = "general"
            result["email_found"] = True

        if enrichment_result.founder_name:
            contact_info["founder_name"] = enrichment_result.founder_name
            result["founder_found"] = True

        if enrichment_result.business_phone:
            contact_info["phone"] = enrichment_result.business_phone
            result["phone_found"] = True
        elif enrichment_result.phones:
            best_phone = max(enrichment_result.phones, key=lambda p: p.confidence)
            contact_info["phone"] = best_phone.value
            result["phone_found"] = True

        if enrichment_result.linkedin_urls:
            contact_info["linkedin"] = enrichment_result.linkedin_urls[0]
            result["linkedin_found"] = True

        if enrichment_result.instagram_urls:
            contact_info["instagram"] = enrichment_result.instagram_urls[0]
        if enrichment_result.facebook_urls:
            contact_info["facebook"] = enrichment_result.facebook_urls[0]

        if enrichment_result.decision_makers:
            contact_info["decision_makers"] = [
                {"name": dm.name, "role": dm.role, "email": dm.email}
                for dm in enrichment_result.decision_makers[:3]
            ]

        contact_info["pages_scraped"] = enrichment_result.pages_scraped
        contact_info["enrichment_source"] = "real_contact_enricher"

        async with AsyncSessionLocal() as session:
            event_result = await session.execute(
                select(BuyingEvent).where(BuyingEvent.id == event_id)
            )
            event = event_result.scalar_one_or_none()

            if event:
                existing = event.contact_info or {}
                existing.update(contact_info)
                event.contact_info = existing

                if contact_info.get("email") and contact_info.get("email_type") == "founder":
                    event.contact_type = ContactType.DECISION_MAKER_DIRECT
                    event.is_high_contactability = True
                elif contact_info.get("email"):
                    event.contact_type = ContactType.VERIFIED_WORK_EMAIL
                    event.is_high_contactability = False
                elif contact_info.get("linkedin"):
                    event.contact_type = ContactType.LINKEDIN_DIRECT
                    event.is_high_contactability = False
                elif contact_info.get("phone"):
                    event.contact_type = ContactType.PLATFORM_DM
                    event.is_high_contactability = False
                else:
                    event.contact_type = ContactType.UNKNOWN
                    event.is_high_contactability = False

                await session.commit()
                result["enriched"] = True

        logger.info(
            f"Enriched {company_name}: email={result['email_found']}, "
            f"founder={result['founder_found']}, phone={result['phone_found']}"
        )

    except Exception as e:
        logger.error(f"Failed to enrich {company_name} ({domain}): {e}")
        result["error"] = str(e)

        try:
            from packages.collectors.extraction.public_contacts import recover_from_official_website

            fallback_result = recover_from_official_website(
                f"https://{domain}",
                timeout=8.0,
                max_pages=6,
            )

            if fallback_result.get("emails") or fallback_result.get("phones"):
                async with AsyncSessionLocal() as session:
                    event_result = await session.execute(
                        select(BuyingEvent).where(BuyingEvent.id == event_id)
                    )
                    event = event_result.scalar_one_or_none()

                    if event:
                        existing = event.contact_info or {}
                        if fallback_result.get("emails"):
                            existing["email"] = fallback_result["emails"][0]
                            existing["email_type"] = "general"
                            result["email_found"] = True
                        if fallback_result.get("phones"):
                            existing["phone"] = fallback_result["phones"][0]
                            result["phone_found"] = True
                        if fallback_result.get("linkedin"):
                            existing["linkedin"] = fallback_result["linkedin"][0]
                            result["linkedin_found"] = True
                        if fallback_result.get("decision_makers"):
                            existing["founder_name"] = fallback_result["decision_makers"][0].get("name")
                            result["founder_found"] = True

                        existing["enrichment_source"] = "public_contacts_fallback"
                        event.contact_info = existing
                        await session.commit()
                        result["enriched"] = True
                        result["error"] = None

        except Exception as fallback_error:
            logger.error(f"Fallback also failed for {company_name}: {fallback_error}")

    return result


@shared_task(
    name="buying_events.enrich_contacts",
    bind=True,
    max_retries=2,
    soft_time_limit=600,
    time_limit=660,
)
def enrich_contacts(self):
    """Enrich contact info for buying events missing email/phone/founder data."""
    return asyncio.run(_enrich_contacts_async())


async def _enrich_contacts_async() -> dict[str, Any]:
    """Async implementation of contact enrichment."""
    enriched_count = 0
    failed_count = 0
    skipped_count = 0
    results = []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BuyingEvent).where(
                and_(
                    BuyingEvent.company_domain.isnot(None),
                    BuyingEvent.company_domain != "",
                    or_(
                        BuyingEvent.contact_info["email"].is_(None),
                        BuyingEvent.contact_info["email"].astext == "",
                        BuyingEvent.contact_info["email"].astext == "null",
                        BuyingEvent.contact_info.is_(None),
                    ),
                )
            ).limit(50)
        )
        events = result.scalars().all()

        if not events:
            logger.info("No buying events need enrichment")
            return {
                "total": 0,
                "enriched": 0,
                "failed": 0,
                "skipped": 0,
                "message": "All buying events already enriched",
            }

        logger.info(f"Found {len(events)} buying events to enrich")

        for event in events:
            domain = event.company_domain
            company_name = event.company_name

            if not domain:
                skipped_count += 1
                continue

            enrichment_result = await _enrich_single_event(
                str(event.id), domain, company_name
            )

            results.append(enrichment_result)

            if enrichment_result["enriched"]:
                enriched_count += 1
            else:
                failed_count += 1

    summary = {
        "total": len(events),
        "enriched": enriched_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results,
    }

    logger.info(
        f"Enrichment complete: {enriched_count} enriched, "
        f"{failed_count} failed, {skipped_count} skipped"
    )

    return summary


@shared_task(name="buying_events.enrich_single")
def enrich_single_event(event_id: str):
    """Enrich a single buying event by ID."""
    return asyncio.run(_enrich_single_event_by_id(event_id))


async def _enrich_single_event_by_id(event_id: str) -> dict[str, Any]:
    """Enrich a single buying event by its ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BuyingEvent).where(BuyingEvent.id == event_id)
        )
        event = result.scalar_one_or_none()

        if not event:
            return {"error": "Event not found"}

        if not event.company_domain:
            return {"error": "No domain available for enrichment"}

        return await _enrich_single_event(
            str(event.id), event.company_domain, event.company_name
        )
