from __future__ import annotations

from revenue_hunter.filters.taxonomy import normalize_funding, normalize_industry, size_band_from_employees
from revenue_hunter.models.types import (
    FilterMatch,
    PainPoint,
    RevenueHunterInput,
    ServiceMatchResult,
    WebsiteIntelligence,
    WhyNowV2,
)


BUDGET_BY_SERVICE: dict[str, dict[str, str]] = {
    "COMAI": {"Startup": "$15k–$35k", "SMB": "$25k–$55k", "Mid Market": "$45k–$90k", "Enterprise": "$80k–$180k"},
    "Custom AI": {"Startup": "$20k–$45k", "SMB": "$35k–$75k", "Mid Market": "$60k–$120k", "Enterprise": "$100k–$250k"},
    "Website": {"Startup": "$8k–$18k", "SMB": "$12k–$30k", "Mid Market": "$25k–$60k", "Enterprise": "$40k–$100k"},
    "Mobile App": {"Startup": "$20k–$40k", "SMB": "$30k–$70k", "Mid Market": "$50k–$120k", "Enterprise": "$90k–$200k"},
    "SaaS": {"Startup": "$30k–$60k", "SMB": "$45k–$90k", "Mid Market": "$75k–$150k", "Enterprise": "$120k–$300k"},
    "Internal Software": {"Startup": "$15k–$35k", "SMB": "$25k–$60k", "Mid Market": "$45k–$100k", "Enterprise": "$80k–$200k"},
    "Automation": {"Startup": "$12k–$28k", "SMB": "$20k–$45k", "Mid Market": "$35k–$80k", "Enterprise": "$60k–$150k"},
    "AI Chatbot": {"Startup": "$10k–$22k", "SMB": "$15k–$35k", "Mid Market": "$30k–$65k", "Enterprise": "$50k–$120k"},
    "CRM": {"Startup": "$10k–$25k", "SMB": "$18k–$40k", "Mid Market": "$30k–$70k", "Enterprise": "$55k–$140k"},
    "ERP": {"Startup": "$25k–$50k", "SMB": "$40k–$90k", "Mid Market": "$70k–$160k", "Enterprise": "$120k–$350k"},
    "Multi Agent Systems": {
        "Startup": "$25k–$50k",
        "SMB": "$40k–$80k",
        "Mid Market": "$70k–$140k",
        "Enterprise": "$110k–$280k",
    },
}


class WhyNowEngineV2:
    """Structured why-this / why-today / why-us with budget, timeline, probability, evidence."""

    def generate(
        self,
        item: RevenueHunterInput,
        *,
        filter_match: FilterMatch,
        service: ServiceMatchResult,
        pains: list[PainPoint],
        website: WebsiteIntelligence,
    ) -> WhyNowV2:
        industry = normalize_industry(item.industry) or item.industry or "their market"
        size = item.company_size_band or size_band_from_employees(item.employee_count) or "unknown size"
        funding = normalize_funding(item.funding_stage)

        why_company_parts = [
            f"{item.company_name} is a {size} {industry} company",
        ]
        if filter_match.matched_country:
            why_company_parts.append(f"in {filter_match.matched_country}")
        if funding:
            why_company_parts.append(f"at {funding} stage")
        if pains:
            why_company_parts.append(f"showing {pains[0].problem.lower()}")
        why_this_company = " ".join(why_company_parts) + f" — strong fit for {service.service}."

        today_parts: list[str] = []
        if item.funding_days_ago is not None and item.funding_days_ago <= 90:
            today_parts.append(f"funding event {item.funding_days_ago} days ago")
        if item.hiring_count > 0:
            roles = ", ".join(item.hiring_roles[:3]) or "key roles"
            today_parts.append(f"actively hiring {item.hiring_count} roles ({roles})")
        if website.opportunities:
            high = [o for o in website.opportunities if o.severity == "high"]
            if high:
                today_parts.append(f"website risk: {high[0].area}")
        for signal in item.signals[:3]:
            today_parts.append(signal.replace("_", " "))
        if not today_parts:
            today_parts.append("ICP and buying signals align for outreach today")
        why_today = "Why today: " + "; ".join(list(dict.fromkeys(today_parts))[:5]) + "."

        pain_names = ", ".join(p.problem for p in pains[:3]) or "operational friction"
        why_us = (
            f"Beacon delivers {service.service} with evidence-backed delivery — "
            f"addresses {pain_names} at confidence {service.confidence:.0f}%."
        )

        revenue_key = self._revenue_key(item)
        budget_map = BUDGET_BY_SERVICE.get(service.service, BUDGET_BY_SERVICE["Custom AI"])
        expected_budget = budget_map.get(revenue_key, budget_map["SMB"])

        if item.funding_days_ago is not None and item.funding_days_ago <= 60:
            timeline = "2–4 weeks to discovery; 6–10 weeks to first delivery"
        elif item.hiring_count >= 5:
            timeline = "3–5 weeks to scoped proposal; 8–12 weeks delivery"
        else:
            timeline = "4–6 weeks nurture → meeting → proposal"

        probability = self._probability(item, service=service, pains=pains, website=website, filter_match=filter_match)

        evidence_chain = list(
            dict.fromkeys(
                filter_match.evidence
                + service.evidence
                + [e for p in pains for e in p.evidence]
                + website.evidence
                + ([f"funding_days_ago:{item.funding_days_ago}"] if item.funding_days_ago is not None else [])
                + ([f"hiring_count:{item.hiring_count}"] if item.hiring_count else [])
            )
        )[:40]

        summary = f"{why_this_company} {why_today} {why_us} Budget {expected_budget}. Probability {probability:.0f}%."

        return WhyNowV2(
            why_this_company=why_this_company,
            why_today=why_today,
            why_us=why_us,
            expected_budget=expected_budget,
            expected_timeline=timeline,
            probability=probability,
            evidence_chain=evidence_chain,
            summary=summary,
        )

    def _revenue_key(self, item: RevenueHunterInput) -> str:
        if item.revenue_band:
            from revenue_hunter.filters.taxonomy import normalize_revenue

            return normalize_revenue(item.revenue_band) or "SMB"
        count = item.employee_count or 0
        if count >= 500:
            return "Enterprise"
        if count >= 100:
            return "Mid Market"
        if count >= 25:
            return "SMB"
        return "Startup"

    def _probability(
        self,
        item: RevenueHunterInput,
        *,
        service: ServiceMatchResult,
        pains: list[PainPoint],
        website: WebsiteIntelligence,
        filter_match: FilterMatch,
    ) -> float:
        score = 30.0
        if filter_match.passed:
            score += 15.0
        score += min(25.0, service.confidence * 0.25)
        score += min(15.0, len(pains) * 4.0)
        if item.funding_days_ago is not None and item.funding_days_ago <= 90:
            score += 10.0
        if item.hiring_count >= 3:
            score += 8.0
        if any(o.severity == "high" for o in website.opportunities):
            score += 6.0
        if item.decision_makers:
            score += 5.0
        if item.verification_score >= 70:
            score += 4.0
        return round(min(95.0, max(5.0, score)), 4)
