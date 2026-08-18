from fastapi import APIRouter

from app.api.routes.acquisition import router as acquisition_router
from app.api.routes.account_intelligence import router as account_intelligence_router
from app.api.routes.account_journey import router as account_journey_router
from app.api.routes.autonomous_sales_agent import router as autonomous_sales_agent_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.client_execution import router as client_execution_router
from app.api.routes.communication import router as communication_router
from app.api.routes.cybersecurity import router as cybersecurity_router
from app.api.routes.context import router as context_router
from app.api.routes.copilot import router as copilot_router
from app.api.routes.decision import router as decision_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.enrichment import router as enrichment_router
from app.api.routes.enrichment_csv import router as enrichment_csv_router
from app.api.routes.lead_engine import router as lead_engine_router
from app.api.routes.founder_os import router as founder_os_router
from app.api.routes.global_opportunity_acquisition import router as global_opportunity_acquisition_router
from app.api.routes.health import router as health_router
from app.api.routes.improvement import router as improvement_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.live_revenue import router as live_revenue_router
from app.api.routes.live_opportunity_discovery import router as live_opportunity_discovery_router
from app.api.routes.opportunity import router as opportunity_router
from app.api.routes.operations import router as operations_router
from app.api.routes.operations_center import router as operations_center_router
from app.api.routes.outcomes import router as outcomes_router
from app.api.routes.production_hardening import router as production_hardening_router
from app.api.routes.production_validation import router as production_validation_router
from app.api.routes.quality import router as quality_router
from app.api.routes.revenue import router as revenue_router
from app.api.routes.revenue_hunter import router as revenue_hunter_router
from app.api.routes.revenue_operations import router as revenue_operations_router
from app.api.routes.revenue_optimization import router as revenue_optimization_router
from app.api.routes.revenue_readiness_validation import router as revenue_readiness_validation_router
from app.api.routes.revenue_data_recovery import router as revenue_data_recovery_router
from app.api.routes.revenue_quality_recovery import router as revenue_quality_recovery_router
from app.api.routes.beacon_alpha import router as beacon_alpha_router
from app.api.routes.ground_truth import router as ground_truth_router
from app.api.routes.company_resolution import router as company_resolution_router
from app.api.routes.entity_resolution import router as entity_resolution_router
from app.api.routes.identity_graph import router as identity_graph_router
from app.api.routes.identity_coverage import router as identity_coverage_router
from app.api.routes.revenue_data_acquisition import router as revenue_data_acquisition_router
from app.api.routes.revenue_readiness_perfection import router as revenue_readiness_perfection_router
from app.api.routes.operation_first_customer import router as operation_first_customer_router
from app.api.routes.revenue_validation import router as revenue_validation_router
from app.api.routes.execution import router as execution_router
from app.api.routes.opportunity_intelligence import router as opportunity_intelligence_router
from app.api.routes.intelligence_center import build_routers as build_intelligence_center_routers
from app.api.routes.lead_explorer import router as lead_explorer_router
from app.api.routes.company_intelligence import router as company_intelligence_router
from app.api.routes.revenue_execution_validation import router as revenue_execution_validation_router
from app.api.routes.sales_readiness import router as sales_readiness_router
from app.api.routes.sales_intelligence import router as sales_intelligence_router
from app.api.routes.source_health import router as source_health_router
from app.api.routes.targets import router as targets_router
from app.api.routes.verification import router as verification_router
from app.api.routes.opportunity_connector import router as opportunity_connector_router
from app.api.routes.validation_engine import router as validation_engine_router
from app.api.routes.version import router as version_router
from app.api.routes.ecommerce_leads import router as ecommerce_leads_router
from app.api.routes.revenue_intelligence import router as revenue_intelligence_router
from app.api.routes.sales_account import router as sales_account_router
from app.api.routes.founder_sales_workspace import router as fsw_router
from app.api.routes.arie import router as arie_router
from app.api.routes.dsip import router as dsip_router
from app.api.routes.ricvp import router as ricvp_router
from app.api.routes.rdrp import router as rdrp_router
from app.api.routes.lead_discovery import router as lead_discovery_router
from app.api.routes.intelligence_loop import router as intelligence_loop_router
from app.api.routes.company_universe import router as company_universe_router
from app.api.routes.buying_events_api import router as buying_events_router
from app.api.routes.workspace_hub import router as workspace_hub_router
from app.api.routes.unified_leads import router as unified_leads_router
from app.api.routes.comai_b2b_partners import router as comai_b2b_partners_router

