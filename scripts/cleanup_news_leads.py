"""Soft-delete news/platform fake leads from earlier pipeline runs."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]

from collectors.freshness import NEWS_OR_PLATFORM_HOSTS  # noqa: E402


async def main() -> None:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.intelligence import Company

    removed = 0
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(Company).where(Company.deleted_at.is_(None)))).scalars().all()
        for company in rows:
            domain = (company.primary_domain or "").lower().removeprefix("www.")
            if domain in NEWS_OR_PLATFORM_HOSTS or any(domain.endswith("." + h) for h in NEWS_OR_PLATFORM_HOSTS):
                company.deleted_at = datetime.now(UTC)
                removed += 1
                print(f"removed {company.name} ({domain})")
        await session.commit()
    print(f"removed={removed}")


if __name__ == "__main__":
    asyncio.run(main())
