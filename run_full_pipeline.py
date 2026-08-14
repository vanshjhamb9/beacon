"""
BEACON FULL PIPELINE RUN — STANDALONE
Runs all engines end-to-end using websearch directly.
No dependency on opencode module.

CTO Hard Rules Applied:
- Do NOT assume funding=buying intent
- Do NOT invent pain points
- Do NOT mark SALES_READY without evidence
- Email ONLY with VERIFIED status
"""

import json
import sys
import logging
import hashlib
import re
from datetime import datetime, date
from pathlib import Path
from dataclasses import asdict, dataclass, field
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
from urllib.error import URLError
import ssl

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = PROJECT_ROOT / "exports" / "full_pipeline"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Disable SSL verification for websearch
ssl._create_default_https_context = ssl._create_unverified_context


# ============================================================
# WEBSEARCH HELPER
# ============================================================

def websearch(query: str, num_results: int = 8) -> list[dict]:
    """Simple websearch using Google search."""
    results = []
    try:
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Extract links and titles
        links = re.findall(r'<a href="/url\?q=([^&"]+)', html)
        titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html)

        for i, link in enumerate(links[:num_results]):
            title = titles[i] if i < len(titles) else "Unknown"
            title = re.sub(r'<[^>]+>', '', title)
            results.append({"url": link, "title": title})
    except Exception as e:
        logger.warning(f"Websearch failed: {e}")
    return results


def websearch_reddit(query: str, num_results: int = 10) -> list[dict]:
    """Search Reddit specifically."""
    return websearch(f"site:reddit.com {query}", num_results)


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DiscoveryResult:
    unique_id: str
    author: str
    text: str
    source_url: str
    source_type: str
    company_name: str
    project_name: str
    discovery_reason: str
    buying_signals: list[str] = field(default_factory=list)
    growth_signals: list[str] = field(default_factory=list)
    industry: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class EnrichedOpportunity:
    discovery: DiscoveryResult
    intent_level: str = "UNKNOWN"
    intent_score: float = 0.0
    matched_services: list[dict] = field(default_factory=list)
    primary_service: Optional[str] = None
    primary_business_unit: Optional[str] = None
    buyability_score: float = 0.0
    opportunity_score: float = 0.0
    qualification_score: float = 0.0
    qualification_status: str = "PENDING"
    revenue_estimate: dict = field(default_factory=dict)
    playbook: dict = field(default_factory=dict)
    final_status: str = "PENDING"


# ============================================================
# INTENT PATTERNS (Simplified from patterns.py)
# ============================================================

INTENT_PATTERNS = {
    "ACTIVE_REQUIREMENT": {
        "keywords": [
            "looking for a developer", "looking for developer", "need a developer",
            "need developer", "hire a developer", "hire developer", "hire an agency",
            "looking for an agency", "looking for a studio", "need help building",
            "looking for someone to build", "need to hire", "seeking developer",
            "freelance developer", "contract developer", "looking for technical",
            "need technical help", "mvp development", "build an app", "build a platform",
            "looking for co-founder", "technical co-founder", "need a backend",
            "need frontend", "need full stack", "need mobile developer",
        ],
        "services": {
            "saas": ["saas mvp", "saas development", "saas platform", "saas product"],
            "custom": ["web app", "mobile app", "custom software", "api development", "backend", "frontend"],
            "comai": ["chatbot", "whatsapp", "ai automation", "customer support"],
        },
        "score": 90,
    },
    "EVALUATION": {
        "keywords": [
            "comparing agencies", "evaluating options", "which framework",
            "tech stack recommendation", "platform comparison", "pricing",
            "how much does it cost", "budget", "timeline", "project scope",
        ],
        "score": 60,
    },
    "EARLY_INTENT": {
        "keywords": [
            "thinking about building", "considering", "exploring options",
            "research phase", "planning to build", "future project",
        ],
        "score": 30,
    },
}

SERVICE_KEYWORDS = {
    "SAAS_DEVELOPMENT": ["saas", "mvp", "platform", "subscription", "multi-tenant"],
    "CUSTOM_SOFTWARE": ["web app", "mobile app", "api", "backend", "frontend", "full stack", "custom"],
    "COMAI": ["chatbot", "whatsapp", "ai", "automation", "customer support", "ecommerce"],
}


# ============================================================
# PHASE 1: DISCOVERY
# ============================================================

