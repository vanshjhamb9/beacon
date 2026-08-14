"""Calibration engine — provides deterministic analytics for scoring calibration.

Never changes scores. Only records facts. Reality changes Beacon.
"""

from __future__ import annotations

from typing import Any

from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.industry_roi import IndustryRoiEngine
from validation_engine.persona_roi import PersonaRoiEngine
from validation_engine.service_roi import ServiceRoiEngine
from validation_engine.trigger_roi import TriggerRoiEngine


class CalibrationEngine:
    """Deterministic calibration analytics. Never modifies scores."""

    def __init__(
        self,
        *,
        connector_roi: ConnectorRoiEngine | None = None,
        industry_roi: IndustryRoiEngine | None = None,
        service_roi: ServiceRoiEngine | None = None,
        persona_roi: PersonaRoiEngine | None = None,
        trigger_roi: TriggerRoiEngine | None = None,
        deal_tracker: DealTracker | None = None,
    ) -> None:
        self.connector_roi = connector_roi or ConnectorRoiEngine()
        self.industry_roi = industry_roi or IndustryRoiEngine()
        self.service_roi = service_roi or ServiceRoiEngine()
        self.persona_roi = persona_roi or PersonaRoiEngine()
        self.trigger_roi = trigger_roi or TriggerRoiEngine()
        self.deal_tracker = deal_tracker or DealTracker()

    def get_calibration_summary(self) -> dict[str, Any]:
        return {
            "connector_ranking": [
                {"connector": c.connector, "revenue": c.revenue, "meetings": c.meetings}
                for c in self.connector_roi.rank_by_revenue()
            ],
            "industry_ranking": [
                {"industry": i.industry, "revenue": i.revenue, "win_rate": i.win_rate}
                for i in self.industry_roi.rank_by_revenue()
            ],
            "service_ranking": [
                {"service": s.service, "revenue": s.revenue, "win_rate": s.win_rate}
                for s in self.service_roi.rank_by_revenue()
            ],
            "persona_ranking": [
                {"persona": p.persona, "revenue": p.revenue, "reply_rate": p.reply_rate}
                for p in self.persona_roi.rank_by_revenue()
            ],
            "trigger_ranking": [
                {"trigger": t.trigger, "revenue": t.revenue, "conversion_rate": t.revenue_rate}
                for t in self.trigger_roi.rank_by_revenue()
            ],
            "total_revenue": self.deal_tracker.get_total_revenue(),
            "win_rate": self.deal_tracker.get_win_rate(),
            "avg_deal_size": self.deal_tracker.get_avg_deal_size(),
        }

    def get_connector_calibration(self) -> list[dict[str, Any]]:
        return [
            {
                "connector": c.connector,
                "signals": c.signals,
                "revenue_ready": c.revenue_ready,
                "replies": c.replies,
                "meetings": c.meetings,
                "deals": c.deals,
                "revenue": c.revenue,
                "reply_rate": c.reply_rate,
                "meeting_rate": c.meeting_rate,
                "win_rate": c.win_rate,
            }
            for c in self.connector_roi.rank_by_revenue()
        ]

    def get_industry_calibration(self) -> list[dict[str, Any]]:
        return [
            {
                "industry": i.industry,
                "companies": i.companies,
                "revenue_ready": i.revenue_ready,
                "replies": i.replies,
                "meetings": i.meetings,
                "deals": i.deals,
                "revenue": i.revenue,
                "reply_rate": i.reply_rate,
                "meeting_rate": i.meeting_rate,
                "win_rate": i.win_rate,
            }
            for i in self.industry_roi.rank_by_revenue()
        ]

    def get_service_calibration(self) -> list[dict[str, Any]]:
        return [
            {
                "service": s.service,
                "companies": s.companies,
                "replies": s.replies,
                "meetings": s.meetings,
                "deals": s.deals,
                "revenue": s.revenue,
                "reply_rate": s.reply_rate,
                "meeting_rate": s.meeting_rate,
                "win_rate": s.win_rate,
            }
            for s in self.service_roi.rank_by_revenue()
        ]

    def get_persona_calibration(self) -> list[dict[str, Any]]:
        return [
            {
                "persona": p.persona,
                "contacted": p.contacted,
                "replies": p.replies,
                "meetings": p.meetings,
                "revenue": p.revenue,
                "reply_rate": p.reply_rate,
                "meeting_rate": p.meeting_rate,
            }
            for p in self.persona_roi.rank_by_revenue()
        ]

    def get_trigger_calibration(self) -> list[dict[str, Any]]:
        return [
            {
                "trigger": t.trigger,
                "companies": t.companies,
                "replies": t.replies,
                "meetings": t.meetings,
                "revenue": t.revenue,
                "reply_rate": t.reply_rate,
                "meeting_rate": t.meeting_rate,
                "revenue_rate": t.revenue_rate,
            }
            for t in self.trigger_roi.rank_by_revenue()
        ]
