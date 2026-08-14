"""Seed FSW with Revenue Ready leads from the pipeline."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main():
    from app.db.session import AsyncSessionLocal
    from app.repositories.founder_sales_workspace import FSWRepository
    from app.services.founder_sales_workspace import FSWService
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        # Get existing companies from the pipeline
        result = await session.execute(text("""
            SELECT c.id, c.name, c.industry, c.attributes->>'source' as source,
                   c.attributes->>'lead_quality_score' as lqs,
                   c.attributes->>'lead_quality_grade' as grade
            FROM companies c
            WHERE c.deleted_at IS NULL
            ORDER BY c.created_at DESC
            LIMIT 50
        """))
        companies = result.fetchall()
        print(f"Found {len(companies)} companies in pipeline")

        # Get target accounts
        result2 = await session.execute(text("""
            SELECT ta.id, ta.company_name, ta.revenue_opportunity_score, ta.fit_score,
                   ta.intent_score, ta.matched_icp_name, ta.service_match, ta.why_now,
                   ta.buying_signals
            FROM target_accounts ta
            WHERE ta.deleted_at IS NULL
            ORDER BY ta.revenue_opportunity_score DESC
            LIMIT 30
        """))
        targets = result2.fetchall()
        print(f"Found {len(targets)} target accounts")

        repo = FSWRepository(session)
        svc = FSWService(repo)

        created = 0
        for ta in targets:
            try:
                lead = await svc.create_lead({
                    "company_name": ta[1],
                    "stage": "revenue_ready",
                    "revenue_opportunity_score": float(ta[2] or 0),
                    "fit_score": float(ta[3] or 0),
                    "intent_score": float(ta[4] or 0),
                    "service_match": ta[5],
                    "why_now": ta[6],
                    "buying_signals": ta[7] or [],
                    "owner": None,
                })
                created += 1
            except Exception as e:
                print(f"  Skip {ta[1]}: {e}")

        await session.commit()
        print(f"\nCreated {created} FSW leads")

        # Verify
        counts = await svc.get_stage_counts()
        print(f"Stage counts: {counts}")


if __name__ == "__main__":
    asyncio.run(main())
