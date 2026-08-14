"""Founder Workspace — Today's view when founder opens Beacon.

Shows:
    Today's Opportunities
    Today's Revenue Ready
    Today's Expired
    Today's Replies
    Today's Meetings
    Today's Follow Ups
    Today's Connector Winner
    Today's Worst Connector
    Today's Revenue Forecast

Default filter: Today
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


class FounderWorkspace:
    """Founder's daily workspace view."""

    def __init__(self):
        self._opportunities: list[dict[str, Any]] = []
        self._outreach: list[dict[str, Any]] = []
        self._replies: list[dict[str, Any]] = []
        self._meetings: list[dict[str, Any]] = []
        self._revenue: list[dict[str, Any]] = []

    def set_opportunities(self, opportunities: list[dict[str, Any]]):
        """Set opportunities for workspace."""
        self._opportunities = opportunities

    def set_outreach(self, outreach: list[dict[str, Any]]):
        """Set outreach records."""
        self._outreach = outreach

    def set_replies(self, replies: list[dict[str, Any]]):
        """Set reply records."""
        self._replies = replies

    def set_meetings(self, meetings: list[dict[str, Any]]):
        """Set meeting records."""
        self._meetings = meetings

    def set_revenue(self, revenue: list[dict[str, Any]]):
        """Set revenue records."""
        self._revenue = revenue

    def get_todays_view(self) -> dict[str, Any]:
        """Get today's complete workspace view."""
        today = datetime.now(timezone.utc).date()

        todays_opps = self._filter_by_date(self._opportunities, today)
        todays_replies = self._filter_by_date(self._replies, today)
        todays_meetings = self._filter_by_date(self._meetings, today)

        return {
            "date": today.isoformat(),
            "opportunities": {
                "total": len(todays_opps),
                "new": sum(1 for o in todays_opps if o.get("status") == "new"),
                "revenue_ready": sum(1 for o in todays_opps if o.get("status") == "revenue_ready"),
                "expired": sum(1 for o in todays_opps if o.get("status") == "expired"),
            },
            "replies": {
                "total": len(todays_replies),
                "positive": sum(1 for r in todays_replies if r.get("sentiment") == "positive"),
                "negative": sum(1 for r in todays_replies if r.get("sentiment") == "negative"),
            },
            "meetings": {
                "total": len(todays_meetings),
                "scheduled": sum(1 for m in todays_meetings if m.get("status") == "scheduled"),
                "completed": sum(1 for m in todays_meetings if m.get("status") == "completed"),
            },
            "connector_winner": self._get_connector_winner(),
            "worst_connector": self._get_worst_connector(),
            "revenue_forecast": self._calculate_revenue_forecast(),
            "follow_ups_needed": self._get_follow_ups_needed(),
        }

    def get_custom_view(self, period: str) -> dict[str, Any]:
        """Get workspace view for custom period."""
        now = datetime.now(timezone.utc)

        if period == "15_minutes":
            start = now - timedelta(minutes=15)
        elif period == "30_minutes":
            start = now - timedelta(minutes=30)
        elif period == "1_hour":
            start = now - timedelta(hours=1)
        elif period == "6_hours":
            start = now - timedelta(hours=6)
        elif period == "12_hours":
            start = now - timedelta(hours=12)
        elif period == "yesterday":
            start = now - timedelta(days=1)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "7_days":
            start = now - timedelta(days=7)
        elif period == "30_days":
            start = now - timedelta(days=30)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        filtered_opps = [
            o for o in self._opportunities
            if self._parse_timestamp(o.get("created_at")) >= start
        ]

        return {
            "period": period,
            "start": start.isoformat(),
            "end": now.isoformat(),
            "opportunities": {
                "total": len(filtered_opps),
                "by_status": self._count_by_status(filtered_opps),
            },
            "connector_winner": self._get_connector_winner(),
            "worst_connector": self._get_worst_connector(),
        }

    def _filter_by_date(self, records: list[dict[str, Any]], date) -> list[dict[str, Any]]:
        """Filter records by date."""
        filtered = []
        for record in records:
            created = record.get("created_at")
            if created:
                try:
                    if isinstance(created, str):
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    else:
                        dt = created
                    if dt.date() == date:
                        filtered.append(record)
                except (ValueError, AttributeError):
                    pass
        return filtered

    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp string to datetime."""
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)

    def _get_connector_winner(self) -> dict[str, Any]:
        """Get best performing connector today."""
        connector_stats: dict[str, dict[str, int]] = {}
        for opp in self._opportunities:
            connector = opp.get("connector", "unknown")
            if connector not in connector_stats:
                connector_stats[connector] = {"total": 0, "revenue_ready": 0}
            connector_stats[connector]["total"] += 1
            if opp.get("status") == "revenue_ready":
                connector_stats[connector]["revenue_ready"] += 1

        if not connector_stats:
            return {"connector": "none", "score": 0}

        best = max(
            connector_stats.items(),
            key=lambda x: x[1]["revenue_ready"]
        )
        return {
            "connector": best[0],
            "revenue_ready": best[1]["revenue_ready"],
            "total": best[1]["total"],
        }

    def _get_worst_connector(self) -> dict[str, Any]:
        """Get worst performing connector today."""
        connector_stats: dict[str, dict[str, int]] = {}
        for opp in self._opportunities:
            connector = opp.get("connector", "unknown")
            if connector not in connector_stats:
                connector_stats[connector] = {"total": 0, "rejected": 0}
            connector_stats[connector]["total"] += 1
            if opp.get("status") in ("archived", "spam", "not_icp"):
                connector_stats[connector]["rejected"] += 1

        if not connector_stats:
            return {"connector": "none", "rejection_rate": 0}

        worst = max(
            connector_stats.items(),
            key=lambda x: x[1]["rejected"] / max(x[1]["total"], 1)
        )
        rate = worst[1]["rejected"] / max(worst[1]["total"], 1)
        return {
            "connector": worst[0],
            "rejection_rate": round(rate, 3),
            "total": worst[1]["total"],
        }

    def _calculate_revenue_forecast(self) -> dict[str, Any]:
        """Calculate revenue forecast."""
        pipeline_value = sum(
            o.get("revenue_potential", 0)
            for o in self._opportunities
            if o.get("status") in ("contacted", "replied", "meeting", "proposal", "negotiation")
        )

        return {
            "pipeline_value": pipeline_value,
            "opportunities_in_pipeline": sum(
                1 for o in self._opportunities
                if o.get("status") in ("contacted", "replied", "meeting", "proposal", "negotiation")
            ),
        }

    def _get_follow_ups_needed(self) -> list[dict[str, Any]]:
        """Get opportunities needing follow-up."""
        follow_ups = []
        now = datetime.now(timezone.utc)

        for opp in self._opportunities:
            if opp.get("status") == "contacted":
                last_contact = opp.get("last_contacted_at")
                if last_contact:
                    try:
                        if isinstance(last_contact, str):
                            dt = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
                        else:
                            dt = last_contact
                        days_since = (now - dt).days
                        if days_since >= 3:
                            follow_ups.append({
                                "opportunity_id": opp.get("id"),
                                "company_name": opp.get("company_name"),
                                "days_since_contact": days_since,
                            })
                    except (ValueError, AttributeError):
                        pass

        return sorted(follow_ups, key=lambda x: x["days_since_contact"], reverse=True)

    def _count_by_status(self, opportunities: list[dict[str, Any]]) -> dict[str, int]:
        """Count opportunities by status."""
        counts: dict[str, int] = {}
        for opp in opportunities:
            status = opp.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts
