"""Seed minimal demo data for local operator dashboard testing."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.context import CompanyProfile
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.revenue import (
    DealEstimate,
    RecommendationHistory,
    RevenueBuyerPersona,
    SalesPlaybook,
    SolutionMatch,
)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Company).limit(1))
        if existing.scalar_one_or_none():
            print("demo data already present")
            return

        now = datetime.now(UTC)
        company = Company(
            id=uuid4(),
            name="Acme Logistics",
            normalized_name="acme logistics",
            primary_domain="acmelogistics.example",
            industry="logistics",
            last_seen_at=now,
            signal_frequency=12,
            memory_summary="Scaling logistics operator showing automation and support pressure.",
            attributes={"technology_stack": ["Salesforce", "OpenAI"]},
            created_at=now,
            updated_at=now,
        )
        session.add(company)
        await session.flush()

        session.add(
            CompanyProfile(
                id=uuid4(),
                company_id=company.id,
                industry="logistics",
                business_model="b2b",
                company_stage="scaling",
                growth_pattern="expansion",
                technology_stack=["Salesforce", "OpenAI"],
                digital_maturity=72.0,
                ai_adoption=68.0,
                automation_adoption=74.0,
                hiring_pattern="active",
                expansion_pattern="regional",
                innovation_score=70.0,
                support_maturity=55.0,
                operational_maturity=60.0,
                technology_maturity=72.0,
                customer_maturity=65.0,
                completeness_score=78.0,
                evidence={"seed": True},
                created_at=now,
                updated_at=now,
            )
        )

        opportunity = Opportunity(
            id=uuid4(),
            company_id=company.id,
            company_name=company.name,
            status="high_intent",
            recommendation="contact_within_7_days",
            opportunity_score=84.0,
            confidence_score=81.0,
            timing_score=78.0,
            urgency_score=76.0,
            narrative="Acme Logistics shows rising automation demand after expansion signals.",
            created_from_context_ids=[],
            score_breakdown={},
            delta={
                "direction": "increased",
                "score_change": 12.0,
                "reason": "New automation pain + expansion",
            },
            created_at=now,
            updated_at=now,
        )
        session.add(opportunity)
        await session.flush()

        match = SolutionMatch(
            id=uuid4(),
            company_id=company.id,
            opportunity_id=opportunity.id,
            primary_service_key="ai_automation",
            secondary_service_key="api_integration",
            cross_sell_service_keys=["custom_ai_development"],
            upsell_service_keys=["comai"],
            confidence=79.5,
            reasoning=(
                "AI Automation is the strongest deterministic service match for Acme Logistics "
                "based on operations pain and opportunity score."
            ),
            evidence={
                "opportunity_score": 84.0,
                "quality_score": 88.0,
                "why_now": "contact_within_7_days",
            },
            created_at=now,
            updated_at=now,
        )
        session.add(match)
        await session.flush()

        session.add(
            RevenueBuyerPersona(
                id=uuid4(),
                company_id=company.id,
                solution_match_id=match.id,
                persona="Operations Head",
                confidence=82.0,
                explanation="Workflow and operations pains map to Operations Head ownership.",
                evidence={},
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            DealEstimate(
                id=uuid4(),
                solution_match_id=match.id,
                company_id=company.id,
                opportunity_id=opportunity.id,
                project_size="medium",
                implementation_complexity="medium",
                estimated_budget_range="medium",
                priority_level="high",
                mrr_potential=1800.0,
                one_time_revenue=22000.0,
                expansion_potential=9000.0,
                renewal_potential=15000.0,
                strategic_account_value=46000.0,
                revenue_score=46.0,
                urgency=76.0,
                closing_probability=62.0,
                strategic_importance=80.0,
                expected_sales_cycle_days=45,
                explanation="Seeded demo estimate",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            SalesPlaybook(
                id=uuid4(),
                company_id=company.id,
                opportunity_id=opportunity.id,
                solution_match_id=match.id,
                business_pain="automation: manual ops workflows",
                recommended_service="AI Automation",
                why="Opportunity score and operations pain make AI Automation the best fit now.",
                conversation_angle="Validate whether manual ops workflows are a priority this quarter.",
                decision_maker="Operations Head",
                expected_outcome="Deliver a medium engagement that reduces ops friction.",
                risk="Budget ownership may be unclear; confirm decision maker early.",
                playbook={},
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            RecommendationHistory(
                id=uuid4(),
                solution_match_id=match.id,
                recommendation_type="revenue_recommendation",
                recommendation={"seed": True},
                evidence={},
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
        print(f"seeded company={company.id} opportunity={opportunity.id}")


if __name__ == "__main__":
    asyncio.run(main())
