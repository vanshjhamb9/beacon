from __future__ import annotations

from production_validation.alerts.engine import AlertEngine
from production_validation.audit.security import SecurityAuditEngine
from production_validation.diagnostics.freshness import FreshnessEngine
from production_validation.health.engine import HealthEngine
from production_validation.metrics.engine import OutcomeLearningEngine, RevenueMetricsEngine
from production_validation.models.types import ProductionValidationDecision, ProductionValidationInput, SCORING_VERSION
from production_validation.reporting.founder import FounderExperienceEngine
from production_validation.reporting.playbooks import PlaybookEngine
from production_validation.reporting.readiness import ReadinessReportEngine
from production_validation.reporting.weekly import WeeklyReportEngine
from production_validation.validators.engine import CampaignFunnelValidator, LeadQualityValidator


class ProductionValidationPipeline:
    def __init__(self) -> None:
        self.health = HealthEngine()
        self.lead = LeadQualityValidator()
        self.funnels = CampaignFunnelValidator()
        self.freshness = FreshnessEngine()
        self.alerts = AlertEngine()
        self.revenue = RevenueMetricsEngine()
        self.learning = OutcomeLearningEngine()
        self.playbooks = PlaybookEngine()
        self.weekly = WeeklyReportEngine()
        self.security = SecurityAuditEngine()
        self.readiness = ReadinessReportEngine()
        self.founder = FounderExperienceEngine()

    def process(self, item: ProductionValidationInput) -> ProductionValidationDecision:
        health = self.health.evaluate(item)
        lead = self.lead.score(item) if item.company_id is not None else None
        funnels = self.funnels.snapshots(item)
        freshness = self.freshness.evaluate(item)
        alerts = self.alerts.detect(item, health=health, lead=lead)
        revenue = self.revenue.snapshot(item)
        learning = self.learning.snapshot(item)
        playbooks = self.playbooks.all()
        weekly = self.weekly.generate(item, revenue)
        security = self.security.audit(item)
        readiness = self.readiness.build(health=health, revenue=revenue, security=security)
        founder = self.founder.build(item)
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"health:{health.overall_score}",
            f"readiness:{readiness.overall_score}",
            f"alerts:{len(alerts)}",
            f"outreach_allowed:{lead.outreach_allowed if lead else 'n/a'}",
        ]
        return ProductionValidationDecision(
            health=health,
            campaign_funnels=funnels,
            lead_readiness=lead,
            freshness=freshness,
            alerts=alerts,
            revenue=revenue,
            outcome_learning=learning,
            playbooks=playbooks,
            weekly_report=weekly,
            security_audit=security,
            readiness_report=readiness,
            founder_board=founder,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
        )
