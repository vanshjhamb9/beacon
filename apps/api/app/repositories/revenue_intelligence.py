from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revenue_intelligence import RevenueIntelligenceRow
from app.repositories.base import BaseRepository


class RevenueIntelligenceRepository(BaseRepository[RevenueIntelligenceRow]):
    model = RevenueIntelligenceRow

    async def get_by_domain(self, domain: str) -> RevenueIntelligenceRow | None:
        query = self._base_query().where(self.model.domain == domain)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_lead_id(self, lead_id: str) -> RevenueIntelligenceRow | None:
        query = self._base_query().where(self.model.ecommerce_lead_id == lead_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        priority: str | None = None,
        icp_match: bool | None = None,
        min_probability: float | None = None,
        platform: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[RevenueIntelligenceRow], int]:
        query = self._base_query()
        count_query = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )

        if priority:
            query = query.where(self.model.priority == priority)
            count_query = count_query.where(self.model.priority == priority)
        if icp_match is not None:
            query = query.where(self.model.icp_match == icp_match)
            count_query = count_query.where(self.model.icp_match == icp_match)
        if min_probability is not None:
            query = query.where(self.model.probability_to_buy >= min_probability)
            count_query = count_query.where(self.model.probability_to_buy >= min_probability)
        if platform:
            query = query.where(self.model.platform == platform)
            count_query = count_query.where(self.model.platform == platform)
        if category:
            query = query.where(self.model.category == category)
            count_query = count_query.where(self.model.category == category)

        total = (await self.session.execute(count_query)).scalar_one()
        query = query.order_by(self.model.probability_to_buy.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all(), total

    async def upsert_by_domain(self, data: dict[str, Any]) -> RevenueIntelligenceRow:
        existing = await self.get_by_domain(data["domain"])
        if existing:
            return await self.update(existing, data)
        return await self.create(data)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        total_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        total = (await self.session.execute(total_q)).scalar_one()

        hot_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.priority == "HOT"
        )
        hot = (await self.session.execute(hot_q)).scalar_one()

        warm_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.priority == "WARM"
        )
        warm = (await self.session.execute(warm_q)).scalar_one()

        low_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.priority == "LOW"
        )
        low = (await self.session.execute(low_q)).scalar_one()

        reject_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.priority == "REJECT"
        )
        rejected = (await self.session.execute(reject_q)).scalar_one()

        avg_prob_q = select(func.avg(self.model.probability_to_buy)).select_from(
            self.model
        ).where(self.model.deleted_at.is_(None))
        avg_prob = (await self.session.execute(avg_prob_q)).scalar_one() or 0.0

        avg_pain_q = select(func.avg(self.model.pain_score)).select_from(
            self.model
        ).where(self.model.deleted_at.is_(None))
        avg_pain = (await self.session.execute(avg_pain_q)).scalar_one() or 0.0

        platform_q = (
            select(self.model.platform, func.count())
            .where(self.model.deleted_at.is_(None))
            .group_by(self.model.platform)
        )
        platforms = {r[0]: r[1] for r in (await self.session.execute(platform_q)).all()}

        category_q = (
            select(self.model.category, func.count())
            .where(self.model.deleted_at.is_(None))
            .group_by(self.model.category)
        )
        categories = {r[0]: r[1] for r in (await self.session.execute(category_q)).all()}

        return {
            "total_analyzed": total,
            "hot_leads": hot,
            "warm_leads": warm,
            "low_leads": low,
            "rejected": rejected,
            "avg_probability": round(float(avg_prob), 1),
            "avg_pain_score": round(float(avg_pain), 1),
            "avg_growth_score": 0,
            "platforms": platforms,
            "categories": categories,
        }
