"""COMAI Buyability Pipeline — verified-brand-first discovery + scoring.

This pipeline:
1. Loads verified Indian D2C brand websites (real URLs, not guessed domains)
2. Enriches with evidence-backed detection
3. Scores with evidence-based buyability scoring
4. Outputs companies for founder review

Every claim requires evidence. No invented data.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.ecommerce_leads.models import (
    DetectionState,
    EnrichedEcommerceLead,
    RawEcommerceLead,
    is_valid_email,
)
from packages.qualification_engine.icp_loader import load_icp
from packages.qualification_engine.scorer import BuyabilityScorer, ScoringResult
from packages.qualification_engine.discovery import VerifiedBrandDiscovery
from packages.qualification_engine.enrichment import enrich_leads_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("comai_buyability.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def run_buyability_pipeline(target_prospects: int = 50):
    """Run the evidence-based buyability pipeline."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("COMAI BUYABILITY PIPELINE — Evidence-Based")
    logger.info("Target: %d NEW companies (not famous brands)", target_prospects)
    logger.info("=" * 60)

    # Load ICP
    icp = load_icp("comai")
    scorer = BuyabilityScorer(icp)

    # Phase 1: Verified brand discovery
    logger.info("\nPHASE 1: Verified Brand Discovery")
    logger.info("Loading verified Indian D2C brand websites...")

    discovery = VerifiedBrandDiscovery()
    discovered_leads = []
    signal_by_domain = {}

    async for lead, signal in discovery.discover(limit=200):
        discovered_leads.append(lead)
        signal_by_domain[lead.domain] = signal
        if len(discovered_leads) % 10 == 0:
            logger.info("  Loaded %d verified brands...", len(discovered_leads))

    logger.info("  Total loaded: %d verified brands", len(discovered_leads))

    # Phase 2: Enrichment with evidence
    logger.info("\nPHASE 2: Enrichment with Evidence")
    logger.info("Detecting technology, contacts, pain points...")

    enriched_leads = await enrich_leads_batch(discovered_leads, batch_size=10)
    logger.info("  Successfully enriched: %d", len(enriched_leads))

    # Phase 3: Add discovery signals to enriched leads
    for lead in enriched_leads:
        signal = signal_by_domain.get(lead.raw.domain)
        if signal:
            # Add discovery signal as growth/buying signal
            if not lead.growth_signals:
                lead.growth_signals = []
            lead.growth_signals.append({
                "type": "discovery",
                "evidence": signal.evidence,
                "confidence": signal.strength,
                "source": signal.source,
            })

    # Phase 4: Buyability scoring
    logger.info("\nPHASE 3: Buyability Scoring")
    logger.info("Scoring with evidence-based criteria...")

    scored_leads = []
    grade_counts = {}

    for lead in enriched_leads:
        result = scorer.score(lead)
        lead.buyability_score = result.total_score
        lead.buying_intent_score = result.buying_intent_total
        lead.grade = result.grade
        lead.business_stage = result.business_stage
        lead.evidence_grade = result.evidence_grade
        lead.missing_signals = result.missing_signals

        # Copy output fields
        lead.who_they_are = result.who_they_are
        lead.how_big = result.how_big
        lead.are_growing = result.are_growing
        lead.who_owns = result.who_owns
        lead.can_reach = result.can_reach
        lead.what_problem = result.what_problem
        lead.why_buy_comai = result.why_buy_comai
        lead.why_now = result.why_now
        lead.what_to_say = result.what_to_say

        scored_leads.append({
            "lead": lead,
            "result": result,
        })

        grade_counts[result.grade] = grade_counts.get(result.grade, 0) + 1

    logger.info("  Score distribution:")
    for grade, count in sorted(grade_counts.items()):
        logger.info("    %s: %d", grade, count)

    # Phase 5: Filter and rank
    logger.info("\nPHASE 4: Filtering and Ranking")

    # Sort by total score descending
    scored_leads.sort(key=lambda x: x["result"].total_score, reverse=True)

    # Take top N (exclude REJECT and NEEDS_ENRICHMENT)
    eligible = [
        s for s in scored_leads
        if s["result"].grade not in ["REJECT", "NEEDS_ENRICHMENT"]
    ]
    top_prospects = eligible[:target_prospects]

    # Calculate stats
    elapsed = time.time() - start_time
    scores = [s["result"].total_score for s in top_prospects]
    avg_score = sum(scores) / len(scores) if scores else 0

    logger.info("  Top %d prospects selected", len(top_prospects))
    logger.info("  Average score: %.1f", avg_score)
    if scores:
        logger.info("  Score range: %.1f - %.1f", min(scores), max(scores))

    # Phase 6: Output
    logger.info("\nPHASE 5: Output")

    exports_dir = PROJECT_ROOT / "exports"
    exports_dir.mkdir(exist_ok=True)

    # JSON output
    json_output = []
    for item in top_prospects:
        lead = item["lead"]
        result = item["result"]

        json_output.append({
            "company": lead.raw.company_name,
            "website": lead.raw.website,
            "domain": lead.raw.domain,
            "industry": lead.raw.industry,
            "city": lead.raw.city,
            "country": lead.raw.country,

            # Platform
            "platform": lead.platform,
            "platform_source": lead.platform_source,

            # Business size (evidence-based)
            "employee_count": lead.employee_count,
            "employee_source": lead.employee_source,
            "product_count": lead.product_count,
            "product_count_source": lead.product_count_source,

            # Founder (P0)
            "founder_name": lead.founder_name,
            "founder_role": lead.founder_role,
            "founder_source": lead.founder_source,
            "founder_confidence": lead.founder_confidence,
            "founder_linkedin": lead.founder_linkedin,

            # Contacts (validated)
            "email": lead.email,
            "email_valid": lead.email_valid,
            "email_source": lead.email_source,
            "phone": lead.phone,
            "phone_source": lead.phone_source,

            # Technology (three-state)
            "chatbot_state": lead.chatbot_state,
            "chatbot_evidence": lead.chatbot_evidence,
            "chatbot_source": lead.chatbot_source,
            "whatsapp_state": lead.whatsapp_state,
            "whatsapp_evidence": lead.whatsapp_evidence,
            "whatsapp_source": lead.whatsapp_source,
            "crm_state": lead.crm_state,
            "crm_evidence": lead.crm_evidence,
            "crm_source": lead.crm_source,

            # Social
            "social_links": lead.social_links,

            # Evidence
            "pain_points": lead.pain_points,
            "growth_signals": lead.growth_signals,
            "buying_signals": lead.buying_signals,

            # Scoring
            "buyability_score": result.total_score,
            "buying_intent_score": result.buying_intent_total,
            "grade": result.grade,
            "business_stage": result.business_stage,
            "evidence_grade": result.evidence_grade,
            "missing_signals": result.missing_signals,

            # Sales intelligence (evidence-backed)
            "who_they_are": result.who_they_are,
            "how_big": result.how_big,
            "are_growing": result.are_growing,
            "who_owns": result.who_owns,
            "can_reach": result.can_reach,
            "what_problem": result.what_problem,
            "why_buy_comai": result.why_buy_comai,
            "why_now": result.why_now,
            "what_to_say": result.what_to_say,
        })

    # Save JSON
    json_path = exports_dir / "comai_buyability_results.json"
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    logger.info("  Saved JSON: %s", json_path)

    # Save Excel
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "COMAI Buyability Prospects"

        headers = [
            "Company", "Website", "Industry", "City", "Platform",
            "Products", "Employees", "Founder", "Founder Role",
            "Email", "Email Valid", "Phone",
            "Chatbot", "WhatsApp", "CRM",
            "Buyability Score", "Buying Intent", "Grade", "Business Stage",
            "Evidence Grade",
            "Who They Are", "What Problem", "Why Buy COMAI", "What To Say",
        ]
        ws.append(headers)

        for item in json_output:
            ws.append([
                item["company"],
                item["website"],
                item["industry"],
                item["city"],
                item["platform"],
                item["product_count"],
                item["employee_count"],
                item["founder_name"],
                item["founder_role"],
                item["email"],
                item["email_valid"],
                item["phone"],
                item["chatbot_state"],
                item["whatsapp_state"],
                item["crm_state"],
                item["buyability_score"],
                item["buying_intent_score"],
                item["grade"],
                item["business_stage"],
                item["evidence_grade"],
                item["who_they_are"],
                item["what_problem"],
                item["why_buy_comai"],
                item["what_to_say"],
            ])

        excel_path = exports_dir / "comai_buyability_prospects.xlsx"
        try:
            wb.save(excel_path)
            logger.info("  Saved Excel: %s", excel_path)
        except PermissionError:
            # Try with a timestamped filename if the file is locked
            import time as _time
            ts = int(_time.time())
            alt_path = exports_dir / f"comai_buyability_prospects_{ts}.xlsx"
            wb.save(alt_path)
            logger.info("  Saved Excel (alt): %s", alt_path)
    except ImportError:
        logger.warning("  openpyxl not installed — skipping Excel export")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("COMAI BUYABILITY PIPELINE — Complete")
    logger.info("=" * 60)
    logger.info("Time: %.1f seconds", elapsed)
    logger.info("Discovered: %d", len(discovered_leads))
    logger.info("Enriched: %d", len(enriched_leads))
    logger.info("Scored: %d", len(scored_leads))
    logger.info("Top Prospects: %d", len(top_prospects))
    logger.info("Average Score: %.1f", avg_score)

    logger.info("\nGRADE DISTRIBUTION:")
    for grade, count in sorted(grade_counts.items()):
        logger.info("  %s: %d", grade, count)

    logger.info("\nTOP 10 PROSPECTS:")
    for i, item in enumerate(top_prospects[:10], 1):
        lead = item["lead"]
        result = item["result"]
        logger.info(
            "  %d. %s — Score: %.1f (Intent: %.1f) — %s — %s — Evidence: %s",
            i,
            lead.raw.company_name,
            result.total_score,
            result.buying_intent_total,
            result.grade,
            result.business_stage,
            result.evidence_grade,
        )

    logger.info("\n" + "=" * 60)
    logger.info("FOUNDER REVIEW REQUIRED")
    logger.info("=" * 60)
    logger.info("These %d prospects are evidence-backed.", len(top_prospects))
    logger.info("Every claim has a source and confidence level.")
    logger.info("Review and tell me which ones you'd genuinely want to call.")
    logger.info("Then we scale the machine.")

    return top_prospects


if __name__ == "__main__":
    prospects = asyncio.run(run_buyability_pipeline(target_prospects=50))
