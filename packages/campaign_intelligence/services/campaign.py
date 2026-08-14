from campaign_intelligence.approval.workflow import ApprovalWorkflow
from campaign_intelligence.models.types import CampaignInput, CampaignPlan, CampaignStatus
from campaign_intelligence.planner.campaign_planner import CampaignPlanner


class CampaignIntelligenceService:
    def __init__(
        self,
        planner: CampaignPlanner | None = None,
        workflow: ApprovalWorkflow | None = None,
    ) -> None:
        self.planner = planner or CampaignPlanner()
        self.workflow = workflow or ApprovalWorkflow()

    def create_plan(self, item: CampaignInput) -> CampaignPlan:
        return self.planner.plan(item)

    def approve(self, plan: CampaignPlan) -> CampaignPlan:
        # Approval marks execution-ready planning only — no provider send.
        status = self.workflow.approve(plan.status)
        return plan.model_copy(update={"status": status})

    def pause(self, plan: CampaignPlan) -> CampaignPlan:
        return plan.model_copy(update={"status": self.workflow.pause(plan.status)})

    def cancel(self, plan: CampaignPlan) -> CampaignPlan:
        return plan.model_copy(update={"status": self.workflow.cancel(plan.status)})

    def mark_needs_review(self, plan: CampaignPlan) -> CampaignPlan:
        return plan.model_copy(update={"status": CampaignStatus.NEEDS_REVIEW})