from app.api.routes.discovery_quality_engine.v2 import router as dqe_v2_router
from app.api.routes.opportunity_validation import validation_router as lovp_router
from app.api.routes.live_revenue_operations import operations_router as lrop_router
from app.api.routes.beacon_observatory.observatory import router as bolr_router
from app.api.routes.partner_leads import router as partner_leads_router

router = APIRouter()
router.include_router(acquisition_router)
router.include_router(account_intelligence_router)
router.include_router(account_journey_router)
router.include_router(autonomous_sales_agent_router)
router.include_router(client_execution_router)
router.include_router(campaigns_router)
router.include_router(communication_router)
router.include_router(cybersecurity_router)
router.include_router(context_router)
router.include_router(copilot_router)
router.include_router(decision_router)
router.include_router(diagnostics_router)
router.include_router(enrichment_router)
router.include_router(enrichment_csv_router)
router.include_router(lead_engine_router)
router.include_router(founder_os_router)
router.include_router(global_opportunity_acquisition_router)
router.include_router(health_router)
router.include_router(improvement_router)
router.include_router(intelligence_router)
router.include_router(live_revenue_router)
router.include_router(live_opportunity_discovery_router)
router.include_router(opportunity_intelligence_router)
router.include_router(opportunity_router)
router.include_router(operations_center_router)
router.include_router(operations_router)
router.include_router(outcomes_router)
router.include_router(production_hardening_router)
router.include_router(production_validation_router)
router.include_router(quality_router)
router.include_router(revenue_router)
router.include_router(revenue_hunter_router)
router.include_router(revenue_operations_router)
router.include_router(revenue_optimization_router)
router.include_router(revenue_readiness_validation_router)
router.include_router(revenue_data_recovery_router)
router.include_router(revenue_quality_recovery_router)
router.include_router(beacon_alpha_router)
router.include_router(ground_truth_router)
router.include_router(company_resolution_router)
router.include_router(entity_resolution_router)
router.include_router(identity_graph_router)
router.include_router(identity_coverage_router)
router.include_router(revenue_data_acquisition_router)
router.include_router(revenue_readiness_perfection_router)
router.include_router(operation_first_customer_router)
router.include_router(revenue_validation_router)
router.include_router(execution_router)
for _bic_router in build_intelligence_center_routers():
    router.include_router(_bic_router)
router.include_router(lead_explorer_router)
router.include_router(company_intelligence_router)
router.include_router(revenue_execution_validation_router)
router.include_router(sales_readiness_router)
router.include_router(sales_intelligence_router)
router.include_router(source_health_router)
router.include_router(targets_router)
router.include_router(verification_router)
router.include_router(opportunity_connector_router)
router.include_router(validation_engine_router)
router.include_router(fsw_router)
router.include_router(version_router)
router.include_router(ecommerce_leads_router)
router.include_router(revenue_intelligence_router)
router.include_router(sales_account_router)
router.include_router(arie_router)
router.include_router(dsip_router)
router.include_router(ricvp_router)
router.include_router(rdrp_router)
router.include_router(lead_discovery_router)
router.include_router(intelligence_loop_router)
router.include_router(company_universe_router)
router.include_router(buying_events_router)
router.include_router(workspace_hub_router)
router.include_router(unified_leads_router)
router.include_router(comai_b2b_partners_router)
router.include_router(dqe_v2_router)
router.include_router(lovp_router)
router.include_router(lrop_router)
router.include_router(bolr_router)
router.include_router(partner_leads_router)

__all__ = ["router"]
