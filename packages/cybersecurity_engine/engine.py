"""BEACON — Cybersecurity Buyer Discovery Engine.

Main orchestrator that discovers, classifies, and exports cybersecurity opportunities.

Usage:
    python -m cybersecurity_engine [--limit N] [--output DIR]
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from cybersecurity_engine.evidence_engine import SalesReadinessEvaluator
from cybersecurity_engine.export_engine import ExportEngine
from cybersecurity_engine.models import (
    Company,
    CompanySize,
    Contact,
    CybersecurityOpportunity,
    OpportunityPriority,
    OpportunityType,
    ServiceLane,
)
from cybersecurity_engine.outreach_generator import OutreachMessageGenerator
from cybersecurity_engine.signal_detector import CybersecuritySignalDetector
from cybersecurity_engine.sources import RawSignal
from cybersecurity_engine.sources.company_blog_cybersecurity import (
    CompanyBlogCybersecurityCollector,
)
from cybersecurity_engine.sources.hackernews_cybersecurity import (
    HackerNewsCybersecurityCollector,
)
from cybersecurity_engine.sources.reddit_cybersecurity import RedditCybersecurityCollector
from cybersecurity_engine.sources.web_search_cybersecurity import (
    WebSearchCybersecurityCollector,
)

logger = logging.getLogger(__name__)


# ============================================================
# COMPANY NAME EXTRACTION
# ============================================================

def extract_company_from_signal(signal: RawSignal) -> str:
    """Extract company name from a signal's content."""
    import re

    text = signal.content

    # Try to find company mentions
    # Look for "Company Name is/has/was" patterns
    company_patterns = [
        r"(?:at|from|of|for|with|by)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:is|are|has|have|was|were|will|needs?|requires?|looking))",
        r"([A-Z][A-Za-z0-9&.]+?)\s+(?:is|are|has|have|was|were|will|needs?|requires?)",
    ]

    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives
            false_positives = {
                "we", "our", "they", "their", "this", "that", "the",
                "i", "you", "he", "she", "it", "my", "your", "his",
                "her", "its", "our", "their", "what", "how", "when",
                "where", "why", "who", "which", "does", "do", "did",
                "have", "has", "had", "will", "would", "could", "should",
                "can", "may", "might", "must", "shall", "need", "need",
                "looking", "seeking", "finding", "getting", "using",
            }
            if name.lower() not in false_positives and len(name) > 2:
                return name

    # Try domain-based extraction
    if signal.url:
        from urllib.parse import urlparse
        domain = urlparse(signal.url).netloc
        if domain:
            # Remove www. and common TLDs
            domain = re.sub(r"^www\.", "", domain)
            domain = domain.split(".")[0]
            if len(domain) > 2:
                return domain.title()

    return ""


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


# ============================================================
# MAIN ENGINE
# ============================================================

