"""Buyer-first cybersecurity discovery pipeline. No outreach. No scanning."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from packages.cybersecurity_discovery.classifier import classify_raw
from packages.cybersecurity_discovery.enrich import (
    apply_text_contacts,
    apply_website_contacts,
    extract_company_urls,
    maybe_company_from_url,
)
from packages.cybersecurity_discovery.gates import (
    FUNNEL_STAGES,
    classify_contactability,
    evaluate_gates,
)
from packages.cybersecurity_discovery.schema import (
    CyberOpportunity,
    FinalVerdict,
    OpportunityType,
    utc_now_iso,
)
from packages.cybersecurity_discovery.sources import USER_AGENT, discover_sources, fetch_url

logger = logging.getLogger(__name__)

TIMEOUT = 12.0


@dataclass
class PipelineResult:
    generated_at: str
    sales_ready: list[CyberOpportunity] = field(default_factory=list)
    needs_research: list[CyberOpportunity] = field(default_factory=list)
    rejected: list[CyberOpportunity] = field(default_factory=list)
    funnel: dict[str, int] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    @property
    def all_opportunities(self) -> list[CyberOpportunity]:
        return self.sales_ready + self.needs_research + self.rejected


async def run_cybersecurity_discovery(
    *,
    limit: int = 80,
    enrich: bool = True,
    preloaded: list | None = None,
) -> PipelineResult:
    observed = utc_now_iso()
    raw_items = list(preloaded) if preloaded is not None else await discover_sources(limit=limit)
    opportunities: list[CyberOpportunity] = []
    funnel: Counter[str] = Counter()
    funnel["DISCOVERED"] = len(raw_items)

    client: httpx.AsyncClient | None = None
    if enrich:
        client = httpx.AsyncClient(
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        )
    try:
        ddg_enriched = 0
        for raw in raw_items:
            if enrich and client is not None and raw.source_name == "DuckDuckGo" and raw.body == raw.title and ddg_enriched < 10:
                try:
                    page_html = await fetch_url(client, raw.source_url)
                    if page_html:
                        raw.body = page_html[:4000]
                        ddg_enriched += 1
                except Exception:
                    pass
            opp = classify_raw(raw, observed)
            if opp.funnel_stage == "BUYING_EVENT":
                funnel["BUYING_EVENT"] += 1
            if opp.funnel_stage == "REJECT" or (
                opp.final_verdict == FinalVerdict.REJECT.value and opp.rejection_reason
            ):
                funnel["REJECT"] += 1
                opportunities.append(opp)
                continue

            apply_text_contacts(opp, raw.text)
            extra_urls = extract_company_urls(raw.text)
            if extra_urls and not opp.company_url:
                opp.company_url = extra_urls[0]

            if enrich and client is not None:
                if opp.company_url:
                    html = await fetch_url(client, opp.company_url)
                    if html:
                        apply_website_contacts(opp, html, opp.company_url, verified=True)
                elif extra_urls:
                    html = await fetch_url(client, extra_urls[0])
                    if html:
                        apply_website_contacts(opp, html, extra_urls[0], verified=True)
                elif opp.source_url and not opp.email and not _is_platform_url(opp.source_url):
                    thread_html = await fetch_url(client, opp.source_url)
                    if thread_html:
                        apply_text_contacts(opp, thread_html)
                        thread_urls = extract_company_urls(thread_html)
                        if thread_urls and not opp.company_url:
                            site_html = await fetch_url(client, thread_urls[0])
                            if site_html:
                                apply_website_contacts(opp, site_html, thread_urls[0], verified=True)

            if opp.company_url and _is_platform_url(opp.company_url):
                opp.company_url = None
                opp.company_verified = False
                if (opp.company or "").lower() in {"redditstatic", "reddit", "ycombinator"}:
                    opp.company = None
            if not opp.company:
                opp.company = maybe_company_from_url(opp.company_url) or raw.company_hint
            if opp.company and opp.company_url:
                opp.company_verified = True

            classify_contactability(opp)
            opp = evaluate_gates(opp)
            funnel[opp.funnel_stage] += 1
            opportunities.append(opp)
    finally:
        if client is not None:
            await client.aclose()

    sales_ready = [
        o for o in opportunities
        if o.final_verdict == FinalVerdict.SALES_READY.value
        and o.opportunity_type != OpportunityType.SECURITY_PARTNER.value
    ]
    needs_research = [
        o for o in opportunities if o.final_verdict == FinalVerdict.NEEDS_RESEARCH.value
    ]
    rejected = [o for o in opportunities if o.final_verdict == FinalVerdict.REJECT.value]

    partners = [
        o for o in opportunities if o.opportunity_type == OpportunityType.SECURITY_PARTNER.value
    ]
    counters = {
        "TOTAL_DISCOVERED": len(raw_items),
        "BUYING_EVENTS": sum(1 for o in opportunities if o.buying_event_verified),
        "VERIFIED_REQUIREMENTS": sum(1 for o in opportunities if o.requirement_verified),
        "HOT": sum(1 for o in opportunities if o.intent_level == "HOT" or o.currentness == "HOT"),
        "HIGH_INTENT": sum(1 for o in opportunities if o.intent_level in {"HOT", "HIGH"}),
        "CONTACTABLE": sum(1 for o in opportunities if o.contactability in {"HIGH", "MEDIUM", "LOW"}),
        "SALES_READY": len(sales_ready),
        "PARTNER_OPPORTUNITIES": len(partners),
        "NEEDS_RESEARCH": len(needs_research),
        "REJECTED": len(rejected),
        "generated_at": observed,
        "lane": "CYBER",
    }
    funnel_out = {stage: int(funnel.get(stage, 0)) for stage in FUNNEL_STAGES}
    funnel_out["REJECT"] = len(rejected)
    funnel_out["NEEDS_RESEARCH"] = len(needs_research)

    logger.info(
        "Cyber discovery complete: discovered=%s sales_ready=%s needs_research=%s rejected=%s",
        counters["TOTAL_DISCOVERED"],
        counters["SALES_READY"],
        counters["NEEDS_RESEARCH"],
        counters["REJECTED"],
    )
    return PipelineResult(
        generated_at=observed,
        sales_ready=sales_ready,
        needs_research=needs_research,
        rejected=rejected,
        funnel=funnel_out,
        counters=counters,
    )


def _is_platform_url(url: str | None) -> bool:
    if not url:
        return False
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == p or host.endswith("." + p) or "reddit" in host for p in ("reddit.com", "redditstatic.com", "news.ycombinator.com", "github.com", "stackexchange.com"))
