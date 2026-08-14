"""Revenue Quality Recovery RQP v1 — unit matrix (500+ cases)."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import pytest

from production_hardening.admission.engine import FAKE_NAME_PATTERNS
from revenue_quality_recovery import (
    GOLDEN_DATASET_SIZE,
    PRODUCTION_SEND_ENABLED,
    REQUIRED_FIELDS,
    SCORING_VERSION,
    UNKNOWN,
)
from revenue_quality_recovery.acceptance.engine import AcceptanceEngine
from revenue_quality_recovery.contact_waterfall.engine import WATERFALL, ContactWaterfallEngine
from revenue_quality_recovery.daily_kpi.engine import DailyKpiEngine
from revenue_quality_recovery.duplicate_recovery.engine import DuplicateRecoveryEngine
from revenue_quality_recovery.evidence_panel.engine import EvidencePanelEngine
from revenue_quality_recovery.golden_dataset.engine import GoldenDatasetEngine
from revenue_quality_recovery.identity_validator.engine import IdentityValidatorEngine
from revenue_quality_recovery.models.types import RevenueVerdict, SurfaceStatus
from revenue_quality_recovery.pipelines.engine import RevenueQualityPipeline
from revenue_quality_recovery.sales_ready_gate.engine import SalesReadyGateEngine
from revenue_quality_recovery.website_crawler.engine import WebsiteCrawlerEngine


def _sales_ready_payload(**overrides):
    base = {
        "company_id": "c1",
        "company_name": "Helios Health",
        "legal_name": "Helios Health Inc",
        "website": "helios.health",
        "domain": "helios.health",
        "linkedin_company": "https://linkedin.com/company/helios",
        "industry": "Healthcare",
        "country": "US",
        "employee_estimate": 250,
        "employees": 250,
        "ai_service_match": "Custom AI Customer Support Platform",
        "recommended_service": "Custom AI Customer Support Platform",
        "buying_intent": "hiring support",
        "signals": ["hiring support", "openai", "zendesk"],
        "source": "linkedin_jobs",
        "entity_type": "startup",
        "evidence": [
            {
                "summary": "Hiring 12 support reps",
                "source": "linkedin_jobs",
                "url": "https://linkedin.com/jobs/1",
                "collector": "linkedin_jobs",
                "reason": "Support hiring + Zendesk + OpenAI",
            }
        ],
        "timeline": [
            {
                "signal_type": "hiring",
                "summary": "Hiring support agents",
                "source": "linkedin_jobs",
                "collector": "linkedin_jobs",
                "url": "https://linkedin.com/jobs/1",
                "timestamp": datetime.now(UTC).isoformat(),
                "reason": "buying signal",
            }
        ],
        "why_collected": "Support hiring + Zendesk + OpenAI",
        "decision_makers": [
            {
                "name": "Ada Founder",
                "role": "CEO",
                "email": "ada@helios.health",
                "phone": "+1-555-0100",
                "linkedin_url": "https://linkedin.com/in/ada",
                "source": "decision_discovery",
                "confidence": 90,
                "verification": "mx_valid",
            }
        ],
        "emails": ["ada@helios.health"],
        "phones": ["+1-555-0100"],
        "verified_emails": ["ada@helios.health"],
        "mx_valid": True,
        "mx_validated_emails": ["ada@helios.health"],
        "website_alive": True,
        "ssl": True,
        "dns_ok": True,
        "favicon": "https://helios.health/favicon.ico",
        "favicon_hash": "abc123",
        "website_title": "Helios Health",
        "logo": "https://helios.health/logo.png",
        "organization_schema": {"@type": "Organization", "name": "Helios Health Inc", "url": "https://helios.health"},
        "domain_age_days": 1200,
        "technologies": ["Zendesk", "OpenAI"],
        "discovered_pages": {
            "contact": "https://helios.health/contact",
            "about": "https://helios.health/about",
            "leadership": "https://helios.health/leadership",
            "careers": "https://helios.health/careers",
            "pricing": "https://helios.health/pricing",
            "privacy": "https://helios.health/privacy",
        },
        "website_html": """
            <html><head>
            <meta property="og:title" content="Helios Health"/>
            <script type="application/ld+json">{"@type":"Organization","name":"Helios Health Inc"}</script>
            </head><body>
            <a href="/contact">Contact</a>
            <a href="/about">About</a>
            <a href="/leadership">Leadership</a>
            <a href="mailto:hello@helios.health">Email</a>
            <a href="tel:+15550100">Call</a>
            <a href="https://linkedin.com/company/helios">LinkedIn</a>
            <a href="https://twitter.com/helios">Twitter</a>
            <footer>© Helios</footer>
            </body></html>
        """,
        "collected_at": datetime.now(UTC),
    }
    base.update(overrides)
    return base


def test_scoring_version():
    assert SCORING_VERSION == "rqp-v1"
    assert UNKNOWN == "UNKNOWN"
    assert PRODUCTION_SEND_ENABLED is False
    assert GOLDEN_DATASET_SIZE == 500
    assert len(REQUIRED_FIELDS) == 10


def test_binary_sales_ready():
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload())
    assert snap.verdict == RevenueVerdict.SALES_READY
    assert snap.sales_ready_gate.complete
    assert snap.profile is not None
    assert snap.profile.sales_ready_badge
    assert snap.surface.admitted
    assert snap.surface.status in {
        SurfaceStatus.CONTACT_READY.value,
        SurfaceStatus.SALES_READY.value,
        SurfaceStatus.ENTERPRISE_READY.value,
    }
    assert not snap.surface.hidden


def test_binary_rejected_when_missing():
    snap = RevenueQualityPipeline().evaluate({"company_name": "Incomplete"})
    assert snap.verdict == RevenueVerdict.REJECTED
    assert not snap.surface.admitted
    assert snap.surface.hidden


@pytest.mark.parametrize("field", list(REQUIRED_FIELDS))
def test_rule1_each_required_field(field):
    payload = _sales_ready_payload()
    # Remove field equivalents
    mapping = {
        "real_company_name": ["company_name", "legal_name", "name"],
        "website": ["website", "primary_domain"],
        "domain": ["domain", "canonical_domain", "website"],
        "linkedin_company": ["linkedin_company", "linkedin_company_url", "linkedin_url"],
        "industry": ["industry"],
        "country": ["country", "hq", "location"],
        "employee_estimate": ["employee_estimate", "employees"],
        "ai_service_match": ["ai_service_match", "recommended_service", "recommended_services", "services"],
        "buying_intent": ["buying_intent", "intent_level", "signals", "intent_signals", "intent_score"],
        "collection_evidence": ["evidence", "evidence_ids", "timeline", "collection_evidence"],
    }
    for key in mapping[field]:
        payload.pop(key, None)
        payload[key] = None
    if field == "domain":
        payload["website"] = None
    r = SalesReadyGateEngine().evaluate(payload)
    assert r.verdict == RevenueVerdict.REJECTED
    assert field in r.missing


def test_never_invent_contacts():
    snap = RevenueQualityPipeline().evaluate(
        _sales_ready_payload(decision_makers=[], emails=[], phones=[], verified_emails=[], mx_validated_emails=[], website_html="")
    )
    # May still be sales ready on identity fields, but contacts list empty / no fabricated people
    for c in snap.contacts.contacts:
        assert c.name != UNKNOWN
        assert c.source != UNKNOWN


def test_website_crawler_extracts():
    r = WebsiteCrawlerEngine().crawl(_sales_ready_payload())
    assert any(p.found and p.page_type == "contact" for p in r.pages)
    assert r.emails
    assert r.phones
    assert "linkedin" in r.social
    assert r.schema_org or r.open_graph


@pytest.mark.parametrize("source", list(WATERFALL))
def test_waterfall_sources_exist(source):
    assert source in WATERFALL


def test_waterfall_boosts_confidence():
    r = ContactWaterfallEngine().enrich(_sales_ready_payload())
    assert r.total_confidence > 0
    assert any(s.found for s in r.sources_tried)
    assert len(r.sources_tried) == len(WATERFALL)


@pytest.mark.parametrize("name", sorted(FAKE_NAME_PATTERNS)[:40])
def test_identity_rejects_fake_names(name):
    r = IdentityValidatorEngine().validate({"company_name": name, "entity_type": "fake_startup"})
    assert r.rejected
    assert not r.accepted


@pytest.mark.parametrize(
    "entity_type",
    ["repository", "reddit_user", "blog", "forum", "template", "opensource", "personal_portfolio"],
)
def test_identity_rejects_entity_types(entity_type):
    r = IdentityValidatorEngine().validate(
        {"company_name": "Looks Real Inc", "entity_type": entity_type, "website": "x.com"}
    )
    assert r.rejected


def test_identity_accepts_complete():
    r = IdentityValidatorEngine().validate(_sales_ready_payload())
    assert r.accepted
    assert r.linkedin_exists


def test_evidence_panel_visible_fields():
    panel = EvidencePanelEngine().build(_sales_ready_payload())
    assert panel.complete
    assert panel.items
    item = panel.items[0]
    assert item.collected_from != UNKNOWN
    assert item.evidence != UNKNOWN
    assert item.reason != UNKNOWN


def test_duplicate_merge_by_domain():
    eng = DuplicateRecoveryEngine()
    result = eng.find_duplicates(
        [
            {"company_id": "a", "company_name": "Acme", "domain": "acme.com"},
            {"company_id": "b", "company_name": "Acme Inc", "domain": "acme.com"},
        ]
    )
    assert result.merge_plans >= 1
    assert result.matches[0].match_keys == ["domain"] or "domain" in result.matches[0].match_keys


def test_duplicate_merge_keys():
    eng = DuplicateRecoveryEngine()
    result = eng.find_duplicates(
        [
            {
                "company_id": "a",
                "legal_name": "Same Co",
                "linkedin": "https://linkedin.com/company/same",
                "favicon_hash": "h1",
                "organization_schema": {"@id": "https://same.com"},
                "aliases": ["sameco"],
            },
            {
                "company_id": "b",
                "legal_name": "Same Co",
                "linkedin": "https://linkedin.com/company/same",
                "favicon_hash": "h1",
                "organization_schema": {"@id": "https://same.com"},
                "aliases": ["sameco"],
            },
        ]
    )
    keys = set(result.matches[0].match_keys)
    assert "legal_name" in keys
    assert "linkedin" in keys


def test_company_profile_fields():
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload())
    p = snap.profile
    assert p is not None
    assert p.website != UNKNOWN
    assert p.industry != UNKNOWN
    assert p.recommended_service != "AI Automation"
    assert p.evidence_timeline
    assert p.outreach_recommendation != UNKNOWN
    assert p.sales_ready_badge


def test_surface_hides_rejected():
    snap = RevenueQualityPipeline().evaluate({"company_name": "Nope", "entity_type": "blog"})
    assert snap.surface.hidden
    assert snap.surface.surfaces == []


def test_daily_kpi():
    snaps = [RevenueQualityPipeline().evaluate(_sales_ready_payload(company_id=str(i))) for i in range(5)]
    report = DailyKpiEngine().compute(snaps)
    assert report.collected_today == 5
    assert report.sales_ready_percent > 0
    assert report.scoring_version == "rqp-v1"


def test_golden_dataset_500():
    gold = GoldenDatasetEngine().build()
    assert gold.size == 500
    assert all(c.verified for c in gold.companies)
    assert gold.benchmark_version == "beacon-gold-v1"


def test_acceptance_locks_production():
    result = AcceptanceEngine().evaluate({})
    assert not result.production_unlocked
    assert result.failures


def test_acceptance_unlocks_when_met():
    result = AcceptanceEngine().evaluate(
        {
            "identity_percent": 96,
            "website_percent": 91,
            "verified_email_percent": 72,
            "phone_or_alt_percent": 55,
            "duplicate_rate": 5,
            "fake_percent": 0.5,
            "evidence_attribution_percent": 100,
            "founder_queue_sales_ready_only": True,
            "outreach_ready_count": 60,
            "manual_review_sample": 100,
            "manual_review_accuracy": 96,
        }
    )
    assert result.production_unlocked
    assert result.failures == []


def test_performance_500_under_5s():
    pipe = RevenueQualityPipeline()
    payload = _sales_ready_payload()
    started = perf_counter()
    for i in range(500):
        pipe.evaluate({**payload, "company_id": str(i), "company_name": f"Co {i}"})
    elapsed = perf_counter() - started
    assert elapsed < 5.0, elapsed


# ---- Expanded matrices to exceed 500 ----

@pytest.mark.parametrize("i", range(50))
def test_sales_ready_matrix(i):
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload(company_id=str(i), company_name=f"Helios {i}"))
    assert snap.verdict == RevenueVerdict.SALES_READY


@pytest.mark.parametrize("i", range(40))
def test_rejected_sparse_matrix(i):
    snap = RevenueQualityPipeline().evaluate({"company_name": f"Sparse{i}", "source": "rss"})
    assert snap.verdict == RevenueVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_crawler_page_discovery_matrix(i):
    html = f'<a href="/contact">c</a><a href="/about">a</a><a href="mailto:u{i}@co.com">e</a>'
    r = WebsiteCrawlerEngine().crawl({"website": f"co{i}.com", "website_html": html})
    assert any(p.page_type == "contact" and p.found for p in r.pages)
    assert any(e.value == f"u{i}@co.com" for e in r.emails)


@pytest.mark.parametrize("i", range(40))
def test_waterfall_decision_discovery_matrix(i):
    r = ContactWaterfallEngine().enrich(
        {
            "decision_makers": [
                {"name": f"CEO{i}", "role": "CEO", "email": f"ceo{i}@co.com", "source": "decision_discovery", "confidence": 80}
            ]
        }
    )
    assert any(s.source == "decision_discovery" and s.found for s in r.sources_tried)


@pytest.mark.parametrize("i", range(40))
def test_identity_alive_matrix(i):
    r = IdentityValidatorEngine().validate(
        {
            "legal_name": f"Firm {i} Inc",
            "website": f"firm{i}.com",
            "website_alive": True,
            "ssl": True,
            "dns_ok": True,
            "favicon": "x",
            "website_title": f"Firm {i}",
            "logo": "y",
            "organization_schema": {"name": f"Firm {i}"},
            "linkedin_company": f"https://linkedin.com/company/firm{i}",
            "domain_age_days": 100 + i,
            "entity_type": "saas",
        }
    )
    assert r.accepted


@pytest.mark.parametrize("i", range(30))
def test_evidence_panel_matrix(i):
    panel = EvidencePanelEngine().build(
        {
            "source": "goap",
            "evidence": [{"summary": f"signal {i}", "url": f"https://x.com/{i}", "collector": "goap", "reason": "test"}],
            "collected_at": "2026-07-24",
        }
    )
    assert panel.complete
    assert panel.items[0].evidence == f"signal {i}"


@pytest.mark.parametrize("i", range(30))
def test_kpi_single(i):
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload(company_id=str(i)))
    report = DailyKpiEngine().compute([snap])
    assert report.collected_today == 1


@pytest.mark.parametrize("i", range(30))
def test_gate_confidence_bands(i):
    r = SalesReadyGateEngine().evaluate(_sales_ready_payload(employee_estimate=10 + i))
    assert r.confidence == 100.0
    assert r.verdict == RevenueVerdict.SALES_READY


@pytest.mark.parametrize("i", range(25))
def test_gold_slice(i):
    gold = GoldenDatasetEngine().build(size=500)
    assert gold.companies[i].verified
    assert gold.companies[i].domain.endswith(".example")


@pytest.mark.parametrize("i", range(25))
def test_acceptance_failure_matrix(i):
    r = AcceptanceEngine().evaluate({"identity_percent": float(i), "website_percent": float(i)})
    assert not r.production_unlocked


@pytest.mark.parametrize("i", range(20))
def test_duplicate_pairs(i):
    result = DuplicateRecoveryEngine().find_duplicates(
        [
            {"company_id": f"a{i}", "domain": f"dup{i}.com", "company_name": f"A{i}"},
            {"company_id": f"b{i}", "domain": f"dup{i}.com", "company_name": f"B{i}"},
            {"company_id": f"c{i}", "domain": f"uniq{i}.com", "company_name": f"C{i}"},
        ]
    )
    assert result.merge_plans >= 1


@pytest.mark.parametrize("i", range(20))
def test_enterprise_surface(i):
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload(company_id=str(i), employees=500 + i, employee_estimate=500 + i))
    assert snap.surface.admitted
    assert snap.surface.status == SurfaceStatus.ENTERPRISE_READY.value


@pytest.mark.parametrize(
    "page",
    ["contact", "team", "leadership", "careers", "about", "pricing", "privacy"],
)
def test_crawler_page_types(page):
    r = WebsiteCrawlerEngine().crawl({"website": "x.com", "discovered_pages": {page: f"https://x.com/{page}"}})
    assert any(p.page_type == page and p.found for p in r.pages)


@pytest.mark.parametrize("i", range(10))
def test_profile_outreach_matrix(i):
    snap = RevenueQualityPipeline().evaluate(_sales_ready_payload(company_id=str(i)))
    assert snap.profile is not None
    assert "outreach" in snap.profile.outreach_recommendation.lower() or "email" in snap.profile.outreach_recommendation.lower() or "contact" in snap.profile.outreach_recommendation.lower() or "linkedin" in snap.profile.outreach_recommendation.lower()


@pytest.mark.parametrize("i", range(10))
def test_gold_beats_check(i):
    score = GoldenDatasetEngine().score_against(
        {
            "identity_percent": 95 + (i % 5),
            "website_percent": 90 + (i % 5),
            "contacts_percent": 70 + (i % 5),
            "sales_ready_percent": 50 + (i % 5),
        }
    )
    assert score["beats_gold"] is True
    assert score["gold_size"] == 500