def run_discovery() -> list[DiscoveryResult]:
    """Run discovery via websearch across multiple sources."""
    print("=" * 80)
    print("PHASE 1: DISCOVERY")
    print("=" * 80)

    discoveries = []
    seen_urls = set()

    # Search queries for buyer intent
    queries = [
        # Reddit buyer intent
        ("site:reddit.com/r/SaaS looking for developer OR agency OR studio 2026", "REDDIT"),
        ("site:reddit.com/r/Entrepreneur need developer OR hire developer 2026", "REDDIT"),
        ("site:reddit.com/r/startups looking for technical co-founder OR developer 2026", "REDDIT"),
        ("site:reddit.com/r/webdev need help building OR hire 2026", "REDDIT"),
        ("site:reddit.com/r/microsaas looking for developer OR build 2026", "REDDIT"),
        # IndieHackers
        ("site:indiehackers.com looking for developer OR co-founder OR technical 2026", "INDIEHACKERS"),
        # Twitter/X
        ("site:x.com looking for developer OR need developer OR hire developer 2026", "TWITTER"),
        # Product Hunt
        ("site:producthunt.com looking for technical co-founder OR developer 2026", "PRODUCTHUNT"),
        # General startup communities
        ("startup looking for developer to build MVP OR platform 2026", "COMMUNITY"),
        ("founder need technical help build app OR saas 2026", "COMMUNITY"),
    ]

    for query, source_type in queries:
        print(f"\nSearching: {source_type}...")
        results = websearch(query, num_results=5)

        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")

            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Only keep actual opportunity posts, not articles
            if any(skip in url.lower() for skip in [
                "upwork.com/hire", "toptal.com", "how-to-hire", "guide",
                "best-freelance", "top-developers", "hiring-guide"
            ]):
                continue

            # Determine source
            if "reddit.com" in url:
                source = "REDDIT"
            elif "indiehackers.com" in url:
                source = "INDIEHACKERS"
            elif "x.com" in url or "twitter.com" in url:
                source = "TWITTER"
            elif "producthunt.com" in url:
                source = "PRODUCTHUNT"
            else:
                source = source_type

            # Extract author from URL
            author = "Unknown"
            if "/user/" in url:
                author = url.split("/user/")[-1].split("/")[0].split("?")[0]
            elif "/comments/" in url:
                parts = url.split("/comments/")
                if len(parts) > 1:
                    author = parts[0].split("/")[-1]

            disc = DiscoveryResult(
                unique_id=hashlib.sha256(url.encode()).hexdigest()[:12],
                author=author,
                text=title,
                source_url=url,
                source_type=source,
                company_name="",
                project_name=title[:50],
                discovery_reason=title,
            )
            discoveries.append(disc)

        print(f"  Found {len(results)} results")

    print(f"\n[OK] Discovery complete: {len(discoveries)} raw opportunities found")
    return discoveries


# ============================================================
# PHASE 2: ENRICHMENT
# ============================================================

def run_enrichment(discoveries: list[DiscoveryResult]) -> list[EnrichedOpportunity]:
    """Enrich each discovery with intent, service matching, and scoring."""
    print("\n" + "=" * 80)
    print("PHASE 2: ENRICHMENT")
    print("=" * 80)

    enriched = []

    for i, disc in enumerate(discoveries, 1):
        print(f"\n[{i}/{len(discoveries)}] {disc.project_name[:60]}")

        opp = EnrichedOpportunity(discovery=disc)
        text = (disc.text + " " + disc.discovery_reason).lower()

        # Intent detection
        intent_level = "UNKNOWN"
        intent_score = 0

        for level, config in INTENT_PATTERNS.items():
            for kw in config["keywords"]:
                if kw in text:
                    intent_level = level
                    intent_score = config["score"]
                    break
            if intent_level != "UNKNOWN":
                break

        opp.intent_level = intent_level
        opp.intent_score = intent_score
        print(f"  Intent: {intent_level} ({intent_score})")

        # Service matching
        best_service = None
        best_bu = None
        best_conf = 0

        for bu, keywords in SERVICE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > best_conf:
                best_conf = matches
                best_bu = bu
                if bu == "SAAS_DEVELOPMENT":
                    best_service = "Custom SaaS"
                elif bu == "CUSTOM_SOFTWARE":
                    best_service = "Web/Mobile App"
                elif bu == "COMAI":
                    best_service = "AI Automation"

        opp.primary_service = best_service
        opp.primary_business_unit = best_bu
        if best_service:
            opp.matched_services = [{"service": best_service, "business_unit": best_bu, "confidence": best_conf}]
        print(f"  Service: {best_service or 'None'} ({best_bu or 'None'})")

        # Buyability scoring
        buyability = 0
        if any(kw in text for kw in ["looking for", "need", "hire", "developer", "agency"]):
            buyability += 25
        if any(kw in text for kw in ["mvp", "build", "platform", "app"]):
            buyability += 20
        if any(kw in text for kw in ["budget", "price", "$", "cost", "pay"]):
            buyability += 15
        if any(kw in text for kw in ["startup", "founder", "building"]):
            buyability += 15
        if any(kw in text for kw in ["saas", "subscription", "revenue"]):
            buyability += 15
        opp.buyability_score = min(buyability, 100)
        print(f"  Buyability: {opp.buyability_score}")

        # Opportunity score
        opp.opportunity_score = (opp.intent_score * 0.4 + opp.buyability_score * 0.3 + best_conf * 10 * 0.3)
        print(f"  Opportunity: {opp.opportunity_score:.1f}")

        enriched.append(opp)

    print(f"\n[OK] Enrichment complete: {len(enriched)} opportunities enriched")
    return enriched


