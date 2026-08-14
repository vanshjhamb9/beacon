"""Daily Discovery Task for Intent-First Opportunity Discovery."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from packages.discovery_engine.engine import DiscoveryEngine
from packages.enrichment.opportunity_enrichment import OpportunityEnricher, EnrichedOpportunity
from packages.enrichment.contact_enrichment import ContactEnricher
from packages.enrichment.cross_source_validation import CrossSourceValidator
from packages.qualification.opportunity_qualification import OpportunityQualifier

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPORTS_DIR = PROJECT_ROOT / "exports"


async def run_daily_discovery(target_count: int = 50) -> dict[str, Any]:
    """Run daily opportunity discovery pipeline.
    
    Args:
        target_count: Target number of qualified opportunities.
        
    Returns:
        Dictionary with discovery results and statistics.
    """
    logger.info("Starting daily discovery pipeline...")
    start_time = datetime.now()
    
    # Initialize components
    discovery_engine = DiscoveryEngine()
    enricher = OpportunityEnricher()
    contact_enricher = ContactEnricher()
    cross_source_validator = CrossSourceValidator()
    qualifier = OpportunityQualifier()
    
    # Step 1: Discovery
    logger.info("Step 1: Running discovery sources...")
    discovered = await discovery_engine.discover(limit=target_count * 3)  # Get more than needed
    logger.info("Discovered %d opportunities", len(discovered))
    
    # Step 2: Enrichment
    logger.info("Step 2: Enriching opportunities...")
    enriched: list[EnrichedOpportunity] = []
    for i, opportunity in enumerate(discovered):
        if len(enriched) >= target_count * 2:  # Stop if we have enough
            break
        
        try:
            enriched_opp = await enricher.enrich(opportunity)
            enriched.append(enriched_opp)
            
            if (i + 1) % 10 == 0:
                logger.info("  Enriched %d/%d opportunities", i + 1, min(len(discovered), target_count * 2))
        except Exception as e:
            logger.warning("  Failed to enrich %s: %s", opportunity.company_name, e)
    
    logger.info("Enriched %d opportunities", len(enriched))
    
    # Step 3: Contact Enrichment
    logger.info("Step 3: Enriching contacts...")
    for opp in enriched:
        if opp.person_name and opp.person_name != "Unknown":
            try:
                contact = await contact_enricher.enrich_contact(
                    opp.person_name, opp.company_name, opp.source_url
                )
                opp.linkedin_url = opp.linkedin_url or contact.linkedin_url
                opp.email = opp.email or contact.email
                opp.email_status = contact.email_status if contact.email else opp.email_status
                opp.phone = opp.phone or contact.phone
                opp.company_website = opp.company_website or contact.company_website
            except Exception as e:
                logger.warning("  Failed to enrich contact for %s: %s", opp.company_name, e)
    
    # Step 4: Cross-Source Validation
    logger.info("Step 4: Validating cross-source information...")
    for opp in enriched:
        try:
            validation = await cross_source_validator.validate(
                opp.person_name, opp.company_name, opp.source_url,
                opp.exact_requirement, opp.linkedin_url, opp.company_website
            )
            opp.cross_source_validation = {
                "source_count": validation.source_count,
                "source_urls": validation.source_urls,
                "source_types": validation.source_types,
                "cross_source_confidence": validation.cross_source_confidence
            }
        except Exception as e:
            logger.warning("  Failed to validate %s: %s", opp.company_name, e)
    
    # Step 5: Qualification
    logger.info("Step 5: Qualifying opportunities...")
    qualification_results = qualifier.batch_qualify(enriched)
    
    # Get qualified opportunities
    qualified = qualifier.get_qualified_opportunities(enriched, qualification_results)
    logger.info("Qualified %d opportunities", len(qualified))
    
    # Sort by opportunity score
    qualified.sort(key=lambda x: x.opportunity_score, reverse=True)
    
    # Take top N
    final_qualified = qualified[:target_count]
    
    # Step 6: Generate Output
    logger.info("Step 6: Generating output files...")
    output = generate_output(final_qualified, qualification_results, len(discovered), len(enriched))
    
    # Save output
    save_output(output)
    
    # Generate report
    report = generate_report(output)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("Discovery pipeline completed in %.1f seconds", duration)
    logger.info("Results: %d discovered → %d enriched → %d qualified",
                len(discovered), len(enriched), len(final_qualified))
    
    return {
        "status": "success",
        "duration_seconds": duration,
        "discovered": len(discovered),
        "enriched": len(enriched),
        "qualified": len(final_qualified),
        "target_count": target_count,
        "output_file": str(EXPORTS_DIR / "intent_opportunities_50.json"),
        "report_file": str(EXPORTS_DIR / "intent_opportunities_report.txt"),
        "report": report
    }


def generate_output(
    qualified: list[EnrichedOpportunity],
    qualification_results: list,
    total_discovered: int,
    total_enriched: int
) -> dict[str, Any]:
    """Generate output JSON."""
    opportunities = []
    
    for opp in qualified:
        opp_dict = {
            "company_name": opp.company_name,
            "person_name": opp.person_name,
            "person_role": opp.person_role,
            "company_website": opp.company_website,
            "source_platform": opp.source_platform,
            "source_url": opp.source_url,
            "source_date": opp.source_date,
            "exact_requirement": opp.exact_requirement,
            "intent_level": opp.intent_level,
            "intent_score": opp.intent_score,
            "icp_fit": opp.icp_fit,
            "buyability": opp.buyability,
            "evidence_quality": opp.evidence_quality,
            "opportunity_score": opp.opportunity_score,
            "primary_business_unit": opp.primary_business_unit,
            "secondary_business_unit": opp.secondary_business_unit,
            "recommended_service": opp.recommended_service,
            "decision_maker": opp.decision_maker,
            "decision_maker_confidence": opp.decision_maker_confidence,
            "linkedin_url": opp.linkedin_url,
            "email": opp.email,
            "email_status": opp.email_status,
            "phone": opp.phone,
            "company_stage": opp.company_stage,
            "company_size": opp.company_size,
            "industry": opp.industry,
            "technology": opp.technology,
            "outsourcing_fit": opp.outsourcing_fit,
            "why_now": opp.why_now,
            "why_inowix": opp.why_inowix,
            "evidence": opp.evidence,
            "cross_source_validation": opp.cross_source_validation,
            "missing_information": opp.missing_information,
            "recommended_next_research": opp.recommended_next_research,
            "qualification_status": opp.qualification_status,
            "outreach_status": opp.outreach_status
        }
        opportunities.append(opp_dict)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_discovered": total_discovered,
        "total_enriched": total_enriched,
        "total_qualified": len(qualified),
        "opportunities": opportunities
    }


def save_output(output: dict[str, Any]) -> None:
    """Save output to JSON file."""
    output_file = EXPORTS_DIR / "intent_opportunities_50.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info("Output saved to %s", output_file)


def generate_report(output: dict[str, Any]) -> str:
    """Generate human-readable report."""
    report = []
    
    report.append("=" * 80)
    report.append("BEACON INTENT-FIRST OPPORTUNITY DISCOVERY REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {output['generated_at']}")
    report.append("")
    
    report.append("SUMMARY")
    report.append("-" * 40)
    report.append(f"Total Discovered: {output['total_discovered']}")
    report.append(f"Total Enriched: {output['total_enriched']}")
    report.append(f"Total Qualified: {output['total_qualified']}")
    report.append("")
    
    # Top 10 opportunities
    report.append("TOP 10 OPPORTUNITIES")
    report.append("-" * 40)
    
    for i, opp in enumerate(output["opportunities"][:10], 1):
        report.append(f"\n{i}. {opp['company_name']}")
        report.append(f"   Person: {opp['person_name']} ({opp['person_role']})")
        report.append(f"   Requirement: {opp['exact_requirement'][:100]}...")
        report.append(f"   Intent: {opp['intent_level']} (Score: {opp['intent_score']})")
        report.append(f"   Opportunity Score: {opp['opportunity_score']}")
        report.append(f"   Business Unit: {opp['primary_business_unit']}")
        report.append(f"   Service: {opp['recommended_service']}")
        report.append(f"   Outsourcing Fit: {opp['outsourcing_fit']}")
        report.append(f"   LinkedIn: {opp['linkedin_url'] or 'Not found'}")
        report.append(f"   Email: {opp['email'] or 'Not found'} ({opp['email_status']})")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        result = await run_daily_discovery(target_count=50)
        print(result["report"])
    
    asyncio.run(main())
