from __future__ import annotations

from founder_os.assistant.engine import FounderAssistantEngine
from founder_os.brief.engine import DailyBriefEngine
from founder_os.command.center import CommandCenterBuilder
from founder_os.kpi.engine import SalesKPIEngine
from founder_os.meetings.intelligence import MeetingIntelligenceEngine
from founder_os.models.types import FounderOsDecision, FounderOsInput, SCORING_VERSION
from founder_os.proposals.queue import ProposalQueueEngine
from founder_os.recommendations.engine import FounderRecommendationEngine
from founder_os.tasks.engine import RevenueTaskEngine
from founder_os.timeline.engine import RevenueTimelineEngine


class FounderOsPipeline:
    """Compose existing Beacon signals into the Founder Revenue OS morning pack."""

    def __init__(self) -> None:
        self.brief = DailyBriefEngine()
        self.assistant = FounderAssistantEngine()
        self.tasks = RevenueTaskEngine()
        self.timeline = RevenueTimelineEngine()
        self.kpis = SalesKPIEngine()
        self.recommendations = FounderRecommendationEngine()
        self.proposals = ProposalQueueEngine()
        self.meetings = MeetingIntelligenceEngine()
        self.command = CommandCenterBuilder()

    def process(self, data: FounderOsInput) -> FounderOsDecision:
        brief = self.brief.generate(data)
        kpis = self.kpis.calculate(data)
        tasks = self.tasks.generate(data)
        proposals = self.proposals.build(data)
        meeting_packs = self.meetings.generate(data)
        assistant = self.assistant.brief(data)
        recommendations = self.recommendations.generate(data, kpis)
        timeline_events = self.timeline.build_events(data)
        command_center = self.command.build(data, tasks=tasks, proposals=proposals)
        return FounderOsDecision(
            brief=brief,
            command_center=command_center,
            assistant=assistant,
            tasks=tasks,
            timeline_events=timeline_events,
            kpis=kpis,
            recommendations=recommendations,
            proposals=proposals,
            meeting_packs=meeting_packs,
            scoring_version=SCORING_VERSION,
        )
