"""Unit tests for the cybersecurity buyer-first discovery lane."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from packages.cybersecurity_discovery.classifier import (
    classify_opportunity_type,
    classify_raw,
    match_buying_events,
    match_service,
)
from packages.cybersecurity_discovery.enrich import extract_emails, guess_email
from packages.cybersecurity_discovery.exporters import write_exports
from packages.cybersecurity_discovery.gates import evaluate_gates
from packages.cybersecurity_discovery.pipeline import run_cybersecurity_discovery
from packages.cybersecurity_discovery.rejects import first_reject_reason
from packages.cybersecurity_discovery.sources import _parse_atom_entries
from packages.cybersecurity_discovery.schema import (
    Currentness,
    CyberOpportunity,
    EmailStatus,
    FinalVerdict,
    IntentLevel,
    OpportunityType,
    OutsourcingIntent,
    RawDiscovery,
    utc_now_iso,
)


def _raw(title: str, body: str, **kwargs) -> RawDiscovery:
    published = kwargs.pop("published_at", datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return RawDiscovery(
        source_name=kwargs.pop("source_name", "Reddit r/startups"),
        source_url=kwargs.pop("source_url", "https://www.reddit.com/r/startups/comments/abc/pentest/"),
        title=title,
        body=body,
        published_at=published,
        **kwargs,
    )


def test_reddit_atom_feed_parses_entry_title_and_link():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <entry>
    <author><name>/u/Magusds</name><uri>https://old.reddit.com/user/Magusds</uri></author>
    <title>hello job</title>
    <link href="https://www.reddit.com/r/sysadmin/comments/abc/hello/"/>
    <content type="html">body text</content>
    <updated>2026-08-16T21:57:54+00:00</updated>
  </entry>
</feed>
"""
    parsed = _parse_atom_entries(xml, "Reddit")
    assert len(parsed) == 1
    assert parsed[0].title == "hello job"
    assert "sysadmin/comments/abc" in parsed[0].source_url
    assert parsed[0].author == "Magusds"


def test_buying_event_matches_explicit_pentest_need():
    hits = match_buying_events("We need a penetration testing company to test our SaaS before launch.")
    assert hits
    assert any(h[0] in {"vulnerability_security_issue", "external_security_team", "prelaunch_enterprise"} for h in hits)


def test_reject_cve_news():
    reason = first_reject_reason("Researchers discovered CVE-2026-12345 in a popular library")
    assert reason == "cybersecurity_news"


def test_reject_vendor_pitch():
    reason = first_reject_reason("We offer pentest services. Book a demo of our VAPT platform today.")
    assert reason == "vendor_selling"


def test_reject_job_seeker():
    reason = first_reject_reason("Looking for a job in cybersecurity. Hire me, here is my resume.")
    assert reason == "job_seeker"


def test_service_match_requires_stated_requirement():
    name, reason, conf = match_service("Need web application penetration test before we launch")
    assert name == "Web Application VAPT"
    assert reason
    assert conf == "HIGH"


def test_generic_security_importance_is_not_a_service():
    name, _reason, conf = match_service("Cybersecurity is important for every startup")
    assert name is None
    assert conf == "LOW"


def test_never_guess_emails():
    assert guess_email("Jane Founder", "acme.io") is None
    assert extract_emails("Contact Jane Founder at Acme") == []
    found = extract_emails("Email jane@acme.io if you can help with the pentest")
    assert found == ["jane@acme.io"]


def test_partner_never_sales_ready():
    raw = _raw(
        "Need a VAPT partner for our agency clients",
        "We are a web development agency looking for a cybersecurity partner for clients. Need white-label VAPT.",
        author="agency_owner",
        author_profile_url="https://www.reddit.com/user/agency_owner/",
        company_hint="Northwind Agency",
        company_url_hint="https://northwind.example",
    )
    opp = classify_raw(raw, utc_now_iso())
    assert opp.opportunity_type == OpportunityType.SECURITY_PARTNER.value
    opp.identity_confidence = "HIGH"
    opp.buyer_name = "Alex Founder"
    opp.buyer_role = "Founder"
    opp.company_verified = True
    opp.contactability = "HIGH"
    opp.email = "alex@northwind.example"
    opp.email_status = EmailStatus.VERIFIED.value
    opp.service_match = "Penetration Testing"
    opp.service_match_confidence = "HIGH"
    opp.intent_level = IntentLevel.HOT.value
    evaluated = evaluate_gates(opp)
    assert evaluated.final_verdict != FinalVerdict.SALES_READY.value
    assert evaluated.opportunity_type == OpportunityType.SECURITY_PARTNER.value
    assert "not_partner" in evaluated.failed_gates


