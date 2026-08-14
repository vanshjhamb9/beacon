from __future__ import annotations

from datetime import UTC, datetime

from revenue_operations.agents.orchestrator import MultiAgentOrchestrator
from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.analytics.control_tower import RevenueControlTowerEngine
from revenue_operations.analytics.learning import LearningLabEngine
from revenue_operations.analytics.metrics import OperationalMetricsEngine
from revenue_operations.analytics.radar import RevenueRadarEngine
from revenue_operations.analytics.replay import RevenueReplayEngine
from revenue_operations.dashboard.assistant import FounderAssistantV2Engine
from revenue_operations.dashboard.command_center import CommandCenterEngine
from revenue_operations.forecasting.engine import RevenueForecastEngine
from revenue_operations.forecasting.win_loss import WinLossAnalyticsEngine
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import SCORING_VERSION, RevenueOperationsDecision, RevenueOperationsInput


class RevenueOperationsPipeline:
    """Compose-only Revenue Operations Center — deterministic, no GPT."""

    def __init__(self) -> None:
        self.tower = RevenueControlTowerEngine()
        self.radar = RevenueRadarEngine()
        self.alerts = SmartAlertEngine()
        self.agents = MultiAgentOrchestrator()
        self.memory = AgencyMemoryEngine()
        self.win_loss = WinLossAnalyticsEngine()
        self.forecast = RevenueForecastEngine()
        self.assistant = FounderAssistantV2Engine()
        self.replay = RevenueReplayEngine()
        self.learning = LearningLabEngine()
        self.command = CommandCenterEngine()
        self.metrics = OperationalMetricsEngine()

    def process(self, item: RevenueOperationsInput) -> RevenueOperationsDecision:
        tower = self.tower.build(item)
        radar = self.radar.scan(item)
        alerts = self.alerts.detect(item, radar=radar)
        agent_runs = self.agents.run(item)
        memory = self.memory.build(item)
        win_loss = self.win_loss.analyze(item)
        forecast = self.forecast.forecast(item)
        assistant = self.assistant.generate(item, tower=tower, forecast=forecast)
        replays = self.replay.build(item)
        learning = self.learning.analyze(item, win_loss=win_loss)
        command = self.command.build(item, tower=tower, forecast=forecast, assistant=assistant, learning=learning)
        metrics = self.metrics.compute(item)
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"opps:{len(item.opportunities)}",
            f"alerts:{len(alerts)}",
            f"radar:{len(radar)}",
            f"pipeline:{tower.pipeline_value}",
            f"forecast_week:{forecast.this_week.amount}",
            f"revenue_score:{command.revenue_score}",
            "compose_only:true",
            "no_gpt:true",
        ]
        return RevenueOperationsDecision(
            control_tower=tower,
            radar_signals=radar,
            alerts=alerts,
            agent_runs=agent_runs,
            memory_records=memory,
            win_loss=win_loss,
            forecast=forecast,
            founder_assistant=assistant,
            replays=replays,
            learning=learning,
            command_center=command,
            operational_metrics=metrics,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
            evaluated_at=item.now or datetime.now(UTC),
        )
