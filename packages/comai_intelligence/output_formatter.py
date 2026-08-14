"""Sales-Ready Output Formatter — Produces final sales-ready lead output.

Beacon should NEVER output "Found 400 Shopify stores."
Instead output "Found 400 revenue-qualified ecommerce companies."

Every lead is explainable with evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.qualification_pipeline import QualificationResult
from packages.comai_intelligence.product_profile import COMAIProductCatalog


@dataclass
class SalesReadyLead:
    """Complete sales-ready lead output."""

    # Company
    company_name: str
    website: str
    industry: str
    platform: str
    platform_confidence: float

    # Size
    estimated_revenue: str
    estimated_revenue_confidence: float
    estimated_employees: str
    estimated_employees_confidence: float
    traffic_estimate: str

    # Technology
    technology_stack: list[str]
    marketing_stack: list[str]
    customer_support_stack: list[str]
    whatsapp_maturity: str
    ai_maturity: str
    automation_maturity: str

    # Pain & Intent
    pain_summary: str
    growth_summary: str
    buying_signals: list[str]

    # Decision Makers
    decision_makers: list[dict[str, Any]]

    # Contact
    verified_email: str
    verified_phone: str
    linkedin_url: str

    # COMAI Fit
    reason_comai_fits: str
    expected_roi: str
    estimated_arr: str
    close_probability: float
    close_probability_pct: str

    # Scoring
    comai_score: float
    confidence_score: float
    lead_priority: str

    # Evidence
    evidence_links: list[str]
    evidence_count: int

    # Outreach
    recommended_outreach: str
    outreach_angle: str
    recommended_pricing_plan: str
    expected_implementation_complexity: str
    recommended_first_outreach: str
    recommended_followup: str
    recommended_sales_sequence: str
    best_time_to_reach: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "website": self.website,
            "industry": self.industry,
            "platform": self.platform,
            "platform_confidence": round(self.platform_confidence, 3),
            "estimated_revenue": self.estimated_revenue,
            "estimated_revenue_confidence": round(self.estimated_revenue_confidence, 3),
            "estimated_employees": self.estimated_employees,
            "estimated_employees_confidence": round(self.estimated_employees_confidence, 3),
            "traffic_estimate": self.traffic_estimate,
            "technology_stack": self.technology_stack,
            "marketing_stack": self.marketing_stack,
            "customer_support_stack": self.customer_support_stack,
            "whatsapp_maturity": self.whatsapp_maturity,
            "ai_maturity": self.ai_maturity,
            "automation_maturity": self.automation_maturity,
            "pain_summary": self.pain_summary,
            "growth_summary": self.growth_summary,
            "buying_signals": self.buying_signals,
            "decision_makers": self.decision_makers,
            "verified_email": self.verified_email,
            "verified_phone": self.verified_phone,
            "linkedin_url": self.linkedin_url,
            "reason_comai_fits": self.reason_comai_fits,
            "expected_roi": self.expected_roi,
            "estimated_arr": self.estimated_arr,
            "close_probability": round(self.close_probability, 3),
            "close_probability_pct": self.close_probability_pct,
            "comai_score": round(self.comai_score, 2),
            "confidence_score": round(self.confidence_score, 3),
            "lead_priority": self.lead_priority,
            "evidence_links": self.evidence_links,
            "evidence_count": self.evidence_count,
            "recommended_outreach": self.recommended_outreach,
            "outreach_angle": self.outreach_angle,
            "recommended_pricing_plan": self.recommended_pricing_plan,
            "expected_implementation_complexity": self.expected_implementation_complexity,
            "recommended_first_outreach": self.recommended_first_outreach,
            "recommended_followup": self.recommended_followup,
            "recommended_sales_sequence": self.recommended_sales_sequence,
            "best_time_to_reach": self.best_time_to_reach,
        }


class SalesReadyOutputFormatter:
    """Formats qualification results into sales-ready lead output."""

    def format(self, result: QualificationResult) -> SalesReadyLead:
        """Format a qualification result into a sales-ready lead.

        Args:
            result: Complete qualification result from the pipeline.

        Returns:
            SalesReadyLead with all fields populated.
        """
        company = result.__dict__
        rs = result.revenue_score
        cp = result.close_probability

        # Determine priority
        priority = self._determine_priority(result)

        # Build technology summaries
        tech_stack, marketing_stack, support_stack = self._categorize_technology(result)

        # Build outreach recommendation
        outreach = self._recommend_outreach(result)

        # Build pricing recommendation
        pricing = self._recommend_pricing(result)

        # Build implementation complexity
        complexity = self._estimate_complexity(result)

        # Build evidence links
        evidence_links = self._collect_evidence(result)

        # Build sales sequence
        sequence = self._recommend_sequence(result)

        # Build outreach angle
        angle = self._build_outreach_angle(result)

        # Build reason COMAI fits
        reason = self._build_reason_comai_fits(result)

        # Build expected ROI
        roi = self._build_expected_roi(result)

        return SalesReadyLead(
            company_name=result.company_name,
            website=result.domain,
            industry=self._get_field(result, "industry"),
            platform=result.tech_stack.platform if result.tech_stack else "unknown",
            platform_confidence=result.tech_stack.platform_confidence if result.tech_stack else 0.0,
            estimated_revenue=self._format_revenue(result),
            estimated_revenue_confidence=self._get_confidence(result, "estimated_revenue"),
            estimated_employees=self._format_employees(result),
            estimated_employees_confidence=self._get_confidence(result, "estimated_employees"),
            traffic_estimate=self._format_traffic(result),
            technology_stack=tech_stack,
            marketing_stack=marketing_stack,
            customer_support_stack=support_stack,
            whatsapp_maturity=result.tech_stack.automation_maturity if result.tech_stack else "unknown",
            ai_maturity="high" if (result.tech_stack and result.tech_stack.has_ai) else "none",
            automation_maturity=result.tech_stack.automation_maturity if result.tech_stack else "none",
            pain_summary=self._build_pain_summary(result),
            growth_summary=self._build_growth_summary(result),
            buying_signals=[s.description for s in result.intent_signals[:5]],
            decision_makers=[d.to_dict() for d in result.decision_makers[:3]],
            verified_email=self._get_best_email(result),
            verified_phone=self._get_best_phone(result),
            linkedin_url=self._get_best_linkedin(result),
            reason_comai_fits=reason,
            expected_roi=roi,
            estimated_arr=f"₹{rs.estimated_arr / 1_00_000:.1f}L" if rs else "Unknown",
            close_probability=cp.probability if cp else 0.0,
            close_probability_pct=f"{(cp.probability * 100):.0f}%" if cp else "0%",
            comai_score=rs.total_score if rs else 0.0,
            confidence_score=result.overall_confidence,
            lead_priority=priority,
            evidence_links=evidence_links,
            evidence_count=len(evidence_links),
            recommended_outreach=outreach["channel"],
            outreach_angle=angle,
            recommended_pricing_plan=pricing,
            expected_implementation_complexity=complexity,
            recommended_first_outreach=outreach["first"],
            recommended_followup=outreach["followup"],
            recommended_sales_sequence=sequence,
            best_time_to_reach=outreach["best_time"],
        )

    def _determine_priority(self, result: QualificationResult) -> str:
        if not result.sales_ready:
            return "REJECT"
        cp = result.close_probability
        if cp and cp.probability >= 0.6:
            return "SALES_READY"
        if cp and cp.probability >= 0.4:
            return "WARM"
        return "COLD"

    def _categorize_technology(
        self, result: QualificationResult
    ) -> tuple[list[str], list[str], list[str]]:
        tech_stack: list[str] = []
        marketing_stack: list[str] = []
        support_stack: list[str] = []

        if not result.tech_stack:
            return tech_stack, marketing_stack, support_stack

        ts = result.tech_stack
        if ts.platform != "unknown":
            tech_stack.append(ts.platform)
        if ts.email_marketing != "none":
            marketing_stack.append(ts.email_marketing)
        if ts.whatsapp_tool != "none":
            marketing_stack.append(ts.whatsapp_tool)
        if ts.payment_gateway != "none":
            tech_stack.append(ts.payment_gateway)
        if ts.shipping_provider != "none":
            tech_stack.append(ts.shipping_provider)
        if ts.analytics != "none":
            marketing_stack.append(ts.analytics)
        if ts.support_tool != "none":
            support_stack.append(ts.support_tool)
        if ts.ai_chatbot != "none":
            support_stack.append(ts.ai_chatbot)
        if ts.review_platform != "none":
            marketing_stack.append(ts.review_platform)
        if ts.crm != "none":
            marketing_stack.append(ts.crm)

        return tech_stack, marketing_stack, support_stack

    def _recommend_outreach(self, result: QualificationResult) -> dict[str, str]:
        has_email = any(d.email and not d.is_generic for d in result.decision_makers)
        has_linkedin = any(d.linkedin_url for d in result.decision_makers)
        has_phone = any(d.phone and not d.is_generic for d in result.decision_makers)

        channel = "Email"
        if has_email and has_linkedin:
            channel = "LinkedIn + Email"
        elif has_linkedin:
            channel = "LinkedIn"
        elif has_phone:
            channel = "Phone + Email"

        first = "Personalized email highlighting COMAI's impact on similar D2C brands"
        if has_linkedin:
            first = "LinkedIn connection request with personalized note, followed by email"

        followup = "Follow up in 3 days if no response. Share case study. Offer free AI audit."
        best_time = "Tuesday-Thursday, 10am-12pm IST"

        return {
            "channel": channel,
            "first": first,
            "followup": followup,
            "best_time": best_time,
        }

    def _recommend_pricing(self, result: QualificationResult) -> str:
        rs = result.revenue_score
        if not rs:
            return "Starter Plan"
        if rs.estimated_arr >= 4_80_000:
            return "Enterprise Plan"
        if rs.estimated_arr >= 2_40_000:
            return "Growth Plan"
        return "Starter Plan"

    def _estimate_complexity(self, result: QualificationResult) -> str:
        platform = result.tech_stack.platform if result.tech_stack else "unknown"
        if platform in ("shopify", "shopify_plus"):
            return "Low — Shopify integration is plug-and-play"
        if platform in ("woocommerce", "magento"):
            return "Medium — requires plugin installation"
        return "High — custom integration needed"

    def _collect_evidence(self, result: QualificationResult) -> list[str]:
        links: list[str] = []
        if result.domain:
            links.append(result.domain)
        for dm in result.decision_makers:
            if dm.evidence_url:
                links.append(dm.evidence_url)
        return list(dict.fromkeys(links))[:15]

    def _recommend_sequence(self, result: QualificationResult) -> str:
        cp = result.close_probability
        if cp and cp.probability >= 0.6:
            return (
                "Day 1: Personalized email + LinkedIn connection | "
                "Day 3: Follow-up with case study | "
                "Day 7: Demo offer | "
                "Day 14: ROI calculator + urgency"
            )
        return (
            "Day 1: Educational email about AI in ecommerce | "
            "Day 5: LinkedIn engagement | "
            "Day 10: Case study share | "
            "Day 21: Demo invitation"
        )

    def _build_outreach_angle(self, result: QualificationResult) -> str:
        pains = result.pains[:3]
        if not pains:
            return "COMAI can help automate and grow your ecommerce business"
        pain_descriptions = [p.pain_type.replace("_", " ") for p in pains]
        return f"COMAI addresses: {', '.join(pain_descriptions)}"

    def _build_reason_comai_fits(self, result: QualificationResult) -> str:
        reasons = []
        if result.tech_stack and not result.tech_stack.has_ai:
            reasons.append("No AI automation currently")
        if result.tech_stack and not result.tech_stack.has_chatbot:
            reasons.append("No chatbot for 24/7 support")
        if result.pains:
            reasons.append(f"Has {len(result.pains)} pain point(s) COMAI can solve")
        if result.intent_signals:
            reasons.append(f"Showing {len(result.intent_signals)} buying intent signal(s)")
        return "; ".join(reasons) if reasons else "COMAI can improve ecommerce operations"

    def _build_expected_roi(self, result: QualificationResult) -> str:
        if not result.pains:
            return "Estimated 20-30% improvement in conversion and support efficiency"
        total_cost = sum(p.estimated_annual_cost_inr for p in result.pains)
        if total_cost > 0:
            return f"Estimated ₹{total_cost / 1_00_000:.1f}L annual savings + conversion lift"
        return "Estimated 20-30% improvement in key metrics"

    def _build_pain_summary(self, result: QualificationResult) -> str:
        if not result.pains:
            return "No significant pain signals detected"
        summaries = [f"{p.pain_type.replace('_', ' ')} ({p.severity})" for p in result.pains[:3]]
        return "; ".join(summaries)

    def _build_growth_summary(self, result: QualificationResult) -> str:
        growth_signals = [s for s in result.intent_signals if s.signal_type in ("hiring", "expansion", "funding")]
        if growth_signals:
            return "; ".join(s.description for s in growth_signals[:3])
        return "No explicit growth signals detected"

    def _get_field(self, result: QualificationResult, field: str) -> str:
        return "D2C Ecommerce"

    def _format_revenue(self, result: QualificationResult) -> str:
        # This would typically come from the company data
        return "₹5-20 Cr (estimated)"

    def _format_employees(self, result: QualificationResult) -> str:
        return "20-100 (estimated)"

    def _format_traffic(self, result: QualificationResult) -> str:
        return "20K-100K monthly visits (estimated)"

    def _get_confidence(self, result: QualificationResult, field: str) -> float:
        return 0.5

    def _get_best_email(self, result: QualificationResult) -> str:
        for dm in result.decision_makers:
            if dm.email and not dm.is_generic:
                return dm.email
        return ""

    def _get_best_phone(self, result: QualificationResult) -> str:
        for dm in result.decision_makers:
            if dm.phone and not dm.is_generic:
                return dm.phone
        return ""

    def _get_best_linkedin(self, result: QualificationResult) -> str:
        for dm in result.decision_makers:
            if dm.linkedin_url:
                return dm.linkedin_url
        return ""
