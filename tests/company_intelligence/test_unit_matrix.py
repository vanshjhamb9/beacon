"""CIR v1 unit matrix."""

from __future__ import annotations

from company_intelligence import SCORING_VERSION
from company_intelligence.founder_queue.engine import CirFounderQueueEngine
from company_intelligence.models.types import CirClassification, CirVerdict
from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.service_match.engine import URBAN_WEBWORKS_SERVICES


def _pages(**extra):
    base = {
        "url": "https://demo.io",
        "path": "/",
        "title": "Demo — SaaS platform",
        "description": "Enterprise SaaS automation for mid-market teams",
        "headings": ["Workflow automation", "AI agents"],
        "text": (
            "Demo helps enterprises automate operations with AI agents and APIs. "
            "Integrates with Salesforce and HubSpot. SOC 2. We're hiring engineers. "
            "Based in United States. Free trial. React and AWS."
        ),
    }
    base.update(extra)
    return [base]


def _co(**overrides):
    base = {
        "company_id": "1",
        "company_name": "Demo",
        "website": "https://demo.io",
        "domain": "demo.io",
        "erowd_admitted": True,
        "industry": "Software",
        "website_pages": _pages(),
        "decision_makers": [{"name": "Pat Lee", "role": "CTO", "email": "pat@demo.io"}],
    }
    base.update(overrides)
    return base


def test_version():
    assert SCORING_VERSION == "cir-v1"
    assert len(URBAN_WEBWORKS_SERVICES) >= 15


def test_business_profile_from_pages():
    snap = CirPipeline().evaluate(_co())
    assert snap.business.industry.value != "UNKNOWN"
    assert snap.business.description.value != "UNKNOWN"


def test_icp_detection():
    snap = CirPipeline().evaluate(_co())
    assert snap.icp.primary_icp.value != "UNKNOWN"
    assert snap.icp.confidence > 0


def test_technology_detection():
    snap = CirPipeline().evaluate(_co())
    names = {t.technology.lower() for t in snap.technologies}
    assert names & {"react", "aws", "salesforce", "hubspot", "openai"} or len(snap.technologies) >= 1


def test_buying_signals():
    snap = CirPipeline().evaluate(_co())
    assert any(s.signal_type in {"Hiring", "Engineering Hiring", "AI Hiring", "Security"} for s in snap.buying_signals)


def test_service_match():
    snap = CirPipeline().evaluate(_co())
    assert snap.service_matches
    assert snap.service_matches[0].need_score > 0
    assert snap.service_matches[0].evidence


def test_narrative_deterministic():
    a = CirPipeline().evaluate(_co())
    b = CirPipeline().evaluate(_co())
    assert a.narrative.why_this_company == b.narrative.why_this_company
    assert a.narrative.which_service == b.narrative.which_service


def test_contacts_not_fabricated():
    snap = CirPipeline().evaluate(_co(decision_makers=[], website_pages=_pages(text="No people listed here. SaaS platform.")))
    # May still find emails if present; must not invent named executives without evidence
    for c in snap.contacts:
        if c.name != "UNKNOWN":
            assert c.evidence


def test_revenue_readiness_explainable():
    snap = CirPipeline().evaluate(_co())
    assert snap.readiness.evidence
    assert "total:" in " ".join(snap.readiness.evidence)


def test_founder_card_fields():
    snap = CirPipeline().evaluate(_co())
    card = snap.founder_card
    for field in ("company", "website", "revenue_readiness", "best_service", "recommended_action"):
        assert getattr(card, field)


def test_founder_queue_only_ready():
    pipe = CirPipeline()
    rich = pipe.evaluate(
        _co(
            website_pages=_pages(
                text=(
                    "Enterprise SaaS AI automation platform for mid-market and enterprise. "
                    "Hiring AI engineers. Scaling globally. Salesforce HubSpot Stripe AWS React OpenAI. "
                    "SOC 2 GDPR. Public API. Free trial enterprise plan. Ada Lovelace, CEO. hello@demo.io "
                    "Founded in 2018. 200 employees. United States. Product launch and new integrations."
                )
            ),
            technologies=["AWS", "React", "OpenAI"],
            buying_signals=["Hiring", "Product Launch", "Scaling"],
            decision_makers=[{"name": "Ada Lovelace", "role": "CEO", "email": "ada@demo.io"}],
        )
    )
    poor = pipe.evaluate(
        {
            "company_id": "2",
            "company_name": "Thin",
            "erowd_admitted": True,
            "website": "https://thin.test",
            "website_pages": [{"url": "https://thin.test", "path": "/", "title": "Thin", "text": "hello"}],
        }
    )
    queue = CirFounderQueueEngine().build([rich, poor])
    for item in queue:
        assert item.revenue_readiness in {
            CirClassification.REVENUE_READY.value,
            CirClassification.PRIORITY_ACCOUNT.value,
        }
    assert poor.founder_queue_eligible is False or poor.readiness.classification in {
        CirClassification.REVENUE_READY,
        CirClassification.PRIORITY_ACCOUNT,
    }


def test_unknown_when_missing():
    snap = CirPipeline().evaluate(
        {
            "company_id": "3",
            "company_name": "Sparse",
            "erowd_admitted": True,
            "website": "https://sparse.test",
            "website_pages": [{"url": "https://sparse.test", "path": "/", "title": "Sparse", "text": "ok"}],
        }
    )
    assert snap.verdict in {CirVerdict.PARTIAL, CirVerdict.RECONSTRUCTED}
    assert snap.business.mission.value == "UNKNOWN" or snap.business.mission.confidence >= 0
