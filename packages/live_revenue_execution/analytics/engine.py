from __future__ import annotations

from live_revenue_execution.models.types import LREInput, RevenueAnalyticsSnapshot


class RevenueAnalyticsEngine:
    def snapshot(self, item: LREInput) -> RevenueAnalyticsSnapshot:
        c = item.funnel_counts or {}
        companies = int(c.get("companies_found", 1))
        qualified = int(c.get("qualified", 1 if item.probability >= 40 else 0))
        sales_ready = int(c.get("sales_ready", 1 if (item.priority_grade in {"A+", "A"}) else 0))
        emails = int(c.get("emails", 0))
        delivered = int(c.get("delivered", emails))
        opened = int(c.get("opened", 0))
        clicked = int(c.get("clicked", 0))
        replies = int(c.get("replies", len(item.reply_history)))
        meetings = int(c.get("meetings", 0))
        proposals = int(c.get("proposals", 0))
        won = int(c.get("won", 0))
        lost = int(c.get("lost", 0))
        campaigns = int(c.get("campaigns", 1 if item.campaign_id else 0))
        return RevenueAnalyticsSnapshot(
            companies_found=companies,
            qualified=qualified,
            sales_ready=sales_ready,
            campaigns=campaigns,
            emails=emails,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            replies=replies,
            meetings=meetings,
            proposals=proposals,
            won=won,
            lost=lost,
            revenue_closed=float(item.revenue_closed),
            pipeline_value=float(item.pipeline_value or item.probability * 500),
            avg_response_hours=float(c.get("avg_response_hours", 18)),
            avg_sales_cycle_days=float(c.get("avg_sales_cycle_days", 28)),
            daily=[{"label": "today", "emails": emails, "replies": replies, "meetings": meetings}],
            weekly=[{"label": "week", "pipeline": float(item.pipeline_value), "won": won}],
            monthly=[{"label": "month", "revenue_closed": float(item.revenue_closed)}],
            evidence=[
                f"open_rate:{round((opened / delivered) * 100, 2) if delivered else 0}",
                f"reply_rate:{round((replies / max(emails, 1)) * 100, 2)}",
                f"meeting_rate:{round((meetings / max(replies, 1)) * 100, 2)}",
            ],
        )
