"""Lead Discovery Service - Buyer-first pipeline for COMAI and Inowix departments.

CRITICAL RULES:
1. Only companies with VERIFIED buying events enter the sales pipeline
2. Company existence, funding, hiring alone is NOT a buying event
3. Must have evidence of problem, intent, evaluation, or partnership opportunity
4. Every opportunity MUST be classified: DIRECT_CUSTOMER, PARTNER_OPPORTUNITY, or NOT_A_BUYING_EVENT
5. Never pitch an agency as a direct customer
6. Zero is acceptable - no fabrication
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.founder_sales_workspace import LeadStage

logger = logging.getLogger(__name__)

# COMAI ICP
COMAI_ICP = {
    "department": "COMAI",
    "industries": [
        "fashion", "beauty", "skincare", "cosmetics", "jewellery", "home decor",
        "pets", "health", "supplements", "food", "beverage", "footwear",
        "electronics accessories", "baby products", "grooming", "personal care",
        "lifestyle", "organic", "natural", "wellness", "D2C", "ecommerce",
    ],
    "platforms": ["shopify", "woocommerce", "magento"],
    "countries": ["IN"],
    "cities": [
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune",
        "Kolkata", "Ahmedabad", "Gurugram", "Coimbatore", "Kochi", "Jaipur",
    ],
    "employee_range": (5, 200),
    "revenue_range": (5_000_000, 150_000_000),
    "pain_signals": [
        "no chatbot", "no whatsapp automation", "manual customer support",
        "high support volume", "no crm", "no ai", "manual follow-ups",
    ],
    "services": [
        "COMAI -- AI Chatbot for Commerce",
        "COMAI -- WhatsApp AI Automation",
        "COMAI -- CRM Integration",
        "COMAI -- Workflow Automation",
        "COMAI -- Agency Partner Program",
    ],
}

# Inowix ICP
INOWIX_ICP = {
    "department": "Inowix",
    "industries": [
        "technology", "software", "SaaS", "fintech", "healthtech", "edtech",
        "ecommerce platform", "enterprise", "AI", "machine learning", "cloud",
        "developer tools", "API", "infrastructure", "cybersecurity", "data",
    ],
    "platforms": [],
    "countries": ["US", "UK", "CA", "DE", "AU", "SG", "IN"],
    "employee_range": (10, 10000),
    "revenue_range": (1_000_000, 1_000_000_000),
    "pain_signals": [
        "need mvp", "need developers", "technical cofounder", "build saas",
        "custom software", "mobile app", "backend api", "cloud infrastructure",
        "dedicated team", "cto support", "ai integration", "legacy modernization",
    ],
    "services": [
        "SaaS MVP Development",
        "Custom Software Development",
        "AI Agents & Automation",
        "Mobile App Development",
        "Website Development",
        "API Integration",
        "Cloud Infrastructure",
        "Dedicated Development Teams",
    ],
}


class LeadDiscoveryService:
    """Manages the sales pipeline with buyer-first principles.

    Only companies with verified buying events enter the pipeline.
    Zero is acceptable - no fabrication.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_lead_from_buying_event(
        self,
        buying_event: dict[str, Any],
    ) -> LeadStage | None:
        """Create a lead in the pipeline from a verified buying event.

        Args:
            buying_event: Verified buying event with evidence

        Returns:
            LeadStage if created, None if company already exists
        """
        now = datetime.now(UTC)
        company_name = buying_event.get("company_name")

        if not company_name:
            logger.warning("Buying event missing company_name, skipping")
            return None

        existing = (
            await self.session.execute(
                select(LeadStage.id).where(
                    LeadStage.deleted_at.is_(None),
                    LeadStage.company_name == company_name,
                )
            )
        ).scalar()

        if existing:
            logger.info(f"Company {company_name} already in pipeline, skipping")
            return None

        # Build metadata with new fields
        metadata = {
            "problem": buying_event.get("problem"),
            "why_now": buying_event.get("why_now"),
            "solution_match": buying_event.get("solution_match"),
            "opportunity_type": buying_event.get("opportunity_type", "DIRECT_CUSTOMER"),
            "outreach_reason": buying_event.get("outreach_reason"),
            "event_type": buying_event.get("event_type"),
            "evidence": buying_event.get("evidence", []),
        }

        # Build tags including opportunity type
        tags = buying_event.get("tags", [])
        opp_type = buying_event.get("opportunity_type", "DIRECT_CUSTOMER")
        if opp_type and opp_type not in tags:
            tags.append(opp_type)

        lead = LeadStage(
            id=uuid.uuid4(),
            stage="revenue_ready",
            company_name=company_name,
            industry=buying_event.get("industry"),
            country=buying_event.get("country"),
            service_match=buying_event.get("service_match"),
            trigger=buying_event.get("event_type"),
            why_now=buying_event.get("why_now", "Verified buying event detected"),
            revenue_opportunity_score=buying_event.get("confidence", 0),
            fit_score=buying_event.get("fit_score", 0),
            intent_score=buying_event.get("confidence", 0),
            tags=tags,
            buying_signals=buying_event.get("evidence", []),
            source_connector=buying_event.get("source", "buying_event"),
            metadata_json=metadata,
            created_at=now,
            updated_at=now,
        )

        self.session.add(lead)
        await self.session.flush()

        logger.info(
            f"Created lead: {company_name} | type={opp_type} | "
            f"service={buying_event.get('service_match')} | "
            f"problem={buying_event.get('problem', 'N/A')[:80]}"
        )
        return lead

    async def get_pipeline_stats(self) -> dict[str, Any]:
        """Get pipeline statistics by department from buying_events."""
        from app.models.buying_event import BuyingEvent, BuyingEventDepartment, BuyingEventClassification
        from sqlalchemy import select, func

        total = (
            await self.session.execute(
                select(func.count()).select_from(BuyingEvent)
            )
        ).scalar() or 0

        comai_count = (
            await self.session.execute(
                select(func.count()).select_from(BuyingEvent).where(
                    BuyingEvent.department == BuyingEventDepartment.COMAI
                )
            )
        ).scalar() or 0

        inowix_count = (
            await self.session.execute(
                select(func.count()).select_from(BuyingEvent).where(
                    BuyingEvent.department == BuyingEventDepartment.INOWIX
                )
            )
        ).scalar() or 0

        stage_counts = {}
        rows = (
            await self.session.execute(
                select(BuyingEvent.classification, func.count())
                .group_by(BuyingEvent.classification)
            )
        ).all()
        for classification, count in rows:
            stage_counts[classification.value if hasattr(classification, 'value') else str(classification)] = count

        return {
            "total": total,
            "comai": comai_count,
            "inowix": inowix_count,
            "by_stage": stage_counts,
        }