def test_sales_ready_fails_when_any_hard_gate_is_down():
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    opp = CyberOpportunity(
        opportunity_id="CYBER-TEST",
        company="Acme SaaS",
        company_url="https://acme.example",
        country="USA",
        industry="SaaS",
        buyer_name="Jordan Lee",
        buyer_role="CTO",
        buyer_profile_url="https://www.linkedin.com/in/jordanlee",
        identity_confidence="HIGH",
        buying_event="Need pentest",
        problem="Need pentest",
        why_now="Enterprise customer requires pentest",
        intent_level=IntentLevel.HOT.value,
        requirement_evidence=[{"claim": "requirement_verified", "value": True}],
        source_name="Reddit r/SaaS",
        source_url="https://www.reddit.com/r/SaaS/comments/xyz",
        source_status="VERIFIED",
        published_at=now,
        observed_at=now,
        security_problem="Need penetration testing before enterprise launch",
        security_problem_evidence=[{"claim": "security_problem", "value": "need pentest"}],
        outsourcing_intent=OutsourcingIntent.EXPLICIT.value,
        outsourcing_evidence=[{"claim": "outsourcing_intent", "value": "EXPLICIT"}],
        service_match="Penetration Testing",
        service_match_reason="Buyer stated need penetration testing",
        service_match_confidence="HIGH",
        email="jordan@acme.example",
        email_status=EmailStatus.VERIFIED.value,
        linkedin_url="https://www.linkedin.com/in/jordanlee",
        linkedin_status="VERIFIED",
        contactability="HIGH",
        currentness=Currentness.HOT.value,
        competitor=False,
        safety_clear=True,
        opportunity_type=OpportunityType.SECURITY_TESTING_CLIENT.value,
        company_verified=True,
        requirement_verified=True,
        buying_event_verified=True,
        title="Need pentest",
        body_snippet="Looking for a cybersecurity company. Need penetration testing.",
    )
    passed = evaluate_gates(opp)
    assert passed.final_verdict == FinalVerdict.SALES_READY.value
    assert passed.cto_15_minute_test == "YES"

    broken = evaluate_gates(
        CyberOpportunity(**{**opp.to_dict(), "contactability": "NONE", "email": None, "email_status": "UNKNOWN"})
    )
    assert broken.final_verdict == FinalVerdict.NEEDS_RESEARCH.value
    assert "contact_path" in broken.failed_gates