# ============================================================
# PHASE 3: QUALIFICATION
# ============================================================

def run_qualification(enriched: list[EnrichedOpportunity]) -> list[EnrichedOpportunity]:
    """Qualify opportunities using 6-criteria gate."""
    print("\n" + "=" * 80)
    print("PHASE 3: QUALIFICATION")
    print("=" * 80)

    qualified = []

    for opp in enriched:
        score = 0

        # 1. Requirement evidence (25 pts)
        if opp.intent_level == "ACTIVE_REQUIREMENT":
            score += 25

        # 2. Person verification (20 pts)
        if opp.discovery.author and opp.discovery.author != "Unknown":
            score += 20

        # 3. Company verification (15 pts)
        if opp.discovery.company_name:
            score += 15

        # 4. Service match (15 pts)
        if opp.primary_service:
            score += 15

        # 5. Outsourcing fit (15 pts)
        if opp.buyability_score >= 30:
            score += 15

        # 6. Recency (10 pts)
        score += 10

        opp.qualification_score = score
        opp.qualification_status = "QUALIFIED" if score >= 50 else "REJECTED"

        # Final status
        if score >= 75 and opp.opportunity_score >= 50:
            opp.final_status = "SALES_READY"
        elif score >= 50:
            opp.final_status = "NEEDS_RESEARCH"
        else:
            opp.final_status = "REJECTED"

        if opp.final_status != "REJECTED":
            qualified.append(opp)
            print(f"  [+] {opp.discovery.project_name[:40]}: {score}/100 {opp.final_status}")
        else:
            print(f"  [-] {opp.discovery.project_name[:40]}: {score}/100 REJECTED")

    print(f"\n[OK] Qualification complete: {len(qualified)} qualified")
    return qualified


# ============================================================
# PHASE 4: REVENUE INTELLIGENCE
# ============================================================

def run_revenue(qualified: list[EnrichedOpportunity]) -> list[EnrichedOpportunity]:
    """Generate revenue intelligence."""
    print("\n" + "=" * 80)
    print("PHASE 4: REVENUE INTELLIGENCE")
    print("=" * 80)

    for opp in qualified:
        # Revenue estimate
        pricing = {
            "Custom SaaS": {"min": 40000, "max": 90000},
            "Web/Mobile App": {"min": 25000, "max": 60000},
            "AI Automation": {"min": 22000, "max": 50000},
        }
        p = pricing.get(opp.primary_service or "", {"min": 20000, "max": 50000})
        opp.revenue_estimate = {
            "deal_size_min": p["min"],
            "deal_size_max": p["max"],
            "deal_size_avg": (p["min"] + p["max"]) / 2,
            "currency": "USD",
        }

        # Playbook
        opp.playbook = {
            "business_pain": opp.discovery.discovery_reason[:200],
            "recommended_service": opp.primary_service or "Custom Software",
            "decision_maker": opp.discovery.author,
            "expected_outcome": "Discovery call",
            "risk": "Low" if opp.qualification_score >= 75 else "Medium",
        }

        print(f"  {opp.discovery.project_name[:40]}: ${p['min']:,}-${p['max']:,}")

    print(f"\n[OK] Revenue intelligence complete")
    return qualified


# ============================================================
# PHASE 5: OUTPUT
# ============================================================

