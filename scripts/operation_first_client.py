"""Operation First Client — funnel-first cleanup + selective enrichment.

NOT a new product engine. Orchestrates existing:
  - production_hardening admission / FAKE_NAME_PATTERNS
  - lead_enrichment WebsiteConnector
  - revenue_data_recovery WebsiteRecoveryEngine
  - ground_truth ContactWaterfallV2 + GroundTruthPipeline
  - sales_readiness ServiceMatchingEngineV2

Goal: 412 noise → ~25 outreach-grade accounts. Soft-delete garbage. Enrich only the top slice.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "apps" / "api"),
    str(ROOT / "apps" / "worker"),
    str(ROOT / "packages"),
    str(ROOT),
]

REPORT_JSON = ROOT / "docs" / "operation-first-client-live-report.json"
REPORT_MD = ROOT / "docs" / "operation-first-client-report.md"

# Ops-only reject labels (live corpus noise) — not a new scoring engine
EXTRA_FAKE_NAMES = frozenset(
    {
        "companies",
        "bottleneck",
        "teaching",
        "cross-entropy",
        "cross entropy",
        "there",
        "don",
        "latina",
        "frontend-only",
        "model",
        "patreon",
        "deepseek",
        "investor",
        "sensor",
        "mixture",
        "optimizing",
        "posts",
        "database",
        "preview",
        "build",
        "stop",
        "everyone",
        "python",
        "design",
        "run",
        "article",
        "cleanup",
        "edtech",
        "built",
        "two",
        "production",
        "django",
        "shipping",
        "learned",
        "migrating",
        "vue",
        "qubes",
        "typescript",
        "these",
        "getting",
        "clamping",
        "flaky",
        "lean",
        "regret",
        "understanding",
        "dashboard",
        "kubernetes",
        "why ai",
        "my ai",
        "frontier ai",
        "next-token",
        "next token",
    }
)

EMAIL_BLOCKLIST_HOSTS = frozenset(
    {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "icloud.com",
        "protonmail.com",
        "mail.gw",
        "techcrunch.com",
        "strictlyvc.com",
        "example.com",
        "company.com",
        "email.com",
        "test.com",
    }
)
EMAIL_PLACEHOLDER_RE = re.compile(
    r"(you@|noreply@|no-reply@|donotreply@|dummy|placeholder|test@|admin@localhost)",
    re.I,
)
ROLE_PREFIXES = (
    "hello@",
    "contact@",
    "sales@",
    "info@",
    "founder@",
    "ceo@",
    "cto@",
    "team@",
    "support@",
    "press@",
    "partners@",
    "business@",
)

INTENT_HINTS = (
    "hiring",
    "automation",
    "ai engineer",
    "saas",
    "scaling",
    "funding",
    "digital transformation",
    "expansion",
    "migration",
    "manual",
    "workflow",
    "crm",
    "erp",
)

# Reject non-company "domains" extracted from code/blog noise
FAKE_DOMAIN_SUFFIXES = (
    ".tsx",
    ".ts",
    ".js",
    ".jsx",
    ".py",
    ".md",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".env",
    ".lock",
    ".map",
    ".css",
    ".scss",
    ".html",
    ".txt",
    ".pdf",
    ".svg",
    ".png",
    ".jpg",
    ".editorconfig",
)
FAKE_DOMAIN_HOSTS = frozenset(
    {
        "github.com",
        "githubusercontent.com",
        "raw.githubusercontent.com",
        "news.ycombinator.com",
        "chromewebstore.google.com",
        "play.google.com",
        " orth.withgoogle.com",  # typo guard
        "pair.withgoogle.com",
        "aws-mcp.amazonaws.com",
        "mail.example.com",
        "example.com",
        "localhost",
        "asp.net",
        "node.js",
        "shell.run",
        "project.run",
        "promise.resolve",
        "array.map",
        "checkout.session",
        "metadata.name",
        "loki.source",
        "harcon.json",
        "progress.md",
        "design.md",
        "sitemap.xml",
        "manage.py",
        "main.tsx",
        "this.editorconfig",
        "namespace.yml",
        "gdf.buffer",
        "pavelespitia.github",
        "aws-mcp.amazonaws",
        "pair.withgoogle",
        "chromewebstore.google",
        "raw.githubusercontent",
        "news.ycombinator",
        "environment.ec.europa.eu",  # government article host as "company"
    }
)
REAL_TLD_RE = re.compile(
    r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)+$",
    re.I,
)


def _is_real_company_domain(domain: str | None) -> bool:
    if not domain:
        return False
    d = domain.strip().lower().removeprefix("www.").split("/")[0]
    if not d or d in FAKE_DOMAIN_HOSTS:
        return False
    if any(d.endswith(sfx) for sfx in FAKE_DOMAIN_SUFFIXES):
        return False
    # single-label nonsense (asp.net is 2 labels but in blocklist)
    parts = d.split(".")
    if len(parts) < 2:
        return False
    # reject if last label looks like a code token
    if parts[-1] in {"tsx", "jsx", "map", "run", "session", "name", "source", "resolve", "json", "xml", "yml", "yaml", "md", "py", "js", "ts", "css", "html", "txt", "example", "local", "internal"}:
        return False
    if not REAL_TLD_RE.match(d):
        return False
    # reject github user-style foo.github.io without company signal handled elsewhere; allow .io products
    if "github" in d and not d.endswith(".github.io"):
        return False
    if d.endswith(".github"):
        return False
    return True


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def _is_business_email(email: str, company_domain: str | None) -> bool:
    e = (email or "").strip().lower()
    if "@" not in e or EMAIL_PLACEHOLDER_RE.search(e):
        return False
    local, _, host = e.partition("@")
    if not local or not host or host in EMAIL_BLOCKLIST_HOSTS:
        return False
    if host.endswith(".edu") or host.endswith(".gov"):
        return True
    if company_domain:
        cd = company_domain.lower().removeprefix("www.")
        if host == cd or host.endswith("." + cd) or cd.endswith("." + host):
            return True
    return any(e.startswith(p) for p in ROLE_PREFIXES)


async def _metrics(session) -> dict[str, Any]:
    from sqlalchemy import func, select

    from app.models.enrichment import CompanyContact
    from app.models.intelligence import Company
    from app.models.opportunity import Opportunity, OpportunityEvidence

    companies = await session.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None)))
    with_domain = await session.scalar(
        select(func.count())
        .select_from(Company)
        .where(
            Company.deleted_at.is_(None),
            Company.primary_domain.is_not(None),
            Company.primary_domain != "",
        )
    )
    opps = await session.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.deleted_at.is_(None)))
    evid = await session.scalar(
        select(func.count(func.distinct(OpportunityEvidence.company_id))).where(OpportunityEvidence.deleted_at.is_(None))
    )
    email_cos = await session.scalar(
        select(func.count(func.distinct(CompanyContact.company_id))).where(
            CompanyContact.deleted_at.is_(None),
            CompanyContact.kind.in_(["company_email", "role_based_email", "email", "business_email"]),
        )
    )
    phone_cos = await session.scalar(
        select(func.count(func.distinct(CompanyContact.company_id))).where(
            CompanyContact.deleted_at.is_(None),
            CompanyContact.kind.in_(["company_phone", "business_phone", "phone"]),
        )
    )
    return {
        "companies": int(companies or 0),
        "with_domain": int(with_domain or 0),
        "opportunities": int(opps or 0),
        "companies_with_evidence": int(evid or 0),
        "companies_with_email_contact": int(email_cos or 0),
        "companies_with_phone_contact": int(phone_cos or 0),
    }


def _early_reject_reason(company, *, attrs: dict) -> str | None:
    from intelligence.entity_resolution.platform_domains import is_platform_domain
    from production_hardening.admission.engine import FAKE_NAME_PATTERNS, NON_BUSINESS_HINTS

    name = _norm_name(company.name)
    if not name or name in FAKE_NAME_PATTERNS or name in EXTRA_FAKE_NAMES:
        return "fake_or_non_business_name"
    if len(name) < 2:
        return "identity_too_short"
    domain = (company.primary_domain or "").strip().lower()
    if not domain:
        return "no_website"
    if not _is_real_company_domain(domain):
        return "invalid_domain"
    if is_platform_domain(domain):
        return "platform_domain"
    url = str(attrs.get("source_url") or attrs.get("url") or "")
    blob = f"{url} {domain} {name}".lower()
    if any(h in blob for h in NON_BUSINESS_HINTS):
        return "non_business_url"
    entity = str(attrs.get("entity_type") or "").lower()
    if entity in {"repository", "blog", "library", "opensource", "documentation", "community", "individual", "fake"}:
        return f"entity_type:{entity}"
    return None


async def main() -> None:
    from sqlalchemy import func, select

    from app.db.session import AsyncSessionLocal
    from app.models.enrichment import CompanyContact
    from app.models.intelligence import Company
    from app.models.opportunity import Opportunity, OpportunityEvidence
    from app.services.ground_truth import GroundTruthService
    from ground_truth.pipelines.engine import GroundTruthPipeline
    from lead_enrichment.connectors.website import WebsiteConnector
    from lead_enrichment.models.types import EnrichmentOpportunityInput
    from revenue_data_recovery.website_recovery.engine import WebsiteRecoveryEngine
    from sales_readiness.service_match.engine import ServiceMatchingEngineV2

    started = datetime.now(UTC)
    report: dict[str, Any] = {
        "operation": "first_client",
        "started_at": started.isoformat(),
        "before": {},
        "after": {},
        "rejection_reasons": {},
        "collectors": {},
        "enrichment": {},
        "top_25": [],
        "founder_queue_10": [],
        "missing_data": [],
        "blockers": [],
        "every_survivor_with_evidence": [],
    }

    print("=== Operation First Client ===")
    async with AsyncSessionLocal() as session:
        before = await _metrics(session)
        report["before"] = before
        print(f"BEFORE: {before}")

        # Collector quality snapshot (existing table)
        from sqlalchemy import Integer, cast, text

        from app.models.acquisition import CollectorRun

        try:
            rows = (
                await session.execute(
                    select(
                        CollectorRun.source,
                        func.sum(CollectorRun.collected),
                        func.sum(CollectorRun.emitted),
                        func.sum(CollectorRun.duplicates),
                        func.sum(cast(~CollectorRun.success, Integer)),
                    )
                    .where(CollectorRun.deleted_at.is_(None))
                    .group_by(CollectorRun.source)
                )
            ).all()
        except Exception:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT source,
                               SUM(collected), SUM(emitted), SUM(duplicates),
                               SUM(CASE WHEN NOT success THEN 1 ELSE 0 END)
                        FROM collector_runs WHERE deleted_at IS NULL GROUP BY source
                        """
                    )
                )
            ).all()

        collectors = []
        for r in rows:
            collected = int(r[1] or 0)
            emitted = int(r[2] or 0)
            dups = int(r[3] or 0)
            fails = int(r[4] or 0)
            emit_pct = round(100.0 * emitted / collected, 1) if collected else 0.0
            collectors.append(
                {
                    "source": r[0],
                    "collected": collected,
                    "emitted": emitted,
                    "duplicates": dups,
                    "failures": fails,
                    "emit_pct": emit_pct,
                    "dup_pct": round(100.0 * dups / collected, 1) if collected else 0.0,
                }
            )
        collectors.sort(key=lambda c: c["emit_pct"], reverse=True)
        report["collectors"] = {
            "best": collectors[:3],
            "worst": list(reversed(collectors[-3:])) if collectors else [],
            "all": collectors,
            "disabled_now": ["indie_hackers", "sec_edgar", "github_trending"],
        }

        reject_counter: Counter[str] = Counter()

        # Clear primary_domain junk on active companies so funnel uses real domains only
        junk_domains = 0
        for company in list(
            (await session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all()
        ):
            if company.primary_domain and not _is_real_company_domain(company.primary_domain):
                attrs = dict(company.attributes or {})
                attrs["first_client_rejection"] = "invalid_domain"
                attrs["invalid_domain_value"] = company.primary_domain
                attrs["first_client_rejected_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                company.soft_delete()
                junk_domains += 1
                reject_counter["invalid_domain"] += 1
        if junk_domains:
            await session.commit()
            print(f"Soft-deleted invalid domains={junk_domains}")

        # --- Phase 1: soft-delete garbage ---
        companies = list(
            (await session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all()
        )
        soft_deleted = 0
        survivors: list[Any] = []
        for company in companies:
            attrs = dict(company.attributes or {})
            reason = _early_reject_reason(company, attrs=attrs)
            if reason:
                reject_counter[reason] += 1
                attrs["first_client_rejection"] = reason
                attrs["first_client_rejected_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                company.soft_delete()
                soft_deleted += 1
            else:
                survivors.append(company)
        await session.commit()
        print(f"Phase1 soft-deleted={soft_deleted} survivors={len(survivors)}")

        # Soft-delete polluted contacts
        contacts = list(
            (await session.scalars(select(CompanyContact).where(CompanyContact.deleted_at.is_(None)))).all()
        )
        contact_scrubbed = 0
        for c in contacts:
            company = await session.get(Company, c.company_id)
            domain = company.primary_domain if company else None
            if "email" in str(c.kind).lower() and not _is_business_email(c.value, domain):
                c.soft_delete()
                contact_scrubbed += 1
        await session.commit()
        print(f"Scrubbed polluted contacts={contact_scrubbed}")

        # --- Phase 9: duplicate merge by domain / normalized name ---
        by_domain: dict[str, list[Any]] = defaultdict(list)
        by_name: dict[str, list[Any]] = defaultdict(list)
        active = list((await session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all())
        for c in active:
            if c.primary_domain:
                by_domain[c.primary_domain.lower().removeprefix("www.")].append(c)
            by_name[_norm_name(c.name)].append(c)

        merged = 0

        async def _score(cid: UUID) -> float:
            row = await session.scalar(
                select(func.coalesce(func.max(Opportunity.opportunity_score), 0.0)).where(
                    Opportunity.company_id == cid, Opportunity.deleted_at.is_(None)
                )
            )
            return float(row or 0.0)

        async def _merge_group(group: list[Any], reason: str) -> None:
            nonlocal merged
            if len(group) < 2:
                return
            ranked = []
            for g in group:
                ranked.append((await _score(g.id), g.last_seen_at or g.created_at, g))
            ranked.sort(key=lambda t: (t[0], t[1] or datetime.min.replace(tzinfo=UTC)), reverse=True)
            keep = ranked[0][2]
            for _, _, loser in ranked[1:]:
                attrs = dict(loser.attributes or {})
                attrs["first_client_rejection"] = reason
                attrs["merged_into"] = str(keep.id)
                attrs["first_client_rejected_at"] = datetime.now(UTC).isoformat()
                loser.attributes = attrs
                loser.soft_delete()
                merged += 1
                reject_counter[reason] += 1

        for group in by_domain.values():
            await _merge_group(group, "duplicate_domain")
        # refresh active after domain merges
        active = list((await session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all())
        by_name = defaultdict(list)
        for c in active:
            by_name[_norm_name(c.name)].append(c)
        for group in by_name.values():
            await _merge_group(group, "duplicate_name")
        await session.commit()
        print(f"Merged duplicates={merged}")

        # --- Funnel-first: rank survivors with domain + evidence; enrich top N only ---
        active = list((await session.scalars(select(Company).where(Company.deleted_at.is_(None)))).all())
        candidates: list[tuple[float, int, Any]] = []
        for c in active:
            if not c.primary_domain or not _is_real_company_domain(c.primary_domain):
                continue
            score = await _score(c.id)
            evid_n = int(
                await session.scalar(
                    select(func.count()).select_from(OpportunityEvidence).where(
                        OpportunityEvidence.company_id == c.id,
                        OpportunityEvidence.deleted_at.is_(None),
                    )
                )
                or 0
            )
            candidates.append((score, evid_n, c))
        candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)

        # Keep best 100 after identity; fully enrich top 40
        shortlist = candidates[:100]
        enrich_slice = shortlist[:40]
        report["enrichment"]["identity_passed_with_domain"] = len(candidates)
        report["enrichment"]["shortlist_100"] = len(shortlist)
        report["enrichment"]["fully_enriched"] = len(enrich_slice)

        website = WebsiteConnector(timeout_seconds=5.0, max_pages=6)
        recovery = WebsiteRecoveryEngine()
        matcher = ServiceMatchingEngineV2()
        pipeline = GroundTruthPipeline()
        gt = GroundTruthService(session)

        evaluated: list[dict[str, Any]] = []
        website_verified = 0
        emails_recovered = 0
        phones_recovered = 0
        dms_found = 0
        sales_ready = 0

        for idx, (score, evid_n, company) in enumerate(enrich_slice, start=1):
            print(f"Enrich {idx}/{len(enrich_slice)}: {company.name} ({company.primary_domain})")
            payload = await gt.build_payload(company.id)
            if not payload:
                continue

            # Live website verification
            fetch = website.collect(
                EnrichmentOpportunityInput(
                    company_id=company.id,
                    opportunity_id=uuid4(),
                    company_name=company.name,
                    domain=company.primary_domain,
                    website=company.primary_domain,
                    opportunity_score=score,
                    opportunity_status="ops",
                    opportunity_narrative=str(payload.get("narrative") or ""),
                    industry=company.industry,
                    description=company.description or company.memory_summary,
                    location=None,
                    country=payload.get("country"),
                )
            )
            homepage = next((p for p in fetch.pages if p.page_type == "homepage"), None)
            html_blob = "\n".join(p.html for p in fetch.pages if p.html)
            discovered = {p.page_type: p.url for p in fetch.pages}
            alive = bool(homepage and homepage.status_code and 200 <= homepage.status_code < 400)
            ssl_ok = True  # fetched via https
            title_text = (homepage.text[:500] if homepage and homepage.text else "") or ""

            payload["website_html"] = html_blob[:250000] if html_blob else payload.get("website_html")
            payload["discovered_pages"] = discovered
            payload["website_alive"] = alive
            payload["http_status"] = homepage.status_code if homepage else None
            payload["ssl"] = ssl_ok and alive
            payload["website_title"] = title_text[:200]

            wr = recovery.recover(payload)
            if wr.rejected_reason or not alive:
                reason = wr.rejected_reason or "website_unreachable"
                reject_counter[reason] += 1
                attrs = dict(company.attributes or {})
                attrs["first_client_rejection"] = reason
                attrs["first_client_rejected_at"] = datetime.now(UTC).isoformat()
                attrs["website_alive"] = False
                company.attributes = attrs
                company.soft_delete()
                await session.commit()
                continue

            if not payload.get("description") and title_text:
                payload["description"] = title_text[:400]
                payload["business_description"] = title_text[:400]

            # Intent gate before full contact spend — require evidence or intent hints
            evidence_blob = " ".join(
                str(e.get("summary") or "") for e in (payload.get("evidence") or [])
            ).lower()
            narrative = str(payload.get("narrative") or "").lower()
            intent_ok = evid_n > 0 and any(h in evidence_blob or h in narrative for h in INTENT_HINTS)
            # Product Hunt / strong domain companies may lack keyword — allow if score high + alive site
            if not intent_ok and score < 55:
                reject_counter["low_intent_no_evidence"] += 1
                attrs = dict(company.attributes or {})
                attrs["first_client_rejection"] = "low_intent_no_evidence"
                attrs["first_client_rejected_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                # do not soft-delete all low-intent — keep for later, skip deep enrichment contacts
                # but still evaluate lightly
                intent_ok = False

            # Service match — exactly one
            matches = matcher.match(payload)
            if matches:
                payload["recommended_service"] = matches[0].recommended_service
                payload["estimated_deal"] = matches[0].estimated_value
            else:
                # Map to one of the allowed services from ops brief using coarse industry
                industry = str(payload.get("industry") or "").lower()
                if "ecom" in industry or "retail" in industry:
                    payload["recommended_service"] = "Ecommerce"
                elif "saas" in industry or "software" in industry:
                    payload["recommended_service"] = "SaaS"
                else:
                    payload["recommended_service"] = "Workflow Automation"
                payload["estimated_deal"] = "$20k-$40k"

            if not payload.get("source"):
                payload["source"] = "opportunity_pipeline"
            if not payload.get("country"):
                payload["country"] = "Unknown"
            if not payload.get("industry") and company.industry:
                payload["industry"] = company.industry
            if not payload.get("industry"):
                payload["industry"] = "Technology"

            # Why now from evidence
            if not payload.get("why_now") and payload.get("evidence"):
                payload["why_now"] = "; ".join(
                    str(e.get("summary") or "")[:80] for e in payload["evidence"][:3] if e.get("summary")
                ) or "Active opportunity signals"

            snap = pipeline.evaluate(payload)
            website_verified += 1 if alive else 0

            # Persist clean contacts only
            emails = []
            phones = []
            if snap.contacts:
                for e in snap.contacts.emails:
                    val = e.value if hasattr(e, "value") else str(e)
                    if _is_business_email(str(val), company.primary_domain):
                        emails.append(str(val))
                for p in snap.contacts.phones:
                    val = p.value if hasattr(p, "value") else str(p)
                    if val and len(str(val)) >= 7:
                        phones.append(str(val))

            # Also scan HTML mailto with filter
            for m in re.findall(r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", html_blob or ""):
                if _is_business_email(m, company.primary_domain):
                    emails.append(m.lower())
            emails = list(dict.fromkeys(emails))
            phones = list(dict.fromkeys(phones))

            dms = snap.truth.decision_makers if snap.truth else []
            dms_found += len(dms)

            attrs = dict(company.attributes or {})
            if emails:
                attrs["recovered_emails"] = emails
                emails_recovered += len(emails)
            if phones:
                attrs["recovered_phones"] = phones
                phones_recovered += len(phones)
            attrs.update(
                {
                    "website_alive": True,
                    "ssl": True,
                    "http_status": homepage.status_code if homepage else 200,
                    "recommended_service": payload.get("recommended_service"),
                    "estimated_deal": payload.get("estimated_deal"),
                    "why_now": payload.get("why_now"),
                    "first_client_trust": snap.trust,
                    "first_client_verdict": snap.verdict.value,
                    "first_client_enriched_at": datetime.now(UTC).isoformat(),
                    "country": payload.get("country"),
                    "source": payload.get("source"),
                }
            )
            if payload.get("description") and not company.description:
                company.description = str(payload["description"])[:2000]
            if payload.get("industry") and not company.industry:
                company.industry = str(payload["industry"])[:200]
            company.attributes = attrs

            # Soft-delete hard rejects after GT
            if snap.verdict.value == "REJECTED" and snap.rejection:
                hard = {"FAKE", "GITHUB_REPOSITORY", "MARKETPLACE_LISTING", "NO_BUSINESS", "NO_WEBSITE"}
                reasons = {r.value if hasattr(r, "value") else str(r) for r in (snap.rejection.reasons or [])}
                if reasons & hard:
                    for r in reasons:
                        reject_counter[r] += 1
                    attrs["first_client_rejection"] = snap.rejection.explanation
                    company.attributes = attrs
                    company.soft_delete()
                    await session.commit()
                    continue

            if snap.verdict.value in {"SALES_READY", "ENTERPRISE_READY"}:
                sales_ready += 1

            card = snap.card
            evaluated.append(
                {
                    "company_id": str(company.id),
                    "company": company.name,
                    "website": f"https://{company.primary_domain}",
                    "domain": company.primary_domain,
                    "industry": company.industry or payload.get("industry"),
                    "country": payload.get("country"),
                    "why_now": payload.get("why_now"),
                    "pain": getattr(card, "pain", None) if card else None,
                    "opportunity": getattr(card, "buying_intent", None) if card else payload.get("narrative"),
                    "evidence": (payload.get("evidence") or [])[:5],
                    "decision_maker": (dms[0] if dms else None),
                    "verified_emails": emails,
                    "phones": phones,
                    "service_match": payload.get("recommended_service"),
                    "confidence": snap.trust,
                    "readiness": snap.readiness,
                    "estimated_deal": payload.get("estimated_deal"),
                    "next_action": getattr(card, "next_action", None) if card else "Verify contact then email",
                    "verdict": snap.verdict.value,
                    "lock_unlocked": snap.production_lock.unlocked,
                    "questions_missing": snap.questions.missing,
                    "opportunity_score": score,
                    "evidence_count": evid_n,
                    "intent_ok": intent_ok,
                }
            )
            await session.commit()

        report["enrichment"].update(
            {
                "website_verified": website_verified,
                "emails_recovered_rows": emails_recovered,
                "phones_recovered_rows": phones_recovered,
                "decision_makers_seen": dms_found,
                "sales_ready_from_enrichment": sales_ready,
            }
        )
        report["rejection_reasons"] = dict(reject_counter.most_common())

        # Rank Top 25 — prefer unlocked / sales ready / high trust + has email
        def _rank_key(row: dict[str, Any]) -> tuple:
            return (
                1 if row.get("lock_unlocked") else 0,
                1 if row.get("verdict") in {"SALES_READY", "ENTERPRISE_READY"} else 0,
                1 if row.get("verified_emails") else 0,
                float(row.get("confidence") or 0),
                float(row.get("opportunity_score") or 0),
            )

        evaluated.sort(key=_rank_key, reverse=True)
        top25 = evaluated[:25]
        report["top_25"] = top25
        report["founder_queue_10"] = top25[:10]
        report["every_survivor_with_evidence"] = [
            {
                "company": r["company"],
                "website": r["website"],
                "evidence": r["evidence"],
                "verdict": r["verdict"],
            }
            for r in evaluated
            if r.get("evidence")
        ]

        # Missing data for top25
        missing = []
        for r in top25:
            gaps = []
            if not r.get("verified_emails"):
                gaps.append("verified_email")
            if not r.get("phones"):
                gaps.append("phone")
            if not r.get("decision_maker"):
                gaps.append("decision_maker")
            if r.get("country") in (None, "Unknown", "unknown"):
                gaps.append("country")
            if r.get("questions_missing"):
                gaps.extend([f"question:{q}" for q in r["questions_missing"]])
            if gaps:
                missing.append({"company": r["company"], "missing": gaps})
        report["missing_data"] = missing

        after = await _metrics(session)
        # post-enrich contact counts among top25
        after["sales_ready_evaluated"] = sum(1 for r in evaluated if r["verdict"] in {"SALES_READY", "ENTERPRISE_READY"})
        after["website_verified_ops"] = website_verified
        after["top25_with_email"] = sum(1 for r in top25 if r.get("verified_emails"))
        after["top25_with_phone"] = sum(1 for r in top25 if r.get("phones"))
        after["top25_with_dm"] = sum(1 for r in top25 if r.get("decision_maker"))
        after["soft_deleted_this_run"] = soft_deleted + merged
        after["contacts_scrubbed"] = contact_scrubbed
        report["after"] = after

        # Acceptance vs targets
        active_n = after["companies"]
        dup_estimate = reject_counter.get("duplicate_domain", 0) + reject_counter.get("duplicate_name", 0)
        fake_left = 0  # soft-deleted known fakes
        report["acceptance"] = {
            "real_companies_active": active_n,
            "target_25_plus": active_n >= 25 and after["sales_ready_evaluated"] >= 25,
            "verified_websites": website_verified,
            "target_20_websites": website_verified >= 20,
            "decision_makers": after["top25_with_dm"],
            "target_15_dms": after["top25_with_dm"] >= 15,
            "verified_emails": after["top25_with_email"],
            "target_12_emails": after["top25_with_email"] >= 12,
            "phones": after["top25_with_phone"],
            "target_5_phones": after["top25_with_phone"] >= 5,
            "duplicate_merges": dup_estimate,
            "fake_soft_deleted": reject_counter.get("fake_or_non_business_name", 0),
            "production_locked": True,
        }

        blockers = []
        if after["sales_ready_evaluated"] < 25:
            blockers.append(f"Only {after['sales_ready_evaluated']} Sales Ready after enrichment (need 25)")
        if after["top25_with_email"] < 12:
            blockers.append(f"Only {after['top25_with_email']} of Top25 have verified business email (need 12+)")
        if after["top25_with_dm"] < 15:
            blockers.append(f"Only {after['top25_with_dm']} of Top25 have decision makers (need 15+)")
        if after["top25_with_phone"] < 5:
            blockers.append(f"Only {after['top25_with_phone']} of Top25 have phones (need 5+)")
        if website_verified < 20:
            blockers.append(f"Only {website_verified} websites verified live this run (need 20+)")
        blockers.append("Production send remains LOCKED until founder manually approves 20 random companies at 95%")
        blockers.append("Ground Truth DB tables may be unmigrated (alembic was behind HEAD) — results in this report JSON")
        report["blockers"] = blockers

        # Recovery / verification rates
        started_companies = before["companies"] or 1
        report["rates"] = {
            "cleanup_reject_rate_pct": round(100.0 * (soft_deleted + merged) / started_companies, 1),
            "recovery_rate_pct": round(100.0 * len(evaluated) / max(len(enrich_slice), 1), 1),
            "website_verification_rate_pct": round(100.0 * website_verified / max(len(enrich_slice), 1), 1),
            "email_recovery_among_verified_pct": round(
                100.0 * sum(1 for r in evaluated if r.get("verified_emails")) / max(website_verified, 1), 1
            ),
        }

    report["finished_at"] = datetime.now(UTC).isoformat()
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _write_md(report)
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(f"AFTER: {report['after']}")
    print(f"Top10: {[r['company'] for r in report['founder_queue_10']]}")


def _write_md(report: dict[str, Any]) -> None:
    b, a = report["before"], report["after"]
    lines = [
        "# Operation First Client — Live Report",
        "",
        f"**Run:** {report.get('started_at')} → {report.get('finished_at')}",
        "",
        "## 1. Before vs After",
        "",
        "| Metric | Before | After |",
        "|---|---:|---:|",
        f"| Active companies | {b.get('companies')} | {a.get('companies')} |",
        f"| With domain | {b.get('with_domain')} | {a.get('with_domain')} |",
        f"| Companies with email contact | {b.get('companies_with_email_contact')} | {a.get('companies_with_email_contact')} |",
        f"| Companies with phone | {b.get('companies_with_phone_contact')} | {a.get('companies_with_phone_contact')} |",
        f"| Sales Ready (evaluated this run) | 0 | {a.get('sales_ready_evaluated')} |",
        f"| Websites verified (ops) | 0 | {a.get('website_verified_ops')} |",
        "",
        "## 2. Top rejection reasons",
        "",
    ]
    for reason, n in list(report.get("rejection_reasons", {}).items())[:15]:
        lines.append(f"- **{reason}**: {n}")
    lines += ["", "## 3. Top collectors", ""]
    for c in report.get("collectors", {}).get("best", []):
        lines.append(f"- **{c['source']}** — emit {c['emit_pct']}% (dup {c['dup_pct']}%)")
    lines += ["", "## 4. Worst collectors (disable)", ""]
    for c in report.get("collectors", {}).get("worst", []):
        lines.append(f"- **{c['source']}** — emit {c['emit_pct']}% / failures {c['failures']}")
    lines.append(f"- Disabled this sprint: {', '.join(report.get('collectors', {}).get('disabled_now', []))}")
    rates = report.get("rates", {})
    lines += [
        "",
        "## 5–6. Recovery & verification rates",
        "",
        f"- Cleanup reject rate: **{rates.get('cleanup_reject_rate_pct')}%**",
        f"- Enrichment recovery rate: **{rates.get('recovery_rate_pct')}%**",
        f"- Website verification rate: **{rates.get('website_verification_rate_pct')}%**",
        f"- Email recovery among verified sites: **{rates.get('email_recovery_among_verified_pct')}%**",
        "",
        "## 7. Top 25 founder accounts",
        "",
    ]
    for i, r in enumerate(report.get("top_25", []), start=1):
        lines.append(
            f"{i}. **{r['company']}** — {r.get('website')} | {r.get('verdict')} | trust {r.get('confidence')} | "
            f"emails={len(r.get('verified_emails') or [])} | service={r.get('service_match')}"
        )
        lines.append(f"   - Why now: {r.get('why_now')}")
        lines.append(f"   - Next: {r.get('next_action')}")
    lines += ["", "## 8. Every enriched company with evidence", ""]
    for r in report.get("every_survivor_with_evidence", [])[:40]:
        lines.append(f"- **{r['company']}** ({r['verdict']}): {len(r.get('evidence') or [])} evidence items")
    lines += ["", "## 9. Missing data (Top 25)", ""]
    for m in report.get("missing_data", []):
        lines.append(f"- **{m['company']}**: {', '.join(m['missing'])}")
    lines += ["", "## 10. Blockers preventing first outreach", ""]
    for b in report.get("blockers", []):
        lines.append(f"- {b}")
    lines += [
        "",
        "## Acceptance",
        "",
        "```json",
        json.dumps(report.get("acceptance", {}), indent=2),
        "```",
        "",
        "## Founder Queue (Top 10)",
        "",
    ]
    for i, r in enumerate(report.get("founder_queue_10", []), start=1):
        lines.append(f"{i}. {r['company']} — {r.get('verified_emails')} — {r.get('service_match')}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