def test_stale_over_90_days_rejects_without_active_evidence():
    old = (datetime.now(UTC) - timedelta(days=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
    opp = classify_raw(
        _raw(
            "Need a pentest vendor",
            "Looking for a cybersecurity company to run a pentest on our platform.",
            published_at=old,
            author="cto_jane",
            author_profile_url="https://www.reddit.com/user/cto_jane/",
        ),
        utc_now_iso(),
    )
    evaluated = evaluate_gates(opp)
    assert evaluated.final_verdict == FinalVerdict.REJECT.value
    assert evaluated.rejection_reason == "stale_over_90_days"


async def test_undated_buying_event_can_be_sales_ready():
    result = await run_cybersecurity_discovery(
        limit=5,
        enrich=False,
        preloaded=[
            _raw(
                "Need a pentest vendor for our SaaS",
                "Looking for a cybersecurity company. Need penetration testing on our platform.",
                published_at=None,
                author="founder_x",
                author_profile_url="https://www.reddit.com/user/founder_x/",
            )
        ],
    )
    assert result.counters["BUYING_EVENTS"] == 1
    assert result.counters["SALES_READY"] == 1
    opp = result.sales_ready[0]
    assert opp.final_verdict == FinalVerdict.SALES_READY.value
    assert opp.rejection_reason != "stale_over_90_days"
    assert opp.cto_15_minute_test == "YES"


async def test_partner_not_in_sales_ready_export(tmp_path):
    raw_items = [
        _raw(
            "Need a cybersecurity partner for clients",
            "Digital agency seeking a pentesting partner. Need white-label cybersecurity provider.",
            source_url="https://www.reddit.com/r/webdev/comments/partner1",
            author="agency",
            author_profile_url="https://www.reddit.com/user/agency/",
        ),
        _raw(
            "CVE-2024-0001 advisory",
            "Researchers discovered CVE-2024-0001 according to TheHackerNews.",
            source_url="https://thehackernews.com/cve-demo",
        ),
    ]
    result = await run_cybersecurity_discovery(limit=10, enrich=False, preloaded=raw_items)
    assert result.counters["SALES_READY"] == 0
    assert all(o.opportunity_type != OpportunityType.SECURITY_PARTNER.value for o in result.sales_ready)
    assert any(o.opportunity_type == OpportunityType.SECURITY_PARTNER.value for o in result.needs_research + result.rejected)
    written = write_exports(result, tmp_path)
    assert (tmp_path / "cyber_sales_ready.json").exists()
    assert (tmp_path / "CYBERSECURITY_FINAL_REPORT.md").exists()
    assert "cyber_sales_ready.json" in written


def test_workspace_sync_excludes_partners_and_keeps_sales_ready():
    from packages.cybersecurity_discovery.schema import CyberOpportunity
    from packages.cybersecurity_discovery.workspace_sync import opportunity_to_workspace_lead

    ready = CyberOpportunity(
        opportunity_id="CYBER-SYNC1",
        company="Acme SaaS",
        title="Need a pentest",
        email="jordan@acme.example",
        final_verdict=FinalVerdict.SALES_READY.value,
        buying_event_verified=True,
        opportunity_type=OpportunityType.SECURITY_TESTING_CLIENT.value,
        source_url="https://www.reddit.com/r/startups/comments/abc/pentest/",
        service_match="Penetration Testing",
        security_problem="Need a pentest",
        why_now="Customer requires pentest",
        buyer_name="Jordan",
    )
    row = opportunity_to_workspace_lead(ready, outreach=True)
    assert row["department"] == "Cyber"
    assert row["grade"] == "SALES_READY"
    assert row["email"] == "jordan@acme.example"
    assert row["lane"] == "cyber"

    partner = CyberOpportunity(
        opportunity_id="CYBER-PART",
        company="Northwind Agency",
        title="Need a VAPT partner",
        email="ops@northwind.example",
        final_verdict=FinalVerdict.NEEDS_RESEARCH.value,
        opportunity_type=OpportunityType.SECURITY_PARTNER.value,
        source_url="https://www.reddit.com/r/webdev/comments/partner1",
    )
    skipped = opportunity_to_workspace_lead(partner, outreach=False)
    assert skipped["grade"] != "SALES_READY"

    no_email = CyberOpportunity(
        opportunity_id="CYBER-NOMAIL",
        company="Silent Co",
        title="Need a pentest",
        email=None,
        final_verdict=FinalVerdict.SALES_READY.value,
        buying_event_verified=True,
        opportunity_type=OpportunityType.SECURITY_TESTING_CLIENT.value,
        source_url="https://news.ycombinator.com/item?id=1",
    )
    research = opportunity_to_workspace_lead(no_email, outreach=True)
    assert research["grade"] == "SALES_READY"
    assert not research["email"]
    assert research["outreach_status"] == "pending"


def test_aging_forum_buyer_is_sales_ready():
    aging = (datetime.now(UTC) - timedelta(days=42)).strftime("%Y-%m-%dT%H:%M:%SZ")
    opp = classify_raw(
        _raw(
            "Need a pentest vendor for our SaaS",
            "Looking for a cybersecurity company. Need penetration testing on our platform.",
            published_at=aging,
            author="cto_jordan",
            author_profile_url="https://news.ycombinator.com/user?id=cto_jordan",
        ),
        utc_now_iso(),
    )
    from packages.cybersecurity_discovery.gates import classify_contactability

    classify_contactability(opp)
    evaluated = evaluate_gates(opp)
    assert evaluated.currentness == Currentness.AGING.value
    assert evaluated.final_verdict == FinalVerdict.SALES_READY.value
    assert evaluated.cto_15_minute_test == "YES"


def test_soc2_vendor_switch_is_sales_ready():
    body = (
        "I’m trying to understand the SOC 2 process a little better, as I’m looking at "
        "Cobalt's human-led Web + API penetration test as part of the evidence for a future "
        "SOC 2 Type II audit. Has anyone here actually gone through SOC 2 Type II this way "
        "(specifically using Cobalt’s human-led pentest )? I’m looking for an alternative "
        "and more affordable option that would work for a startup with a small budget"
    )
    hits = match_buying_events(body)
    assert hits
    opp = classify_raw(
        _raw(
            "Has anyone successfully gotten SOC 2 Type II using a Cobalt Web + API pentest?",
            body,
            source_name="Reddit r/AskNetsec",
            source_url="https://www.reddit.com/r/AskNetsec/comments/soc2pentest/",
            author="MT_321",
            author_profile_url="https://www.reddit.com/user/MT_321/",
        ),
        utc_now_iso(),
    )
    from packages.cybersecurity_discovery.gates import classify_contactability

    classify_contactability(opp)
    evaluated = evaluate_gates(opp)
    assert evaluated.opportunity_type != OpportunityType.REJECT.value
    assert evaluated.final_verdict == FinalVerdict.SALES_READY.value
    assert evaluated.cto_15_minute_test == "YES"
