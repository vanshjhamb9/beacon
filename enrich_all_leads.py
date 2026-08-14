"""Enrich all 51 leads with real contact data."""

import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.repositories.sales_account import SalesAccountRepository
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from packages.sales_intelligence_platform.engines.real_contact_enricher import RealContactEnricher
from packages.sales_intelligence_platform.engines.account_builder import build_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def enrich_all():
    async with AsyncSessionLocal() as session:
        account_repo = SalesAccountRepository(session)
        lead_repo = EcommerceLeadRepository(session)
        
        leads, total = await lead_repo.list_with_filters(limit=500, offset=0)
        logger.info(f"Enriching {total} leads with real contact data")
        
        enricher = RealContactEnricher(timeout=10, delay=1)
        
        processed = 0
        errors = 0
        results = []
        
        for lead in leads:
            try:
                logger.info(f"Enriching {lead.company_name} ({lead.domain})...")
                
                # Enrich contacts
                enrichment = await enricher.enrich(lead.domain, lead.company_name)
                
                # Build lead data with enriched contacts
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
                    # Enrichment data
                    "enrichment_emails": [{"email": e.value, "type": e.label, "confidence": e.confidence} for e in enrichment.emails[:10]],
                    "enrichment_phones": [{"phone": p.value, "confidence": p.confidence} for p in enrichment.phones[:5]],
                    "enrichment_decision_makers": [{"name": dm.name, "role": dm.role, "confidence": dm.confidence} for dm in enrichment.decision_makers[:3]],
                }
                
                # Build account
                account = build_account(lead_data, scrape_website=False)
                
                # Override with enriched data
                if enrichment.founder_name:
                    account.primary_decision_maker = enrichment.founder_name
                if enrichment.founder_email:
                    account.primary_email = enrichment.founder_email
                elif enrichment.support_email:
                    account.primary_email = enrichment.support_email
                if enrichment.business_phone:
                    account.primary_phone = enrichment.business_phone
                if enrichment.linkedin_urls:
                    account.primary_linkedin = enrichment.linkedin_urls[0]
                
                # Store
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
                    "status": "SALES_READY" if (enrichment.founder_name and (enrichment.founder_email or enrichment.business_phone)) else account.status,
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
                    "decision_makers_json": [{"name": dm.name, "role": dm.role, "email": dm.email, "phone": dm.phone, "confidence": dm.confidence} for dm in account.decision_makers],
                    "contact_channels_json": [{"kind": "email", "value": e.value, "label": e.label, "confidence": e.confidence} for e in enrichment.emails[:5]] + [{"kind": "phone", "value": p.value, "label": "business", "confidence": p.confidence} for p in enrichment.phones[:3]],
                    "buying_committee_json": account.buying_committee.__dict__,
                    "evidence_json": [ev.__dict__ for ev in account.evidence_records],
                    "health_json": account.health.__dict__,
                    "score_json": account.score.__dict__,
                    "organization_json": {},
                    "technology_profile_json": account.technology_profile.__dict__,
                    "pain_analysis_json": {
                        "pain_points": [p.__dict__ for p in account.pain_analysis.pain_points],
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
                    "sales_summary_json": account.sales_summary.__dict__,
                    "call_preparation_json": account.call_preparation.__dict__,
                    "website_data_json": {},
                }
                
                await account_repo.upsert_by_domain(store_data)
                await session.commit()
                processed += 1
                
                results.append({
                    "company": account.company_name,
                    "founder": enrichment.founder_name,
                    "email": enrichment.founder_email or enrichment.support_email,
                    "phone": enrichment.business_phone,
                    "email_count": len(enrichment.emails),
                    "phone_count": len(enrichment.phones),
                    "status": store_data["status"],
                    "score": account.opportunity_score.total_score,
                })
                
                logger.info(f"  OK: {account.company_name} | Founder: {enrichment.founder_name or 'N/A'} | Email: {enrichment.founder_email or enrichment.support_email or 'N/A'} | Phone: {enrichment.business_phone or 'N/A'}")
                    
            except Exception as e:
                errors += 1
                logger.error(f"  FAILED: {lead.domain}: {e}")
        
        # Summary
        print("\n" + "=" * 100)
        print("ENRICHMENT RESULTS")
        print("=" * 100)
        print(f"Processed: {processed}/{total}")
        print(f"Errors: {errors}")
        
        with_founder = sum(1 for r in results if r["founder"])
        with_email = sum(1 for r in results if r["email"])
        with_phone = sum(1 for r in results if r["phone"])
        sales_ready = sum(1 for r in results if r["status"] == "SALES_READY")
        
        print(f"\nWith Founder Name: {with_founder}/{processed}")
        print(f"With Email: {with_email}/{processed}")
        print(f"With Phone: {with_phone}/{processed}")
        print(f"Sales Ready: {sales_ready}/{processed}")
        
        print(f"\n{'Company':25s} | {'Founder':20s} | {'Email':30s} | {'Phone':15s} | {'Status'}")
        print("-" * 120)
        for r in sorted(results, key=lambda x: x["score"], reverse=True):
            print(f"{r['company']:25s} | {(r['founder'] or 'N/A'):20s} | {(r['email'] or 'N/A'):30s} | {(r['phone'] or 'N/A'):15s} | {r['status']}")

asyncio.run(enrich_all())
