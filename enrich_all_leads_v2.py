"""Fast batch enrichment for all leads - V2 with concurrency and resume support."""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from app.db.session import AsyncSessionLocal
from app.repositories.sales_account import SalesAccountRepository
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from packages.sales_intelligence_platform.engines.real_contact_enricher import RealContactEnricher
from packages.sales_intelligence_platform.engines.account_builder import build_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 2  # Process N leads concurrently (lower = fewer 429s)


async def enrich_one_lead(lead, enricher, account_repo, session, stats):
    """Enrich a single lead and save to DB."""
    domain = lead.domain
    company = lead.company_name

    try:
        # Enrich contacts
        enrichment = await enricher.enrich(domain, company)

        # Build account (Sprint 39 engines)
        lead_data = {
            "id": str(lead.id),
            "company_name": lead.company_name,
            "website": lead.website,
            "domain": lead.domain,
            "platform": lead.platform,
            "category": lead.category,
            "country": lead.country,
            "city": lead.city,
            "state": lead.state,
            "shopify_detected": lead.shopify_detected,
            "woocommerce_detected": lead.woocommerce_detected,
            "chatbot_detected": lead.chatbot_detected,
            "whatsapp_detected": lead.whatsapp_detected,
            "crm_detected": lead.crm_detected,
            "product_count": lead.product_count,
            "founder_name": enrichment.founder_name or lead.founder_name or "",
            "owner_name": lead.owner_name,
            "email": enrichment.support_email or enrichment.founder_email or enrichment.general_email or lead.email or "",
            "phone": enrichment.business_phone or lead.phone or "",
            "linkedin_url": lead.linkedin_url,
            "social_links": lead.social_links or {},
            "comai_score": lead.comai_score,
        }

        account = build_account(lead_data, scrape_website=False)

        # Override with enriched data
        if enrichment.founder_name:
            account.primary_decision_maker = enrichment.founder_name
        if enrichment.founder_email:
            account.primary_email = enrichment.founder_email
        elif enrichment.support_email:
            account.primary_email = enrichment.support_email
        elif enrichment.general_email:
            account.primary_email = enrichment.general_email
        if enrichment.business_phone:
            account.primary_phone = enrichment.business_phone
        if enrichment.linkedin_urls:
            account.primary_linkedin = enrichment.linkedin_urls[0]

        # Determine status
        has_contact = bool(enrichment.founder_name and (enrichment.founder_email or enrichment.business_phone))
        status = "SALES_READY" if has_contact else account.status

        # Build store data
        from packages.sales_intelligence_platform.engines.web_scraper import WebScraper
        def deep_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: deep_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [deep_to_dict(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: deep_to_dict(v) for k, v in obj.items()}
            return obj

        store_data = {
            "ecommerce_lead_id": str(lead.id),
            "company_name": account.company_name,
            "website": account.website,
            "domain": account.domain,
            "platform": account.platform,
            "category": account.category,
            "country": account.country,
            "city": account.city,
            "state": account.state,
            "status": status,
            "primary_decision_maker": account.primary_decision_maker,
            "primary_email": account.primary_email,
            "primary_phone": account.primary_phone,
            "primary_linkedin": account.primary_linkedin,
            "shopify_detected": account.shopify_detected,
            "woocommerce_detected": account.woocommerce_detected,
            "chatbot_detected": account.chatbot_detected,
            "whatsapp_detected": account.whatsapp_detected,
            "crm_detected": account.crm_detected,
            "pain_score": account.pain_score,
            "growth_score": account.growth_score,
            "buying_intent": account.buying_intent,
            "probability_to_buy": account.probability_to_buy,
            "revenue_potential": account.revenue_potential,
            "account_score": account.score.total,
            "completeness_pct": account.health.completeness_pct,
            "decision_makers_json": [{"name": dm.name, "role": dm.normalized_role, "email": dm.work_email, "phone": dm.business_phone, "confidence": dm.confidence} for dm in account.decision_makers],
            "contact_channels_json": [{"kind": "email", "value": e.value, "label": e.label, "confidence": e.confidence} for e in enrichment.emails[:5]] + [{"kind": "phone", "value": p.value, "label": "business", "confidence": p.confidence} for p in enrichment.phones[:3]],
            "buying_committee_json": deep_to_dict(account.buying_committee),
            "evidence_json": [deep_to_dict(ev) for ev in account.evidence_records],
            "health_json": deep_to_dict(account.health),
            "score_json": deep_to_dict(account.score),
            "organization_json": {},
            "technology_profile_json": deep_to_dict(account.technology_profile),
            "pain_analysis_json": {
                "pain_points": [deep_to_dict(p) for p in account.pain_analysis.pain_points],
                "total_pain_score": account.pain_analysis.total_pain_score,
                "top_pain": account.pain_analysis.top_pain,
                "recommended_module": account.pain_analysis.recommended_module,
                "business_value": account.pain_analysis.business_value,
            },
            "opportunity_score_json": {
                "total_score": account.opportunity_score.total_score,
                "classification": account.opportunity_score.classification,
                "confidence": account.opportunity_score.confidence,
                "score_breakdown": account.opportunity_score.score_breakdown,
            },
            "sales_summary_json": deep_to_dict(account.sales_summary),
            "call_preparation_json": deep_to_dict(account.call_preparation),
            "website_data_json": {},
        }

        await account_repo.upsert_by_domain(store_data)
        await session.commit()

        # Track stats
        email = enrichment.founder_email or enrichment.support_email or enrichment.general_email
        phone = enrichment.business_phone
        dm = enrichment.founder_name

        if email:
            stats["with_email"] += 1
        if phone:
            stats["with_phone"] += 1
        if dm:
            stats["with_dm"] += 1
        if status == "SALES_READY":
            stats["sales_ready"] += 1

        stats["processed"] += 1
        logger.info(f"  OK {company}: email={email or '-'} phone={phone or '-'} dm={dm or '-'} opp={account.opportunity_score.total_score}")

    except Exception as e:
        stats["errors"] += 1
        logger.error(f"  FAIL {company}: {e}")


async def enrich_all(incomplete_only=False):
    async with AsyncSessionLocal() as session:
        account_repo = SalesAccountRepository(session)
        lead_repo = EcommerceLeadRepository(session)

        leads, total = await lead_repo.list_with_filters(limit=500, offset=0)

        if incomplete_only:
            # Filter to only leads missing email, phone, or decision maker
            incomplete = []
            for lead in leads:
                # Check existing account data
                existing = await account_repo.get_by_domain(lead.domain)
                if existing and existing.primary_email and existing.primary_phone and existing.primary_decision_maker:
                    continue  # Already complete
                incomplete.append(lead)
            leads = incomplete
            logger.info(f"Filtered to {len(leads)} incomplete leads (of {total} total)")
        else:
            logger.info(f"Enriching {total} leads (batch={BATCH_SIZE})")

        enricher = RealContactEnricher(timeout=8, delay=1.5, max_concurrent=1)

        stats = {
            "processed": 0, "errors": 0,
            "with_email": 0, "with_phone": 0, "with_dm": 0, "sales_ready": 0,
        }

        start = time.time()

        # Process in batches
        for i in range(0, len(leads), BATCH_SIZE):
            batch = leads[i:i + BATCH_SIZE]
            tasks = [
                enrich_one_lead(lead, enricher, account_repo, session, stats)
                for lead in batch
            ]
            await asyncio.gather(*tasks)
            elapsed = time.time() - start
            rate = stats["processed"] / elapsed if elapsed > 0 else 0
            eta = (total - stats["processed"]) / rate if rate > 0 else 0
            logger.info(f"  Progress: {stats['processed']}/{total} ({rate:.1f}/s, ETA {eta:.0f}s)")

        elapsed = time.time() - start
        print(f"\n{'='*80}")
        print(f"ENRICHMENT COMPLETE in {elapsed:.0f}s")
        print(f"{'='*80}")
        print(f"Processed: {stats['processed']}/{total}")
        print(f"Errors: {stats['errors']}")
        print(f"With Email: {stats['with_email']}/{stats['processed']}")
        print(f"With Phone: {stats['with_phone']}/{stats['processed']}")
        print(f"With Decision Maker: {stats['with_dm']}/{stats['processed']}")
        print(f"Sales Ready: {stats['sales_ready']}/{stats['processed']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich all leads with contact data")
    parser.add_argument("--incomplete-only", action="store_true", help="Only enrich leads missing email/phone/DM")
    args = parser.parse_args()
    asyncio.run(enrich_all(incomplete_only=args.incomplete_only))
