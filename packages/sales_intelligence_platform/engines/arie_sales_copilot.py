"""ARIE: Sales Copilot Engine.

Generates comprehensive sales intelligence for outreach:
- Why this company?
- Why now?
- Pain Summary
- Technology Summary
- Growth Summary
- Recommended Pitch
- ROI Estimate
- Outreach Strategy
- Email, WhatsApp, Call Script, LinkedIn
- Follow-up Plan
- Competitive Talking Points
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SalesPackage:
    """Complete sales intelligence package for a company."""
    domain: str
    company_name: str
    
    # Why this company?
    why_this_company: str = ""
    
    # Why now?
    why_now: str = ""
    
    # Pain summary
    pain_summary: list = field(default_factory=list)
    
    # Technology summary
    technology_summary: dict = field(default_factory=dict)
    
    # Growth summary
    growth_summary: dict = field(default_factory=dict)
    
    # Recommended pitch
    recommended_pitch: str = ""
    
    # ROI estimate
    roi_estimate: dict = field(default_factory=dict)
    
    # Outreach strategy
    outreach_strategy: dict = field(default_factory=dict)
    
    # Generated content
    email_draft: str = ""
    whatsapp_message: str = ""
    call_script: str = ""
    linkedin_message: str = ""
    
    # Follow-up plan
    follow_up_plan: list = field(default_factory=list)
    
    # Competitive talking points
    competitive_points: list = field(default_factory=list)
    
    # Confidence
    confidence_score: float = 0.0


class ARIESalesCopilot:
    """Sales Copilot Engine - generates comprehensive sales intelligence."""
    
    def generate_sales_package(
        self,
        company_data: dict[str, Any],
        revenue_score: dict[str, Any] = None,
        pain_analysis: dict[str, Any] = None,
        technology_analysis: dict[str, Any] = None,
        growth_analysis: dict[str, Any] = None,
        intent_analysis: dict[str, Any] = None,
        decision_makers: list = None,
        verified_contacts: dict[str, Any] = None,
    ) -> SalesPackage:
        """Generate comprehensive sales intelligence package.
        
        Args:
            company_data: Company information
            revenue_score: Revenue scoring results
            pain_analysis: Pain analysis results
            technology_analysis: Technology analysis results
            growth_analysis: Growth analysis results
            intent_analysis: Intent analysis results
            decision_makers: List of decision makers
            verified_contacts: Verified contact information
            
        Returns:
            SalesPackage with all intelligence and outreach content
        """
        domain = company_data.get("domain", "")
        company_name = company_data.get("company_name", company_data.get("name", ""))
        
        package = SalesPackage(
            domain=domain,
            company_name=company_name,
        )
        
        # Generate "Why this company?"
        package.why_this_company = self._generate_why_this_company(
            company_data, revenue_score, pain_analysis
        )
        
        # Generate "Why now?"
        package.why_now = self._generate_why_now(
            intent_analysis, growth_analysis
        )
        
        # Generate pain summary
        package.pain_summary = self._generate_pain_summary(pain_analysis)
        
        # Generate technology summary
        package.technology_summary = self._generate_technology_summary(technology_analysis)
        
        # Generate growth summary
        package.growth_summary = self._generate_growth_summary(growth_analysis)
        
        # Generate recommended pitch
        package.recommended_pitch = self._generate_pitch(
            company_data, pain_analysis, technology_analysis
        )
        
        # Generate ROI estimate
        package.roi_estimate = self._generate_roi_estimate(
            company_data, revenue_score
        )
        
        # Generate outreach strategy
        package.outreach_strategy = self._generate_outreach_strategy(
            company_data, intent_analysis, decision_makers
        )
        
        # Generate content
        package.email_draft = self._generate_email(
            company_data, pain_analysis, decision_makers
        )
        package.whatsapp_message = self._generate_whatsapp(
            company_data, pain_analysis
        )
        package.call_script = self._generate_call_script(
            company_data, pain_analysis, technology_analysis
        )
        package.linkedin_message = self._generate_linkedin(
            company_data, pain_analysis
        )
        
        # Generate follow-up plan
        package.follow_up_plan = self._generate_follow_up_plan(
            intent_analysis, decision_makers
        )
        
        # Generate competitive talking points
        package.competitive_points = self._generate_competitive_points(
            technology_analysis
        )
        
        # Calculate confidence
        package.confidence_score = self._calculate_confidence(
            company_data, revenue_score, pain_analysis
        )
        
        return package
    
    def _generate_why_this_company(
        self,
        company: dict,
        revenue_score: dict = None,
        pain_analysis: dict = None,
    ) -> str:
        """Generate 'Why this company?' narrative."""
        company_name = company.get("company_name", company.get("name", "This company"))
        industry = company.get("industry", "D2C")
        traffic = company.get("monthly_traffic", 0)
        products = company.get("product_count", 0)
        
        reasons = []
        
        # Industry fit
        if industry:
            reasons.append(f"{company_name} is a {industry} brand")
        
        # Scale indicators
        if traffic > 50000:
            reasons.append(f"with significant online traffic ({traffic:,} monthly visitors)")
        elif traffic > 10000:
            reasons.append(f"with growing online presence ({traffic:,} monthly visitors)")
        
        if products > 100:
            reasons.append(f"offering {products}+ products")
        
        # Pain indicators
        if pain_analysis:
            pain_points = pain_analysis.get("pain_points", [])
            if pain_points:
                pain_categories = [p.get("category", "") for p in pain_points[:3]]
                reasons.append(f"showing signs of {', '.join(pain_categories)} challenges")
        
        # Growth indicators
        growth_rate = company.get("traffic_growth_rate", 0)
        if growth_rate > 10:
            reasons.append(f"growing at {growth_rate}% monthly")
        
        if reasons:
            return f"{company_name} {' '.join(reasons)}."
        
        return f"{company_name} operates in the {industry} space and could benefit from COMAI's solutions."
    
    def _generate_why_now(
        self,
        intent_analysis: dict = None,
        growth_analysis: dict = None,
    ) -> str:
        """Generate 'Why now?' narrative."""
        reasons = []
        
        # Intent signals
        if intent_analysis:
            intent_level = intent_analysis.get("intent_level", "")
            buying_timeframe = intent_analysis.get("buying_timeframe", "")
            
            if intent_level == "hot":
                reasons.append("High buying intent detected")
            elif intent_level == "warm":
                reasons.append("Active evaluation signals detected")
            
            if buying_timeframe == "immediate":
                reasons.append("within the next 30 days")
            elif buying_timeframe == "30_days":
                reasons.append("in the next 1-3 months")
        
        # Growth signals
        if growth_analysis:
            growth_trend = growth_analysis.get("growth_trend", "")
            if growth_trend == "accelerating":
                reasons.append("accelerating growth creates urgency for efficient scaling")
        
        # Technology signals
        tech_changes = intent_analysis.get("signals", []) if intent_analysis else []
        for signal in tech_changes:
            if signal.get("signal_type") == "technology_migration":
                reasons.append("currently migrating technology stack")
                break
        
        if reasons:
            return f"Now is the right time because {' '.join(reasons)}."
        
        return "The company is showing growth signals that indicate readiness for automation solutions."
    
    def _generate_pain_summary(self, pain_analysis: dict = None) -> list:
        """Generate pain summary."""
        if not pain_analysis:
            return []
        
        pain_points = pain_analysis.get("pain_points", [])
        summary = []
        
        for pain in pain_points[:5]:
            summary.append({
                "category": pain.get("category", "Unknown"),
                "severity": pain.get("severity", "medium"),
                "description": pain.get("description", ""),
                "evidence": pain.get("evidence", []),
            })
        
        return summary
    
    def _generate_technology_summary(self, tech_analysis: dict = None) -> dict:
        """Generate technology summary."""
        if not tech_analysis:
            return {}
        
        return {
            "platform": tech_analysis.get("platform", "Unknown"),
            "tech_stack": tech_analysis.get("tech_stack", {}),
            "comai_fit_score": tech_analysis.get("comai_fit_score", 0),
            "gaps": tech_analysis.get("gaps", []),
            "opportunities": tech_analysis.get("opportunities", []),
        }
    
    def _generate_growth_summary(self, growth_analysis: dict = None) -> dict:
        """Generate growth summary."""
        if not growth_analysis:
            return {}
        
        return {
            "growth_score": growth_analysis.get("growth_score", 0),
            "growth_trend": growth_analysis.get("growth_trend", "unknown"),
            "expansion_stage": growth_analysis.get("expansion_stage", "unknown"),
            "key_signals": [s.get("signal_type", "") for s in growth_analysis.get("signals", [])[:5]],
        }
    
    def _generate_pitch(
        self,
        company: dict,
        pain_analysis: dict = None,
        tech_analysis: dict = None,
    ) -> str:
        """Generate recommended pitch."""
        company_name = company.get("company_name", company.get("name", "your company"))
        
        # Start with pain
        pain_hook = ""
        if pain_analysis:
            pain_points = pain_analysis.get("pain_points", [])
            if pain_points:
                top_pain = pain_points[0]
                pain_hook = f"I noticed you might be facing challenges with {top_pain.get('category', 'operations')}. "
        
        # Technology gap
        tech_gap = ""
        if tech_analysis:
            gaps = tech_analysis.get("gaps", [])
            if gaps:
                tech_gap = f"Our AI-powered solution can help bridge the gap in {gaps[0]}. "
        
        # Value proposition
        value_prop = f"COMAI can help {company_name} automate customer interactions, reduce support costs, and improve conversion rates by 20-30%. "
        
        # Social proof
        social_proof = "We've helped similar D2C brands achieve 3x ROI within 6 months. "
        
        # Call to action
        cta = "Would you be open to a quick 15-minute call to discuss how we can help?"
        
        return f"{pain_hook}{tech_gap}{value_prop}{social_proof}{cta}"
    
    def _generate_roi_estimate(
        self,
        company: dict,
        revenue_score: dict = None,
    ) -> dict:
        """Generate ROI estimate."""
        # Estimate based on company size
        traffic = company.get("monthly_traffic", 10000)
        aov = company.get("avg_order_value", 500)
        orders = company.get("monthly_orders", 100)
        
        # Current estimated costs
        current_support_cost = orders * 50  # Rs 50 per support ticket
        current_cart_abandonment_loss = orders * aov * 0.7 * 0.3  # 70% abandon, 30% recoverable
        
        # COMAI improvements
        support_reduction = current_support_cost * 0.4  # 40% reduction
        conversion_improvement = current_cart_abandonment_loss * 0.2  # 20% improvement
        
        monthly_savings = support_reduction + conversion_improvement
        annual_savings = monthly_savings * 12
        
        # COMAI cost
        comai_cost = 799 * 12  # Growth plan annually
        
        roi = ((annual_savings - comai_cost) / comai_cost) * 100 if comai_cost > 0 else 0
        
        return {
            "monthly_savings": f"Rs {monthly_savings:,.0f}",
            "annual_savings": f"Rs {annual_savings:,.0f}",
            "comai_cost": f"Rs {comai_cost:,.0f}/year",
            "roi": f"{roi:.0f}%",
            "payback_months": f"{comai_cost / monthly_savings:.1f}" if monthly_savings > 0 else "N/A",
            "breakdown": {
                "support_cost_reduction": f"Rs {support_reduction:,.0f}/month",
                "conversion_improvement": f"Rs {conversion_improvement:,.0f}/month",
            },
        }
    
    def _generate_outreach_strategy(
        self,
        company: dict,
        intent_analysis: dict = None,
        decision_makers: list = None,
    ) -> dict:
        """Generate outreach strategy."""
        strategy = {
            "primary_channel": "email",
            "best_time": "Tuesday-Thursday, 10am-12pm IST",
            "personalization_angles": [],
            "sequence": [],
        }
        
        # Determine primary channel
        if decision_makers:
            dm = decision_makers[0]
            if dm.get("linkedin_url"):
                strategy["primary_channel"] = "linkedin"
            elif dm.get("phone"):
                strategy["primary_channel"] = "phone"
        
        # Personalization angles
        if intent_analysis:
            signals = intent_analysis.get("signals", [])
            for signal in signals[:3]:
                strategy["personalization_angles"].append(signal.get("signal_value", ""))
        
        # Sequence
        strategy["sequence"] = [
            {"day": 1, "channel": "email", "action": "Initial outreach with personalized pitch"},
            {"day": 3, "channel": "linkedin", "action": "Connection request with note"},
            {"day": 5, "channel": "email", "action": "Follow-up with case study"},
            {"day": 8, "channel": "whatsapp", "action": "Quick check-in"},
            {"day": 12, "channel": "email", "action": "Final follow-up with offer"},
        ]
        
        return strategy
    
    def _generate_email(
        self,
        company: dict,
        pain_analysis: dict = None,
        decision_makers: list = None,
    ) -> str:
        """Generate email draft."""
        company_name = company.get("company_name", company.get("name", "your company"))
        dm_name = ""
        if decision_makers:
            dm_name = decision_makers[0].get("name", "").split()[0]
        
        greeting = f"Hi {dm_name}," if dm_name else "Hi there,"
        
        # Pain point hook
        pain_hook = ""
        if pain_analysis:
            pain_points = pain_analysis.get("pain_points", [])
            if pain_points:
                pain_hook = f"\n\nI noticed {company_name} might be facing challenges with {pain_points[0].get('category', 'customer support')}. "
        
        return f"""Subject: Helping {company_name} improve customer experience with AI

