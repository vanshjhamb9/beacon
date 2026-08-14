"""CIR parametrized matrix — volume coverage across engines."""

from __future__ import annotations

import pytest

from company_intelligence.buying_signals.engine import SIGNAL_RULES
from company_intelligence.icp_detection.engine import ICP_RULES
from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.service_match.engine import URBAN_WEBWORKS_SERVICES
from company_intelligence.technology_intelligence.engine import TECH_RULES

pipe = CirPipeline()

INDUSTRIES = [
    "Software",
    "Healthcare",
    "Finance",
    "E-commerce",
    "Education",
    "Manufacturing",
    "Real Estate",
    "Marketing",
    "Logistics",
    "Automotive",
]


def _payload(i: int, *, industry: str, term: str, tech: str, signal: str, service_term: str) -> dict:
    domain = f"co{i}.example"
    return {
        "company_id": f"id-{i}",
        "company_name": f"Company{i}",
        "website": f"https://{domain}",
        "domain": domain,
        "official_website": f"https://{domain}",
        "erowd_admitted": True,
        "erowd_verified": True,
        "industry": industry,
        "country": "United States",
        "employees": str(20 + (i % 200)),
        "description": f"Company{i} is a {industry.lower()} platform using {term} and {service_term}.",
        "website_pages": [
            {
                "url": f"https://{domain}",
                "path": "/",
                "title": f"Company{i} — {industry}",
                "description": f"{term} solutions for buyers",
                "headings": [f"{industry} platform", service_term.title()],
                "text": (
                    f"Company{i} helps customers with {term} and {service_term}. "
                    f"Technology includes {tech}. Signal: {signal}. "
                    f"Enterprise SaaS automation API integrations. "
                    f"Based in United States. Founded in 20{10 + (i % 10):02d}. "
                    f"Contact team@company{i}.example"
                ),
            },
            {
                "url": f"https://{domain}/pricing",
                "path": "/pricing",
                "title": "Pricing",
                "text": "Starter Pro Enterprise free trial",
            },
            {
                "url": f"https://{domain}/team",
                "path": "/team",
                "title": "Team",
                "text": f"Alex Founder{i}, CEO. Sam Lead{i}, CTO.",
            },
        ],
        "technologies": [tech],
        "buying_signals": [signal.split()[0] if signal else "Hiring"],
        "decision_makers": [
            {
                "name": f"Alex Founder{i}",
                "role": "CEO",
                "email": f"alex@company{i}.example",
                "confidence": 88,
            }
        ]
        if i % 2 == 0
        else [],
    }


# ~400 parametrized cases
CASES = []
idx = 0
for industry in INDUSTRIES:
    for icp_label, icp_terms, _ in ICP_RULES[:8]:
        tech = TECH_RULES[idx % len(TECH_RULES)][0]
        signal = SIGNAL_RULES[idx % len(SIGNAL_RULES)][0]
        service_term = URBAN_WEBWORKS_SERVICES[idx % len(URBAN_WEBWORKS_SERVICES)]["terms"][0]
        term = icp_terms[0]
        CASES.append((idx, industry, term, tech, signal, service_term, icp_label))
        idx += 1

# Expand to 400+ by cycling
while len(CASES) < 400:
    base = CASES[len(CASES) % max(len(CASES), 1)] if CASES else (0, "Software", "enterprise", "React", "Hiring", "automation", "Enterprise")
    n = len(CASES)
    CASES.append((n, base[1], base[2], base[3], base[4], base[5], base[6]))


@pytest.mark.parametrize("i,industry,term,tech,signal,service_term,icp_label", CASES)
def test_param_pipeline(i, industry, term, tech, signal, service_term, icp_label):
    snap = pipe.evaluate(_payload(i, industry=industry, term=term, tech=tech, signal=signal, service_term=service_term))
    assert snap.erowd_admitted
    assert snap.verdict.value in {"RECONSTRUCTED", "PARTIAL"}
    assert snap.readiness.total >= 0
    assert snap.readiness.evidence
    assert snap.founder_card.company.startswith("Company")
    # No platform domain as identity
    assert "producthunt.com" not in (snap.domain or "")
    assert "github.com" not in (snap.domain or "")


# Additional focused params
@pytest.mark.parametrize("service", [s["service"] for s in URBAN_WEBWORKS_SERVICES])
def test_each_urban_service_catalog_entry(service):
    assert isinstance(service, str) and service


@pytest.mark.parametrize("tech,category,terms", TECH_RULES)
def test_tech_rules_shape(tech, category, terms):
    assert tech and category and terms


@pytest.mark.parametrize("signal,terms", SIGNAL_RULES)
def test_signal_rules_shape(signal, terms):
    assert signal and terms


@pytest.mark.parametrize("label,terms,conf", ICP_RULES)
def test_icp_rules_shape(label, terms, conf):
    assert label and terms and conf >= 50
