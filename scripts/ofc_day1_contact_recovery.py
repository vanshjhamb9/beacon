"""OFC Day 1b — recover public contacts from companies that already have verified domains.

Does not invent. Writes attributed evidence onto company.attributes only.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "apps" / "api", ROOT / "packages", ROOT):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "ofc-day1-contact-recovery-live-report.json"


async def main() -> None:
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    from app.db.session import AsyncSessionLocal
    from app.models import Company
    from collectors.extraction.public_contacts import recover_from_official_website

    results: list[dict[str, Any]] = []
    with_email = 0
    with_dm = 0
    with_phone = 0
    with_li = 0

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()

        for company in rows:
            domain = str(company.primary_domain or "").strip()
            if not domain:
                continue
            website = domain if domain.startswith("http") else f"https://{domain}"
            contacts = await asyncio.to_thread(recover_from_official_website, website)
            emails = contacts.get("emails") or []
            phones = contacts.get("phones") or []
            linkedin = contacts.get("linkedin") or []
            dms = contacts.get("decision_makers") or []
            about = contacts.get("about_excerpt")

            attrs = dict(company.attributes or {})
            attrs["ofc_contact_recovery_at"] = datetime.now(UTC).isoformat()
            attrs["ofc_contact_pages"] = contacts.get("pages_fetched") or []
            if emails:
                attrs["ofc_business_email"] = emails[0]
                attrs["ofc_emails"] = emails
                attrs["business_email"] = emails[0]
                with_email += 1
            if phones:
                attrs["ofc_phone"] = phones[0]
                attrs["phone"] = phones[0]
                with_phone += 1
            if linkedin:
                attrs["ofc_linkedin"] = linkedin
                company_li = next((u for u in linkedin if "/company/" in u), None)
                person_li = next((u for u in linkedin if "/in/" in u), None)
                if company_li:
                    attrs["linkedin_company"] = company_li
                if person_li:
                    attrs["linkedin"] = person_li
                with_li += 1
            if dms:
                attrs["ofc_decision_makers"] = dms
                top = dms[0]
                attrs["decision_maker"] = f"{top['name']} ({top['role']})"
                attrs["decision_makers"] = dms
                with_dm += 1
            if about and not company.description:
                company.description = str(about)[:2000]
                attrs["description"] = about
            attrs["ofc_evidence"] = [
                "company_website",
                f"domain:{domain}",
                *(f"page:{p}" for p in (contacts.get("pages_fetched") or [])[:4]),
            ]
            company.attributes = attrs
            flag_modified(company, "attributes")

            results.append(
                {
                    "company_id": str(company.id),
                    "company": company.name,
                    "website": website,
                    "emails": emails,
                    "phones": phones[:2],
                    "linkedin": linkedin[:3],
                    "decision_makers": dms[:3],
                    "about": (about or "")[:120],
                }
            )
        await session.commit()

    payload = {
        "mission": "OFC Day 1b — contact recovery on verified-domain companies",
        "generated_at": datetime.now(UTC).isoformat(),
        "companies_scanned": len(results),
        "with_business_email": with_email,
        "with_decision_maker": with_dm,
        "with_phone": with_phone,
        "with_linkedin": with_li,
        "results": results,
        "run_id": str(uuid4()),
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
