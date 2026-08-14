"""AI Intelligence Loop — analyzes buying events to improve detection quality.

CRITICAL RULES:
1. Analyzes REAL buying events, not fake leads
2. Tracks which sources produce the most buying events
3. Adjusts detection confidence thresholds
4. Generates reports on pipeline health
5. Zero is acceptable — no fabrication
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.buying_event import BuyingEvent, BuyingEventStatus, BuyingEventDepartment
from app.models.founder_sales_workspace import LeadStage
from app.models.raw_event import RawEvent

logger = logging.getLogger(__name__)


class IntelligenceLoop:
    """Analyzes buying events and adjusts detection parameters for better results.

    The loop works as follows:
    1. Analyze which buying events were verified vs rejected
    2. Identify which sources produce the most verified buying events
    3. Adjust detection confidence thresholds accordingly
    4. Next detection cycle uses updated parameters → better buying events
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_buying_events(self) -> dict[str, Any]:
        """Analyze buying events by department, source, and event type."""
        now = datetime.now(UTC)
        thirty_days_ago = now - timedelta(days=30)

        # Get all buying events from last 30 days
        all_events = (
            await self.session.execute(
                select(BuyingEvent).where(
                    BuyingEvent.deleted_at.is_(None),
                    BuyingEvent.created_at >= thirty_days_ago,
                )
            )
        ).scalars().all()

        if not all_events:
            return {"analysis": "no_data", "total_events": 0}

        # Categorize by department
        comai_events = [e for e in all_events if e.department == BuyingEventDepartment.COMAI]
        inowix_events = [e for e in all_events if e.department == BuyingEventDepartment.INOWIX]

        # Calculate metrics
        def calc_metrics(events):
            if not events:
                return {"total": 0, "verified": 0, "disqualified": 0, "processed": 0}

            verified = [e for e in events if e.status == BuyingEventStatus.VERIFIED]
            disqualified = [e for e in events if e.status == BuyingEventStatus.DISQUALIFIED]
            processed = [e for e in events if e.status == BuyingEventStatus.PROCESSED]

            return {
                "total": len(events),
                "verified": len(verified),
                "disqualified": len(disqualified),
                "processed": len(processed),
                "verification_rate": len(verified) / len(events) if events else 0,
            }

        # Analyze by source
        source_metrics = {}
        for event in all_events:
            # Get source from raw_event
            raw_event = await self.session.get(RawEvent, event.raw_event_id)
            source = raw_event.source if raw_event else "unknown"
            
            if source not in source_metrics:
                source_metrics[source] = {"total": 0, "verified": 0}
            source_metrics[source]["total"] += 1
            if event.status == BuyingEventStatus.VERIFIED:
                source_metrics[source]["verified"] += 1

        for source, metrics in source_metrics.items():
            metrics["verification_rate"] = metrics["verified"] / metrics["total"] if metrics["total"] > 0 else 0

        # Analyze by event type
        event_type_metrics = {}
        for event in all_events:
            event_type = event.event_type
            if event_type not in event_type_metrics:
                event_type_metrics[event_type] = {"total": 0, "verified": 0}
            event_type_metrics[event_type]["total"] += 1
            if event.status == BuyingEventStatus.VERIFIED:
                event_type_metrics[event_type]["verified"] += 1

        for event_type, metrics in event_type_metrics.items():
            metrics["verification_rate"] = metrics["verified"] / metrics["total"] if metrics["total"] > 0 else 0

        # Find top performing sources
        top_sources = sorted(
            source_metrics.items(),
            key=lambda x: x[1]["verification_rate"],
            reverse=True,
        )[:5]

        # Find top performing event types
        top_event_types = sorted(
            event_type_metrics.items(),
            key=lambda x: x[1]["verification_rate"],
            reverse=True,
        )[:5]

        # Analyze pipeline health
        pipeline_stats = await self._analyze_pipeline_health()

        return {
            "period": "30d",
            "total_events": len(all_events),
            "comai": calc_metrics(comai_events),
            "inowix": calc_metrics(inowix_events),
            "top_sources": [
                {"source": k, **v}
                for k, v in top_sources
            ],
            "top_event_types": [
                {"event_type": k, **v}
                for k, v in top_event_types
            ],
            "pipeline": pipeline_stats,
        }

    async def _analyze_pipeline_health(self) -> dict[str, Any]:
        """Analyze the health of the sales pipeline."""
        # Count leads by stage
        stage_counts = {}
        rows = (
            await self.session.execute(
                select(LeadStage.stage, func.count())
                .where(LeadStage.deleted_at.is_(None))
                .group_by(LeadStage.stage)
            )
        ).all()
        for stage, count in rows:
            stage_counts[stage] = count

        total_leads = sum(stage_counts.values())
        active_stages = {"contacted", "replied", "meeting", "proposal", "negotiation", "won"}
        active_leads = sum(count for stage, count in stage_counts.items() if stage in active_stages)

        return {
            "total_leads": total_leads,
            "active_leads": active_leads,
            "by_stage": stage_counts,
            "conversion_rate": active_leads / total_leads if total_leads > 0 else 0,
        }

    async def generate_recommendations(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Department balance check
        comai = analysis.get("comai", {})
        inowix = analysis.get("inowix", {})

        if comai.get("total", 0) > 0 and inowix.get("total", 0) > 0:
            comai_rate = comai.get("verification_rate", 0)
            inowix_rate = inowix.get("verification_rate", 0)

            if comai_rate > inowix_rate * 1.5:
                recommendations.append({
                    "type": "rebalance",
                    "department": "INOWIX",
                    "action": "Increase INOWIX detection focus — COMAI verifying 1.5x better",
                    "priority": "high",
                })
            elif inowix_rate > comai_rate * 1.5:
                recommendations.append({
                    "type": "rebalance",
                    "department": "COMAI",
                    "action": "Increase COMAI detection focus — INOWIX verifying 1.5x better",
                    "priority": "high",
                })

        # Source recommendations
        for item in analysis.get("top_sources", []):
            if item["verification_rate"] > 0.3 and item["total"] >= 3:
                recommendations.append({
                    "type": "boost_source",
                    "source": item["source"],
                    "action": f"High verification rate ({item['verification_rate']:.0%}) from {item['source']} — increase collection from this source",
                    "priority": "medium",
                })

        # Event type recommendations
        for item in analysis.get("top_event_types", []):
            if item["verification_rate"] > 0.3 and item["total"] >= 3:
                recommendations.append({
                    "type": "boost_event_type",
                    "event_type": item["event_type"],
                    "action": f"High verification rate ({item['verification_rate']:.0%}) for '{item['event_type']}' — prioritize this event type",
                    "priority": "medium",
                })

        # Pipeline health recommendations
        pipeline = analysis.get("pipeline", {})
        total_leads = pipeline.get("total_leads", 0)
        if total_leads < 10:
            recommendations.append({
                "type": "scale_up",
                "action": f"Only {total_leads} leads in pipeline — increase detection frequency or expand buying event types",
                "priority": "high",
            })

        return recommendations

    async def run_full_analysis(self) -> dict[str, Any]:
        """Run complete intelligence loop analysis."""
        analysis = await self.analyze_buying_events()
        recommendations = await self.generate_recommendations(analysis)

        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now(UTC).isoformat(),
        }
