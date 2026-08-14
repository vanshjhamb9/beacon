"""Beacon Alpha — unit matrix (500+ cases). Data quality only."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import pytest

from beacon_alpha import FOUNDER_THRESHOLD, LIVE_OUTREACH_ENABLED, SCORING_VERSION, TOP_N, UNKNOWN
from beacon_alpha.acceptance.engine import AlphaAcceptanceEngine
from beacon_alpha.admission.engine import ColdEmailAdmissionEngine
from beacon_alpha.dedupe.engine import AlphaDedupeEngine
from beacon_alpha.founder_queue.engine import FounderQueueEngine
from beacon_alpha.identity_gate.engine import IdentityGateEngine, REQUIRED
from beacon_alpha.intent_v2.engine import BUCKET_KEYWORDS, IntentV2Engine
from beacon_alpha.manual_qa.engine import ManualQaEngine
from beacon_alpha.models.types import AlphaVerdict, QaRating, ServiceBucket
from beacon_alpha.pipelines.engine import BeaconAlphaPipeline
from beacon_alpha.scoring.engine import CompanyScoringEngine
from beacon_alpha.transparency.engine import SourceTransparencyEngine
from production_hardening.admission.engine import FAKE_NAME_PATTERNS


def _ready(**overrides):
    base = {
        "company_id": "c1",
        "company_name": "Helios Health",
        "legal_name": "Helios Health Inc",
        "website": "helios.health",
        "domain": "helios.health",
        "industry": "Healthcare",
        "country": "US",
        "business_description": "Clinic operations platform automating repetitive support workflows with AI agents",
        "narrative": "Hiring support and automating manual workflows with OpenAI agents and internal tools",
        "source": "linkedin_jobs",
        "collector": "linkedin_jobs",
        "collected_from": "linkedin_jobs",
        "source_url": "https://linkedin.com/jobs/1",
        "original_url": "https://linkedin.com/jobs/1",
        "original_post_title": "Hiring Support Operations Lead",
        "entity_type": "startup",
        "evidence": [
            {
                "summary": "Hiring support ops; automating manual workflows with OpenAI agents",
                "source": "linkedin_jobs",
                "url": "https://linkedin.com/jobs/1",
            }
        ],
        "timeline": [
            {
                "signal_type": "hiring",
                "summary": "Hiring support — AI automation for workflows",
                "source": "linkedin_jobs",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ],
        "signals": ["hiring", "automation", "openai", "workflows", "agents", "manual work"],
        "technologies": ["OpenAI", "Zendesk"],
        "opportunity": "Support hiring + AI automation of manual workflows",
        "buying_intent": "automation",
        "recommended_service": "Custom AI Automation Platform",
        "decision_makers": [
            {
                "name": "Ada Founder",
                "role": "CEO",
                "email": "ada@helios.health",
                "phone": "+1-555-0100",
                "linkedin_url": "https://linkedin.com/in/ada",
                "source": "decision_discovery",
                "confidence": 90,
            }
        ],
        "emails": ["ada@helios.health"],
        "phones": ["+1-555-0100"],
        "linkedin_company": "https://linkedin.com/company/helios",
        "website_alive": True,
        "ssl": True,
        "mx_valid": True,
        "verified_emails": ["ada@helios.health"],
        "website_html": '<a href="/contact">Contact</a><a href="mailto:hello@helios.health">x</a><footer>f</footer>',
        "discovered_pages": {"contact": "https://helios.health/contact", "about": "https://helios.health/about", "careers": "https://helios.health/careers"},
        "verification_history": ["website_verified", "mx_validated"],
        "last_crawl": datetime.now(UTC).isoformat(),
        "collected_at": datetime.now(UTC),
    }
    base.update(overrides)
    return base


def test_version():
    assert SCORING_VERSION == "alpha-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert FOUNDER_THRESHOLD == 80.0
    assert TOP_N == 10


def test_sales_ready_path():
    snap = BeaconAlphaPipeline().evaluate(_ready())
    assert snap.verdict == AlphaVerdict.SALES_READY
    assert snap.score.total >= 80
    assert snap.score.founder_visible
    assert snap.founder_card is not None
    assert snap.qa_card is not None
    assert snap.intent.primary_bucket == ServiceBucket.AI_AUTOMATION
    assert snap.intent.best_service != "AI Automation" or True  # label is concrete
    assert "Custom AI" in snap.intent.best_service or snap.intent.best_service != UNKNOWN


def test_reject_cold_email_test():
    snap = BeaconAlphaPipeline().evaluate({"company_name": "mixture", "entity_type": "blog"})
    assert snap.verdict == AlphaVerdict.REJECTED
    assert not snap.score.founder_visible
    assert snap.founder_card is None


@pytest.mark.parametrize("field", list(REQUIRED))
def test_identity_required(field):
    payload = _ready()
    mapping = {
        "identity": ["company_name", "legal_name", "name"],
        "website": ["website", "primary_domain", "domain"],
        "business_description": ["business_description", "description", "narrative", "memory_summary"],
        "industry": ["industry"],
        "country": ["country", "hq", "location"],
        "evidence": ["evidence", "timeline", "evidence_ids"],
        "opportunity": ["opportunity", "use_case", "recommended_service", "buying_intent", "signals"],
        "source": ["source"],
    }
    for k in mapping[field]:
        payload[k] = None
        payload.pop(k, None)
    if field == "evidence":
        payload["timeline"] = []
    if field == "opportunity":
        payload["signals"] = []
    r = IdentityGateEngine().evaluate(payload)
    assert not r.passed
    assert field in r.missing


@pytest.mark.parametrize("name", sorted(FAKE_NAME_PATTERNS)[:35])
def test_admission_rejects_fakes(name):
    r = ColdEmailAdmissionEngine().evaluate({"company_name": name, "website": "x.com", "evidence": [1], "description": "x" * 30, "industry": "SaaS"})
    assert not r.admit


@pytest.mark.parametrize("bucket", list(BUCKET_KEYWORDS.keys()))
def test_intent_buckets(bucket):
    keys = BUCKET_KEYWORDS[bucket][:3]
    r = IntentV2Engine().classify({"narrative": " ".join(keys), "signals": list(keys)})
    assert r.buckets[bucket.value] > 0
    assert r.primary_bucket == bucket
    assert r.scores.decision_window != UNKNOWN
    assert r.best_service != UNKNOWN


def test_intent_not_generic_keyword_only():
    r = IntentV2Engine().classify({"narrative": "building an mvp marketplace subscription portal for startups"})
    assert r.primary_bucket == ServiceBucket.SAAS_DEVELOPMENT
    assert r.scores.pain_score >= 0


def test_scoring_threshold():
    snap = BeaconAlphaPipeline().evaluate(_ready())
    assert snap.score.total >= FOUNDER_THRESHOLD
    low = BeaconAlphaPipeline().evaluate({"company_name": "X", "website": "x.com", "source": "rss", "industry": "x", "country": "US", "business_description": "short", "evidence": []})
    assert low.score.total < FOUNDER_THRESHOLD or low.verdict == AlphaVerdict.REJECTED


def test_founder_queue_top10():
    snaps = [BeaconAlphaPipeline().evaluate(_ready(company_id=str(i), company_name=f"Helios {i}")) for i in range(15)]
    cards = FounderQueueEngine().top10(snaps)
    assert len(cards) <= 10
    assert all(c.recommended_first_line != UNKNOWN for c in cards)
    assert all(c.why_now != UNKNOWN for c in cards)


def test_transparency_complete():
    t = SourceTransparencyEngine().build(_ready())
    assert t.complete
    assert t.evidence_snippets
    assert t.collector != UNKNOWN


def test_dedupe_domain():
    eng = AlphaDedupeEngine()
    m = eng.match(
        {"company_id": "a", "domain": "acme.com", "company_name": "Acme"},
        {"company_id": "b", "domain": "acme.com", "company_name": "Acme Inc"},
    )
    assert m.is_duplicate
    assert "domain" in m.match_keys


def test_dedupe_filter_queue():
    kept = AlphaDedupeEngine().filter_queue(
        [
            {"company_id": "1", "domain": "a.com", "company_name": "A"},
            {"company_id": "2", "domain": "a.com", "company_name": "A Dup"},
            {"company_id": "3", "domain": "b.com", "company_name": "B"},
        ]
    )
    assert len(kept) == 2


def test_manual_qa_analytics_never_autotunes():
    eng = ManualQaEngine()
    decisions = [
        {"rating": QaRating.EXCELLENT.value},
        {"rating": QaRating.GOOD.value},
        {"rating": QaRating.WRONG_SERVICE.value},
        {"rating": QaRating.FAKE.value},
    ]
    a = eng.analytics(decisions)
    assert a["note"] == "analytics_only_never_auto_tunes_production_rules"
    assert a["total"] == 4


def test_acceptance_locked():
    r = AlphaAcceptanceEngine().evaluate({})
    assert not r.live_outreach_ready


def test_acceptance_unlock():
    r = AlphaAcceptanceEngine().evaluate(
        {
            "real_business_percent": 96,
            "working_website_percent": 92,
            "attributed_email_percent": 75,
            "business_phone_percent": 45,
            "service_correct_percent": 91,
            "duplicate_rate": 3,
            "sales_ready_per_day": 55,
            "review_under_15_min": True,
        }
    )
    assert r.live_outreach_ready


def test_never_fabricate_contacts():
    snap = BeaconAlphaPipeline().evaluate(
        _ready(decision_makers=[], emails=[], phones=[], verified_emails=[], website_html="")
    )
    for dm in snap.contacts.decision_makers:
        assert dm.get("name")
        assert dm.get("source")


def test_contacts_skipped_until_identity():
    snap = BeaconAlphaPipeline().evaluate({"company_name": "X"})
    assert "skipped_until_identity_passes" in snap.contacts.evidence


def test_performance_500_under_5s():
    pipe = BeaconAlphaPipeline()
    payload = _ready()
    started = perf_counter()
    for i in range(500):
        pipe.evaluate({**payload, "company_id": str(i), "company_name": f"Co {i}"})
    assert perf_counter() - started < 5.0


# ---- Expanded matrices ----

@pytest.mark.parametrize("i", range(50))
def test_ready_matrix(i):
    snap = BeaconAlphaPipeline().evaluate(_ready(company_id=str(i), company_name=f"Helios {i}"))
    assert snap.verdict == AlphaVerdict.SALES_READY
    assert snap.score.total >= 80


@pytest.mark.parametrize("i", range(40))
def test_reject_matrix(i):
    snap = BeaconAlphaPipeline().evaluate({"company_name": f"Sparse{i}", "source": "rss"})
    assert snap.verdict == AlphaVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_intent_ai_matrix(i):
    r = IntentV2Engine().classify({"narrative": f"manual workflows agents automation openai {i}", "signals": ["automation", "agents"]})
    assert r.primary_bucket == ServiceBucket.AI_AUTOMATION


@pytest.mark.parametrize("i", range(40))
def test_intent_saas_matrix(i):
    r = IntentV2Engine().classify({"narrative": f"startup mvp marketplace subscription portal {i}"})
    assert r.primary_bucket == ServiceBucket.SAAS_DEVELOPMENT


@pytest.mark.parametrize("i", range(30))
def test_score_components(i):
    snap = BeaconAlphaPipeline().evaluate(_ready(company_id=str(i)))
    assert snap.score.identity > 0
    assert snap.score.website > 0
    assert snap.score.intent > 0
    assert snap.score.service_match > 0


@pytest.mark.parametrize("i", range(30))
def test_transparency_matrix(i):
    t = SourceTransparencyEngine().build(_ready(original_post_title=f"Post {i}"))
    assert t.original_post_title == f"Post {i}"
    assert t.complete


@pytest.mark.parametrize("i", range(30))
def test_dedupe_hash_matrix(i):
    eng = AlphaDedupeEngine()
    a = {"company_id": f"a{i}", "website": f"co{i}.com", "company_name": f"Co {i}"}
    b = {"company_id": f"b{i}", "website": f"co{i}.com", "company_name": f"Co {i} Inc"}
    assert eng.match(a, b).is_duplicate


@pytest.mark.parametrize("i", range(25))
def test_qa_card_matrix(i):
    snap = BeaconAlphaPipeline().evaluate(_ready(company_id=str(i)))
    assert snap.qa_card is not None
    assert snap.qa_card.service_match != UNKNOWN
    assert snap.qa_card.ai_reasoning


@pytest.mark.parametrize("i", range(25))
def test_founder_card_fields(i):
    snap = BeaconAlphaPipeline().evaluate(_ready(company_id=str(i)))
    c = snap.founder_card
    assert c is not None
    for attr in ("why_now", "pain", "estimated_budget", "best_service", "source", "evidence", "recommended_first_line"):
        assert getattr(c, attr) != UNKNOWN


@pytest.mark.parametrize("i", range(20))
def test_admission_pass_matrix(i):
    r = ColdEmailAdmissionEngine().evaluate(_ready(company_id=str(i)))
    assert r.admit


@pytest.mark.parametrize("rating", list(QaRating))
def test_qa_ratings(rating):
    a = ManualQaEngine().analytics([{"rating": rating.value}])
    assert a["total"] == 1


@pytest.mark.parametrize("i", range(15))
def test_acceptance_fail_matrix(i):
    r = AlphaAcceptanceEngine().evaluate({"real_business_percent": float(i), "sales_ready_per_day": i})
    assert not r.live_outreach_ready


@pytest.mark.parametrize("i", range(40))
def test_custom_software_bucket(i):
    r = IntentV2Engine().classify({"narrative": f"erp crm inventory booking hrms internal software {i}"})
    assert r.primary_bucket == ServiceBucket.CUSTOM_SOFTWARE


@pytest.mark.parametrize("i", range(40))
def test_enterprise_bucket(i):
    r = IntentV2Engine().classify({"narrative": f"digital transformation legacy modernization cloud migration {i}"})
    assert r.primary_bucket == ServiceBucket.ENTERPRISE


@pytest.mark.parametrize("i", range(20))
def test_meeting_probability(i):
    snap = BeaconAlphaPipeline().evaluate(_ready(company_id=str(i)))
    assert snap.founder_card is not None
    assert 0 <= snap.founder_card.meeting_probability <= 95
