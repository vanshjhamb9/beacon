from __future__ import annotations

from global_opportunity_acquisition.models.types import (
    ConnectorAccessMode,
    ConnectorDefinition,
    ConnectorStatus,
)


def connector_catalog() -> list[ConnectorDefinition]:
    """Interface contracts for all GOAP sources. Licensed/restricted remain disabled."""

    current = [
        ("reddit", "Reddit", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "community"),
        ("rss", "RSS", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "feeds"),
        ("hacker_news", "Hacker News", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "community"),
        ("product_hunt", "Product Hunt", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "launches"),
        ("github", "GitHub", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "engineering"),
        ("devto", "Dev.to", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "community"),
        ("indie_hackers", "IndieHackers", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "community"),
        ("sec", "SEC EDGAR", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "filings"),
    ]
    jobs = [
        ("linkedin_jobs_public", "LinkedIn Jobs (public)", ConnectorAccessMode.PUBLIC_JOBS, ConnectorStatus.ACTIVE, "hiring"),
        ("google_jobs", "Google Jobs", ConnectorAccessMode.PUBLIC_JOBS, ConnectorStatus.ACTIVE, "hiring"),
        ("wellfound", "Wellfound", ConnectorAccessMode.PUBLIC_JOBS, ConnectorStatus.INTERFACE_ONLY, "hiring"),
        ("yc_jobs", "YC Jobs", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "hiring"),
    ]
    news = [
        ("techcrunch", "TechCrunch", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "funding"),
        ("venturebeat", "VentureBeat", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "funding"),
        ("yourstory", "YourStory", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "funding"),
        ("inc42", "Inc42", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "funding"),
        ("eu_startups", "EU Startups", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "funding"),
        ("betalist", "BetaList", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "launches"),
    ]
    licensed = [
        ("crunchbase", "Crunchbase", ConnectorAccessMode.LICENSED, ConnectorStatus.PENDING_CREDENTIALS, "funding"),
    ]
    reviews = [
        ("clutch", "Clutch", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("goodfirms", "GoodFirms", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("designrush", "DesignRush", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("upcity", "UpCity", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("capterra", "Capterra", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("g2", "G2", ConnectorAccessMode.INTERFACE_ONLY, ConnectorStatus.INTERFACE_ONLY, "reviews"),
        ("saashub", "SaaSHub", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "reviews"),
        ("alternativeto", "AlternativeTo", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "reviews"),
    ]
    commerce = [
        ("shopify_ecosystem", "Shopify ecosystem", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "commerce"),
        ("woocommerce_ecosystem", "WooCommerce ecosystem", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "commerce"),
        ("bigcommerce_ecosystem", "BigCommerce ecosystem", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "commerce"),
        ("magento_ecosystem", "Magento ecosystem", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "commerce"),
    ]
    procurement = [
        ("public_procurement", "Public procurement portals", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "procurement"),
        ("government_tenders", "Government tenders", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "procurement"),
        ("public_rfp_feeds", "Public RFP feeds", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "procurement"),
    ]
    web = [
        ("company_blogs", "Company blogs", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "web"),
        ("press_releases", "Press releases", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "web"),
        ("engineering_blogs", "Engineering blogs", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "web"),
        ("career_pages", "Career pages", ConnectorAccessMode.PUBLIC_JOBS, ConnectorStatus.ACTIVE, "hiring"),
        ("public_changelogs", "Public changelogs", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "product"),
        ("developer_docs", "Developer documentation", ConnectorAccessMode.PUBLIC_FEED, ConnectorStatus.ACTIVE, "engineering"),
    ]

    out: list[ConnectorDefinition] = []
    for group in (current, jobs, news, licensed, reviews, commerce, procurement, web):
        for cid, name, mode, status, category in group:
            requires = mode in {ConnectorAccessMode.LICENSED, ConnectorAccessMode.CREDENTIALS_REQUIRED}
            notes = ""
            if status == ConnectorStatus.PENDING_CREDENTIALS:
                notes = "Disabled until valid licensed credentials are supplied."
            elif status == ConnectorStatus.INTERFACE_ONLY:
                notes = "Interface contract only — no unsupported crawler; enable via compliant provider."
            elif mode == ConnectorAccessMode.PUBLIC_JOBS:
                notes = "Public job listings only; no private profile scraping."
            out.append(
                ConnectorDefinition(
                    connector_id=cid,
                    connector_name=name,
                    access_mode=mode,
                    status=status if status != ConnectorStatus.INTERFACE_ONLY else ConnectorStatus.DISABLED,
                    category=category,
                    respects_robots_txt=True,
                    public_information_only=True,
                    requires_license=requires,
                    notes=notes or "Public information only; respects robots.txt and platform ToS.",
                )
            )
    return out
