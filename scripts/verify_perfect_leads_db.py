"""Verify persisted perfect/outbound leads."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]


async def main() -> None:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.intelligence import Company

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(Company)
                .where(Company.deleted_at.is_(None))
                .order_by(Company.last_seen_at.desc())
                .limit(30)
            )
        ).scalars().all()
        shown = 0
        for company in rows:
            attrs = company.attributes or {}
            if not (
                attrs.get("perfect_lead")
                or attrs.get("rrp_revenue_ready")
                or attrs.get("lead_quality_score")
            ):
                continue
            print(
                f"{company.name} | {company.primary_domain} | "
                f"LQS={attrs.get('lead_quality_score')} grade={attrs.get('lead_quality_grade')} "
                f"perfect={attrs.get('perfect_lead')} email={attrs.get('business_email')} "
                f"dm={attrs.get('decision_maker')}"
            )
            shown += 1
        print(f"shown={shown}")


if __name__ == "__main__":
    asyncio.run(main())
