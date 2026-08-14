from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ecommerce_leads import EcommerceLeadRow
from app.repositories.base import BaseRepository


class EcommerceLeadRepository(BaseRepository[EcommerceLeadRow]):
    model = EcommerceLeadRow

    async def get_by_domain(self, domain: str) -> EcommerceLeadRow | None:
        query = self._base_query().where(self.model.domain == domain)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        country: str | None = None,
        state: str | None = None,
        category: str | None = None,
        platform: str | None = None,
        min_score: float | None = None,
        priority: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[EcommerceLeadRow], int]:
        query = self._base_query()
        count_query = select(func.count()).select_from(self.model).where(self.model.deleted_at.is_(None))

        if country:
            query = query.where(self.model.country == country)
            count_query = count_query.where(self.model.country == country)
        if state:
            query = query.where(self.model.state == state)
            count_query = count_query.where(self.model.state == state)
        if category:
            query = query.where(self.model.category == category)
            count_query = count_query.where(self.model.category == category)
        if platform:
            query = query.where(self.model.platform == platform)
            count_query = count_query.where(self.model.platform == platform)
        if min_score is not None:
            query = query.where(self.model.comai_score >= min_score)
            count_query = count_query.where(self.model.comai_score >= min_score)
        if priority:
            query = query.where(self.model.lead_priority == priority)
            count_query = count_query.where(self.model.lead_priority == priority)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(self.model.comai_score.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all(), total

    async def upsert_by_domain(self, data: dict[str, Any]) -> EcommerceLeadRow:
        existing = await self.get_by_domain(data["domain"])
        if existing:
            return await self.update(existing, data)
        return await self.create(data)

    async def get_stats(self) -> dict[str, Any]:
        total_q = select(func.count()).select_from(self.model).where(self.model.deleted_at.is_(None))
        total = (await self.session.execute(total_q)).scalar_one()

        hot_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.lead_priority == "HOT"
        )
        hot = (await self.session.execute(hot_q)).scalar_one()

        warm_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.lead_priority == "WARM"
        )
        warm = (await self.session.execute(warm_q)).scalar_one()

        low_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.lead_priority == "LOW"
        )
        low = (await self.session.execute(low_q)).scalar_one()

        avg_q = select(func.avg(self.model.comai_score)).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        avg_score = (await self.session.execute(avg_q)).scalar_one() or 0.0

        platform_q = (
            select(self.model.platform, func.count())
            .where(self.model.deleted_at.is_(None))
            .group_by(self.model.platform)
        )
        platforms = {row[0]: row[1] for row in (await self.session.execute(platform_q)).all()}

        category_q = (
            select(self.model.category, func.count())
            .where(self.model.deleted_at.is_(None))
            .group_by(self.model.category)
        )
        categories = {row[0]: row[1] for row in (await self.session.execute(category_q)).all()}

        return {
            "total_leads": total,
            "hot_leads": hot,
            "warm_leads": warm,
            "low_leads": low,
            "platforms": platforms,
            "categories": categories,
            "avg_score": round(float(avg_score), 1),
        }
