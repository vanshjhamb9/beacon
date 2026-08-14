"""Admit 30 YC companies without nested savepoints — smoke test."""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]


async def main() -> None:
    from sqlalchemy.orm.attributes import flag_modified

    from app.db.session import AsyncSessionLocal
    from app.models.intelligence import Company
    from app.services.identity_graph import IdentityGraphService
    from dataset_unlock.yc.collector import YCCompanyCollector
    from identity_graph.pipelines.engine import IdentityResolutionPipeline

    t0 = time.time()
    events = YCCompanyCollector(max_items=80).collect()
    print(f"collected {len(events)} in {time.time()-t0:.1f}s", flush=True)

    async with AsyncSessionLocal() as session:
        igf = IdentityResolutionPipeline()
        igf_service = IdentityGraphService(session)
        existing = await igf_service._existing_canonical()
        created = 0
        for i, ev in enumerate(events):
            meta = dict(ev.metadata or {})
            enriched = {
                "title": ev.title,
                "source": ev.source,
                "url": ev.url,
                "official_website": meta.get("official_website"),
                "homepage": meta.get("official_website"),
                "official_domain": meta.get("domain"),
                "domain": meta.get("domain"),
                "metadata": meta,
                "buying_signals": meta.get("buying_signals") or [],
                "description": meta.get("description"),
            }
            snap = igf.evaluate(enriched, existing=existing)
            if not (snap.admission.allow_create_company and snap.domain and snap.canonical):
                continue
            try:
                cid = await igf_service._upsert_company(snap)
                await session.flush()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                existing = await igf_service._existing_canonical()
                print(f"skip {ev.title}: {type(exc).__name__}", flush=True)
                continue
            if not cid:
                continue
            company = await session.get(Company, cid)
            if company:
                attrs = dict(company.attributes or {})
                attrs["source"] = "yc"
                attrs["buying_signals"] = meta.get("buying_signals") or []
                attrs["odu_unlocked_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                flag_modified(company, "attributes")
            existing.append(
                {
                    "id": str(cid),
                    "official_domain": snap.domain,
                    "trade_name": snap.canonical.trade_name,
                    "legal_name": snap.canonical.legal_name,
                    "aliases": snap.canonical.aliases,
                }
            )
            created += 1
            if created % 10 == 0:
                await session.commit()
                print(f"committed {created} @ {time.time()-t0:.1f}s", flush=True)
        await session.commit()
        print(f"done created={created} elapsed={time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
