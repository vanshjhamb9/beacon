from __future__ import annotations

from production_validation.models.types import (
    ProductionValidationInput,
    RevenueHealthSnapshot,
    WeeklyRevenueReport,
)


class WeeklyReportEngine:
    def generate(self, item: ProductionValidationInput, revenue: RevenueHealthSnapshot) -> WeeklyRevenueReport:
        m = item.revenue_metrics or {}
        funnel = item.funnel or {}
        companies = int(m.get("companies_found") or 0)
        qualified = int(m.get("qualified_companies") or revenue.qualified_companies)
        sales_ready = int(m.get("sales_ready") or revenue.sales_ready)
        campaigns = revenue.campaigns
        emails = int(funnel.get("emails") or m.get("emails") or 0)
        replies = revenue.replies
        meetings = revenue.meetings
        proposals = revenue.proposals
        lost = int(m.get("lost") or funnel.get("lost") or 0)
        reasons = list(m.get("reasons_lost") or ["timing", "budget", "incumbent"])
        industries = list(m.get("top_industries") or ([item.industry] if item.industry else ["SaaS"]))
        services = list(m.get("top_services") or ([item.service_match] if item.service_match else ["AI Automation"]))
        best = m.get("best_campaign")
        worst = m.get("worst_campaign")
        suggestions = list(m.get("improvement_suggestions") or [
            "Focus A+/A accounts only",
            "Require readiness score ≥ 90 before outreach",
            "Ship proposals within 24h of meetings",
        ])
        lines = [
            "metric,value",
            f"companies_found,{companies}",
            f"qualified,{qualified}",
            f"sales_ready,{sales_ready}",
            f"campaigns,{campaigns}",
            f"emails,{emails}",
            f"replies,{replies}",
            f"meetings,{meetings}",
            f"proposals,{proposals}",
            f"revenue,{revenue.revenue_closed}",
            f"lost_deals,{lost}",
        ]
        pdf = "\n".join(
            [
                "WEEKLY REVENUE REPORT — Beacon",
                f"Companies Found: {companies}",
                f"Qualified: {qualified}",
                f"Sales Ready: {sales_ready}",
                f"Campaigns: {campaigns}",
                f"Emails: {emails}",
                f"Replies: {replies}",
                f"Meetings: {meetings}",
                f"Proposals: {proposals}",
                f"Revenue: {revenue.revenue_closed}",
                f"Lost: {lost}",
                f"Top Industries: {', '.join(str(x) for x in industries)}",
                f"Top Services: {', '.join(str(x) for x in services)}",
                "Suggestions:",
                *[f"- {s}" for s in suggestions],
            ]
        )
        return WeeklyRevenueReport(
            companies_found=companies,
            qualified=qualified,
            sales_ready=sales_ready,
            campaigns=campaigns,
            emails=emails,
            replies=replies,
            meetings=meetings,
            proposals=proposals,
            revenue=revenue.revenue_closed,
            lost_deals=lost,
            reasons_lost=[str(r) for r in reasons],
            top_industries=[str(i) for i in industries if i],
            top_services=[str(s) for s in services if s],
            best_campaign=str(best) if best else None,
            worst_campaign=str(worst) if worst else None,
            improvement_suggestions=[str(s) for s in suggestions],
            csv_text="\n".join(lines) + "\n",
            pdf_text=pdf,
            evidence=["format:csv", "format:pdf_text", "source:composed_metrics"],
        )
