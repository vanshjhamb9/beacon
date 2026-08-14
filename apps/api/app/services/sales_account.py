from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.models.ecommerce_leads import EcommerceLeadRow
from app.models.sales_account import SalesAccountRow
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.sales_account import SalesAccountRepository
from packages.sales_intelligence_platform.engines.account_builder import build_account
from packages.sales_intelligence_platform.engines.account_dashboard import (
    generate_dashboard_data,
)
from packages.sales_intelligence_platform.engines.account_export import export_accounts
from packages.sales_intelligence_platform.models import Account

logger = logging.getLogger(__name__)


class SalesAccountService:
    """Service layer for sales account operations."""

    def __init__(
        self,
        account_repo: SalesAccountRepository,
        lead_repo: EcommerceLeadRepository,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.account_repo = account_repo
        self.lead_repo = lead_repo
        self.settings = settings

    async def list_accounts(
        self,
        *,
        status: str | None = None,
        platform: str | None = None,
        category: str | None = None,
        min_score: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        accounts, total = await self.account_repo.list_with_filters(
            status=status,
            platform=platform,
            category=category,
            min_score=min_score,
            limit=limit,
            offset=offset,
        )
        return {
            "accounts": accounts,
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit,
        }

    async def get_account(self, account_id: UUID) -> SalesAccountRow | None:
        return await self.account_repo.get(account_id)

    async def get_account_contacts(self, account_id: UUID) -> dict | None:
        account = await self.account_repo.get(account_id)
        if not account:
            return None
        return {
            "contact_channels": account.contact_channels_json,
            "primary_email": account.primary_email,
            "primary_phone": account.primary_phone,
            "primary_linkedin": account.primary_linkedin,
        }

    async def get_account_committee(self, account_id: UUID) -> dict | None:
        account = await self.account_repo.get(account_id)
        if not account:
            return None
        return {"buying_committee": account.buying_committee_json}

    async def get_account_health(self, account_id: UUID) -> dict | None:
        account = await self.account_repo.get(account_id)
        if not account:
            return None
        return {"health": account.health_json}

    async def get_account_evidence(self, account_id: UUID) -> dict | None:
        account = await self.account_repo.get(account_id)
        if not account:
            return None
        return {"evidence": account.evidence_json}

    async def get_dashboard(self) -> dict[str, Any]:
        return await self.account_repo.get_dashboard_stats()

    async def refresh_account(self, lead_id: str) -> dict[str, Any]:
        """Refresh a single account from its ecommerce lead."""
        lead = await self.lead_repo.get(UUID(lead_id)) if len(lead_id) == 36 else None
        if not lead:
            # Try by domain
            lead = await self.lead_repo.get_by_domain(lead_id) if hasattr(self.lead_repo, 'get_by_domain') else None
        if not lead:
            return {"status": "error", "message": "Lead not found"}

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
            "founder_name": lead.founder_name,
            "owner_name": lead.owner_name,
            "email": lead.email,
            "phone": lead.phone,
            "linkedin_url": lead.linkedin_url,
            "social_links": lead.social_links or {},
            "comai_score": lead.comai_score,
        }

        account = build_account(lead_data)

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
            "status": account.status,
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
            "decision_makers_json": [dm.__dict__ for dm in account.decision_makers],
            "contact_channels_json": [cc.__dict__ for cc in account.contact_channels],
            "buying_committee_json": account.buying_committee.__dict__,
            "evidence_json": [ev.__dict__ for ev in account.evidence_records],
            "health_json": account.health.__dict__,
            "score_json": account.score.__dict__,
            "organization_json": {},
            # Sprint 39 fields
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
            "website_data_json": account.website_data,
        }

        await self.account_repo.upsert_by_domain(store_data)
        await self.account_repo.commit()

        return {"status": "completed", "account_id": account.id, "status_label": account.status}

    async def bulk_refresh(self, limit: int = 500) -> dict[str, Any]:
        """Refresh accounts for all ecommerce leads."""
        leads, total = await self.lead_repo.list_with_filters(limit=limit, offset=0) if hasattr(self.lead_repo, 'list_with_filters') else ([], 0)

        processed = 0
        for lead in leads:
            try:
                await self.refresh_account(str(lead.id))
                processed += 1
            except Exception as e:
                logger.debug("Failed to refresh %s: %s", lead.domain, e)

        return {
            "status": "completed",
            "processed": processed,
            "total_leads": total,
        }

    async def export_accounts(self, *, status: str | None = None) -> bytes:
        """Export accounts to Excel."""
        all_accounts: list[SalesAccountRow] = []
        offset = 0
        batch = 500

        while True:
            accounts, total = await self.account_repo.list_with_filters(
                status=status, limit=batch, offset=offset
            )
            all_accounts.extend(accounts)
            offset += batch
            if offset >= total or not accounts:
                break

        # Convert to Account objects for export
        account_objs = []
        for a in all_accounts:
            obj = Account(
                id=str(a.id),
                company_name=a.company_name,
                website=a.website,
                domain=a.domain,
                platform=a.platform,
                category=a.category,
                country=a.country,
                city=a.city,
                state=a.state,
                status=a.status,
                primary_decision_maker=a.primary_decision_maker,
                primary_email=a.primary_email,
                primary_phone=a.primary_phone,
                primary_linkedin=a.primary_linkedin,
                pain_score=a.pain_score,
                growth_score=a.growth_score,
                buying_intent=a.buying_intent,
                probability_to_buy=a.probability_to_buy,
                revenue_potential=a.revenue_potential,
            )
            obj.score.total = a.account_score
            obj.health.completeness_pct = a.completeness_pct
            # Load Sprint 39 data from JSONB
            if a.technology_profile_json:
                from packages.sales_intelligence_platform.engines.technology_detector import TechnologyProfile
                obj.technology_profile = TechnologyProfile(**a.technology_profile_json)
            if a.opportunity_score_json:
                from packages.sales_intelligence_platform.engines.comai_opportunity_score import OpportunityScore
                obj.opportunity_score = OpportunityScore(**a.opportunity_score_json)
            if a.sales_summary_json:
                from packages.sales_intelligence_platform.engines.sales_intel_summary import SalesIntelligenceSummary
                obj.sales_summary = SalesIntelligenceSummary(**a.sales_summary_json)
            if a.pain_analysis_json:
                from packages.sales_intelligence_platform.engines.pain_point_detector import PainAnalysis, PainPoint
                pain_data = a.pain_analysis_json
                pain_points = [PainPoint(**p) for p in pain_data.get("pain_points", [])]
                obj.pain_analysis = PainAnalysis(
                    pain_points=pain_points,
                    total_pain_score=pain_data.get("total_pain_score", 0),
                    top_pain=pain_data.get("top_pain", ""),
                    recommended_module=pain_data.get("recommended_module", ""),
                    business_value=pain_data.get("business_value", ""),
                )
            if a.call_preparation_json:
                from packages.sales_intelligence_platform.engines.call_preparation import CallPreparation
                obj.call_preparation = CallPreparation(**a.call_preparation_json)
            account_objs.append(obj)

        return export_accounts(account_objs)