class CybersecurityDiscoveryEngine:
    """Main orchestrator for cybersecurity buyer discovery."""

    def __init__(
        self,
        *,
        output_dir: str = ".",
        sender_name: str = "Security Team",
        sender_company: str = "",
        max_items_per_source: int = 30,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.sender_name = sender_name
        self.sender_company = sender_company
        self.max_items_per_source = max_items_per_source

        self.signal_detector = CybersecuritySignalDetector()
        self.evaluator = SalesReadinessEvaluator()
        self.message_generator = OutreachMessageGenerator(
            sender_name=sender_name,
            sender_company=sender_company,
        )
        self.export_engine = ExportEngine(output_dir=str(output_dir))

    async def run(self, limit: int = 50) -> dict[str, Any]:
        """Run the full discovery pipeline.

        Returns summary statistics.
        """
        start_time = time.time()
        print("=" * 70)
        print("BEACON — CYBERSECURITY BUYER DISCOVERY ENGINE")
        print("=" * 70)

        # Step 1: Collect raw signals from all sources
        print("\n[1/5] Collecting signals from sources...")
        raw_signals = await self._collect_signals()
        print(f"  Collected {len(raw_signals)} raw signals")

        # Step 2: Classify signals and create opportunities
        print("\n[2/5] Classifying signals...")
        opportunities = self._classify_signals(raw_signals)
        print(f"  Created {len(opportunities)} opportunities")

        # Step 3: Evaluate sales readiness
        print("\n[3/5] Evaluating sales readiness...")
        opportunities = self._evaluate_opportunities(opportunities)
        sales_ready = [o for o in opportunities if o.final_verdict == "SALES_READY"]
        marketing_ready = [o for o in opportunities if o.final_verdict == "MARKETING_READY"]
        print(f"  SALES_READY: {len(sales_ready)}")
        print(f"  MARKETING_READY: {len(marketing_ready)}")

        # Step 4: Generate outreach messages
        print("\n[4/5] Generating outreach messages...")
        for opp in opportunities:
            if opp.final_verdict == "SALES_READY":
                opp.outreach_preparation = self.message_generator.generate(opp)
        print(f"  Generated {len(sales_ready)} outreach messages")

        # Step 5: Export results
        print("\n[5/5] Exporting results...")
        files = self.export_engine.export_all(opportunities)
        for name, path in files.items():
            print(f"  {name}: {path}")

        elapsed = time.time() - start_time

        # Summary
        summary = {
            "total_signals": len(raw_signals),
            "total_opportunities": len(opportunities),
            "sales_ready": len(sales_ready),
            "marketing_ready": len(marketing_ready),
            "not_ready": len([o for o in opportunities if o.final_verdict == "NOT_READY"]),
            "p0_count": len([o for o in opportunities if o.priority == OpportunityPriority.P0]),
            "p1_count": len([o for o in opportunities if o.priority == OpportunityPriority.P1]),
            "p2_count": len([o for o in opportunities if o.priority == OpportunityPriority.P2]),
            "elapsed_seconds": elapsed,
            "output_files": files,
        }

        print("\n" + "=" * 70)
        print("DISCOVERY COMPLETE")
        print("=" * 70)
        print(f"Total signals: {summary['total_signals']}")
        print(f"Total opportunities: {summary['total_opportunities']}")
        print(f"SALES_READY: {summary['sales_ready']}")
        print(f"MARKETING_READY: {summary['marketing_ready']}")
        print(f"P0 (Active): {summary['p0_count']}")
        print(f"P1 (Verified Pain): {summary['p1_count']}")
        print(f"P2 (Outbound): {summary['p2_count']}")
        print(f"Time: {elapsed:.1f}s")

        return summary

    async def _collect_signals(self) -> list[RawSignal]:
        """Collect signals from all sources."""
        all_signals: list[RawSignal] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
            timeout=httpx.Timeout(15.0),
        ) as client:
            # Reddit
            print("  [Reddit] Collecting cybersecurity signals...")
            try:
                reddit = RedditCybersecurityCollector(
                    client, max_items=self.max_items_per_source
                )
                signals = await reddit.collect()
                for s in signals:
                    if s.url not in seen_urls:
                        seen_urls.add(s.url)
                        all_signals.append(s)
                print(f"    Reddit: {len(signals)} signals")
            except Exception as e:
                print(f"    Reddit failed: {e}")

            # Hacker News
            print("  [HackerNews] Collecting cybersecurity signals...")
            try:
                hn = HackerNewsCybersecurityCollector(
                    client, max_items=self.max_items_per_source
                )
                signals = await hn.collect()
                for s in signals:
                    if s.url not in seen_urls:
                        seen_urls.add(s.url)
                        all_signals.append(s)
                print(f"    HackerNews: {len(signals)} signals")
            except Exception as e:
                print(f"    HackerNews failed: {e}")

            # Web Search
            print("  [WebSearch] Collecting cybersecurity signals...")
            try:
                web = WebSearchCybersecurityCollector(
                    client, max_items=self.max_items_per_source
                )
                signals = await web.collect()
                for s in signals:
                    if s.url not in seen_urls:
                        seen_urls.add(s.url)
                        all_signals.append(s)
                print(f"    WebSearch: {len(signals)} signals")
            except Exception as e:
                print(f"    WebSearch failed: {e}")

            # Company Blog (Tier 1 source - high value)
            # Auto-discover company URLs from web search signals
            company_urls = self._extract_company_urls_from_signals(all_signals)
            if company_urls:
                print(f"  [CompanyBlog] Checking {len(company_urls)} company security pages...")
                try:
                    blog = CompanyBlogCybersecurityCollector(
                        client,
                        company_urls=company_urls,
                        max_items=self.max_items_per_source,
                    )
                    signals = await blog.collect()
                    for s in signals:
                        if s.url not in seen_urls:
                            seen_urls.add(s.url)
                            all_signals.append(s)
                    print(f"    CompanyBlog: {len(signals)} signals")
                except Exception as e:
                    print(f"    CompanyBlog failed: {e}")
            else:
                print("  [CompanyBlog] No company URLs discovered, skipping")

        return all_signals

    def _extract_company_urls_from_signals(self, signals: list[RawSignal]) -> list[str]:
        """Extract unique company URLs from collected signals for CompanyBlog checking."""
        company_urls: list[str] = []
        seen_domains: set[str] = set()

        for signal in signals:
            # Extract domain from signal URL
            url = signal.url
            if not url or not url.startswith("http"):
                continue

            # Skip non-company URLs (social media, forums, etc.)
            skip_domains = [
                "reddit.com", "news.ycombinator.com", "twitter.com", "x.com",
                "linkedin.com", "facebook.com", "instagram.com", "duckduckgo.com",
                "github.com", "stackoverflow.com",
            ]
            if any(d in url for d in skip_domains):
                continue

            # Extract base domain
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    # Construct base URL
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    company_urls.append(base_url)
            except Exception:
                continue

            # Limit to top 20 companies to avoid excessive scraping
            if len(company_urls) >= 20:
                break

        return company_urls

    def _classify_signals(
        self,
        signals: list[RawSignal],
    ) -> list[CybersecurityOpportunity]:
        """Classify raw signals into opportunities."""
        opportunities: list[CybersecurityOpportunity] = []
        seen_companies: set[str] = set()

        for signal in signals:
            # Extract company info
            company_name = extract_company_from_signal(signal)
            if not company_name:
                # Use signal source as company proxy
                company_name = extract_domain_from_url(signal.url) or signal.source

            # Deduplicate by company
            company_key = company_name.lower().strip()
            if company_key in seen_companies:
                continue
            seen_companies.add(company_key)

            # Classify signal
            full_text = f"{signal.title} {signal.content}"
            priority, buying_event = self.signal_detector.detect_priority(
                full_text, source_tier=signal.source_tier
            )

            # Skip P3 (no signal) unless it has high relevance
            if priority == OpportunityPriority.P3:
                continue

            # Create company
            company = Company(
                name=company_name,
                url=extract_domain_from_url(signal.url) or signal.url,
                country=self._detect_country(full_text),
                industry=self._detect_industry(full_text),
            )

            # Create contact (basic extraction)
            contact = self._extract_contact(signal)

            # Create opportunity
            opp_id = hashlib.sha256(
                f"{company_name}:{signal.url}".encode()
            ).hexdigest()[:12]

            opportunity = CybersecurityOpportunity(
                opportunity_id=opp_id,
                company=company,
                opportunity_type=OpportunityType.CYBERSECURITY,
                priority=priority,
                buying_event=buying_event,
                contact=contact,
                source_name=signal.source,
                source_type="event",
                source_url=signal.url,
                source_status="accessible",
                published_at=signal.published_at,
            )

            # Add evidence
            opportunity.add_evidence(
                claim="buying_signal_detected",
                value=buying_event.description[:200],
                source_name=signal.source,
                source_type="event",
                source_url=signal.url,
                source_status="accessible",
                method="web_scrape",
                confidence=min(90.0, signal.score * 2),
                verified=True,
            )

            opportunities.append(opportunity)

        return opportunities

    def _evaluate_opportunities(
        self,
        opportunities: list[CybersecurityOpportunity],
    ) -> list[CybersecurityOpportunity]:
        """Evaluate all opportunities for sales readiness."""
        evaluated = []
        for opp in opportunities:
            evaluated_opp = self.evaluator.evaluate(opp)
            evaluated.append(evaluated_opp)
        return evaluated

    def _detect_country(self, text: str) -> str:
        """Detect country from text content."""
        text_lower = text.lower()
        country_indicators = {
            "united states": "United States", "usa": "United States",
            "us ": "United States", "america": "United States",
            "united kingdom": "United Kingdom", "uk ": "United Kingdom",
            "london": "United Kingdom",
            "canada": "Canada", "toronto": "Canada",
            "australia": "Australia", "sydney": "Australia",
            "uae": "UAE", "dubai": "UAE",
            "saudi arabia": "Saudi Arabia",
            "singapore": "Singapore",
            "germany": "Germany", "berlin": "Germany",
            "netherlands": "Netherlands", "amsterdam": "Netherlands",
            "switzerland": "Switzerland",
            "ireland": "Ireland", "dublin": "Ireland",
            "israel": "Israel", "tel aviv": "Israel",
        }
        for indicator, country in country_indicators.items():
            if indicator in text_lower:
                return country
        return ""

    def _detect_industry(self, text: str) -> str:
        """Detect industry from text content."""
        text_lower = text.lower()
        industry_indicators = {
            "saas": "SaaS", "b2b saas": "B2B SaaS",
            "fintech": "Fintech", "financial": "Fintech",
            "healthtech": "Healthtech", "healthcare": "Healthtech",
            "ecommerce": "Ecommerce", "e-commerce": "Ecommerce",
            "marketplace": "Marketplace",
            "ai ": "AI", "artificial intelligence": "AI",
            "edtech": "EdTech", "education": "EdTech",
            "hrtech": "HRTech", "human resources": "HRTech",
            "insurtech": "InsurTech", "insurance": "InsurTech",
            "legaltech": "LegalTech", "legal": "LegalTech",
            "proptech": "PropTech", "real estate": "PropTech",
            "logistics": "Logistics",
        }
        for indicator, industry in industry_indicators.items():
            if indicator in text_lower:
                return industry
        return ""

    def _extract_contact(self, signal: RawSignal) -> Contact:
        """Extract contact information from a signal."""
        contact = Contact()

        # Extract author if available
        if signal.author:
            contact.name = signal.author
            contact.identity_confidence = 30.0

        # Extract author URL (e.g., Reddit profile, HN profile)
        if signal.author_url:
            contact.linkedin_url = signal.author_url
            contact.linkedin_status = "unverified"

        # Try to extract email from content
        import re
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        emails = email_pattern.findall(signal.content)
        if emails:
            # Filter out generic emails
            generic = {"support", "info", "hello", "sales", "noreply", "admin"}
            for email in emails:
                prefix = email.split("@")[0].lower()
                if prefix not in generic:
                    contact.email = email
                    contact.email_status = "unverified"
                    contact.email_evidence = f"Found in {signal.source} post"
                    break

        return contact


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BEACON — Cybersecurity Buyer Discovery Engine"
    )
    parser.add_argument(
        "--limit", type=int, default=50,
        help="Maximum number of opportunities to discover (default: 50)"
    )
    parser.add_argument(
        "--output", type=str, default=".",
        help="Output directory for results (default: current directory)"
    )
    parser.add_argument(
        "--sender-name", type=str, default="Security Team",
        help="Name for outreach messages"
    )
    parser.add_argument(
        "--sender-company", type=str, default="",
        help="Company name for outreach messages"
    )
    parser.add_argument(
        "--max-per-source", type=int, default=30,
        help="Maximum signals per source (default: 30)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Run engine
    engine = CybersecurityDiscoveryEngine(
        output_dir=args.output,
        sender_name=args.sender_name,
        sender_company=args.sender_company,
        max_items_per_source=args.max_per_source,
    )

    summary = asyncio.run(engine.run(limit=args.limit))

    # Exit with appropriate code
    if summary["sales_ready"] > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
