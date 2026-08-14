"""Perfect-lead pipeline: collect fresh events → website → contacts → LQS → persist.

Writes docs/perfect-leads-live-report.json with perfect/outbound candidates.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "apps" / "api"),
    str(ROOT / "apps" / "worker"),
    str(ROOT / "packages"),
    str(ROOT),
]


def _plausible_person(name: str) -> bool:
    parts = [p for p in name.strip().split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    blocked = {
        "rankings",
        "function",
        "team",
        "about",
        "company",
        "report",
        "latest",
        "institute",
        "university",
        "college",
        "foundation",
        "inc",
        "llc",
    }
    if any(p.lower().rstrip(".") in blocked for p in parts):
        return False
    return all(p[:1].isupper() for p in parts)


def _company_name_from_title(title: str, source: str, website: str | None = None) -> str:
    text = title.strip()
    text = re.sub(r"^(Show HN|Launch HN|Ask HN|Tell HN)\s*:\s*", "", text, flags=re.I)
    # "Name – description" / "Name - description"
    for sep in (" – ", " — ", " - ", " | "):
        if sep in text:
            left = text.split(sep, 1)[0].strip()
            if 2 <= len(left) <= 60 and len(left.split()) <= 6:
                text = left
                break
    # "Name (YC …)"
    m = re.match(r"^(.+?)\s*\(YC\b", text, re.I)
    if m:
        text = m.group(1).strip()
    # Prefer domain brand when title looks like a headline (too many words)
    if website and len(text.split()) > 6:
        host = urlparse(website).netloc.lower().removeprefix("www.").split(".")[0]
        if host and host not in {"www", "app", "www2"}:
            return host.replace("-", " ").title()
    return text[:80]


def _title_matches_domain(company: str, website: str | None) -> bool:
    if not website:
        return False
    host = urlparse(website).netloc.lower().removeprefix("www.")
    brand = host.split(".")[0]
    tokens = re.findall(r"[a-z0-9]+", company.lower())
    if brand and brand in "".join(tokens):
        return True
    if brand and any(brand.startswith(t) or t.startswith(brand) for t in tokens if len(t) >= 4):
        return True
    # Launch HN posts with domain link are OK even if title is descriptive
    return "launch hn" in company.lower() or brand in company.lower().replace(" ", "")



async def _resolve_ph_website(client: Any, meta: dict[str, Any]) -> str | None:
    from intelligence.entity_resolution.platform_domains import is_platform_domain

    for cand in (meta.get("official_website"), meta.get("homepage"), meta.get("ph_redirect_url")):
        if not cand:
            continue
        try:
            resp = await client.head(str(cand), follow_redirects=True)
            host = urlparse(str(resp.url)).netloc.lower().removeprefix("www.")
            if host and not is_platform_domain(host) and "producthunt.com" not in host:
                return f"https://{host}"
        except Exception:  # noqa: BLE001
            continue
    return None


async def collect_and_score() -> dict[str, Any]:
    import httpx

    from collectors.extraction.public_contacts import recover_from_official_website
    from collectors.freshness import FRESH_HOURS, filter_fresh_events
    from collectors.sources.hacker_news import HackerNewsCollector
    from collectors.sources.product_hunt import ProductHuntCollector
    from lead_quality import LeadQualityScorer, OUTBOUND_THRESHOLD, PERFECT_THRESHOLD, SCORING_VERSION
    from revenue_readiness_perfection.why_now.engine import WhyNowEngine

    scorer = LeadQualityScorer()
    why_engine = WhyNowEngine()
    candidates: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        collectors = [
            (
                "hacker_news",
                HackerNewsCollector(
                    client,
                    feed_urls=[
                        "https://hnrss.org/newest?q=hiring+OR+funding+OR+launch+OR+SaaS",
                        "https://hnrss.org/frontpage",
                    ],
                    max_items=25,
                ),
            ),
            (
                "product_hunt",
                ProductHuntCollector(
                    client,
                    feed_urls=["https://www.producthunt.com/feed"],
                    max_items=20,
                ),
            ),
        ]
        for source_name, collector in collectors:
            try:
                events = filter_fresh_events(list(await collector.collect()), max_age_hours=FRESH_HOURS)
            except Exception as exc:  # noqa: BLE001
                print(f"  {source_name}: ERROR {exc}")
                continue
            print(f"  {source_name}: fresh={len(events)}")
            for ev in events:
                title_l = ev.title.lower()
                # HN quality gate: only Launch/Show/hiring posts become lead candidates
                if source_name == "hacker_news" and not (
                    title_l.startswith("launch hn")
                    or title_l.startswith("show hn")
                    or "hiring" in title_l
                ):
                    continue
                meta = dict(ev.metadata or {})
                website = meta.get("official_website") or meta.get("homepage")
                if not website and source_name == "product_hunt":
                    website = await _resolve_ph_website(client, meta)
                    if website:
                        host = urlparse(website).netloc.lower().removeprefix("www.")
                        meta["official_website"] = website
                        meta["domain"] = host
                        meta["article_only"] = False
                        contacts = recover_from_official_website(website)
                        if contacts.get("emails"):
                            meta["business_email"] = contacts["emails"][0]
                            meta["emails"] = contacts["emails"]
                        dms = [
                            dm
                            for dm in (contacts.get("decision_makers") or [])
                            if _plausible_person(str(dm.get("name") or ""))
                        ]
                        if dms:
                            meta["decision_makers"] = dms
                            meta["decision_maker"] = f"{dms[0]['name']} ({dms[0]['role']})"
                        if contacts.get("about_excerpt"):
                            meta["description"] = contacts["about_excerpt"]

                company = _company_name_from_title(ev.title, ev.source, website)
                if website and not _title_matches_domain(company + " " + ev.title, website):
                    # Skip mismatched publisher/news links (e.g. jfrog.com article about security)
                    host = urlparse(website).netloc.lower()
                    brand = host.split(".")[0]
                    if brand not in title_l.replace(" ", "") and brand not in (meta.get("domain") or ""):
                        continue
                    if brand not in title_l and len(ev.title.split()) > 8:
                        # headline pointing at big vendor site — not a startup launch
                        continue

                # Drop non-person DMs before scoring
                if meta.get("decision_maker") and not _plausible_person(
                    str(meta.get("decision_maker")).split("(")[0].strip()
                ):
                    meta.pop("decision_maker", None)
                    meta.pop("decision_makers", None)

                signals = list(meta.get("buying_signals") or [f"{ev.source}: {ev.title[:100]}"])
                why, evidence = why_engine.build(
                    signals=signals,
                    source=ev.source,
                    attrs=meta,
                    company=company,
                )
                payload = {
                    "company_name": company,
                    "source": ev.source,
                    "website": website,
                    "official_website": website,
                    "primary_domain": meta.get("domain"),
                    "industry": meta.get("industry") or "Technology",
                    "description": meta.get("description") or meta.get("about") or ev.content[:240],
                    "business_email": meta.get("business_email"),
                    "decision_maker": meta.get("decision_maker"),
                    "why_now": why,
                    "buying_signals": signals,
                    "evidence": evidence,
                    "website_verified": bool(website),
                    "published_at": ev.published_at,
                    "title": ev.title,
                    "content": ev.content[:500],
                    "url": ev.url,
                    "attributes": {
                        **meta,
                        "source": ev.source,
                        "source_kind": "event",
                        "lead_eligible": True,
                        "rrp_why_now": why,
                    },
                }
                result = scorer.score(payload)
                row = {
                    **payload,
                    "published_at": ev.published_at.isoformat(),
                    "lead_quality": result.as_dict(),
                    "lead_quality_score": result.total,
                    "lead_quality_grade": result.grade,
                    "outbound_ready": result.outbound_ready,
                    "perfect_lead": result.perfect,
                    "pipeline_worthy": result.pipeline_worthy,
                }
                # Drop heavy nested attrs for report readability
                row["attributes"] = {
                    "source": ev.source,
                    "domain": meta.get("domain"),
                    "emails": meta.get("emails"),
                    "decision_makers": meta.get("decision_makers"),
                }
                candidates.append(row)

    candidates.sort(
        key=lambda r: (bool(r["perfect_lead"]), bool(r["outbound_ready"]), float(r["lead_quality_score"])),
        reverse=True,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scoring_version": SCORING_VERSION,
        "outbound_threshold": OUTBOUND_THRESHOLD,
        "perfect_threshold": PERFECT_THRESHOLD,
        "counts": {
            "scored": len(candidates),
            "pipeline_worthy": sum(1 for c in candidates if c["pipeline_worthy"]),
            "with_website": sum(1 for c in candidates if c.get("website")),
            "with_email": sum(1 for c in candidates if c.get("business_email")),
            "with_dm": sum(1 for c in candidates if c.get("decision_maker")),
            "outbound": sum(1 for c in candidates if c["outbound_ready"]),
            "perfect": sum(1 for c in candidates if c["perfect_lead"]),
        },
        "perfect_leads": [c for c in candidates if c["perfect_lead"]],
        "outbound_leads": [c for c in candidates if c["outbound_ready"]],
        "top_20": candidates[:20],
    }


async def persist_leads(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Upsert perfect/outbound leads into Company + RRP profile attributes."""
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    from app.db.session import AsyncSessionLocal
    from app.models.intelligence import Company
    from app.models.revenue_readiness_perfection import RrpCompanyProfile

    created = 0
    updated = 0
    async with AsyncSessionLocal() as session:
        for lead in leads:
            website = str(lead.get("website") or "")
            domain = urlparse(website).netloc.lower().removeprefix("www.") if website else ""
            if not domain:
                continue
            existing = (
                await session.execute(
                    select(Company).where(Company.primary_domain == domain, Company.deleted_at.is_(None))
                )
            ).scalar_one_or_none()
            now = datetime.now(UTC)
            attrs = {
                "source": lead.get("source"),
                "source_kind": "event",
                "lead_eligible": True,
                "content_occurred_at": lead.get("published_at"),
                "official_website": website,
                "business_email": lead.get("business_email"),
                "decision_maker": lead.get("decision_maker"),
                "rrp_why_now": lead.get("why_now"),
                "rrp_confidence": lead.get("lead_quality_score"),
                "rrp_revenue_ready": bool(lead.get("outbound_ready")),
                "outbound_ready": bool(lead.get("outbound_ready")),
                "lead_quality_score": lead.get("lead_quality_score"),
                "lead_quality_grade": lead.get("lead_quality_grade"),
                "perfect_lead": bool(lead.get("perfect_lead")),
                "buying_signals": lead.get("buying_signals") or [],
                "description": lead.get("description"),
                "industry": lead.get("industry") or "Technology",
            }
            if existing:
                existing.name = str(lead.get("company_name") or existing.name)
                existing.last_seen_at = now
                merged = dict(existing.attributes or {})
                merged.update(attrs)
                existing.attributes = merged
                flag_modified(existing, "attributes")
                company = existing
                updated += 1
            else:
                company = Company(
                    id=uuid.uuid4(),
                    name=str(lead.get("company_name") or domain),
                    normalized_name=str(lead.get("company_name") or domain).lower(),
                    primary_domain=domain,
                    industry=str(lead.get("industry") or "Technology"),
                    last_seen_at=now,
                    attributes=attrs,
                )
                session.add(company)
                created += 1
            await session.flush()

            profile = (
                await session.execute(
                    select(RrpCompanyProfile).where(
                        RrpCompanyProfile.company_id == company.id,
                        RrpCompanyProfile.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if profile is None:
                profile = RrpCompanyProfile(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    revenue_ready=bool(lead.get("outbound_ready")),
                    payload={
                        "why_now": lead.get("why_now"),
                        "lead_quality": lead.get("lead_quality"),
                        "business_email": lead.get("business_email"),
                        "decision_maker": lead.get("decision_maker"),
                        "source": lead.get("source"),
                    },
                )
                session.add(profile)
            else:
                profile.revenue_ready = bool(lead.get("outbound_ready"))
                profile.payload = {
                    **(profile.payload or {}),
                    "why_now": lead.get("why_now"),
                    "lead_quality": lead.get("lead_quality"),
                    "business_email": lead.get("business_email"),
                    "decision_maker": lead.get("decision_maker"),
                    "source": lead.get("source"),
                }
                flag_modified(profile, "payload")
        await session.commit()
    return {"created": created, "updated": updated}


async def main() -> None:
    print("=== Perfect Lead Pipeline ===")
    report = await collect_and_score()
    counts = report["counts"]
    print(
        f"scored={counts['scored']} websites={counts['with_website']} "
        f"emails={counts['with_email']} dms={counts['with_dm']} "
        f"outbound={counts['outbound']} perfect={counts['perfect']}"
    )
    for lead in report["perfect_leads"][:10]:
        print(
            f"  PERFECT {lead['lead_quality_score']} | {lead['company_name']} | "
            f"{lead.get('website')} | {lead.get('business_email')} | {lead.get('decision_maker')}"
        )
    for lead in report["outbound_leads"][:10]:
        if lead.get("perfect_lead"):
            continue
        print(
            f"  OUTBOUND {lead['lead_quality_score']} | {lead['company_name']} | "
            f"{lead.get('website')} | {lead.get('business_email')}"
        )

    persistable = report["outbound_leads"] or [
        c for c in report["top_20"] if c.get("website") and c.get("business_email")
    ]
    persist_stats = {"created": 0, "updated": 0, "skipped": True}
    if persistable:
        try:
            persist_stats = await persist_leads(persistable)
            persist_stats["skipped"] = False
            print(f"persisted created={persist_stats['created']} updated={persist_stats['updated']}")
        except Exception as exc:  # noqa: BLE001
            persist_stats = {"error": str(exc), "skipped": True}
            print(f"persist skipped: {exc}")

    report["persist"] = persist_stats
    report["complete"] = counts["perfect"] >= 1 or counts["outbound"] >= 1
    out = ROOT / "docs" / "perfect-leads-live-report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report: {out}")
    print(f"complete={report['complete']}")
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
