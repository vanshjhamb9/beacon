"""Lead quality unit tests — perfect vs reject fixtures."""

from datetime import UTC, datetime, timedelta

from lead_quality import LeadQualityScorer, OUTBOUND_THRESHOLD, PERFECT_THRESHOLD


def test_perfect_product_hunt_lead():
    now = datetime.now(UTC)
    result = LeadQualityScorer().score(
        {
            "company_name": "Nova Health",
            "source": "product_hunt",
            "website": "https://novahealth.io",
            "official_website": "https://novahealth.io",
            "industry": "Healthcare SaaS",
            "description": "AI intake",
            "business_email": "founders@novahealth.io",
            "decision_maker": "James Lee",
            "why_now": "Recent product launch signal",
            "buying_signals": ["Product Hunt launch signal: Nova Health"],
            "evidence": ["PH"],
            "website_verified": True,
            "published_at": now - timedelta(hours=4),
            "attributes": {"source": "product_hunt", "source_kind": "event", "lead_eligible": True},
        }
    )
    assert result.perfect is True
    assert result.outbound_ready is True
    assert result.total >= PERFECT_THRESHOLD
    assert result.grade == "A"


def test_rejects_yc_directory():
    result = LeadQualityScorer().score(
        {
            "company_name": "Legacy",
            "source": "yc",
            "website": "https://legacy.com",
            "business_email": "a@legacy.com",
            "decision_maker": "X",
            "why_now": "YC portfolio company (Summer 2015) — expansion / growth context",
            "buying_signals": ["YC company directory: Summer 2015"],
            "published_at": datetime.now(UTC),
            "attributes": {"source": "yc", "source_kind": "directory"},
        }
    )
    assert result.outbound_ready is False
    assert result.perfect is False
    assert result.total < OUTBOUND_THRESHOLD
    assert "directory_source" in result.blockers or "directory_source_not_lead" in result.blockers


def test_rejects_news_publisher_host():
    result = LeadQualityScorer().score(
        {
            "company_name": "CNBC Blurb",
            "source": "hacker_news",
            "website": "https://cnbc.com",
            "business_email": "tips@cnbc.com",
            "decision_maker": "Editor",
            "why_now": "Recent hacker_news signal",
            "buying_signals": ["HN launch"],
            "published_at": datetime.now(UTC) - timedelta(hours=2),
            "attributes": {"source": "hacker_news", "source_kind": "event"},
        }
    )
    assert result.outbound_ready is False
    assert "news_or_platform_host" in result.blockers


def test_rejects_stale_signal():
    result = LeadQualityScorer().score(
        {
            "company_name": "OldLaunch",
            "source": "product_hunt",
            "website": "https://old.com",
            "business_email": "hi@old.com",
            "decision_maker": "A",
            "why_now": "Recent product launch signal",
            "buying_signals": ["Product Hunt launch"],
            "published_at": datetime.now(UTC) - timedelta(hours=80),
            "attributes": {"source": "product_hunt", "source_kind": "event"},
        }
    )
    assert result.outbound_ready is False
    assert "stale_signal" in result.blockers
