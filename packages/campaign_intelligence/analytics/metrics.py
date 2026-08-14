from __future__ import annotations

from collections import Counter
from typing import Any

from campaign_intelligence.models.types import CampaignStatus


class CampaignAnalytics:
    def dashboard(self, campaigns: list[dict[str, Any]]) -> dict[str, Any]:
        status_counts = Counter(str(item.get("status") or "unknown") for item in campaigns)
        priority_counts = Counter(str(item.get("priority") or "unknown") for item in campaigns)
        channel_counts = Counter(str(item.get("primary_channel") or "unknown") for item in campaigns)
        avg_confidence = 0.0
        if campaigns:
            avg_confidence = sum(float(item.get("expected_confidence") or 0.0) for item in campaigns) / len(campaigns)
        needs_review = status_counts.get(CampaignStatus.NEEDS_REVIEW.value, 0)
        approved = status_counts.get(CampaignStatus.APPROVED.value, 0) + status_counts.get(
            CampaignStatus.SCHEDULED.value, 0
        )
        return {
            "total_campaigns": len(campaigns),
            "needs_review": needs_review,
            "approved_or_scheduled": approved,
            "paused": status_counts.get(CampaignStatus.PAUSED.value, 0),
            "cancelled": status_counts.get(CampaignStatus.CANCELLED.value, 0),
            "completed": status_counts.get(CampaignStatus.COMPLETED.value, 0),
            "average_confidence": round(avg_confidence, 2),
            "by_status": dict(status_counts),
            "by_priority": dict(priority_counts),
            "by_primary_channel": dict(channel_counts),
            "delivery_enabled": False,
        }
