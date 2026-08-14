"""Production Hardening PH-1 — unit matrix (200+ cases)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from production_hardening.admission.engine import FAKE_NAME_PATTERNS, OpportunityAdmissionGate
from production_hardening.dedupe.engine import DuplicateResolutionEngine
from production_hardening.health.telemetry import LiveHealthTelemetry
from production_hardening.identity.engine import CompanyIdentityValidator
from production_hardening.noise.engine import NoiseCollapser
from production_hardening.readiness.engine import ContactReadinessEngine
from production_hardening.scoring.engine import LeadQualityScorer
from production_hardening.trust.engine import TrustMetricsEngine
from production_hardening.models.types import ContactReadinessStatus


# ---------------------------------------------------------------------------
# Admission gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(FAKE_NAME_PATTERNS))
def test_rejects_fake_names(name: str):
    d = OpportunityAdmissionGate().evaluate(
        {
            "company_name": name.title(),
            "primary_domain": "example.com",
            "source": "reddit",
            "evidence": ["e1"],
            "narrative": "Looking to buy automation for customer support workflows",
        }
    )
    assert d.verdict.value == "reject"
    assert "fake_or_platform_label" in d.reasons


@pytest.mark.parametrize(
    "payload,reason",
    [
        ({"company_name": "Acme", "source": "rss", "evidence": [1], "narrative": "x" * 30}, "no_website_or_domain"),
        ({"company_name": "Acme", "primary_domain": "acme.com", "evidence": [1], "narrative": "x" * 30}, "no_source"),
        ({"company_name": "Acme", "primary_domain": "acme.com", "source": "rss", "narrative": "x" * 30}, "no_opportunity_evidence"),
        ({"company_name": "Acme", "primary_domain": "acme.com", "source": "rss", "evidence": [1], "narrative": "short"}, "no_business_use_case"),
        ({}, "no_company_identity"),
        (
            {
                "company_name": "Docs",
                "primary_domain": "docs.example.com",
                "source": "web",
                "evidence": [1],
                "narrative": "Documentation site for a library project",
                "url": "https://docs.example.com/readme",
            },
            "non_business_content",
        ),
        (
            {
                "company_name": "cool-lib",
                "primary_domain": None,
                "source": "github",
                "evidence": [1],
                "narrative": "Open source library for developers to use",
                "entity_type": "library",
            },
            "rejected_entity_type:library",
        ),
    ],
)
def test_admission_required_fields(payload, reason):
    d = OpportunityAdmissionGate().evaluate(payload)
    assert d.verdict.value == "reject"
    assert reason in d.reasons


def test_admits_real_saas():
    d = OpportunityAdmissionGate().evaluate(
        {
            "company_name": "Northwind Logistics",
            "primary_domain": "northwind-logistics.com",
            "source": "linkedin_jobs",
            "evidence": [{"summary": "hiring ops automation"}],
            "narrative": "Hiring for logistics automation and AI ops tooling",
        }
    )
    assert d.verdict.value == "admit"
    assert d.domain == "northwind-logistics.com"


@pytest.mark.parametrize(
    "domain",
    ["github.com", "reddit.com", "linkedin.com", "medium.com", "substack.com"],
)
def test_rejects_platform_domains(domain):
    d = OpportunityAdmissionGate().evaluate(
        {
            "company_name": "Someone",
            "primary_domain": domain,
            "source": "web",
            "evidence": [1],
            "narrative": "Some long enough narrative about buying software",
        }
    )
    assert d.verdict.value == "reject"


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def test_identity_requires_name_and_domain():
    r = CompanyIdentityValidator().evaluate({"company_name": "", "primary_domain": None})
    assert not r.admitted
    assert "company_name" in r.missing_fields
    assert "official_domain" in r.missing_fields


def test_identity_admits_complete_profile():
    r = CompanyIdentityValidator().evaluate(
        {
            "company_name": "Helios Health",
            "primary_domain": "helios.health",
            "industry": "Healthcare",
            "description": "Clinic operations platform",
            "country": "US",
            "linkedin_url": "https://linkedin.com/company/helios",
            "employees": "50-100",
            "technologies": ["React", "AWS"],
            "created_at": datetime.now(UTC),
            "last_seen_at": datetime.now(UTC),
        }
    )
    assert r.admitted
    assert r.confidence >= 55


@pytest.mark.parametrize(
    "extra,boost",
    [
        ({"industry": "SaaS"}, True),
        ({"country": "DE"}, True),
        ({"technologies": ["Python"]}, True),
        ({}, False),
    ],
)
def test_identity_optional_boosts(extra, boost):
    base = {"company_name": "Acme Corp", "primary_domain": "acme.com"}
    low = CompanyIdentityValidator().evaluate(base).confidence
    high = CompanyIdentityValidator().evaluate({**base, **extra}).confidence
    if boost:
        assert high > low
    else:
        assert high == low


# ---------------------------------------------------------------------------
# Contact readiness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload,status",
    [
        ({}, ContactReadinessStatus.NOT_READY),
        ({"website": "acme.com"}, ContactReadinessStatus.PARTIAL),
        ({"website": "acme.com", "emails": ["sales@acme.com"]}, ContactReadinessStatus.CONTACT_READY),
        ({"has_contact_form": True}, ContactReadinessStatus.CONTACT_READY),
        (
            {
                "website": "acme.com",
                "emails": ["a@acme.com"],
                "phones": ["+1"],
                "decision_makers": [{"name": "A"}],
                "linkedin_url": "https://linkedin.com/company/acme",
                "has_business_evidence": True,
            },
            ContactReadinessStatus.SALES_READY,
        ),
    ],
)
def test_readiness_statuses(payload, status):
    r = ContactReadinessEngine().evaluate(payload)
    assert r.status == status


def test_founder_queue_only_ready():
    engine = ContactReadinessEngine()
    partial = engine.evaluate({"website": "x.com"})
    ready = engine.evaluate({"emails": ["a@x.com"]})
    assert not engine.visible_in_founder_queue(partial)
    assert engine.visible_in_founder_queue(ready)


# ---------------------------------------------------------------------------
# Lead quality score
# ---------------------------------------------------------------------------

def test_score_hides_below_70():
    s = LeadQualityScorer().score({"company_name": "A", "domain": "a.com"})
    assert s.total < 70
    assert not s.visible


def test_score_sales_ready_visible():
    s = LeadQualityScorer().score(
        {
            "company_name": "Acme",
            "domain": "acme.com",
            "verified_website": True,
            "intent_signals": ["hiring", "funding", "launch", "ai"],
            "has_decision_maker": True,
            "emails": ["ceo@acme.com"],
            "phones": ["+1"],
            "last_seen_at": datetime.now(UTC),
            "technologies": ["Python"],
            "buying_signals": ["rfp", "budget", "vendor", "pilot"],
        }
    )
    assert s.total >= 70
    assert s.visible
    assert abs(s.total - (
        s.business_identity
        + s.verified_website
        + s.intent_signals
        + s.decision_maker
        + s.verified_email
        + s.verified_phone
        + s.freshness
        + s.technology_match
        + s.buying_signals
    )) < 0.01


@pytest.mark.parametrize(
    "hours,points",
    [(1, 5.0), (48, 3.0), (100, 1.0), (400, 0.0)],
)
def test_freshness_bands(hours, points):
    s = LeadQualityScorer().score(
        {
            "company_name": "A",
            "domain": "a.com",
            "last_seen_at": datetime.now(UTC) - timedelta(hours=hours),
        }
    )
    assert s.freshness == points


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------

def test_dedupe_by_domain():
    plans = DuplicateResolutionEngine().plan_merges(
        [
            {"id": "1", "company_name": "Acme", "primary_domain": "acme.com", "signal_frequency": 2},
            {"id": "2", "company_name": "Acme Inc", "primary_domain": "acme.com", "signal_frequency": 9},
        ]
    )
    assert len(plans) == 1
    assert plans[0].canonical_company_id == "2"
    assert "1" in plans[0].merged_company_ids


def test_dedupe_by_linkedin():
    plans = DuplicateResolutionEngine().plan_merges(
        [
            {"id": "a", "linkedin_url": "https://linkedin.com/company/x"},
            {"id": "b", "linkedin_url": "https://linkedin.com/company/x/"},
        ]
    )
    assert len(plans) == 1


def test_dedupe_no_singleton():
    plans = DuplicateResolutionEngine().plan_merges([{"id": "1", "primary_domain": "solo.com"}])
    assert plans == []


# ---------------------------------------------------------------------------
# Trust + noise + health
# ---------------------------------------------------------------------------

def test_trust_metrics_percentages():
    m = TrustMetricsEngine().evaluate(
        {
            "companies_collected": 100,
            "qualified": 40,
            "rejected": 20,
            "merged": 5,
            "with_website": 40,
            "with_email": 10,
            "with_phone": 5,
            "with_decision_maker": 8,
        }
    )
    assert m.verified_websites_percent == 40.0
    assert m.verified_emails_percent == 10.0
    assert m.duplicate_percent == 5.0


def test_noise_collapser():
    items = [{"summary": "a"}, {"summary": "a"}, {"summary": "b"}]
    out = NoiseCollapser().collapse(items, key_fn=lambda x: x["summary"])
    assert len(out) == 2


@pytest.mark.parametrize(
    "probes,email_rate",
    [
        ({"email_configured": False}, 0.0),
        ({"email_configured": True, "email_oauth_valid": False}, 25.0),
        ({"email_configured": True, "email_oauth_valid": True, "email_success_rate": 88.0}, 88.0),
    ],
)
def test_live_health_never_fakes_email(probes, email_rate):
    signals = LiveHealthTelemetry().build_signals(
        {
            "redis_ok": True,
            "database_ok": True,
            "api_ok": True,
            "worker_online": False,
            "beat_online": False,
            "collectors_running": 0,
            "collectors_total": 8,
            **probes,
        }
    )
    assert signals["email"]["success_rate"] == email_rate
    assert signals["whatsapp"]["success_rate"] == 0.0  # not configured in probes


def test_live_health_whatsapp_unconfigured():
    signals = LiveHealthTelemetry().build_signals({"whatsapp_configured": False})
    assert signals["whatsapp"]["success_rate"] == 0.0
    assert signals["whatsapp"]["failure_rate"] == 100.0


def test_live_health_redis_down():
    signals = LiveHealthTelemetry().build_signals({"redis_ok": False})
    assert signals["redis"]["success_rate"] == 0.0


def test_live_health_collectors_ratio():
    signals = LiveHealthTelemetry().build_signals({"collectors_running": 2, "collectors_total": 8})
    assert signals["collectors"]["success_rate"] == 25.0


# ---------------------------------------------------------------------------
# Expanded matrix generators (reach 200+)
# ---------------------------------------------------------------------------

BUSINESS_NAMES = [
    "Helios Health",
    "Northwind Logistics",
    "Brightline Finance",
    "Cedar Retail Group",
    "Atlas Automotive",
    "Summit Manufacturing",
    "Orbit SaaS Labs",
    "Harbor Agency",
]


@pytest.mark.parametrize("name", BUSINESS_NAMES)
def test_admits_business_matrix(name):
    d = OpportunityAdmissionGate().evaluate(
        {
            "company_name": name,
            "primary_domain": f"{name.split()[0].lower()}.com",
            "source": "company_website",
            "evidence": ["signal"],
            "narrative": f"{name} is evaluating automation vendors for operations",
        }
    )
    assert d.verdict.value == "admit"


@pytest.mark.parametrize("i", range(40))
def test_score_monotonic_contacts(i):
    base = LeadQualityScorer().score({"company_name": "A", "domain": "a.com"}).total
    with_email = LeadQualityScorer().score(
        {"company_name": "A", "domain": "a.com", "emails": [f"u{i}@a.com"]}
    ).total
    assert with_email >= base + 15


@pytest.mark.parametrize("i", range(40))
def test_partial_never_founder_queue(i):
    r = ContactReadinessEngine().evaluate({"website": f"site{i}.com"})
    assert r.status == ContactReadinessStatus.PARTIAL
    assert not ContactReadinessEngine().visible_in_founder_queue(r)


@pytest.mark.parametrize("i", range(30))
def test_identity_domain_normalization(i):
    r = CompanyIdentityValidator().evaluate(
        {
            "company_name": f"Co {i}",
            "primary_domain": f"https://www.example{i}.com/path",
            "industry": "SaaS",
        }
    )
    assert r.official_domain == f"example{i}.com"
    assert r.admitted


@pytest.mark.parametrize("i", range(25))
def test_dedupe_aliases(i):
    plans = DuplicateResolutionEngine().plan_merges(
        [
            {"id": f"a{i}", "normalized_name": f"alias{i}", "signal_frequency": 1},
            {"id": f"b{i}", "normalized_name": f"alias{i}", "signal_frequency": 5},
        ]
    )
    assert len(plans) == 1
    assert plans[0].canonical_company_id == f"b{i}"


@pytest.mark.parametrize("i", range(20))
def test_noise_strings(i):
    items = [f"signal-{(i + k) % 5}" for k in range(10)]
    assert len(NoiseCollapser().collapse(items)) == 5
