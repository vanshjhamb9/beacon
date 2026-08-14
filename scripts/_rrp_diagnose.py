import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]


async def main() -> None:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.intelligence import Company
    from revenue_execution_validation.revenue_ready.engine import RevenueReadyDefinitionEngine

    eng = RevenueReadyDefinitionEngine()
    async with AsyncSessionLocal() as s:
        rows = (await s.execute(select(Company).where(Company.deleted_at.is_(None)))).scalars().all()
    sr = [c for c in rows if (c.attributes or {}).get("rdap_sales_ready")]
    print("sales_ready", len(sr))
    for c in sr:
        a = c.attributes or {}
        email = a.get("business_email") or a.get("ofc_business_email")
        payload = {
            "company_name": c.name,
            "website": f"https://{c.primary_domain}",
            "official_website": f"https://{c.primary_domain}",
            "domain": c.primary_domain,
            "industry": a.get("industry") or "Software",
            "country": a.get("country") or "United States",
            "description": a.get("description")
            or (a.get("rdap_dossier") or {}).get("business", {}).get("description")
            or c.name,
            "business_email": email,
            "decision_maker": a.get("decision_maker"),
            "buying_signals": a.get("buying_signals") or [],
            "best_service": "AI Customer Support Automation",
            "service_matches": [{"service": "AI Customer Support Automation"}],
            "service_match_evidence": ["deterministic_saas_service_match"],
            "why_now": (a.get("buying_signals") or ["Verified sales-ready company"])[0],
            "opportunity": f"Outreach to {c.name}",
            "confidence": 92,
            "erowd_verified": True,
            "erowd_admitted": True,
            "source": a.get("source"),
            "evidence": [
                f"website:{c.primary_domain}",
                f"email:{email}",
                f"dm:{a.get('decision_maker')}",
            ],
            "attributes": a,
        }
        check = eng.evaluate(payload)
        print(
            c.name[:40],
            "rr",
            check.is_revenue_ready,
            "reasons",
            [r.value for r in check.rejection_reasons][:5],
            "checks",
            check.checks,
        )


if __name__ == "__main__":
    asyncio.run(main())
