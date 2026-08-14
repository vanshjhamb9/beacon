"""Beacon Pipeline Orchestrator.

Runs the full opportunity pipeline:
1. Load discovered companies
2. Combine all text signals into one content string
3. Detect intent (EXPLICIT REQUIREMENTS > ICP FIT)
4. Score against all three ICPs (COMAI, SaaS, Custom)
5. Match services
6. Compute opportunity score (ICP * 0.3 + Intent * 0.4 + Buyability * 0.3)
7. Generate sales intelligence
8. Output ranked opportunities

Every opportunity has evidence explaining WHY contact NOW and WHICH service.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.intent_engine.detector import classify_overall_intent, detect_intent
from packages.intent_engine.service_matcher import match_services
from packages.opportunity_intelligence.canonical import (
    BusinessUnit,
    ICPScore,
    Opportunity,
    QualificationStatus,
    OutreachStatus,
    IntentLevel,
    EvidenceConfidence,
    EvidenceRecord,
    IntentSignal,
    ServiceMatch,
)
from packages.multi_icp_scorer.scorer import (
    compute_opportunity_score,
    route_primary_business_unit,
    score_all_icps,
)
from packages.multi_icp_scorer.sales_intel import generate_sales_intel


# ============================================================
# BUYABILITY (simplified — will expand later)
# ============================================================

def compute_buyability(text: str) -> float:
    """Simplified buyability score based on profile signals."""
    score = 0.0
    text_lower = text.lower()

    if any(kw in text_lower for kw in ["funded", "raised", "series", "investment"]):
        score += 20
    if any(kw in text_lower for kw in ["team", "employees", "staff"]):
        score += 15
    if any(kw in text_lower for kw in ["revenue", "customers", "users", "clients"]):
        score += 20
    if any(kw in text_lower for kw in ["d2c", "ecommerce", "shopify", "brand"]):
        score += 15
    if any(kw in text_lower for kw in ["startup", "founded", "new", "early stage"]):
        score += 10
    if any(kw in text_lower for kw in ["enterprise", "large", "200+ employees"]):
        score -= 20
    if any(kw in text_lower for kw in ["listed", "public", "unicorn"]):
        score -= 30

    return max(min(score, 100.0), 0.0)


# ============================================================
# PIPELINE
# ============================================================

def run_pipeline(discovery_file: str) -> list[Opportunity]:
    """Run full opportunity pipeline on discovery results.

    Args:
        discovery_file: Path to JSON file with discovered companies.

    Returns:
        List of ranked Opportunity objects.
    """
    with open(discovery_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies from {discovery_file}")
    print("=" * 70)

    opportunities: list[Opportunity] = []

    for company in companies:
        opp = _process_company(company)
        if opp:
            opportunities.append(opp)

    # Sort by opportunity score descending
    opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)

    print(f"\nProcessed {len(opportunities)} opportunities")
    return opportunities


def _process_company(company: dict) -> Opportunity | None:
    """Process a single company through the full pipeline."""
    company_name = company.get("company_name", company.get("name", "Unknown"))
    domain = company.get("domain", "")

    # Combine all text signals into one content string for intent detection
    text_parts = [
        company.get("discovery_reason", ""),
        company.get("discovery_text", ""),
        company.get("discovery_description", ""),
        " ".join(company.get("growth_signals", [])),
        " ".join(company.get("buying_signals", [])),
        " ".join(company.get("technology_signals", [])),
    ]
    text = " ".join(p for p in text_parts if p).lower()

    if not text.strip():
        print(f"  [SKIP] {company_name}: No discovery text")
        return None

    # --- STEP 1: Intent Detection ---
    signals = detect_intent(text)
    intent_level, intent_score = classify_overall_intent(signals)

    # --- STEP 2: Multi-ICP Scoring ---
    icp_scores = score_all_icps(text, intent_level, intent_score)
    comai = icp_scores[BusinessUnit.COMAI]
    saas = icp_scores[BusinessUnit.SAAS_DEVELOPMENT]
    custom = icp_scores[BusinessUnit.CUSTOM_SOFTWARE]

    # --- STEP 3: Service Matching ---
    service_matches = match_services(text)

    # --- STEP 4: Buyability ---
    buyability = compute_buyability(text)

    # --- STEP 5: Routing ---
    primary_bu, secondary_bus = route_primary_business_unit(comai, saas, custom)

    # If intent is COMAI-focused, route accordingly
    intent_bu_hints = set()
    for s in signals:
        if "comai" in s.signal_source.lower() or "whatsapp" in s.signal_text.lower() or \
           "chatbot" in s.signal_text.lower() or "shopify" in s.signal_text.lower():
            intent_bu_hints.add(BusinessUnit.COMAI)
        elif "saas" in s.signal_source.lower() or "developer" in s.signal_text.lower() or \
             "mvp" in s.signal_text.lower():
            intent_bu_hints.add(BusinessUnit.SAAS_DEVELOPMENT)
        elif "custom" in s.signal_source.lower() or "erp" in s.signal_text.lower() or \
             "automation" in s.signal_text.lower():
            intent_bu_hints.add(BusinessUnit.CUSTOM_SOFTWARE)

    if intent_bu_hints:
        primary_bu = list(intent_bu_hints)[0]

    # --- STEP 6: Compute Opportunity Score ---
    icp_fit = max(comai.score, saas.score, custom.score)
    opp_score = compute_opportunity_score(icp_fit, intent_score, buyability, intent_level)

    # --- STEP 7: Qualification ---
    qual_status = QualificationStatus.DISCOVERED
    if intent_level in (IntentLevel.ACTIVE_REQUIREMENT, IntentLevel.EVALUATION):
        qual_status = QualificationStatus.QUALIFIED
    elif intent_level == IntentLevel.EARLY_INTENT:
        qual_status = QualificationStatus.ENRICHED
    elif opp_score >= 40:
        qual_status = QualificationStatus.ENRICHED
    elif opp_score < 15:
        qual_status = QualificationStatus.REJECTED

    if intent_level == IntentLevel.NO_INTENT and opp_score < 20:
        return None

    # --- Build Opportunity ---
    opp = Opportunity(
        opportunity_id=f"{company_name.lower().replace(' ', '_')}_{date.today().isoformat()}",
        discovery_source=company.get("source", "unknown"),
        discovery_source_url=company.get("source_url", ""),
        discovery_date=date.today(),
        discovery_reason=company.get("discovery_reason", ""),
        company_name=company_name,
        domain=domain,
        company_stage=company.get("stage", "unknown"),
        industry=company.get("industry", "unknown"),
        city=company.get("city", ""),
        country=company.get("country", "India"),
        founder_name=company.get("founder", ""),
        intent_level=intent_level,
        intent_score=intent_score,
        intent_signals=signals,
        explicit_requirement=_extract_explicit_requirement(text),
        comai_score=comai,
        saas_score=saas,
        custom_score=custom,
        icp_fit_score=icp_fit,
        buyability_score=buyability,
        opportunity_score=opp_score,
        primary_business_unit=primary_bu,
        secondary_business_units=secondary_bus,
        service_matches=service_matches,
        buying_signals=company.get("buying_signals", []),
        buying_signal_sources=company.get("buying_signal_sources", []),
        growth_signals=company.get("growth_signals", []),
        technology_signals=company.get("technology_signals", []),
        evidence=[
            EvidenceRecord(
                claim=e.get("claim", ""),
                value=e.get("value", ""),
                source=e.get("source", ""),
                source_url=e.get("source_url", ""),
                confidence=EvidenceConfidence(e.get("confidence", "MEDIUM")),
                observed_at=date.today(),
            )
            for e in company.get("evidence", [])
        ],
        missing_information=company.get("missing_information", []),
        recommended_research=company.get("recommended_research", []),
        qualification_status=qual_status,
    )

    # --- STEP 8: Generate Sales Intel ---
    opp = generate_sales_intel(opp)

    # --- Print summary ---
    intent_label = intent_level.value.replace("_", " ").title()
    print(f"\n  {company_name} | Intent: {intent_label} ({intent_score:.0f}) | "
          f"Primary: {primary_bu.value} | Opp Score: {opp_score:.0f} | "
          f"Qual: {qual_status.value}")

    return opp


def _extract_explicit_requirement(text: str) -> str:
    """Extract the explicit requirement from text, if any."""
    text_lower = text.lower()
    requirements = [
        "looking for", "need", "require", "seeking", "want to build",
        "want to hire", "searching for", "open to", "looking to hire"
    ]
    for req in requirements:
        if req in text_lower:
            idx = text_lower.index(req)
            snippet = text[max(0, idx - 20):idx + 100]
            return snippet.strip()
    return ""


# ============================================================
# OUTPUT
# ============================================================

def save_results(opportunities: list[Opportunity], output_file: str) -> None:
    """Save ranked opportunities to JSON."""
    output = []
    for opp in opportunities:
        output.append({
            "company": opp.company_name,
            "domain": opp.domain,
            "industry": opp.industry,
            "intent_level": opp.intent_level.value,
            "intent_score": opp.intent_score,
            "primary_bu": opp.primary_business_unit.value,
            "secondary_bus": [b.value for b in opp.secondary_business_units],
            "comai_score": opp.comai_score.score,
            "saas_score": opp.saas_score.score,
            "custom_score": opp.custom_score.score,
            "icp_fit": opp.icp_fit_score,
            "buyability": opp.buyability_score,
            "opportunity_score": opp.opportunity_score,
            "recommended_service": opp.recommended_service,
            "why_this_matters": opp.why_this_matters,
            "likely_pain": opp.likely_pain,
            "evidence_for_pain": opp.evidence_for_pain,
            "why_inowix_relevant": opp.why_inowix_relevant,
            "recommended_pitch": opp.recommended_pitch,
            "why_now": opp.why_now,
            "likely_objection": opp.likely_objection,
            "suggested_cta": opp.suggested_cta,
            "buying_signals": opp.buying_signals,
            "discovery_reason": opp.discovery_reason,
            "qualification_status": opp.qualification_status.value,
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(output)} opportunities to {output_file}")


def print_ranked_table(opportunities: list[Opportunity]) -> None:
    """Print ranked opportunities as a readable table."""
    print("\n" + "=" * 90)
    print("RANKED OPPORTUNITIES (sorted by opportunity score)")
    print("=" * 90)
    print(f"{'Rank':<5} {'Company':<30} {'Intent':<18} {'ICP':<6} {'Buy':<6} {'Opp':<6} {'Primary BU':<18} {'Qual Status'}")
    print("-" * 90)

    for i, opp in enumerate(opportunities, 1):
        intent_short = {
            IntentLevel.ACTIVE_REQUIREMENT: "ACTIVE",
            IntentLevel.EVALUATION: "EVAL",
            IntentLevel.EARLY_INTENT: "EARLY",
            IntentLevel.COMPANY_OPPORTUNITY: "PROF",
            IntentLevel.NO_INTENT: "NONE",
        }.get(opp.intent_level, "?")

        print(f"{i:<5} {opp.company_name:<30} {intent_short:<18} {opp.icp_fit_score:<6.0f} "
              f"{opp.buyability_score:<6.0f} {opp.opportunity_score:<6.0f} "
              f"{opp.primary_business_unit.value:<18} {opp.qualification_status.value}")

    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    discovery_file = str(PROJECT_ROOT / "exports" / "discovery_raw_results.json")
    output_file = str(PROJECT_ROOT / "exports" / "opportunity_rankings.json")

    opportunities = run_pipeline(discovery_file)
    save_results(opportunities, output_file)
    print_ranked_table(opportunities)
