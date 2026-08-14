"""Lead pipeline orchestrator for ecommerce leads."""

from __future__ import annotations

import logging
from typing import Any

from packages.ecommerce_leads.collectors.shopify_collector import ShopifyCollector
from packages.ecommerce_leads.collectors.web_collector import WebCollector
from packages.ecommerce_leads.collectors.social_collector import SocialCollector
from packages.ecommerce_leads.enrichment.company_enrichment import CompanyEnricher
from packages.ecommerce_leads.enrichment.contact_enrichment import ContactEnricher
from packages.ecommerce_leads.enrichment.technology_enrichment import TechnologyEnricher
from packages.ecommerce_leads.models import EnrichedEcommerceLead, RawEcommerceLead
from packages.ecommerce_leads.scoring.ecommerce_score import EcommerceScorer
from packages.ecommerce_leads.scoring.quality_gate import QualityGate
from packages.ecommerce_leads.scoring.sales_intelligence import SalesIntelligenceGenerator

logger = logging.getLogger(__name__)


class LeadPipeline:
    """Orchestrate the full lead discovery, enrichment, and scoring pipeline."""

    def __init__(self) -> None:
        self.shopify_collector = ShopifyCollector()
        self.web_collector = WebCollector()
        self.social_collector = SocialCollector()
        self.company_enricher = CompanyEnricher()
        self.contact_enricher = ContactEnricher()
        self.technology_enricher = TechnologyEnricher()
        self.scorer = EcommerceScorer()
        self.quality_gate = QualityGate()
        self.sales_intel = SalesIntelligenceGenerator()

    async def run_discovery(
        self,
        *,
        limit: int = 500,
        country: str = "India",
    ) -> list[dict[str, Any]]:
        """Run the full discovery pipeline and return scored leads."""
        logger.info("Starting ecommerce lead discovery (limit=%d, country=%s)", limit, country)

        raw_leads = await self._collect_raw_leads(limit=limit)
        logger.info("Collected %d raw leads", len(raw_leads))

        if not raw_leads:
            logger.info("No leads from collectors, using seed data")
            raw_leads = self._get_seed_leads(limit=limit)
            logger.info("Loaded %d seed leads", len(raw_leads))

        enriched = await self._enrich_leads(raw_leads)
        logger.info("Enriched %d leads", len(enriched))

        scored = self._score_leads(enriched)
        logger.info("Scored %d leads", len(scored))

        # Apply quality gate
        gated = self._apply_quality_gate(scored)
        logger.info("Quality gate applied: %d passed, %d failed",
                     sum(1 for l in gated if l.quality_gate_passed),
                     sum(1 for l in gated if not l.quality_gate_passed))

        # Generate sales intelligence
        with_intel = self._generate_sales_intelligence(gated)
        logger.info("Sales intelligence generated for %d leads", len(with_intel))

        results = self._to_dicts(with_intel)
        return results

    async def _collect_raw_leads(self, limit: int) -> list[RawEcommerceLead]:
        """Collect raw leads from all sources."""
        all_leads: list[RawEcommerceLead] = []
        seen_domains: set[str] = set()

        try:
            async for lead in self.shopify_collector.collect_shopify_directories(limit=limit):
                if lead.domain not in seen_domains:
                    seen_domains.add(lead.domain)
                    all_leads.append(lead)
        except Exception as e:
            logger.error("Shopify collection failed: %s", e, exc_info=True)

        remaining = limit - len(all_leads)
        if remaining > 0:
            try:
                async for lead in self.web_collector.collect_uknown_shopify_stores(limit=remaining):
                    if lead.domain not in seen_domains:
                        seen_domains.add(lead.domain)
                        all_leads.append(lead)
            except Exception as e:
                logger.error("Web collection failed: %s", e, exc_info=True)

        remaining = limit - len(all_leads)
        if remaining > 0:
            try:
                async for lead in self.web_collector.collect_from_lists(limit=remaining):
                    if lead.domain not in seen_domains:
                        seen_domains.add(lead.domain)
                        all_leads.append(lead)
            except Exception as e:
                logger.error("List collection failed: %s", e, exc_info=True)

        remaining = limit - len(all_leads)
        if remaining > 0:
            try:
                async for lead in self.web_collector.collect_from_search(limit=remaining):
                    if lead.domain not in seen_domains:
                        seen_domains.add(lead.domain)
                        all_leads.append(lead)
            except Exception as e:
                logger.error("Search collection failed: %s", e, exc_info=True)

        return all_leads[:limit]

    async def _enrich_leads(
        self, raw_leads: list[RawEcommerceLead]
    ) -> list[EnrichedEcommerceLead]:
        """Enrich all raw leads."""
        enriched: list[EnrichedEcommerceLead] = []
        for raw in raw_leads:
            try:
                lead = EnrichedEcommerceLead(raw=raw)
                lead = await self.technology_enricher.enrich(lead)
                lead = await self.company_enricher.enrich(lead)
                lead = await self.contact_enricher.enrich(lead)

                social = await self.social_collector.enrich_social_links(raw.website)
                lead.raw.social_links.update(social)
                lead.instagram_url = social.get("instagram", "")
                lead.facebook_url = social.get("facebook", "")
                lead.linkedin_url = social.get("linkedin", "")

                enriched.append(lead)
            except Exception as e:
                logger.debug("Enrichment failed for %s: %s", raw.website, e)
                enriched.append(EnrichedEcommerceLead(raw=raw))

        return enriched

    def _score_leads(
        self, leads: list[EnrichedEcommerceLead]
    ) -> list[EnrichedEcommerceLead]:
        """Score all enriched leads."""
        return [self.scorer.score(lead) for lead in leads]

    def _apply_quality_gate(
        self, leads: list[EnrichedEcommerceLead]
    ) -> list[EnrichedEcommerceLead]:
        """Apply quality gate to all scored leads."""
        return [self.quality_gate.evaluate(lead) for lead in leads]

    def _generate_sales_intelligence(
        self, leads: list[EnrichedEcommerceLead]
    ) -> list[EnrichedEcommerceLead]:
        """Generate sales intelligence for all leads."""
        return [self.sales_intel.generate(lead) for lead in leads]

    def _to_dicts(
        self, leads: list[EnrichedEcommerceLead]
    ) -> list[dict[str, Any]]:
        """Convert enriched leads to dictionaries for storage."""
        results: list[dict[str, Any]] = []
        for lead in leads:
            d = {
                "company_name": lead.raw.company_name,
                "website": lead.raw.website,
                "domain": lead.raw.domain,
                "platform": lead.raw.platform,
                "industry": lead.raw.industry,
                "category": lead.raw.category,
                "country": lead.raw.country,
                "city": lead.raw.city,
                "state": lead.raw.state,
                "description": lead.raw.description,
                "product_count": lead.raw.product_count,
                "estimated_size": lead.estimated_size,
                "social_links": lead.raw.social_links,
                "instagram_url": lead.instagram_url,
                "facebook_url": lead.facebook_url,
                "linkedin_url": lead.linkedin_url,
                "owner_name": lead.owner_name,
                "founder_name": lead.founder_name,
                "decision_maker_role": lead.decision_maker_role,
                "email": lead.email,
                "phone": lead.phone,
                "contact_source": lead.contact_source,
                "contact_confidence": lead.contact_confidence,
                "shopify_detected": lead.shopify_detected,
                "woocommerce_detected": lead.woocommerce_detected,
                "magento_detected": lead.magento_detected,
                "chatbot_detected": lead.chatbot_detected,
                "whatsapp_detected": lead.whatsapp_detected,
                "crm_detected": lead.crm_detected,
                "comai_score": lead.comai_score,
                "lead_priority": lead.lead_priority,
                "sales_reason": lead.sales_reason,
                "pain_points": lead.pain_points,
                "source": lead.raw.source,
                # Sales intelligence fields
                "call_opener": lead.call_opener,
                "pitch_angle": lead.pitch_angle,
                "recommended_feature": lead.recommended_feature,
                "opportunity_summary": lead.opportunity_summary,
                "confidence_score": lead.confidence_score,
                "quality_gate_passed": lead.quality_gate_passed,
            }
            results.append(d)
        return results

    def _get_seed_leads(self, limit: int) -> list[RawEcommerceLead]:
        """Return curated seed data of known Indian D2C/ecommerce brands."""
        seed_data = [
            ("mamaearth.in", "Mamaearth", "beauty", "Mumbai", "Maharashtra", "Mamaearth is an Indian D2C beauty brand offering natural personal care products.", 500),
            ("beardo.in", "Beardo", "grooming", "Mumbai", "Maharashtra", "Beardo is an Indian men's grooming brand selling beard care, hair care, and skincare products.", 200),
            ("mcaffeine.com", "mCaffeine", "skincare", "Mumbai", "Maharashtra", "mCaffeine is India's first caffeinated personal care brand for millennials.", 300),
            ("sugarcosmetics.com", "Sugar Cosmetics", "cosmetics", "Mumbai", "Maharashtra", "Sugar Cosmetics is a premium Indian makeup brand with 10,000+ retail touchpoints.", 500),
            ("nykaa.com", "Nykaa", "beauty marketplace", "Mumbai", "Maharashtra", "Nykaa is India's leading beauty and wellness e-commerce platform.", 1000),
            ("purplle.com", "Purplle", "beauty marketplace", "Mumbai", "Maharashtra", "Purplle is India's second largest online beauty destination.", 800),
            ("boat-lifestyle.com", "boAt", "electronics", "New Delhi", "Delhi", "boAt is India's #1 audio and wearables brand with 8M+ products sold.", 500),
            ("noise.tech", "Noise", "electronics", "Gurugram", "Haryana", "Noise is India's leading connected lifestyle brand for smartwatches and audio.", 400),
            ("fireboltt.com", "Fire-Boltt", "electronics", "New Delhi", "Delhi", "Fire-Boltt is India's fastest growing smartwatch and audio brand.", 350),
            ("thesouledstore.com", "The Souled Store", "fashion", "Mumbai", "Maharashtra", "The Souled Store is India's largest pop-culture fashion brand.", 400),
            ("bewakoof.com", "Bewakoof", "fashion", "Mumbai", "Maharashtra", "Bewakoof is India's leading D2C fashion brand for youth.", 500),
            ("snitch.co.in", "Snitch", "fashion", "Bangalore", "Karnataka", "Snitch is a fast-growing Indian menswear D2C brand.", 300),
            ("pepperfry.com", "Pepperfry", "furniture", "Mumbai", "Maharashtra", "Pepperfry is India's largest online furniture and home decor marketplace.", 800),
            ("urbanladder.com", "Urban Ladder", "furniture", "Bangalore", "Karnataka", "Urban Ladder is a premium Indian online furniture brand.", 500),
            ("fabindia.com", "Fabindia", "lifestyle", "New Delhi", "Delhi", "Fabindia is India's largest private platform for products made from traditional techniques.", 600),
            ("firstcry.com", "FirstCry", "kids", "Pune", "Maharashtra", "FirstCry is Asia's largest online store for kids and baby products.", 1000),
            ("plumgoodness.com", "Plum Goodness", "beauty", "Mumbai", "Maharashtra", "Plum Goodness is a 100% vegan and cruelty-free Indian beauty brand.", 250),
            ("wowskinscience.com", "WOW Skin Science", "skincare", "Bangalore", "Karnataka", "WOW Skin Science is an Indian D2C personal care brand.", 300),
            ("bombayshavingcompany.com", "Bombay Shaving Company", "grooming", "New Delhi", "Delhi", "Bombay Shaving Company is an Indian men's grooming D2C brand.", 200),
            ("theomancompany.com", "The Man Company", "grooming", "Ahmedabad", "Gujarat", "The Man Company is an Indian men's grooming and personal care brand.", 200),
            ("juicychemistry.com", "Juicy Chemistry", "organic beauty", "Coimbatore", "Tamil Nadu", "Juicy Chemistry is an Indian organic and natural skincare brand.", 150),
            ("pilgrim.in", "Pilgrim", "skincare", "Mumbai", "Maharashtra", "Pilgrim is an Indian skincare brand inspired by global beauty secrets.", 200),
            ("dermaco.in", "Derma Co", "skincare", "New Delhi", "Delhi", "Derma Co is an Indian derma-cosmetics brand by Mamaearth parent.", 250),
            ("craftsvilla.com", "CraftsVilla", "handicrafts", "Mumbai", "Maharashtra", "CraftsVilla is an Indian ethnic handicrafts and handlooms marketplace.", 300),
            ("jaypore.com", "Jaypore", "lifestyle", "New Delhi", "Delhi", "Jaypore is an Indian online lifestyle and home decor brand.", 200),
            ("nicobar.com", "Nicobar", "lifestyle", "Mumbai", "Maharashtra", "Nicobar is a modern Indian lifestyle brand for travel and home.", 150),
            ("okhai.org", "Okhai", "handicrafts", "Ahmedabad", "Gujarat", "Okhai is a handcrafted lifestyle brand empowering rural artisans.", 100),
            ("hopscotch.in", "Hopscotch", "kids", "Mumbai", "Maharashtra", "Hopscotch is India's leading online store for kids' fashion.", 250),
            ("roastea.com", "Roastea", "tea/coffee", "Ahmedabad", "Gujarat", "Roastea is an Indian premium tea and coffee D2C brand.", 100),
            ("minimalist.ind.in", "Minimalist", "skincare", "New Delhi", "Delhi", "Minimalist is an Indian skincare brand focused on active ingredients.", 300),
            ("dotkey.in", "Dot Key", "skincare", "Mumbai", "Maharashtra", "Dot Key is an Indian skincare brand with clean beauty formulations.", 150),
            ("chemistatplay.com", "Chemist at Play", "skincare", "Mumbai", "Maharashtra", "Chemist at Play is an Indian dermat-recommended skincare brand.", 150),
            ("khadinatural.com", "Khadi Natural", "natural products", "Ahmedabad", "Gujarat", "Khadi Natural is an Indian natural personal care brand.", 200),
            ("lakmeindia.com", "Lakme", "beauty", "Mumbai", "Maharashtra", "Lakme is India's leading beauty brand by Unilever.", 500),
            ("forestessentialsindia.com", "Forest Essentials", "luxury beauty", "New Delhi", "Delhi", "Forest Essentials is an Indian luxury Ayurvedic beauty brand.", 300),
            ("berrylush.com", "Berrylush", "fashion", "New Delhi", "Delhi", "Berrylush is an Indian women's western wear D2C brand.", 200),
            ("libas.in", "Libas", "fashion", "New Delhi", "Delhi", "Libas is an Indian ethnic wear brand for women.", 200),
            ("addresshome.com", "Address Home", "home decor", "New Delhi", "Delhi", "Address Home is an Indian premium home decor and lifestyle brand.", 150),
            ("homecentre.com", "Home Centre", "home decor", "Dubai", "", "Home Centre is a leading home furnishing retailer with strong India presence.", 400),
            ("godrejinterio.com", "Godrej Interio", "furniture", "Mumbai", "Maharashtra", "Godrej Interio is India's largest furniture brand by Godrej.", 600),
            ("hamleys.com", "Hamleys", "toys", "Mumbai", "Maharashtra", "Hamleys is the world's oldest and largest toy retailer with India ops.", 300),
            ("zeptonow.com", "Zepto", "quick commerce", "Mumbai", "Maharashtra", "Zepto is India's leading quick commerce delivery platform.", 500),
            ("blinkit.com", "Blinkit", "quick commerce", "Gurugram", "Haryana", "Blinkit (formerly Grofers) is Zomato's quick commerce platform.", 500),
            ("dmart.in", "DMart", "retail", "Mumbai", "Maharashtra", "DMart is Avenue Supermarts' retail chain, India's largest discount retailer.", 800),
            ("tatacliq.com", "Tata CLiQ", "marketplace", "Mumbai", "Maharashtra", "Tata CLiQ is Tata Group's premium lifestyle e-commerce platform.", 500),
            ("reliancedigital.in", "Reliance Digital", "electronics", "Mumbai", "Maharashtra", "Reliance Digital is India's largest electronics retail chain.", 600),
            ("croma.com", "Croma", "electronics", "Mumbai", "Maharashtra", "Croma is Tata's consumer electronics retail chain.", 500),
            ("vijaysales.com", "Vijay Sales", "electronics", "Mumbai", "Maharashtra", "Vijay Sales is one of India's largest consumer electronics retail chains.", 400),
            ("syska.com", "Syska", "electronics", "Pune", "Maharashtra", "Syska is an Indian LED lighting and personal care electronics brand.", 200),
            ("ambraneindia.com", "Ambrane", "electronics", "New Delhi", "Delhi", "Ambrane is an Indian consumer electronics brand for power banks and accessories.", 150),
            ("ptron.com", "pTron", "electronics", "Hyderabad", "Telangana", "pTron is an Indian budget audio and mobile accessories brand.", 200),
        ]

        leads = []
        for domain, name, category, city, state, desc, products in seed_data[:limit]:
            lead = RawEcommerceLead(
                company_name=name,
                website=f"https://{domain}",
                domain=domain,
                platform="shopify",
                industry="ecommerce",
                category=category,
                country="India",
                city=city,
                state=state,
                description=desc,
                product_count=products,
                source="seed_data",
            )
            leads.append(lead)
        return leads
