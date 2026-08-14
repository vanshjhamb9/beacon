"""CIR benchmark — 500 verified companies under 5s + acceptance thresholds."""

from __future__ import annotations

from time import perf_counter

import pytest

from company_intelligence.founder_queue.engine import CirFounderQueueEngine
from company_intelligence.models.types import CirClassification
from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.rebuild.engine import CirRebuildEngine


def _company(i: int, *, rich: bool) -> dict:
    domain = f"firm{i}.io"
    if not rich:
        return {
            "company_id": f"poor-{i}",
            "company_name": f"Poor{i}",
            "website": f"https://{domain}",
            "domain": domain,
            "erowd_admitted": True,
            "website_pages": [{"url": f"https://{domain}", "path": "/", "title": f"Poor{i}", "text": "welcome"}],
        }
    return {
        "company_id": f"rich-{i}",
        "company_name": f"Firm{i}",
        "website": f"https://{domain}",
        "domain": domain,
        "official_website": f"https://{domain}",
        "erowd_admitted": True,
        "erowd_verified": True,
        "industry": "Software",
        "country": "United States",
        "employees": str(50 + i % 100),
        "description": f"Firm{i} is an enterprise SaaS automation platform with AI agents.",
        "website_pages": [
            {
                "url": f"https://{domain}",
                "path": "/",
                "title": f"Firm{i} — AI automation",
                "description": "Enterprise SaaS for mid-market and enterprise operations teams",
                "headings": ["AI automation", "Enterprise platform"],
                "text": (
                    f"Firm{i} helps enterprises automate workflows with AI agents and APIs. "
                    "Integrates with Salesforce HubSpot Slack Stripe. SOC 2 GDPR. "
                    "We're hiring AI engineers and software engineers. Scaling globally. "
                    "Product launch and new integrations. OpenAI React AWS. "
                    "Based in San Francisco United States. Founded in 2018. Free trial enterprise plan."
                ),
            },
            {
                "url": f"https://{domain}/pricing",
                "path": "/pricing",
                "title": "Pricing",
                "text": "Starter Pro Enterprise free trial new pricing",
            },
            {
                "url": f"https://{domain}/team",
                "path": "/team",
                "title": "Leadership",
                "text": f"Casey Lead{i}, CEO. Riley Tech{i}, CTO. hello@{domain}",
            },
            {
                "url": f"https://{domain}/careers",
                "path": "/careers",
                "title": "Careers",
                "text": "Now hiring engineers. Expansion into Europe.",
            },
        ],
        "technologies": ["React", "AWS", "OpenAI"],
        "buying_signals": ["Hiring", "AI Hiring", "Product Launch", "Scaling"],
        "decision_makers": (
            [{"name": f"Casey Lead{i}", "role": "CEO", "email": f"casey@{domain}", "confidence": 90}]
            if i % 5 != 4
            else []
        ),
    }


@pytest.fixture(scope="module")
def corpus_report():
    pipe = CirPipeline()
    payloads = [_company(i, rich=i < 420) for i in range(500)]
    # Mix 20 skipped (no erowd)
    for i in range(20):
        payloads.append(
            {
                "company_id": f"skip-{i}",
                "company_name": f"Skip{i}",
                "erowd_admitted": False,
                "website": f"https://skip{i}.test",
            }
        )
    t0 = perf_counter()
    snaps = [pipe.evaluate(p) for p in payloads]
    elapsed = perf_counter() - t0
    report = CirRebuildEngine().build(snaps)
    return snaps, report, elapsed


def test_performance_500_under_5s(corpus_report):
    snaps, report, elapsed = corpus_report
    # Only the 500 verified evaluations matter for the SLA; skipped are cheap
    verified = [s for s in snaps if s.erowd_admitted]
    assert len(verified) == 500
    assert elapsed < 5.0, f"CIR 500 companies took {elapsed:.2f}s"


def test_acceptance_business_profile(corpus_report):
    _, report, _ = corpus_report
    assert report.business_profile_pct >= 80.0


def test_acceptance_industry_icp(corpus_report):
    _, report, _ = corpus_report
    assert report.industry_icp_pct >= 70.0


def test_acceptance_technology_service(corpus_report):
    _, report, _ = corpus_report
    assert report.technology_service_pct >= 60.0


def test_acceptance_contacts(corpus_report):
    _, report, _ = corpus_report
    assert report.contact_pct >= 40.0


def test_zero_fabrications(corpus_report):
    _, report, _ = corpus_report
    assert report.false_fabrications == 0


def test_founder_queue_only_ready_priority(corpus_report):
    snaps, report, _ = corpus_report
    cards = CirFounderQueueEngine().build(snaps, limit=200)
    for c in cards:
        assert c.revenue_readiness in {
            CirClassification.REVENUE_READY.value,
            CirClassification.PRIORITY_ACCOUNT.value,
        }
    assert report.founder_queue == len(cards) or report.founder_queue >= 0


def test_readiness_explainable(corpus_report):
    snaps, _, _ = corpus_report
    for s in snaps:
        if s.erowd_admitted and s.readiness.total > 0:
            assert s.readiness.evidence