{greeting}

{pain_hook}I'm reaching out because we've helped similar D2C brands automate their customer interactions and see significant improvements.

COMAI's AI-powered WhatsApp automation can help {company_name}:
• Reduce support tickets by 40%
• Improve response time from hours to seconds
• Increase conversion rates by 20-30%

Would you be open to a quick 15-minute call to discuss how we can help?

Best regards,
[Your Name]"""
    
    def _generate_whatsapp(self, company: dict, pain_analysis: dict = None) -> str:
        """Generate WhatsApp message."""
        company_name = company.get("company_name", company.get("name", "your company"))
        
        return f"""Hi! I'm reaching out about helping {company_name} with AI-powered customer automation.

We've helped similar D2C brands reduce support costs by 40% and improve conversions by 20%.

Would you be interested in a quick 15-minute demo?"""
    
    def _generate_call_script(
        self,
        company: dict,
        pain_analysis: dict = None,
        tech_analysis: dict = None,
    ) -> str:
        """Generate call script."""
        company_name = company.get("company_name", company.get("name", "your company"))
        
        return f"""OPENING (30 seconds):
"Hi [Name], thank you for taking the time to speak with me. I'm [Your Name] from COMAI. I reached out because I noticed {company_name} is growing rapidly, and I wanted to share how we've helped similar D2C brands automate their customer interactions."