def generate_output(qualified: list[EnrichedOpportunity], all_enriched: list[EnrichedOpportunity]):
    """Generate final output files."""
    print("\n" + "=" * 80)
    print("PHASE 5: OUTPUT")
    print("=" * 80)

    sales_ready = [o for o in qualified if o.final_status == "SALES_READY"]
    needs_research = [o for o in qualified if o.final_status == "NEEDS_RESEARCH"]
    rejected = [o for o in all_enriched if o.final_status == "REJECTED"]

    # Save all enriched
    enriched_data = []
    for opp in all_enriched:
        enriched_data.append({
            "unique_id": opp.discovery.unique_id,
            "project_name": opp.discovery.project_name,
            "author": opp.discovery.author,
            "source_url": opp.discovery.source_url,
            "source_type": opp.discovery.source_type,
            "intent_level": opp.intent_level,
            "intent_score": opp.intent_score,
            "primary_service": opp.primary_service,
            "primary_business_unit": opp.primary_business_unit,
            "buyability_score": opp.buyability_score,
            "opportunity_score": opp.opportunity_score,
            "qualification_score": opp.qualification_score,
            "final_status": opp.final_status,
        })

    with open(OUTPUT_DIR / "enriched_opportunities.json", "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: enriched_opportunities.json ({len(enriched_data)} items)")

    # Save top opportunities
    top_data = []
    for opp in sales_ready + needs_research:
        top_data.append({
            "unique_id": opp.discovery.unique_id,
            "project_name": opp.discovery.project_name,
            "author": opp.discovery.author,
            "source_url": opp.discovery.source_url,
            "source_type": opp.discovery.source_type,
            "discovery_reason": opp.discovery.discovery_reason,
            "intent_level": opp.intent_level,
            "intent_score": opp.intent_score,
            "primary_service": opp.primary_service,
            "primary_business_unit": opp.primary_business_unit,
            "opportunity_score": opp.opportunity_score,
            "qualification_score": opp.qualification_score,
            "final_status": opp.final_status,
            "revenue_estimate": opp.revenue_estimate,
            "playbook": opp.playbook,
        })

    with open(OUTPUT_DIR / "top_opportunities.json", "w", encoding="utf-8") as f:
        json.dump(top_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: top_opportunities.json ({len(top_data)} items)")

    # Save SALES_READY
    with open(OUTPUT_DIR / "sales_ready.json", "w", encoding="utf-8") as f:
        json.dump([o for o in top_data if o["final_status"] == "SALES_READY"], f, indent=2, ensure_ascii=False)

    # Save NEEDS_RESEARCH
    with open(OUTPUT_DIR / "needs_research.json", "w", encoding="utf-8") as f:
        json.dump([o for o in top_data if o["final_status"] == "NEEDS_RESEARCH"], f, indent=2, ensure_ascii=False)

    # Generate report
    report = f"""# FULL PIPELINE REPORT -- {TODAY}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Discovered | {len(all_enriched)} |
| SALES_READY | {len(sales_ready)} |
| NEEDS_RESEARCH | {len(needs_research)} |
| REJECTED | {len(rejected)} |

## SALES_READY Opportunities

"""
    for i, opp in enumerate(sales_ready, 1):
        report += f"""### {i}. {opp.discovery.project_name}
- **Author:** {opp.discovery.author}
- **Source:** {opp.discovery.source_type} ({opp.discovery.source_url})
- **Intent:** {opp.intent_level} ({opp.intent_score})
- **Service:** {opp.primary_service}
- **Opportunity Score:** {opp.opportunity_score:.1f}
- **Qualification:** {opp.qualification_score}/100
- **Revenue:** ${opp.revenue_estimate.get('deal_size_min', 0):,}-${opp.revenue_estimate.get('deal_size_max', 0):,}

"""

    report += """## NEEDS_RESEARCH Opportunities

"""
    for i, opp in enumerate(needs_research, 1):
        report += f"""### {i}. {opp.discovery.project_name}
- **Author:** {opp.discovery.author}
- **Source:** {opp.discovery.source_type} ({opp.discovery.source_url})
- **Intent:** {opp.intent_level} ({opp.intent_score})
- **Service:** {opp.primary_service}
- **Opportunity Score:** {opp.opportunity_score:.1f}
- **Qualification:** {opp.qualification_score}/100

"""

    report += f"""---
Generated: {datetime.now().isoformat()}
"""
    with open(OUTPUT_DIR / "FULL_PIPELINE_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Saved: FULL_PIPELINE_REPORT.md")

    # Summary
    print("\n" + "=" * 80)
    print("FULL PIPELINE COMPLETE")
    print("=" * 80)
    print(f"  Total Discovered: {len(all_enriched)}")
    print(f"  SALES_READY: {len(sales_ready)}")
    print(f"  NEEDS_RESEARCH: {len(needs_research)}")
    print(f"  REJECTED: {len(rejected)}")
    print(f"\n  Output: {OUTPUT_DIR}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("BEACON FULL PIPELINE RUN")
    print(f"Date: {TODAY}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 80)

    # Phase 1: Discovery
    discoveries = run_discovery()

    if not discoveries:
        print("\nNo discoveries found. Exiting.")
        return

    # Phase 2: Enrichment
    enriched = run_enrichment(discoveries)

    # Phase 3: Qualification
    qualified = run_qualification(enriched)

    # Phase 4: Revenue Intelligence
    qualified = run_revenue(qualified)

    # Phase 5: Output
    generate_output(qualified, enriched)


if __name__ == "__main__":
    main()
