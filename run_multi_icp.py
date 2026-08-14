"""Multi-ICP qualification engine. Scores each company against 3 business units:
COMAI, SaaS Development, Custom Software.

Rules:
- Do NOT assume funding = buying intent
- Do NOT assume ecommerce = COMAI
- Do NOT assume startup = SaaS development
- Do NOT invent pain points
- Missing data = UNKNOWN, not assumed
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ICPScore:
    """Score for a single ICP."""
    score: int = 0  # 0-100
    confidence: float = 0.0  # 0-1
    evidence: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    signals_found: list[str] = field(default_factory=list)


@dataclass
class CompanyQualification:
    """Qualification result for a company across all 3 ICPs."""
    company_name: str
    domain: str
    discovery_source: str
    discovery_date: str
    discovery_reason: str
    founder: str
    company_stage: str
    funding_summary: str

    comai: ICPScore = field(default_factory=ICPScore)
    saas: ICPScore = field(default_factory=ICPScore)
    custom: ICPScore = field(default_factory=ICPScore)

    best_opportunity: str = "UNKNOWN"
    opportunity_confidence: float = 0.0
    primary_buying_signal: str = ""
    why_now: str = ""
    evidence_summary: str = ""
    missing_information: str = ""
    recommended_research: str = ""


def score_comai(company: dict) -> ICPScore:
    """Score company against COMAI ICP (ecommerce automation, WhatsApp, customer support)."""
    s = ICPScore()
    industry = company.get("industry", "").lower()
    reason = company.get("discovery_reason", "").lower()
    stage = company.get("business_stage", "").lower()
    signals = [sig.lower() for sig in company.get("growth_signals", [])]
    buying = [sig.lower() for sig in company.get("buying_signals", [])]

    # Industry fit (0-25 points)
    ecommerce_industries = [
        "fashion", "beauty", "skincare", "food", "nutrition", "health",
        "sportswear", "kids", "fragrance", "lifestyle", "home",
        "jewellery", "footwear", "electronics", "pet",
    ]
    if any(ind in industry for ind in ecommerce_industries):
        s.score += 20
        s.evidence.append(f"Industry '{industry}' is D2C-relevant")
    elif "d2c" in reason or "ecommerce" in reason:
        s.score += 15
        s.evidence.append("D2C/ecommerce mentioned in discovery")
    else:
        s.score += 5
        s.missing.append("Industry not clearly D2C-relevant")

    # D2C/online sales model (0-20 points)
    d2c_signals = ["d2c", "ecommerce", "online", "website", "marketplace", "digital-first"]
    if any(sig in reason for sig in d2c_signals):
        s.score += 15
        s.evidence.append("D2C/online model confirmed")
    elif any(sig in industry for sig in ["fashion", "beauty", "food"]):
        s.score += 10
        s.evidence.append("Likely D2C based on industry")
    else:
        s.missing.append("Online sales model not confirmed")

    # Growth signals that suggest customer volume (0-15 points)
    volume_signals = ["customer", "revenue", "arr", "orders", "repeat"]
    if any(sig in " ".join(signals) for sig in volume_signals):
        s.score += 10
        s.evidence.append("Growth signals suggest customer traction")
    else:
        s.missing.append("Customer volume data unknown")

    # Multi-channel suggests support complexity (0-15 points)
    channel_signals = ["offline", "marketplace", "quick commerce", "omnichannel"]
    if any(sig in " ".join(signals + buying) for sig in channel_signals):
        s.score += 10
        s.evidence.append("Multi-channel presence (support complexity)")
    else:
        s.missing.append("Channel mix unknown")

    # Automation gap signals (0-15 points)
    automation_signals = ["manual", "scaling", "expansion", "team", "operations"]
    if any(sig in " ".join(signals + buying) for sig in automation_signals):
        s.score += 8
        s.evidence.append("Growth may create automation needs")
    else:
        s.missing.append("Automation gap not assessed")

    # Buying intent signals (0-10 points)
    intent_signals = ["expansion", "hiring", "new product", "new category", "offline"]
    if any(sig in " ".join(buying) for sig in intent_signals):
        s.score += 5
        s.evidence.append("Active expansion signals present")
    else:
        s.missing.append("No explicit buying intent confirmed")

    # Cap at 100
    s.score = min(s.score, 100)

    # Confidence based on evidence density
    s.confidence = min(len(s.evidence) / 5, 1.0)

    return s


def score_saas(company: dict) -> ICPScore:
    """Score company against SaaS Development ICP."""
    s = ICPScore()
    industry = company.get("industry", "").lower()
    reason = company.get("discovery_reason", "").lower()
    stage = company.get("business_stage", "").lower()
    signals = [sig.lower() for sig in company.get("growth_signals", [])]
    buying = [sig.lower() for sig in company.get("buying_signals", [])]

    # Startup stage (0-20 points)
    if stage == "early":
        s.score += 15
        s.evidence.append("Early stage — likely building product")
    elif stage == "growing":
        s.score += 10
        s.evidence.append("Growing stage — may need product development")
    else:
        s.score += 5
        s.missing.append("Stage not clearly startup-oriented")

    # Funding suggests product development budget (0-20 points)
    reason_lower = reason.lower()
    if "series a" in reason_lower or "series b" in reason_lower:
        s.score += 15
        s.evidence.append("Institutional funding — product development budget likely")
    elif "pre-series" in reason_lower or "seed" in reason_lower:
        s.score += 12
        s.evidence.append("Early funding — building product")
    elif "raised" in reason_lower:
        s.score += 8
        s.evidence.append("Funding received — some product budget")
    else:
        s.missing.append("Funding level not clear")

    # Product complexity signals (0-15 points)
    tech_signals = ["technology", "platform", "ai", "iot", "app", "software", "data"]
    if any(sig in " ".join(signals) for sig in tech_signals):
        s.score += 12
        s.evidence.append("Technology/product signals present")
    else:
        s.missing.append("Product complexity not assessed")

    # Engineering team signals (0-15 points)
    eng_signals = ["engineering", "technical", "cto", "tech", "development"]
    if any(sig in " ".join(signals) for sig in eng_signals):
        s.score += 10
        s.evidence.append("Engineering signals present")
    else:
        s.missing.append("Engineering team size unknown")

    # AI adoption signals (0-10 points)
    if any(sig in " ".join(signals + buying) for sig in ["ai", "machine learning", "automation"]):
        s.score += 8
        s.evidence.append("AI/automation adoption signals")
    else:
        s.missing.append("AI adoption not assessed")

    # Integration needs (0-10 points)
    integration_signals = ["marketplace", "api", "integration", "multi-channel"]
    if any(sig in " ".join(signals + buying) for sig in integration_signals):
        s.score += 5
        s.evidence.append("Multi-platform suggests integration needs")
    else:
        s.missing.append("Integration needs unknown")

    # Expansion suggests product work (0-10 points)
    expansion_signals = ["expansion", "new product", "new category", "offline"]
    if any(sig in " ".join(buying) for sig in expansion_signals):
        s.score += 5
        s.evidence.append("Expansion may require product development")
    else:
        s.missing.append("Expansion plans not confirmed")

    s.score = min(s.score, 100)
    s.confidence = min(len(s.evidence) / 5, 1.0)

    return s


def score_custom(company: dict) -> ICPScore:
    """Score company against Custom Software ICP."""
    s = ICPScore()
    industry = company.get("industry", "").lower()
    reason = company.get("discovery_reason", "").lower()
    stage = company.get("business_stage", "").lower()
    signals = [sig.lower() for sig in company.get("growth_signals", [])]
    buying = [sig.lower() for sig in company.get("buying_signals", [])]

    # Industry complexity (0-20 points)
    complex_industries = [
        "logistics", "supply chain", "manufacturing", "healthcare",
        "elder care", "packaging", "organic", "agriculture",
    ]
    simple_industries = ["fashion", "beauty", "skincare", "food"]
    if any(ind in industry for ind in complex_industries):
        s.score += 18
        s.evidence.append(f"Industry '{industry}' has operational complexity")
    elif any(ind in industry for ind in simple_industries):
        s.score += 8
        s.evidence.append(f"Industry '{industry}' — lower custom software need")
    else:
        s.score += 10
        s.missing.append("Industry complexity not assessed")

    # Operational complexity signals (0-20 points)
    ops_signals = ["supply chain", "operations", "logistics", "manufacturing", "inventory"]
    if any(sig in " ".join(signals + buying) for sig in ops_signals):
        s.score += 15
        s.evidence.append("Operational complexity signals present")
    else:
        s.missing.append("Operational complexity not assessed")

    # Multiple departments/teams (0-15 points)
    dept_signals = ["team", "departments", "multiple", "expansion", "hiring"]
    if any(sig in " ".join(signals) for sig in dept_signals):
        s.score += 8
        s.evidence.append("Growth signals suggest organizational complexity")
    else:
        s.missing.append("Organizational complexity unknown")

    # Digital transformation needs (0-15 points)
    digital_signals = ["legacy", "manual", "digital", "modernization", "automation"]
    if any(sig in " ".join(signals + buying) for sig in digital_signals):
        s.score += 10
        s.evidence.append("Digital transformation signals")
    else:
        s.missing.append("Digital transformation needs not assessed")

    # Custom platform opportunity (0-15 points)
    platform_signals = ["platform", "marketplace", "network", "multi-sided"]
    if any(sig in " ".join(signals) for sig in platform_signals):
        s.score += 10
        s.evidence.append("Platform/marketplace model — custom build opportunity")
    else:
        s.missing.append("Custom platform opportunity not identified")

    # Expansion suggests custom needs (0-15 points)
    if any(sig in " ".join(buying) for sig in ["expansion", "new market", "new city"]):
        s.score += 5
        s.evidence.append("Geographic expansion may need custom systems")
    else:
        s.missing.append("Expansion custom needs not assessed")

    s.score = min(s.score, 100)
    s.confidence = min(len(s.evidence) / 5, 1.0)

    return s


def determine_best_opportunity(comai: ICPScore, saas: ICPScore, custom: ICPScore) -> tuple[str, float]:
    """Determine best opportunity and confidence."""
    scores = {
        "COMAI": comai.score,
        "SAAS_DEVELOPMENT": saas.score,
        "CUSTOM_SOFTWARE": custom.score,
    }

    best_name = max(scores, key=scores.get)
    best_score = scores[best_name]
    second_best = sorted(scores.values(), reverse=True)[1]

    # If best is significantly higher than second
    gap = best_score - second_best

    if best_score < 30:
        return "NURTURE", 0.3

    if gap > 20:
        return best_name, 0.7
    elif gap > 10:
        return best_name, 0.5
    elif best_score > 50:
        return "MULTIPLE_OPPORTUNITIES", 0.4
    else:
        return "NURTURE", 0.3


def qualify_companies(companies: list[dict]) -> list[CompanyQualification]:
    """Run all 3 ICP scores on each company."""
    results = []

    for company in companies:
        comai = score_comai(company)
        saas = score_saas(company)
        custom = score_custom(company)

        best, confidence = determine_best_opportunity(comai, saas, custom)

        # Extract funding summary from discovery reason
        reason = company.get("discovery_reason", "")
        funding_summary = ""
        for keyword in ["Raised", "raised", "Secured", "secured", "Achieved", "achieved"]:
            if keyword in reason:
                funding_summary = reason.split(".")[0]
                break
        if not funding_summary:
            funding_summary = reason[:100]

        # Primary buying signal
        buying = company.get("buying_signals", [])
        primary_signal = buying[0] if buying else "No explicit buying signal confirmed"

        # Why now
        why_now_parts = []
        if "2026" in reason or "2025" in reason:
            why_now_parts.append("Recent funding (2025-2026)")
        stage = company.get("business_stage", "")
        if stage == "early":
            why_now_parts.append("Early stage — building systems")
        elif stage == "growing":
            why_now_parts.append("Growth phase — scaling operations")
        if any(sig in " ".join(buying) for sig in ["expansion", "new", "offline"]):
            why_now_parts.append("Active expansion")
        why_now = "; ".join(why_now_parts) if why_now_parts else "Timing needs more evidence"

        # Evidence summary
        all_evidence = comai.evidence + saas.evidence + custom.evidence
        evidence_summary = "; ".join(all_evidence[:5]) if all_evidence else "Limited evidence available"

        # Missing info
        all_missing = comai.missing + saas.missing + custom.missing
        missing_info = "; ".join(all_missing[:5]) if all_missing else "N/A"

        # Recommended research
        research = []
        if not company.get("founder_name"):
            research.append("Verify founder identity and LinkedIn")
        if comai.missing:
            research.append("Verify ecommerce platform (Shopify/WooCommerce)")
        if saas.missing:
            research.append("Check engineering team size and tech stack")
        if custom.missing:
            research.append("Assess operational complexity and legacy systems")
        research.append("Verify company website and actual products")
        recommended = "; ".join(research[:4])

        q = CompanyQualification(
            company_name=company["company_name"],
            domain=company.get("domain", ""),
            discovery_source=company.get("source", ""),
            discovery_date=company.get("discovery_date", ""),
            discovery_reason=reason,
            founder=company.get("founder_name", "Unknown"),
            company_stage=stage,
            funding_summary=funding_summary,
            comai=comai,
            saas=saas,
            custom=custom,
            best_opportunity=best,
            opportunity_confidence=confidence,
            primary_buying_signal=primary_signal,
            why_now=why_now,
            evidence_summary=evidence_summary,
            missing_information=missing_info,
            recommended_research=recommended,
        )
        results.append(q)

    # Sort by best opportunity score (highest first)
    def sort_key(q: CompanyQualification) -> int:
        if q.best_opportunity == "COMAI":
            return q.comai.score
        elif q.best_opportunity == "SAAS_DEVELOPMENT":
            return q.saas.score
        elif q.best_opportunity == "CUSTOM_SOFTWARE":
            return q.custom.score
        return 0

    results.sort(key=sort_key, reverse=True)
    return results


def main():
    with open("exports/discovery_raw_results.json", "r", encoding="utf-8") as f:
        companies = json.load(f)

    results = qualify_companies(companies)

    # Print ranked table
    print("=" * 120)
    print("MULTI-ICP QUALIFICATION RESULTS — 30 DISCOVERED COMPANIES")
    print("=" * 120)
    print()
    print(f"{'#':<3} {'Company':<20} {'COMAI':<7} {'SaaS':<7} {'Custom':<7} {'Best Opportunity':<22} {'Conf':<6} {'Why'}")
    print("-" * 120)

    for i, q in enumerate(results, 1):
        why_short = q.why_now[:50] + "..." if len(q.why_now) > 50 else q.why_now
        print(
            f"{i:<3} {q.company_name:<20} "
            f"{q.comai.score:>3}({q.comai.confidence:.0%})  "
            f"{q.saas.score:>3}({q.saas.confidence:.0%})  "
            f"{q.custom.score:>3}({q.custom.confidence:.0%})  "
            f"{q.best_opportunity:<22} "
            f"{q.opportunity_confidence:>4.0%}   "
            f"{why_short}"
        )

    # Print detailed view for top 10
    print()
    print("=" * 120)
    print("DETAILED VIEW — TOP 10 COMPANIES")
    print("=" * 120)

    for i, q in enumerate(results[:10], 1):
        print()
        print("-" * 80)
        print(f"#{i} | {q.company_name} ({q.domain})")
        print("-" * 80)
        print(f"  Discovery:      {q.discovery_reason}")
        print(f"  Founder:        {q.founder}")
        print(f"  Stage:          {q.company_stage}")
        print(f"  Funding:        {q.funding_summary}")
        print()
        print(f"  COMAI Score:    {q.comai.score}/100 (confidence: {q.comai.confidence:.0%})")
        for ev in q.comai.evidence:
            print(f"    + {ev}")
        for m in q.comai.missing:
            print(f"    ? {m}")
        print()
        print(f"  SaaS Score:     {q.saas.score}/100 (confidence: {q.saas.confidence:.0%})")
        for ev in q.saas.evidence:
            print(f"    + {ev}")
        for m in q.saas.missing:
            print(f"    ? {m}")
        print()
        print(f"  Custom Score:   {q.custom.score}/100 (confidence: {q.custom.confidence:.0%})")
        for ev in q.custom.evidence:
            print(f"    + {ev}")
        for m in q.custom.missing:
            print(f"    ? {m}")
        print()
        print(f"  BEST OPPORTUNITY: {q.best_opportunity} (confidence: {q.opportunity_confidence:.0%})")
        print(f"  Primary Signal:   {q.primary_buying_signal}")
        print(f"  Why Now:          {q.why_now}")
        print(f"  Evidence:         {q.evidence_summary}")
        print(f"  Missing Info:     {q.missing_information}")
        print(f"  Next Research:    {q.recommended_research}")

    # Summary stats
    print()
    print("=" * 120)
    print("SUMMARY")
    print("=" * 120)

    opp_counts = {}
    for q in results:
        opp_counts[q.best_opportunity] = opp_counts.get(q.best_opportunity, 0) + 1

    print("\nOpportunity Distribution:")
    for opp, cnt in sorted(opp_counts.items(), key=lambda x: -x[1]):
        print(f"  {opp}: {cnt}")

    # Average scores by opportunity
    print("\nAverage Scores by Best Opportunity:")
    for opp in ["COMAI", "SAAS_DEVELOPMENT", "CUSTOM_SOFTWARE", "MULTIPLE_OPPORTUNITIES", "NURTURE"]:
        matching = [q for q in results if q.best_opportunity == opp]
        if matching:
            avg_comai = sum(q.comai.score for q in matching) / len(matching)
            avg_saas = sum(q.saas.score for q in matching) / len(matching)
            avg_custom = sum(q.custom.score for q in matching) / len(matching)
            print(f"  {opp}: COMAI={avg_comai:.0f}, SaaS={avg_saas:.0f}, Custom={avg_custom:.0f} (n={len(matching)})")

    # Save to JSON
    output = []
    for q in results:
        output.append({
            "company_name": q.company_name,
            "domain": q.domain,
            "discovery_source": q.discovery_source,
            "discovery_date": q.discovery_date,
            "discovery_reason": q.discovery_reason,
            "founder": q.founder,
            "company_stage": q.company_stage,
            "funding_summary": q.funding_summary,
            "comai_score": q.comai.score,
            "comai_confidence": q.comai.confidence,
            "comai_evidence": q.comai.evidence,
            "comai_missing": q.comai.missing,
            "saas_score": q.saas.score,
            "saas_confidence": q.saas.confidence,
            "saas_evidence": q.saas.evidence,
            "saas_missing": q.saas.missing,
            "custom_score": q.custom.score,
            "custom_confidence": q.custom.confidence,
            "custom_evidence": q.custom.evidence,
            "custom_missing": q.custom.missing,
            "best_opportunity": q.best_opportunity,
            "opportunity_confidence": q.opportunity_confidence,
            "primary_buying_signal": q.primary_buying_signal,
            "why_now": q.why_now,
            "evidence_summary": q.evidence_summary,
            "missing_information": q.missing_information,
            "recommended_research": q.recommended_research,
        })

    with open("exports/multi_icp_qualification.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: exports/multi_icp_qualification.json")


if __name__ == "__main__":
    main()