DISCOVERY (2-3 minutes):
1. "How are you currently handling customer support inquiries?"
2. "What's your biggest challenge with customer experience right now?"
3. "How much time does your team spend on repetitive customer queries?"

VALUE PROPOSITION (2 minutes):
"COMAI's AI-powered WhatsApp automation can help {company_name}:
• Reduce support tickets by 40%
• Improve response time from hours to seconds
• Increase conversion rates by 20-30%"

OBJECTION HANDLING:
• "We're too small" → "Many of our clients started with similar sizes and saw ROI within 3 months"
• "We already have a chatbot" → "How is it performing? Our AI solution typically outperforms traditional chatbots by 3x"
• "Budget constraints" → "We offer flexible pricing and the ROI typically pays for itself within 6 months"

CLOSE:
"Would you like to see a quick demo of how this would work for {company_name}?"
"""
    
    def _generate_linkedin(self, company: dict, pain_analysis: dict = None) -> str:
        """Generate LinkedIn message."""
        company_name = company.get("company_name", company.get("name", "your company"))
        
        return f"""Hi! I noticed {company_name} is growing rapidly in the D2C space.

We've helped similar brands automate their customer interactions with AI, reducing support costs by 40% and improving conversions by 20%.

Would you be open to connecting and sharing some insights?"""
    
    def _generate_follow_up_plan(
        self,
        intent_analysis: dict = None,
        decision_makers: list = None,
    ) -> list:
        """Generate follow-up plan."""
        plan = [
            {"day": 1, "channel": "email", "action": "Initial outreach", "goal": "Introduction"},
            {"day": 3, "channel": "linkedin", "action": "Connection request", "goal": "Network building"},
            {"day": 5, "channel": "email", "action": "Case study follow-up", "goal": "Provide value"},
            {"day": 8, "channel": "whatsapp", "action": "Quick check-in", "goal": "Personal touch"},
            {"day": 12, "channel": "email", "action": "Final follow-up", "goal": "Create urgency"},
        ]
        
        # Adjust based on intent
        if intent_analysis:
            intent_level = intent_analysis.get("intent_level", "")
            if intent_level == "hot":
                # Accelerate for hot leads
                plan[1]["day"] = 2
                plan[2]["day"] = 3
                plan[3]["day"] = 5
                plan[4]["day"] = 7
        
        return plan
    
    def _generate_competitive_points(self, tech_analysis: dict = None) -> list:
        """Generate competitive talking points."""
        points = [
            "COMAI offers 3x better AI accuracy than traditional chatbots",
            "Setup takes 24 hours vs weeks for enterprise solutions",
            "Pricing is 70% lower than enterprise alternatives",
            "Dedicated support for Indian D2C brands",
            "WhatsApp-first approach (most popular channel in India)",
        ]
        
        # Add specific points based on current tech
        if tech_analysis:
            current_tools = tech_analysis.get("tech_stack", {})
            
            if current_tools.get("chatbot"):
                points.append("Our AI outperforms rule-based chatbots by 3x")
            
            if current_tools.get("crm"):
                points.append("Seamless integration with your existing CRM")
        
        return points
    
    def _calculate_confidence(
        self,
        company: dict,
        revenue_score: dict = None,
        pain_analysis: dict = None,
    ) -> float:
        """Calculate confidence in sales package."""
        data_points = [
            bool(company.get("company_name")),
            bool(company.get("industry")),
            bool(revenue_score),
            bool(pain_analysis),
            bool(company.get("traffic")),
        ]
        
        available = sum(1 for p in data_points if p)
        return (available / len(data_points)) * 100
