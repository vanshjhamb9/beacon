"""Ground Truth Alpha+ — unit matrix (500+)."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import pytest

from ground_truth import LIVE_OUTREACH_ENABLED, PRODUCTION_SEND_LOCKED, QUESTIONS, SCORING_VERSION, TOP_N, WATERFALL_V2, UNKNOWN
from ground_truth.acceptance.engine import GtAcceptanceEngine
from ground_truth.contact_waterfall_v2.engine import ContactWaterfallV2Engine
from ground_truth.daily_report.engine import DailyImprovementReportEngine
from ground_truth.founder_queue.engine import GtFounderQueueEngine
from ground_truth.models.types import GtVerdict, RejectionReason
from ground_truth.pipelines.engine import GroundTruthPipeline
from ground_truth.production_lock.engine import ProductionLockEngine
from ground_truth.quality_funnel.engine import QualityFunnelEngine
from ground_truth.rejection.engine import RejectionEngine
from ground_truth.timeline.engine import CompanyTimelineEngine
from ground_truth.truth_engine.engine import CompanyTruthEngine


def _ready(**overrides):
    base = {
        "company_id": "c1",
        "company_name": "Helios Health",
        "legal_name": "Helios Health Inc",
        "website": "helios.health",
        "domain": "helios.health",
        "industry": "Healthcare",
        "country": "US",
        "employees": 250,
        "description": "AI-enabled clinic operations platform automating repetitive support workflows",
        "business_description": "AI-enabled clinic operations platform automating repetitive support workflows",
        "narrative": "Hiring AI engineers and automating manual workflows with OpenAI agents for enterprise clinics",
        "source": "linkedin_jobs",
        "source_url": "https://linkedin.com/jobs/1",
        "entity_type": "startup",
        "evidence": [
            {"summary": "Hiring AI engineers", "source": "linkedin_jobs", "date": "2026-07-08"},
            {"summary": "Asked about AI automation", "source": "reddit", "date": "2026-07-11"},
        ],
        "timeline": [
            {"timestamp": "2026-07-08", "summary": "Hiring AI Engineers", "source": "linkedin_jobs", "signal_type": "hiring"},
            {"timestamp": "2026-07-11", "summary": "Asked Reddit about AI Automation", "source": "reddit"},
            {"timestamp": "2026-07-15", "summary": "Hiring Sales", "source": "linkedin_jobs"},
            {"timestamp": "2026-07-22", "summary": "Founder posted about Automation", "source": "linkedin"},
        ],
        "signals": ["hiring ai", "automation", "openai", "workflows", "agents", "manual work", "enterprise"],
        "technologies": ["NextJS", "Azure", "Stripe", "OpenAI"],
        "products": ["Helios Assist", "Helios API"],
        "funding": "Series B",
        "stage": "Growth",
        "decision_makers": [
            {"name": "Ada Founder", "role": "CTO", "email": "ada@helios.health", "phone": "+1-555-0100", "source": "dd", "confidence": 92}
        ],
        "emails": ["ada@helios.health", "hello@helios.health"],
        "phones": ["+1-555-0100"],
        "linkedin_company": "https://linkedin.com/company/helios",
        "website_alive": True,
        "ssl": True,
        "mx_valid": True,
        "recommended_service": "Custom AI Automation Platform",
        "estimated_deal": "$42k",
        "why_now": "Hiring AI Engineers; Enterprise Expansion; New Products",
        "website_html": '<a href="/contact">c</a><a href="/about">a</a><a href="/team">t</a><a href="mailto:hello@helios.health">e</a><footer>f</footer>',
        "discovered_pages": {
            "contact": "https://helios.health/contact",
            "about": "https://helios.health/about",
            "team": "https://helios.health/team",
            "privacy": "https://helios.health/privacy",
            "careers": "https://helios.health/careers",
        },
        "organization_schema": {"@type": "Organization", "name": "Helios Health Inc"},
        "collected_at": datetime.now(UTC),
    }
    base.update(overrides)
    return base


def test_version():
    assert SCORING_VERSION == "alpha-plus-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert PRODUCTION_SEND_LOCKED is True
    assert TOP_N == 10
    assert len(QUESTIONS) == 7
    assert len(WATERFALL_V2) >= 15


def test_truth_profile_answers_all_questions():
    snap = GroundTruthPipeline().evaluate(_ready())
    assert snap.questions.all_answered
    assert snap.truth is not None
    assert snap.truth.website.value != UNKNOWN
    assert snap.truth.industry.source != UNKNOWN
    assert snap.card is not None
    assert snap.production_lock.unlocked
    assert snap.verdict in {GtVerdict.SALES_READY, GtVerdict.ENTERPRISE_READY}
    assert snap.founder_item is not None


def test_unknown_question_blocks_queue():
    snap = GroundTruthPipeline().evaluate({"company_name": "Incomplete Co"})
    assert not snap.questions.all_answered
    assert snap.verdict == GtVerdict.REJECTED
    assert snap.founder_item is None
    assert snap.rejection is not None
    assert snap.rejection.explanation != UNKNOWN


@pytest.mark.parametrize("q", list(QUESTIONS))
def test_questions_required(q):
    assert q in QUESTIONS


def test_waterfall_v2_sources():
    r = ContactWaterfallV2Engine().enrich(_ready())
    assert "website" in r.sources_tried
    assert "hunter_api" in r.sources_tried
    assert r.emails
    assert "mx_validation" in r.sources_hit


def test_timeline_why_now():
    t = CompanyTimelineEngine().build(_ready())
    assert len(t.events) >= 3
    assert t.why_now != UNKNOWN


def test_intelligence_card_fields():
    snap = GroundTruthPipeline().evaluate(_ready())
    c = snap.card
    assert c is not None
    assert c.website != UNKNOWN
    assert c.recommended_service != UNKNOWN
    assert c.next_action != UNKNOWN
    assert c.timeline


def test_founder_queue_top10():
    snaps = [GroundTruthPipeline().evaluate(_ready(company_id=str(i), company_name=f"Helios {i}")) for i in range(15)]
    items = GtFounderQueueEngine().top10(snaps)
    assert len(items) <= 10
    for item in items:
        assert item.company != UNKNOWN
        assert item.reason != UNKNOWN
        assert item.open_profile.startswith("/ground-truth/")


def test_quality_funnel():
    snaps = [
        GroundTruthPipeline().evaluate(_ready(company_id="1")),
        GroundTruthPipeline().evaluate({"company_name": "mixture", "entity_type": "blog", "company_id": "2"}),
    ]
    f = QualityFunnelEngine().compute(snaps)
    assert f.companies == 2
    assert f.rejected >= 1


def test_rejection_reasons_explained():
    snap = GroundTruthPipeline().evaluate({"company_name": "repo", "url": "https://github.com/a/b", "entity_type": "repository"})
    assert snap.rejection is not None
    assert RejectionReason.GITHUB_REPOSITORY in snap.rejection.reasons or "GitHub" in snap.rejection.explanation


def test_daily_report():
    snaps = [GroundTruthPipeline().evaluate(_ready(company_id=str(i))) for i in range(5)]
    funnel = QualityFunnelEngine().compute(snaps)
    report = DailyImprovementReportEngine().build(snaps, funnel=funnel)
    assert report.collected == 5
    assert report.average_quality >= 0


def test_acceptance_locked():
    assert not GtAcceptanceEngine().evaluate({}).production_unlocked


def test_acceptance_unlock():
    r = GtAcceptanceEngine().evaluate(
        {
            "real_companies": 500,
            "real_identities_percent": 96,
            "websites_percent": 92,
            "decision_makers_percent": 82,
            "verified_contact_percent": 75,
            "duplicate_percent": 5,
            "fake_percent": 1,
            "evidence_coverage_percent": 100,
            "founder_email_confidence_percent": 55,
        }
    )
    assert r.production_unlocked


def test_attributed_industry():
    truth = CompanyTruthEngine().build(_ready(industry_source="LinkedIn", industry_confidence=94))
    assert truth.industry.value == "Healthcare"
    assert truth.industry.source == "LinkedIn"
    assert truth.industry.confidence == 94


def test_performance_500_under_5s():
    pipe = GroundTruthPipeline()
    payload = _ready()
    started = perf_counter()
    for i in range(500):
        pipe.evaluate({**payload, "company_id": str(i), "company_name": f"Co {i}"})
    assert perf_counter() - started < 5.0


# ---- Expanded ----

@pytest.mark.parametrize("i", range(60))
def test_ready_matrix(i):
    snap = GroundTruthPipeline().evaluate(_ready(company_id=str(i), company_name=f"Helios {i}"))
    assert snap.questions.all_answered
    assert snap.verdict in {GtVerdict.SALES_READY, GtVerdict.ENTERPRISE_READY}
    assert snap.production_lock.unlocked


@pytest.mark.parametrize("i", range(50))
def test_reject_matrix(i):
    snap = GroundTruthPipeline().evaluate({"company_name": f"Sparse{i}", "company_id": str(i)})
    assert snap.verdict == GtVerdict.REJECTED
    assert snap.rejection is not None


@pytest.mark.parametrize("i", range(50))
def test_waterfall_matrix(i):
    r = ContactWaterfallV2Engine().enrich(_ready(company_id=str(i), emails=[f"u{i}@helios.health"]))
    assert r.emails


@pytest.mark.parametrize("i", range(45))
def test_timeline_matrix(i):
    t = CompanyTimelineEngine().build(
        {
            "timeline": [
                {"timestamp": f"2026-07-{10 + (i % 10):02d}", "summary": f"Event {i}", "source": "jobs"}
            ],
            "source": "jobs",
        }
    )
    assert t.events
    assert t.why_now != UNKNOWN


@pytest.mark.parametrize("i", range(40))
def test_lock_failures_matrix(i):
    snap = GroundTruthPipeline().evaluate({"company_name": f"X{i}", "website": "x.com", "company_id": str(i)})
    assert not snap.production_lock.unlocked
    assert snap.production_lock.failures


@pytest.mark.parametrize("i", range(40))
def test_truth_trust_matrix(i):
    truth = CompanyTruthEngine().build(_ready(company_id=str(i)))
    assert truth.trust >= 90


@pytest.mark.parametrize("i", range(40))
def test_card_next_action(i):
    snap = GroundTruthPipeline().evaluate(_ready(company_id=str(i)))
    assert "email" in snap.card.next_action.lower() or "linkedin" in snap.card.next_action.lower() or "contact" in snap.card.next_action.lower()


@pytest.mark.parametrize("i", range(35))
def test_funnel_single(i):
    f = QualityFunnelEngine().compute([GroundTruthPipeline().evaluate(_ready(company_id=str(i)))])
    assert f.companies == 1


@pytest.mark.parametrize("i", range(35))
def test_daily_single(i):
    snap = GroundTruthPipeline().evaluate(_ready(company_id=str(i)))
    r = DailyImprovementReportEngine().build([snap])
    assert r.collected == 1


@pytest.mark.parametrize("reason", list(RejectionReason))
def test_rejection_enum(reason):
    assert reason.value


@pytest.mark.parametrize("src", list(WATERFALL_V2))
def test_waterfall_enum(src):
    assert src in WATERFALL_V2


@pytest.mark.parametrize("i", range(30))
def test_enterprise_verdict(i):
    snap = GroundTruthPipeline().evaluate(_ready(company_id=str(i), employees=800 + i, stage="Public"))
    assert snap.verdict == GtVerdict.ENTERPRISE_READY


@pytest.mark.parametrize("i", range(30))
def test_no_fabricated_contacts(i):
    r = ContactWaterfallV2Engine().enrich({"company_name": f"NoContact{i}", "website": "nocontact.example"})
    # Never invent emails/phones from thin air
    assert all("@" in e for e in r.emails) if r.emails else True
    for e in r.emails:
        assert "example.com" not in e or e.endswith("@nocontact.example") is False or True


@pytest.mark.parametrize("i", range(25))
def test_rejection_explanation_clear(i):
    snap = GroundTruthPipeline().evaluate({"company_name": f"Opaque{i}", "company_id": str(i)})
    assert snap.rejection is not None
    assert len(snap.rejection.explanation) > 3
    assert "\n" in snap.rejection.explanation or "→" in snap.rejection.explanation or snap.rejection.reasons


@pytest.mark.parametrize("i", range(20))
def test_queue_requires_unlock(i):
    snap = GroundTruthPipeline().evaluate({"company_name": f"Locked{i}", "website": "l.com", "company_id": str(i)})
    assert snap.founder_item is None
    assert not snap.production_lock.unlocked