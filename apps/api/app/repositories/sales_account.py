from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales_account import SalesAccountRow
from app.repositories.base import BaseRepository


class SalesAccountRepository(BaseRepository[SalesAccountRow]):
    model = SalesAccountRow

    async def get_by_domain(self, domain: str) -> SalesAccountRow | None:
        query = self._base_query().where(self.model.domain == domain)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_lead_id(self, lead_id: str) -> SalesAccountRow | None:
        query = self._base_query().where(self.model.ecommerce_lead_id == lead_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        status: str | None = None,
        platform: str | None = None,
        category: str | None = None,
        min_score: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[SalesAccountRow], int]:
        query = self._base_query()
        count_query = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )

        if status:
            query = query.where(self.model.status == status)
            count_query = count_query.where(self.model.status == status)
        if platform:
            query = query.where(self.model.platform == platform)
            count_query = count_query.where(self.model.platform == platform)
        if category:
            query = query.where(self.model.category == category)
            count_query = count_query.where(self.model.category == category)
        if min_score is not None:
            query = query.where(self.model.account_score >= min_score)
            count_query = count_query.where(self.model.account_score >= min_score)

        total = (await self.session.execute(count_query)).scalar_one()
        query = query.order_by(self.model.account_score.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all(), total

    async def upsert_by_domain(self, data: dict[str, Any]) -> SalesAccountRow:
        existing = await self.get_by_domain(data["domain"])
        if existing:
            return await self.update(existing, data)
        return await self.create(data)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        total_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        total = (await self.session.execute(total_q)).scalar_one()

        sales_ready_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.status == "SALES_READY"
        )
        sales_ready = (await self.session.execute(sales_ready_q)).scalar_one()

        needs_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.status == "NEEDS_ENRICHMENT"
        )
        needs = (await self.session.execute(needs_q)).scalar_one()

        review_q = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None), self.model.status == "MANUAL_REVIEW"
        )
        review = (await self.session.execute(review_q)).scalar_one()

        avg_q = select(func.avg(self.model.account_score)).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        avg_score = (await self.session.execute(avg_q)).scalar_one() or 0.0

        return {
            "total_accounts": total,
            "sales_ready": sales_ready,
            "needs_enrichment": needs,
            "manual_review": review,
            "avg_score": round(float(avg_score), 1),
        }
